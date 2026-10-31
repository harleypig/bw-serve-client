#!/usr/bin/env python3

"""Report whether Bitwarden changed anything this library depends on.

Fetches every upstream source, compares it with what ``upstream/lock.json``
recorded, writes the raw snapshots and the lock file, and writes a Markdown
change report. It never commits.

Sources:

- The OpenAPI spec embedded in the Vault Management API help page.
- The latest ``cli-v*`` release of bitwarden/clients.
- The commits of the two files that register the ``bw serve`` routes, as of
  that release, and the method and path of every route they register.
- The state of the GitHub issues and pull requests, and the version of the
  PyPI packages, listed in ``upstream/watch.json``.

Exit codes:

- 0: nothing changed, and every fix still matches.
- 1: error. A fetch failed or returned something unusable; nothing but the
  report was written.
- 2: work to do. A source changed (snapshots, lock file and report are
  updated), or a fix in ``spec-fixes.json`` no longer matches the raw spec.

Set ``GITHUB_TOKEN`` to raise the GitHub API rate limit; it is optional.
"""

import argparse
from dataclasses import dataclass
from dataclasses import field
import datetime
import hashlib
import html
import json
import os
from pathlib import Path
import re
import sys
from typing import Any, Callable, Dict, List, Optional, Tuple

import requests

HELP_PAGE_URL = "https://bitwarden.com/help/vault-management-api/"
GITHUB_API = "https://api.github.com"
GITHUB_RAW = "https://raw.githubusercontent.com"
PYPI_URL = "https://pypi.org/pypi/{package}/json"
CLIENTS_REPO = "bitwarden/clients"
CLI_TAG_PREFIX = "cli-v"
TIMEOUT = 30

# Short names keep the snapshot readable; the paths are what upstream uses.
CONFIGURATORS = {
  "oss": "apps/cli/src/oss-serve-configurator.ts",
  "bit": "bitwarden_license/bit-cli/src/bit-serve-configurator.ts",
}

HTTP_METHODS = ("get", "put", "post", "delete", "options", "head", "patch", "trace")

UPSTREAM_DIR = Path(__file__).resolve().parent
SPEC_SNAPSHOT = UPSTREAM_DIR / "vault-management-api-original.json"
ROUTES_SNAPSHOT = UPSTREAM_DIR / "serve-routes.txt"
LOCK_FILE = UPSTREAM_DIR / "lock.json"
WATCH_FILE = UPSTREAM_DIR / "watch.json"
FIXES_FILE = UPSTREAM_DIR / "spec-fixes.json"
PATCHED_SPEC = UPSTREAM_DIR / "vault-management-api-fixed.json"
REPORT_FILE = UPSTREAM_DIR / "change-report.md"

ROUTE_RE = re.compile(r"""router\.(get|post|put|delete|patch)\(\s*["'`]([^"'`]+)["'`]""")
ROUTE_PARAM_RE = re.compile(r":([A-Za-z_][A-Za-z0-9_]*)")
DATA_PAGE_SCRIPT_RE = re.compile(r'<script[^>]*\bdata-page="app"[^>]*>(.*?)</script>', re.DOTALL)
DATA_PAGE_ATTR_RE = re.compile(r'data-page="(\{[^"]*)"')
WATCHED_ITEM_RE = re.compile(r"^([\w.-]+/[\w.-]+)#(\d+)$")

_MISSING = object()


class FetchError(Exception):
  """An upstream source could not be fetched, or returned something unusable."""


@dataclass
class Upstream:
  """Everything fetched from upstream in one run.

  Attributes:
      spec: The raw OpenAPI spec.
      cli_release: The newest ``cli-v*`` release tag.
      configurator_commits: Each configurator's path, mapped to its commit.
      routes: The sorted ``METHOD /path  name`` route lines.
      watched: Each watched GitHub item, mapped to its state.
      packages: Each watched PyPI package, mapped to its version.
  """

  spec: Dict[str, Any]
  cli_release: str
  configurator_commits: Dict[str, str]
  routes: List[str]
  watched: Dict[str, str]
  packages: Dict[str, str]


@dataclass
class Changes:
  """What differs between the recorded state and the fetched one.

  Attributes:
      sources: ``(source, was, now)`` for each lock entry that changed.
      spec: The spec's route, parameter and schema changes.
      routes: The route lines added and removed.
      watched: The watched items and packages that changed.
      stale_fixes: The fixes that no longer match the raw spec.
      changed: Whether any recorded source changed, or the lock file is new.
  """

  sources: List[Tuple[str, str, str]] = field(default_factory=list)
  spec: List[str] = field(default_factory=list)
  routes: List[str] = field(default_factory=list)
  watched: List[str] = field(default_factory=list)
  stale_fixes: List[str] = field(default_factory=list)

  @property
  def changed(self: "Changes") -> bool:
    """Whether any recorded source changed, or the lock file is new."""
    return bool(self.sources)


###############################################################################
# Fetching


# -----------------------------------------------------------------------------
def http_get(session: requests.Session, url: str, headers: Optional[Dict[str, str]] = None) -> requests.Response:
  """GET a URL, turning any failure into a FetchError.

  Arguments:
      session: The HTTP session to fetch with.
      url: The URL to fetch.
      headers: Extra request headers, if any.

  Raises:
      FetchError: On a network error or a non-200 status.

  Returns:
      requests.Response: The successful response.
  """
  try:
    response = session.get(url, headers=headers, timeout=TIMEOUT)

  except requests.RequestException as exc:
    raise FetchError(f"GET {url} failed: {exc}") from exc

  if response.status_code != 200:
    raise FetchError(f"GET {url} returned HTTP {response.status_code}")

  return response


# -----------------------------------------------------------------------------
def github_headers() -> Dict[str, str]:
  """Headers for the GitHub API, with a token when one is set.

  Returns:
      Dict[str, str]: The request headers.
  """
  headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}

  token = os.environ.get("GITHUB_TOKEN")
  if token:
    headers["Authorization"] = f"Bearer {token}"

  return headers


# -----------------------------------------------------------------------------
def github_json(session: requests.Session, path: str) -> Any:
  """GET a GitHub API path and decode the JSON body.

  Arguments:
      session: The HTTP session to fetch with.
      path: The API path, starting with ``/``, including any query string.

  Raises:
      FetchError: When the request fails or the body is not JSON.

  Returns:
      Any: The decoded body.
  """
  response = http_get(session, f"{GITHUB_API}{path}", github_headers())

  try:
    return response.json()

  except ValueError as exc:
    raise FetchError(f"GitHub {path} returned a body that is not JSON") from exc


# -----------------------------------------------------------------------------
def extract_spec(page: str) -> Dict[str, Any]:
  """Pull the OpenAPI spec out of the help page's HTML.

  The page renders client-side; the spec arrives as Inertia page data, at
  ``props.swaggerData.fields.body``. Bitwarden serves both of Inertia's
  forms: a ``<script data-page="app">`` JSON element, and the older
  HTML-escaped ``data-page`` attribute on the root element.

  Arguments:
      page: The help page's HTML.

  Raises:
      FetchError: When the page data, the path or a usable spec is missing.

  Returns:
      Dict[str, Any]: The spec.
  """
  script = DATA_PAGE_SCRIPT_RE.search(page)
  attribute = DATA_PAGE_ATTR_RE.search(page)

  if script:
    raw = script.group(1)

  elif attribute:
    raw = html.unescape(attribute.group(1))

  else:
    raise FetchError("help page has no Inertia page data (no data-page script or attribute)")

  try:
    body = json.loads(raw)["props"]["swaggerData"]["fields"]["body"]

  except (ValueError, KeyError, TypeError) as exc:
    raise FetchError(f"help page data-page has no spec at props.swaggerData.fields.body ({exc!r})") from exc

  # Older page builds carried the spec as a JSON string rather than an object.
  if isinstance(body, str):
    try:
      body = json.loads(body)

    except ValueError as exc:
      raise FetchError("help page spec body is a string that is not JSON") from exc

  if not isinstance(body, dict) or "openapi" not in body or not isinstance(body.get("paths"), dict):
    raise FetchError("help page spec body is not an OpenAPI document")

  return body


# -----------------------------------------------------------------------------
def fetch_spec(session: requests.Session) -> Dict[str, Any]:
  """Fetch the spec from the help page.

  Arguments:
      session: The HTTP session to fetch with.

  Returns:
      Dict[str, Any]: The spec.
  """
  return extract_spec(http_get(session, HELP_PAGE_URL).text)


# -----------------------------------------------------------------------------
def fetch_cli_release(session: requests.Session) -> str:
  """Find the highest published ``cli-v*`` release tag.

  The API lists releases newest first by creation date, so a hotfix cut
  for an older line would sort ahead of the current one; the version
  decides instead.

  Arguments:
      session: The HTTP session to fetch with.

  Raises:
      FetchError: When no CLI release is among the newest hundred.

  Returns:
      str: The tag name.
  """
  releases = github_json(session, f"/repos/{CLIENTS_REPO}/releases?per_page=100")

  versions = {}
  for release in releases:
    tag = release["tag_name"]
    version = tag[len(CLI_TAG_PREFIX):].split(".")
    published = not release["draft"] and not release["prerelease"]
    if published and tag.startswith(CLI_TAG_PREFIX) and all(part.isdigit() for part in version):
      versions[tag] = tuple(int(part) for part in version)

  if versions:
    return max(versions, key=lambda tag: versions[tag])

  raise FetchError(f"no {CLI_TAG_PREFIX}* release among the newest {len(releases)} releases of {CLIENTS_REPO}")


# -----------------------------------------------------------------------------
def fetch_file_commit(session: requests.Session, path: str, ref: str) -> str:
  """Find the last commit that touched a file, as of a ref.

  Arguments:
      session: The HTTP session to fetch with.
      path: The file's path in bitwarden/clients.
      ref: The tag, branch or commit to look back from.

  Raises:
      FetchError: When no commit touched the file.

  Returns:
      str: The commit SHA.
  """
  commits = github_json(session, f"/repos/{CLIENTS_REPO}/commits?path={path}&sha={ref}&per_page=1")

  if not commits:
    raise FetchError(f"no commit touches {path} as of {ref}")

  return commits[0]["sha"]


# -----------------------------------------------------------------------------
def extract_routes(source: str) -> List[str]:
  """List the routes a configurator file registers.

  Koa's ``:name`` path parameters are rewritten as ``{name}``, the form
  the spec uses. Parameter names can still differ from the spec's
  (``requestId`` against ``request-id``).

  Arguments:
      source: The configurator's TypeScript source.

  Returns:
      List[str]: ``METHOD /path`` strings, in file order.
  """
  # A backslash inside an f-string expression is a syntax error before 3.12.
  return [f"{method.upper()} {ROUTE_PARAM_RE.sub(_brace_param, path)}" for method, path in ROUTE_RE.findall(source)]


# -----------------------------------------------------------------------------
def _brace_param(match: "re.Match[str]") -> str:
  """Rewrite one ``:name`` match as ``{name}``.

  Arguments:
      match: A ``ROUTE_PARAM_RE`` match.
  """
  return f"{{{match.group(1)}}}"


# -----------------------------------------------------------------------------
def fetch_routes(session: requests.Session, release: str) -> Tuple[Dict[str, str], List[str]]:
  """Fetch the configurators as of a release and extract their routes.

  Arguments:
      session: The HTTP session to fetch with.
      release: The CLI release tag to read the configurators at.

  Raises:
      FetchError: When a configurator registers no routes, which means the
          file moved or its syntax changed.

  Returns:
      Tuple[Dict[str, str], List[str]]: The commit of each configurator, and
      the sorted ``METHOD /path  name`` route lines.
  """
  commits: Dict[str, str] = {}
  routes: List[str] = []

  for name, path in CONFIGURATORS.items():
    commit = fetch_file_commit(session, path, release)
    commits[path] = commit

    found = extract_routes(http_get(session, f"{GITHUB_RAW}/{CLIENTS_REPO}/{commit}/{path}").text)
    if not found:
      raise FetchError(f"{path} at {commit} registers no routes; the route pattern no longer matches")

    routes.extend(f"{route}  {name}" for route in found)

  return commits, sorted(routes, key=lambda line: (line.split()[1], line))


# -----------------------------------------------------------------------------
def fetch_watched_item(session: requests.Session, item: str) -> str:
  """Read the state of a GitHub issue or pull request.

  Arguments:
      session: The HTTP session to fetch with.
      item: The item, as ``owner/repo#number``.

  Raises:
      FetchError: When the item is not ``owner/repo#number``.

  Returns:
      str: ``open``, ``closed``, ``closed (not planned)`` or ``merged``.
  """
  match = WATCHED_ITEM_RE.match(item)
  if not match:
    raise FetchError(f"watched item {item!r} is not owner/repo#number")

  issue = github_json(session, f"/repos/{match.group(1)}/issues/{match.group(2)}")

  if (issue.get("pull_request") or {}).get("merged_at"):
    return "merged"

  if issue["state"] == "closed" and issue.get("state_reason") == "not_planned":
    return "closed (not planned)"

  return issue["state"]


# -----------------------------------------------------------------------------
def fetch_package_version(session: requests.Session, package: str) -> str:
  """Read the latest version of a PyPI package.

  Arguments:
      session: The HTTP session to fetch with.
      package: The PyPI package name.

  Raises:
      FetchError: When the response has no version.

  Returns:
      str: The version.
  """
  try:
    return http_get(session, PYPI_URL.format(package=package)).json()["info"]["version"]

  except (ValueError, KeyError, TypeError) as exc:
    raise FetchError(f"PyPI has no version for {package}") from exc


# -----------------------------------------------------------------------------
def fetch_all(session: requests.Session, watch: Dict[str, List[str]]) -> Upstream:
  """Fetch every source, collecting every failure before giving up.

  Arguments:
      session: The HTTP session to fetch with.
      watch: The parsed ``watch.json``: ``github`` items and ``pypi`` packages.

  Raises:
      FetchError: Listing every source that failed.

  Returns:
      Upstream: Everything fetched.
  """
  errors: List[str] = []

  def attempt(fetch: Callable[[], Any], default: Any) -> Any:
    try:
      return fetch()

    except FetchError as exc:
      errors.append(str(exc))

    # A response of an unexpected shape fails on a lookup, not a fetch.
    except (KeyError, IndexError, TypeError, AttributeError, ValueError) as exc:
      errors.append(f"unexpected response shape: {exc!r}")

    return default

  spec = attempt(lambda: fetch_spec(session), {})
  release = attempt(lambda: fetch_cli_release(session), "")
  commits, routes = attempt(lambda: fetch_routes(session, release), ({}, [])) if release else ({}, [])
  watched = {item: attempt(lambda item=item: fetch_watched_item(session, item), "") for item in watch.get("github", [])}
  packages = {name: attempt(lambda name=name: fetch_package_version(session, name), "") for name in watch.get("pypi", [])}

  if errors:
    raise FetchError("\n".join(errors))

  return Upstream(spec, release, commits, routes, watched, packages)


###############################################################################
# Comparing


# -----------------------------------------------------------------------------
def canonical_sha256(data: Any) -> str:
  """Checksum JSON content, independent of key order and whitespace.

  Arguments:
      data: Any JSON-serialisable value.

  Returns:
      str: The hex SHA-256.
  """
  text = json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
  return hashlib.sha256(text.encode("utf-8")).hexdigest()


# -----------------------------------------------------------------------------
def operations(spec: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
  """Index a spec's operations by ``METHOD /path``.

  Arguments:
      spec: An OpenAPI spec.

  Returns:
      Dict[str, Dict[str, Any]]: Each operation object.
  """
  found: Dict[str, Dict[str, Any]] = {}

  for path, item in spec.get("paths", {}).items():
    for method, operation in item.items():
      if method in HTTP_METHODS:
        found[f"{method.upper()} {path}"] = operation

  return found


# -----------------------------------------------------------------------------
def _added_removed(old: Any, new: Any) -> Tuple[List[str], List[str]]:
  """Sorted keys only in ``new``, and only in ``old``.

  Arguments:
      old: The old keys, or a mapping whose keys are compared.
      new: The new keys, or a mapping whose keys are compared.
  """
  return sorted(set(new) - set(old)), sorted(set(old) - set(new))


# -----------------------------------------------------------------------------
def diff_operation(name: str, old: Dict[str, Any], new: Dict[str, Any]) -> List[str]:
  """Describe how one operation changed.

  Arguments:
      name: The operation, as ``METHOD /path``, for the messages.
      old: The recorded operation object.
      new: The fetched operation object.

  Returns:
      List[str]: One line per change.
  """
  lines: List[str] = []

  def params(operation: Dict[str, Any]) -> Dict[str, Any]:
    return {f"{p.get('in')} {p.get('name')}": p for p in operation.get("parameters", [])}

  old_params, new_params = params(old), params(new)
  added, removed = _added_removed(old_params, new_params)

  lines.extend(f"`{name}`: parameter added: {p}" for p in added)
  lines.extend(f"`{name}`: parameter removed: {p}" for p in removed)
  lines.extend(
    f"`{name}`: parameter changed: {p}" for p in sorted(set(old_params) & set(new_params)) if old_params[p] != new_params[p]
  )

  for part in ("requestBody", "responses"):
    if old.get(part) != new.get(part):
      lines.append(f"`{name}`: {part} changed")

  return lines


# -----------------------------------------------------------------------------
def diff_schema(name: str, old: Dict[str, Any], new: Dict[str, Any]) -> List[str]:
  """Describe how one component schema changed.

  Arguments:
      name: The schema's name, for the messages.
      old: The recorded schema.
      new: The fetched schema.

  Returns:
      List[str]: One line per change.
  """
  old_props, new_props = old.get("properties", {}), new.get("properties", {})
  added, removed = _added_removed(old_props, new_props)

  lines = [f"`{name}`: property added: `{p}`" for p in added]
  lines.extend(f"`{name}`: property removed: `{p}`" for p in removed)
  lines.extend(
    f"`{name}`: property changed: `{p}`" for p in sorted(set(old_props) & set(new_props)) if old_props[p] != new_props[p]
  )

  rest_old = {k: v for k, v in old.items() if k != "properties"}
  rest_new = {k: v for k, v in new.items() if k != "properties"}
  if rest_old != rest_new:
    lines.append(f"`{name}`: changed outside its properties")

  return lines


# -----------------------------------------------------------------------------
def diff_spec(old: Dict[str, Any], new: Dict[str, Any]) -> List[str]:
  """Describe how the spec changed: routes, parameters and schemas.

  Arguments:
      old: The recorded raw spec.
      new: The fetched raw spec.

  Returns:
      List[str]: One line per change; empty when the specs are equal.
  """
  if old == new:
    return []

  old_ops, new_ops = operations(old), operations(new)
  added, removed = _added_removed(old_ops, new_ops)

  lines = [f"Route added: `{op}`" for op in added]
  lines.extend(f"Route removed: `{op}`" for op in removed)

  for op in sorted(set(old_ops) & set(new_ops)):
    lines.extend(diff_operation(op, old_ops[op], new_ops[op]))

  old_schemas = old.get("components", {}).get("schemas", {})
  new_schemas = new.get("components", {}).get("schemas", {})
  added, removed = _added_removed(old_schemas, new_schemas)

  lines.extend(f"Schema added: `{s}`" for s in added)
  lines.extend(f"Schema removed: `{s}`" for s in removed)

  for schema in sorted(set(old_schemas) & set(new_schemas)):
    lines.extend(diff_schema(schema, old_schemas[schema], new_schemas[schema]))

  if not lines:
    lines.append("Changed outside the routes and schemas (for example `info` or `servers`)")

  return lines


# -----------------------------------------------------------------------------
def resolve(spec: Any, parts: List[str]) -> Any:
  """Follow a fix path into a spec, the way the spec tool does.

  Arguments:
      spec: The spec to look in.
      parts: The fix path, split on ``|``.

  Returns:
      Any: The value, or ``_MISSING``.
  """
  current = spec

  for part in parts:
    if isinstance(current, list) and part.isdigit() and int(part) < len(current):
      current = current[int(part)]

    elif isinstance(current, dict) and part in current:
      current = current[part]

    else:
      return _MISSING

  return current


# -----------------------------------------------------------------------------
def _identity(element: Any) -> Any:
  """Name an array element the way the spec does, where it can be named.

  Arguments:
      element: An array element from a spec.

  Returns:
      Any: ``(in, name)`` for a parameter-like object, else None.
  """
  if isinstance(element, dict) and "name" in element:
    return (element.get("in"), element["name"])

  return None


# -----------------------------------------------------------------------------
def stale_fixes(fixes: List[Dict[str, Any]], patched: Dict[str, Any], new: Dict[str, Any]) -> List[str]:
  """List the fixes that no longer match the new raw spec.

  A fix is stale when what it targets is gone, when the value it records
  replacing is no longer there, when it addresses a named array element by
  position and a different element now sits there, or when it adds a value
  upstream now supplies itself. Each is judged against the current state,
  not against the previous run, so a stale fix is reported on every run
  until it is fixed.

  Arguments:
      fixes: The ``operations`` list from ``spec-fixes.json``.
      patched: The committed patched spec, which the fixes were last applied to; it shows which element each position meant.
      new: The fetched raw spec the fixes are checked against.

  Returns:
      List[str]: One line per stale fix.
  """
  lines: List[str] = []

  for fix in fixes:
    path = fix.get("path", "")
    kind = fix.get("type", "?")
    parts = path.split("|")
    target = parts if kind == "delete_value" else parts[:-1]

    if resolve(new, target) is _MISSING:
      lines.append(f"`{kind}` `{path}`: target not found")
      continue

    current = resolve(new, parts)
    if "old_value" in fix and current is not _MISSING and current not in (fix["old_value"], fix.get("value")):
      lines.append(f"`{kind}` `{path}`: upstream value is no longer the one this fix replaces")
      continue

    shifted = [
      i for i, part in enumerate(parts) if part.isdigit() and _identity(resolve(patched, parts[:i + 1])) is not None and
      _identity(resolve(patched, parts[:i + 1])) != _identity(resolve(new, parts[:i + 1]))
    ]
    if shifted:
      lines.append(f"`{kind}` `{path}`: addresses an array element by position, and a different element is there now")

    elif kind == "add_if_missing" and current is not _MISSING:
      lines.append(f"`{kind}` `{path}`: upstream now supplies this value")

  return lines


# -----------------------------------------------------------------------------
def build_lock(upstream: Upstream, previous: Dict[str, Any], today: str) -> Dict[str, Any]:
  """Build the new lock file content.

  ``fetched`` is the date the recorded content was first fetched, so it
  moves only when that content changes and an unchanged run rewrites the
  file byte for byte.

  Arguments:
      upstream: Everything fetched this run.
      previous: The lock file content from the last run, or ``{}``.
      today: Today's date, ISO formatted, for entries whose content changed.

  Returns:
      Dict[str, Any]: The lock file content.
  """

  def entry(section: str, key: Optional[str], content: Dict[str, Any]) -> Dict[str, Any]:
    old = previous.get(section, {})
    if key is not None:
      old = old.get(key, {})

    fetched = old.get("fetched") if {k: old.get(k) for k in content} == content else None
    return {**content, "fetched": fetched or today}

  return {
    "spec": entry("spec", None, {
      "source": HELP_PAGE_URL,
      "sha256": canonical_sha256(upstream.spec)
    }),
    "cli": entry("cli", None, {"release": upstream.cli_release}),
    "configurators": {
      path: entry("configurators", path, {"commit": commit})
      for path, commit in sorted(upstream.configurator_commits.items())
    },
    "serve_routes": entry("serve_routes", None, {"sha256": canonical_sha256(upstream.routes)}),
    "watched": {
      item: entry("watched", item, {"state": state})
      for item, state in sorted(upstream.watched.items())
    },
    "packages": {
      name: entry("packages", name, {"version": version})
      for name, version in sorted(upstream.packages.items())
    },
  }


# -----------------------------------------------------------------------------
def _flatten(lock: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
  """One entry per source, without the fetch date, keyed by a display name.

  Arguments:
      lock: Lock file content.
  """
  flat: Dict[str, Dict[str, Any]] = {}

  for section, value in lock.items():
    if "fetched" in value:
      flat[section] = {k: v for k, v in value.items() if k != "fetched"}

    else:
      for key, item in value.items():
        flat[f"{section} {key}"] = {k: v for k, v in item.items() if k != "fetched"}

  return flat


# -----------------------------------------------------------------------------
def _summary(content: Optional[Dict[str, Any]]) -> str:
  """Summarise one lock entry for the report table.

  Arguments:
      content: One flattened lock entry, or None when the source is absent.
  """
  if content is None:
    return "(none)"

  return ", ".join(f"{v[:12]}" if k in ("sha256", "commit") else str(v) for k, v in content.items() if k != "source")


# -----------------------------------------------------------------------------
def compare(
  previous_lock: Dict[str, Any], new_lock: Dict[str, Any], old_spec: Dict[str, Any], old_routes: List[str], upstream: Upstream,
  fixes: List[Dict[str, Any]], patched: Dict[str, Any]
) -> Changes:
  """Work out what changed between the recorded and the fetched state.

  Arguments:
      previous_lock: The lock file content from the last run, or ``{}``.
      new_lock: The lock file content for this run.
      old_spec: The recorded raw spec.
      old_routes: The recorded route lines.
      upstream: Everything fetched this run.
      fixes: The ``operations`` list from ``spec-fixes.json``.
      patched: The committed patched spec.

  Returns:
      Changes: Everything the report needs.
  """
  changes = Changes()

  old_flat, new_flat = _flatten(previous_lock), _flatten(new_lock)
  for name in sorted(set(old_flat) | set(new_flat)):
    if old_flat.get(name) != new_flat.get(name):
      changes.sources.append((name, _summary(old_flat.get(name)), _summary(new_flat.get(name))))

  changes.spec = diff_spec(old_spec, upstream.spec)

  added, removed = _added_removed(old_routes, upstream.routes)
  changes.routes = [f"Added: `{r}`" for r in added] + [f"Removed: `{r}`" for r in removed]

  for item, state in sorted(upstream.watched.items()):
    old = previous_lock.get("watched", {}).get(item, {}).get("state")
    if old != state:
      changes.watched.append(f"{item}: {old or '(new)'} → {state}")

  for name, version in sorted(upstream.packages.items()):
    old = previous_lock.get("packages", {}).get(name, {}).get("version")
    if old != version:
      changes.watched.append(f"{name} (PyPI): {old or '(new)'} → {version}")

  changes.stale_fixes = stale_fixes(fixes, patched, upstream.spec)

  return changes


###############################################################################
# Writing


# -----------------------------------------------------------------------------
def _section(title: str, lines: List[str], empty: str) -> List[str]:
  """Render a report section as a bullet list, or a one-line note when empty.

  Arguments:
      title: The section heading.
      lines: The bullet items.
      empty: The line to show when there are no items.
  """
  return [f"## {title}", "", *([f"- {line}" for line in lines] or [empty]), ""]


# -----------------------------------------------------------------------------
def render_error_report(errors: List[str]) -> str:
  """Render the change report for a run that failed.

  Arguments:
      errors: One line per failure.

  Returns:
      str: The Markdown report.
  """
  lines = ["# Upstream change report", "", "Detection failed. Nothing but this report was written.", ""]
  lines.extend(_section("Errors", errors, ""))
  return "\n".join(lines)


# -----------------------------------------------------------------------------
def render_report(changes: Changes, lock: Dict[str, Any]) -> str:
  """Render the change report.

  It carries no run timestamp, so identical runs write identical reports.

  Arguments:
      changes: What changed.
      lock: The lock file content for this run.

  Returns:
      str: The Markdown report.
  """
  lines = ["# Upstream change report", ""]

  if not changes.changed:
    lines.extend(["No upstream changes.", ""])

    if changes.stale_fixes:
      lines.extend([f"{len(changes.stale_fixes)} fix(es) no longer match the raw spec; see below.", ""])

  else:
    lines.extend([f"{len(changes.sources)} recorded source(s) changed. Review, then run `make build` and `make check`.", ""])
    lines.extend(["| Source | Was | Now |", "|--------|-----|-----|"])
    lines.extend(f"| {name} | {old} | {new} |" for name, old, new in changes.sources)
    lines.append("")

  lines.append(f"CLI release: {lock['cli']['release']}. Spec fetched {lock['spec']['fetched']}.")
  lines.append("")

  lines.extend(_section("Spec changes", changes.spec, "None."))
  lines.extend(_section("Routes bw serve registers", changes.routes, "None."))
  lines.extend(_section("Watched items", changes.watched, "None."))
  lines.extend(_section("Fixes that no longer match", changes.stale_fixes, "None."))
  lines.extend(_section("Regenerated", [], "Not run. `make build` fills this in."))
  lines.extend(_section("Work created", [], "Not run. `make check` fills this in."))

  return "\n".join(lines)


# -----------------------------------------------------------------------------
def write_json(path: Path, data: Any) -> None:
  """Write JSON the way the committed files are formatted.

  Arguments:
      path: The file to write.
      data: The value to write.
  """
  path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


# -----------------------------------------------------------------------------
def read_json(path: Path, default: Any) -> Any:
  """Read a JSON file, or return the default when it does not exist.

  Arguments:
      path: The file to read.
      default: What to return when the file does not exist.

  Returns:
      Any: The decoded content or the default.
  """
  if not path.exists():
    return default

  return json.loads(path.read_text(encoding="utf-8"))


# -----------------------------------------------------------------------------
def run(session: requests.Session, report_path: Path, today: str) -> int:
  """Run detection once.

  Arguments:
      session: The HTTP session to fetch with.
      report_path: Where to write the change report.
      today: Today's date, ISO formatted.

  Returns:
      int: The exit code: 0 no change, 1 error, 2 a change or a fix that
      no longer matches.
  """
  try:
    previous_lock = read_json(LOCK_FILE, {})
    old_spec = read_json(SPEC_SNAPSHOT, {})
    watch = read_json(WATCH_FILE, {})
    fixes = read_json(FIXES_FILE, {}).get("operations", [])
    patched = read_json(PATCHED_SPEC, {})
    old_routes = ROUTES_SNAPSHOT.read_text(encoding="utf-8").splitlines() if ROUTES_SNAPSHOT.exists() else []

    upstream = fetch_all(session, watch)

  except (FetchError, OSError, ValueError) as exc:
    report_path.write_text(render_error_report(str(exc).splitlines()), encoding="utf-8")
    print(f"detect: error:\n{exc}", file=sys.stderr)
    return 1

  new_lock = build_lock(upstream, previous_lock, today)
  changes = compare(previous_lock, new_lock, old_spec, old_routes, upstream, fixes, patched)

  # Bitwarden can reorder keys without changing content; rewriting the file
  # then would leave a diff behind a run that reports no change.
  if canonical_sha256(old_spec) != canonical_sha256(upstream.spec):
    write_json(SPEC_SNAPSHOT, upstream.spec)

  ROUTES_SNAPSHOT.write_text("".join(f"{route}\n" for route in upstream.routes), encoding="utf-8")
  write_json(LOCK_FILE, new_lock)
  report_path.write_text(render_report(changes, new_lock), encoding="utf-8")

  if changes.changed:
    print(f"detect: {len(changes.sources)} source(s) changed; see {report_path}")
    return 2

  if changes.stale_fixes:
    print(f"detect: no upstream changes, but {len(changes.stale_fixes)} fix(es) no longer match; see {report_path}")
    return 2

  print("detect: no upstream changes")
  return 0


# -----------------------------------------------------------------------------
def main(argv: Optional[List[str]] = None) -> int:
  """Parse arguments and run detection.

  Arguments:
      argv: The command-line arguments, without the program name.

  Returns:
      int: The exit code.
  """
  parser = argparse.ArgumentParser(description="Report whether Bitwarden changed anything this library depends on.")
  parser.add_argument("--report", type=Path, default=REPORT_FILE, help=f"where to write the report (default {REPORT_FILE.name})")
  args = parser.parse_args(argv)

  with requests.Session() as session:
    session.headers["User-Agent"] = "bw-serve-client-detect"
    return run(session, args.report, datetime.datetime.now(datetime.timezone.utc).date().isoformat())


if __name__ == "__main__":
  sys.exit(main())
