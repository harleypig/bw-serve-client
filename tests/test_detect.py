"""Tests for upstream change detection (upstream/detect.py)."""

from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional, Union

import pytest
import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "upstream"))

import detect  # noqa: E402 - importable only once upstream/ is on the path.

FIXTURES = Path(__file__).resolve().parent / "fixtures"
TODAY = "2026-10-31"

OSS = detect.CONFIGURATORS["oss"]
BIT = detect.CONFIGURATORS["bit"]


class FakeResponse:
  """The slice of requests.Response that detect reads."""

  def __init__(self: FakeResponse, body: Union[str, Any], status_code: int = 200) -> None:
    self.status_code = status_code
    self.text = body if isinstance(body, str) else json.dumps(body)

  def json(self: FakeResponse) -> Any:
    """Decode the body.

    Returns:
        Any: The decoded body.
    """
    return json.loads(self.text)


class FakeSession:
  """Answers GETs from a URL table; any other URL is a 404."""

  def __init__(self: FakeSession, routes: Dict[str, Union[FakeResponse, Exception]]) -> None:
    self.routes = routes

  def get(
    self: FakeSession,
    url: str,
    headers: Optional[Dict[str, str]] = None,  # noqa: U100 - detect passes it; the fake has no use for it.
    timeout: int = 0,  # noqa: U100 - detect passes it; the fake has no use for it.
  ) -> FakeResponse:
    """Look the URL up.

    Arguments:
        url: The URL requested.
        headers: Ignored; accepted because detect passes it.
        timeout: Ignored; accepted because detect passes it.

    Raises:
        answer: Whatever exception the table holds for the URL.

    Returns:
        FakeResponse: The canned response.
    """
    answer = self.routes.get(url, FakeResponse("not found", 404))
    if isinstance(answer, Exception):
      raise answer

    return answer


def page_html(form: str = "script") -> str:
  """Read a recorded help page.

  Arguments:
      form: Which recording: ``script`` or ``attribute``.

  Returns:
      str: The page's HTML.
  """
  return (FIXTURES / f"help-page-{form}.html").read_text(encoding="utf-8")


def fixture_spec() -> Dict[str, Any]:
  """Return the spec embedded in the recorded pages.

  Returns:
      Dict[str, Any]: The spec.
  """
  return detect.extract_spec(page_html())


def gh(path: str) -> str:
  """Build a GitHub API URL.

  Arguments:
      path: The API path, starting with ``/``.

  Returns:
      str: The full URL.
  """
  return f"{detect.GITHUB_API}{path}"


def upstream_routes(spec_page: Optional[str] = None,
                    release: str = "cli-v2026.10.1",
                    state: str = "open",
                    sdk: str = "2.1.0") -> Dict[str, Union[FakeResponse, Exception]]:
  """Build a URL table for one complete, healthy upstream.

  Arguments:
      spec_page: The help page HTML to serve, instead of the script-form recording.
      release: The newest CLI release tag.
      state: The state of the one watched issue.
      sdk: The latest bitwarden-sdk version.

  Returns:
      Dict[str, Union[FakeResponse, Exception]]: Each URL, mapped to its answer.
  """
  configurator = (FIXTURES / "serve-configurator.ts").read_text(encoding="utf-8")

  routes: Dict[str, Union[FakeResponse, Exception]] = {
    detect.HELP_PAGE_URL:
      FakeResponse(spec_page or page_html()),
    gh(f"/repos/{detect.CLIENTS_REPO}/releases?per_page=100"):
      FakeResponse([
        {
          "tag_name": "web-v2026.10.2",
          "draft": False,
          "prerelease": False
        },
        {
          "tag_name": release,
          "draft": False,
          "prerelease": False
        },
      ]),
    gh("/repos/bitwarden/clients/issues/1"):
      FakeResponse({"state": state}),
    detect.PYPI_URL.format(package="bitwarden-sdk"):
      FakeResponse({"info": {
        "version": sdk
      }}),
  }

  for path, sha in ((OSS, "a" * 40), (BIT, "b" * 40)):
    routes[gh(f"/repos/{detect.CLIENTS_REPO}/commits?path={path}&sha={release}&per_page=1")] = FakeResponse([{"sha": sha}])
    routes[f"{detect.GITHUB_RAW}/{detect.CLIENTS_REPO}/{sha}/{path}"] = FakeResponse(configurator)

  return routes


WATCH = {"github": ["bitwarden/clients#1"], "pypi": ["bitwarden-sdk"]}

# The recorded spec and the synthetic configurator disagree on these routes;
# recording them keeps an unchanged upstream at exit 0.
FIXTURE_DECISIONS = {
  "GET /object/item/{id}": "fixture: the synthetic configurator registers no GET on objects.",
  "GET /list/object/{object}": "fixture: not in the recorded spec.",
  "POST /move/{id}/{organizationId}": "fixture: not in the recorded spec.",
  "DELETE /object/{object}/{id}": "fixture: not in the recorded spec.",
}


@pytest.fixture
def repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
  """Point every file detect reads or writes into a temporary upstream/."""
  for name, filename in (
    ("SPEC_SNAPSHOT", "vault-management-api-original.json"),
    ("ROUTES_SNAPSHOT", "serve-routes.txt"),
    ("LOCK_FILE", "lock.json"),
    ("WATCH_FILE", "watch.json"),
    ("FIXES_FILE", "spec-fixes.json"),
    ("DECISIONS_FILE", "route-decisions.json"),
  ):
    monkeypatch.setattr(detect, name, tmp_path / filename)

  (tmp_path / "watch.json").write_text(json.dumps(WATCH), encoding="utf-8")
  (tmp_path / "spec-fixes.json").write_text(json.dumps({"fixes": []}), encoding="utf-8")
  (tmp_path / "route-decisions.json").write_text(json.dumps({"routes": FIXTURE_DECISIONS}), encoding="utf-8")
  return tmp_path


def run(repo: Path, routes: Dict[str, Union[FakeResponse, Exception]]) -> int:
  """Run detection against a URL table, writing the report into the repo.

  Arguments:
      repo: The temporary upstream directory.
      routes: The URL table to answer requests from.

  Returns:
      int: detect's exit code.
  """
  return detect.run(FakeSession(routes), repo / "change-report.md", TODAY)  # type: ignore[arg-type]


def snapshot(repo: Path) -> Dict[str, bytes]:
  """Read every file in the temporary upstream/.

  Arguments:
      repo: The temporary upstream directory.

  Returns:
      Dict[str, bytes]: Each file's content, by name.
  """
  return {path.name: path.read_bytes() for path in sorted(repo.iterdir())}


class TestExtractSpec:
  """Pulling the spec out of the help page."""

  @pytest.mark.parametrize("form", ["script", "attribute"])
  def test_both_inertia_forms(self: TestExtractSpec, form: str) -> None:
    """Both page-data forms Bitwarden serves yield the same spec."""
    spec = detect.extract_spec(page_html(form))

    assert spec["openapi"] == "3.0.0"
    assert set(spec["paths"]) == {"/status", "/object/item/{id}"}

  def test_body_as_json_string(self: TestExtractSpec) -> None:
    """A body carried as a JSON string is decoded."""
    page = {"props": {"swaggerData": {"fields": {"body": json.dumps(fixture_spec())}}}}
    html = f'<script data-page="app" type="application/json">{json.dumps(page)}</script>'

    assert detect.extract_spec(html) == fixture_spec()

  @pytest.mark.parametrize(
    ("html", "message"),
    [
      ("<html><body><div id='app'></div></body></html>", "no Inertia page data"),
      ('<script data-page="app">{"props": {}}</script>', "no spec at props.swaggerData"),
      ('<script data-page="app">not json</script>', "no spec at props.swaggerData"),
      ('<script data-page="app">{"props": {"swaggerData": {"fields": {"body": {"a": 1}}}}}</script>', "not an OpenAPI"),
      ('<script data-page="app">{"props": {"swaggerData": {"fields": {"body": "{oops"}}}}</script>', "string that is not JSON"),
    ],
  )
  def test_unusable_page_is_an_error(self: TestExtractSpec, html: str, message: str) -> None:
    """A page without a usable spec raises; it never reads as no change."""
    with pytest.raises(detect.FetchError, match=message):
      detect.extract_spec(html)


class TestHttpGet:
  """Turning transport failures into FetchError."""

  def test_non_200_is_an_error(self: TestHttpGet) -> None:
    """An HTTP error status raises."""
    session = FakeSession({"https://x/": FakeResponse("", 503)})

    with pytest.raises(detect.FetchError, match="HTTP 503"):
      detect.http_get(session, "https://x/")  # type: ignore[arg-type]

  def test_network_error_is_an_error(self: TestHttpGet) -> None:
    """A connection failure raises."""
    session = FakeSession({"https://x/": requests.ConnectionError("refused")})

    with pytest.raises(detect.FetchError, match="refused"):
      detect.http_get(session, "https://x/")  # type: ignore[arg-type]

  def test_github_token_is_sent_when_set(self: TestHttpGet, monkeypatch: pytest.MonkeyPatch) -> None:
    """GITHUB_TOKEN becomes a bearer header, and is optional."""
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    assert "Authorization" not in detect.github_headers()

    monkeypatch.setenv("GITHUB_TOKEN", "dummy-test-value")
    assert detect.github_headers()["Authorization"] == "Bearer dummy-test-value"


class TestCliAndRoutes:
  """The CLI release and the routes its configurators register."""

  def test_highest_version_wins_over_creation_order(self: TestCliAndRoutes) -> None:
    """A hotfix for an older line, created later, is not the latest."""
    releases = [
      {
        "tag_name": "cli-v2026.9.3",
        "draft": False,
        "prerelease": False
      },
      {
        "tag_name": "cli-v2026.10.1",
        "draft": False,
        "prerelease": False
      },
      {
        "tag_name": "cli-v2026.10.0",
        "draft": False,
        "prerelease": False
      },
    ]
    session = FakeSession({gh(f"/repos/{detect.CLIENTS_REPO}/releases?per_page=100"): FakeResponse(releases)})

    assert detect.fetch_cli_release(session) == "cli-v2026.10.1"  # type: ignore[arg-type]

  def test_latest_cli_release_skips_other_apps_and_prereleases(self: TestCliAndRoutes) -> None:
    """The first published cli-v* tag wins."""
    releases = [
      {
        "tag_name": "desktop-v1",
        "draft": False,
        "prerelease": False
      },
      {
        "tag_name": "cli-v3",
        "draft": False,
        "prerelease": True
      },
      {
        "tag_name": "cli-v2",
        "draft": True,
        "prerelease": False
      },
      {
        "tag_name": "cli-v1",
        "draft": False,
        "prerelease": False
      },
    ]
    session = FakeSession({gh(f"/repos/{detect.CLIENTS_REPO}/releases?per_page=100"): FakeResponse(releases)})

    assert detect.fetch_cli_release(session) == "cli-v1"  # type: ignore[arg-type]

  def test_no_cli_release_is_an_error(self: TestCliAndRoutes) -> None:
    """No CLI release among the newest releases raises."""
    session = FakeSession({gh(f"/repos/{detect.CLIENTS_REPO}/releases?per_page=100"): FakeResponse([])})

    with pytest.raises(detect.FetchError, match="no cli-v"):
      detect.fetch_cli_release(session)  # type: ignore[arg-type]

  def test_extract_routes_rewrites_parameters(self: TestCliAndRoutes) -> None:
    """Koa :params become {params}; quote style and line breaks do not matter."""
    source = (FIXTURES / "serve-configurator.ts").read_text(encoding="utf-8")

    assert detect.extract_routes(source) == [
      "GET /status",
      "GET /list/object/{object}",
      "POST /move/{id}/{organizationId}",
      "DELETE /object/{object}/{id}",
    ]

  def test_routes_are_sorted_and_tagged(self: TestCliAndRoutes) -> None:
    """Each route carries its configurator, sorted by path then method."""
    commits, routes = detect.fetch_routes(FakeSession(upstream_routes()), "cli-v2026.10.1")  # type: ignore[arg-type]

    assert commits == {OSS: "a" * 40, BIT: "b" * 40}
    assert routes[:3] == [
      "GET /list/object/{object}  bit", "GET /list/object/{object}  oss", "POST /move/{id}/{organizationId}  bit"
    ]

  def test_configurator_without_routes_is_an_error(self: TestCliAndRoutes) -> None:
    """A file that registers nothing means the pattern broke, so it raises."""
    routes = upstream_routes()
    routes[f"{detect.GITHUB_RAW}/{detect.CLIENTS_REPO}/{'a' * 40}/{OSS}"] = FakeResponse("// moved")

    with pytest.raises(detect.FetchError, match="registers no routes"):
      detect.fetch_routes(FakeSession(routes), "cli-v2026.10.1")  # type: ignore[arg-type]

  def test_file_without_commits_is_an_error(self: TestCliAndRoutes) -> None:
    """A path no commit touches raises."""
    session = FakeSession({gh(f"/repos/{detect.CLIENTS_REPO}/commits?path=x&sha=t&per_page=1"): FakeResponse([])})

    with pytest.raises(detect.FetchError, match="no commit touches"):
      detect.fetch_file_commit(session, "x", "t")  # type: ignore[arg-type]


class TestWatched:
  """Watched GitHub items and PyPI packages."""

  @pytest.mark.parametrize(
    ("issue", "state"),
    [
      ({
        "state": "open"
      }, "open"),
      ({
        "state": "closed",
        "state_reason": "completed"
      }, "closed"),
      ({
        "state": "closed",
        "state_reason": "not_planned"
      }, "closed (not planned)"),
      ({
        "state": "closed",
        "pull_request": {
          "merged_at": None
        }
      }, "closed"),
      ({
        "state": "closed",
        "pull_request": {
          "merged_at": "2026-10-01T00:00:00Z"
        }
      }, "merged"),
    ],
  )
  def test_states(self: TestWatched, issue: Dict[str, Any], state: str) -> None:
    """Issues and pull requests map to one display state."""
    session = FakeSession({gh("/repos/o/r/issues/7"): FakeResponse(issue)})

    assert detect.fetch_watched_item(session, "o/r#7") == state  # type: ignore[arg-type]

  def test_malformed_item_is_an_error(self: TestWatched) -> None:
    """An entry that is not owner/repo#number raises."""
    with pytest.raises(detect.FetchError, match="not owner/repo#number"):
      detect.fetch_watched_item(FakeSession({}), "o/r/7")  # type: ignore[arg-type]

  def test_package_without_version_is_an_error(self: TestWatched) -> None:
    """A PyPI answer with no version raises."""
    session = FakeSession({detect.PYPI_URL.format(package="p"): FakeResponse({"info": {}})})

    with pytest.raises(detect.FetchError, match="no version for p"):
      detect.fetch_package_version(session, "p")  # type: ignore[arg-type]


class TestFetchAll:
  """Fetching every source at once."""

  def test_every_failure_is_reported(self: TestFetchAll) -> None:
    """All broken sources are named, not just the first."""
    routes = upstream_routes()
    routes[detect.HELP_PAGE_URL] = FakeResponse("", 500)
    routes[detect.PYPI_URL.format(package="bitwarden-sdk")] = FakeResponse("", 404)

    with pytest.raises(detect.FetchError) as raised:
      detect.fetch_all(FakeSession(routes), WATCH)  # type: ignore[arg-type]

    assert "HTTP 500" in str(raised.value)
    assert "HTTP 404" in str(raised.value)

  def test_unexpected_response_shape_is_reported(self: TestFetchAll) -> None:
    """A body missing a field is a collected error, not a traceback."""
    routes = upstream_routes()
    routes[gh("/repos/bitwarden/clients/issues/1")] = FakeResponse({"title": "no state"})

    with pytest.raises(detect.FetchError, match="unexpected response shape: KeyError"):
      detect.fetch_all(FakeSession(routes), WATCH)  # type: ignore[arg-type]


class TestDiffSpec:
  """Describing how the spec changed."""

  def test_equal_specs_have_no_changes(self: TestDiffSpec) -> None:
    """Identical specs produce nothing."""
    assert detect.diff_spec(fixture_spec(), fixture_spec()) == []

  def test_routes_parameters_and_schemas(self: TestDiffSpec) -> None:
    """Route, parameter and schema changes are each named."""
    old = fixture_spec()
    new = json.loads(json.dumps(old))
    del new["paths"]["/status"]
    new["paths"]["/archive/{id}"] = {"post": {"responses": {}}}
    new["paths"]["/object/item/{id}"]["get"]["parameters"].append({"in": "query", "name": "archived"})
    new["components"]["schemas"]["status"]["properties"]["userId"] = {"type": "string"}

    assert detect.diff_spec(old, new) == [
      "Route added: `POST /archive/{id}`",
      "Route removed: `GET /status`",
      "`GET /object/item/{id}`: parameter added: query archived",
      "`status`: property added: `userId`",
    ]

  def test_change_outside_routes_and_schemas(self: TestDiffSpec) -> None:
    """A change only in metadata is still reported."""
    new = fixture_spec()
    new["info"]["title"] = "Renamed"

    assert detect.diff_spec(fixture_spec(), new) == ["Changed outside the routes and schemas (for example `info` or `servers`)"]


class TestRoutes:
  """Comparing the spec's routes with the routes bw serve registers."""

  @pytest.mark.parametrize(
    ("spec_path", "cli_path", "matches"),
    [
      ("/object/item/{id}", "/object/{object}/{id}", True),
      ("/device-approval/{organizationId}/approve/{request-id}", "/device-approval/{organizationId}/approve/{requestId}", True),
      ("/status", "/status", True),
      ("/object/{id}", "/object/item", False),
      ("/object/item/{id}", "/object/{id}", False),
      ("/lock", "/unlock", False),
    ],
  )
  def test_shape_matching(self: TestRoutes, spec_path: str, cli_path: str, matches: bool) -> None:
    """CLI parameters match any segment; names are ignored; literals must agree."""
    assert detect._route_shape_matches(spec_path, cli_path) is matches

  def test_gaps_in_both_directions(self: TestRoutes) -> None:
    """A route on only one side is a gap, whichever side it is on."""
    result = detect.compare_routes(fixture_spec(), ["GET /status  oss", "POST /lock  oss"], {})

    assert result.gaps == [
      "`GET /object/item/{id}`: documented, but bw serve registers no matching route; needs a decision",
      "`POST /lock`: registered by bw serve, but not documented; needs a decision",
    ]
    assert result.known == []

  def test_recorded_decision_makes_a_gap_known(self: TestRoutes) -> None:
    """A gap with a recorded decision is reported with it, not as needing one."""
    result = detect.compare_routes(
      fixture_spec(), ["GET /status  oss", "GET /object/{object}/{id}  oss", "POST /lock  oss"],
      {"POST /lock": "licensed build only"}
    )

    assert result.gaps == []
    assert result.known == ["`POST /lock`: registered by bw serve, but not documented. Decision: licensed build only"]

  def test_decision_matches_by_shape(self: TestRoutes) -> None:
    """A decision keyed with the spec's parameter names covers the CLI's route."""
    result = detect.compare_routes(
      fixture_spec(), ["GET /status  oss", "GET /object/{object}/{id}  oss", "POST /move/{itemId}  oss"],
      {"POST /move/{id}": "not in the spec"}
    )

    assert result.gaps == []
    assert result.stale == []
    assert result.known == ["`POST /move/{itemId}`: registered by bw serve, but not documented. Decision: not in the spec"]

  def test_licensed_only_route_is_its_own_difference(self: TestRoutes) -> None:
    """A documented route only the licensed build registers is a difference, not served."""
    result = detect.compare_routes(fixture_spec(), ["GET /status  oss", "GET /object/{object}/{id}  bit"], {})

    assert result.gaps == ["`GET /object/item/{id}`: registered only by the licensed build; needs a decision"]

  def test_route_both_builds_register_is_served(self: TestRoutes) -> None:
    """A route the open-source build registers is served, whatever else registers it."""
    result = detect.compare_routes(
      fixture_spec(), ["GET /status  oss", "GET /object/{object}/{id}  oss", "GET /object/{object}/{id}  bit"], {}
    )

    assert result.gaps == []

  def test_decision_matching_nothing_is_stale(self: TestRoutes) -> None:
    """A recorded decision with no difference left is reported for removal."""
    result = detect.compare_routes(
      fixture_spec(), ["GET /status  oss", "GET /object/{object}/{id}  oss"], {"POST /lock": "licensed build only"}
    )

    assert result.gaps == []
    assert result.stale == ["`POST /lock`: recorded decision matches no difference any more; remove it"]


class TestRun:
  """Whole runs: files written and exit codes."""

  def test_first_run_records_everything_and_reports_change(self: TestRun, repo: Path) -> None:
    """With no lock file, every source is new: exit 2, all files written."""
    code = run(repo, upstream_routes())

    lock = json.loads((repo / "lock.json").read_text(encoding="utf-8"))
    assert code == 2
    assert lock["cli"] == {"release": "cli-v2026.10.1", "fetched": TODAY}
    assert lock["configurators"][OSS]["commit"] == "a" * 40
    assert lock["watched"]["bitwarden/clients#1"]["state"] == "open"
    assert lock["packages"]["bitwarden-sdk"]["version"] == "2.1.0"
    assert lock["spec"]["sha256"] == detect.canonical_sha256(fixture_spec())
    assert json.loads((repo / "vault-management-api-original.json").read_text(encoding="utf-8")) == fixture_spec()
    assert "GET /status  oss" in (repo / "serve-routes.txt").read_text(encoding="utf-8")

  def test_second_run_is_a_no_op(self: TestRun, repo: Path) -> None:
    """Running again on unchanged upstream exits 0 and rewrites nothing."""
    run(repo, upstream_routes())
    before = snapshot(repo)

    code = run(repo, upstream_routes())

    assert code == 0
    assert {
      k: v
      for k, v in snapshot(repo).items()
      if k != "change-report.md"
    } == {
      k: v
      for k, v in before.items()
      if k != "change-report.md"
    }
    assert "No upstream changes." in (repo / "change-report.md").read_text(encoding="utf-8")

  def test_change_is_reported_and_fetch_date_moves(self: TestRun, repo: Path) -> None:
    """A new CLI release and a merged PR are reported; unchanged dates hold."""
    run(repo, upstream_routes())
    lock = json.loads((repo / "lock.json").read_text(encoding="utf-8"))
    lock["spec"]["fetched"] = "2026-01-01"
    (repo / "lock.json").write_text(json.dumps(lock), encoding="utf-8")

    code = run(repo, upstream_routes(release="cli-v2026.11.0", state="closed"))

    report = (repo / "change-report.md").read_text(encoding="utf-8")
    new_lock = json.loads((repo / "lock.json").read_text(encoding="utf-8"))
    assert code == 2
    assert "| cli | cli-v2026.10.1 | cli-v2026.11.0 |" in report
    assert "bitwarden/clients#1: open → closed" in report
    assert new_lock["spec"]["fetched"] == "2026-01-01"
    assert new_lock["cli"]["fetched"] == TODAY

  def test_broken_fetch_is_an_error_and_writes_only_the_report(self: TestRun, repo: Path) -> None:
    """A failed fetch exits 1, says why, and leaves the recorded state alone."""
    run(repo, upstream_routes())
    before = snapshot(repo)
    routes = upstream_routes(release="cli-v2026.11.0")
    routes[detect.HELP_PAGE_URL] = FakeResponse("<html></html>")

    code = run(repo, routes)

    after = snapshot(repo)
    report = (repo / "change-report.md").read_text(encoding="utf-8")
    assert code == 1
    assert "## Errors" in report
    assert "no Inertia page data" in report
    assert {
      k: v
      for k, v in after.items()
      if k != "change-report.md"
    } == {
      k: v
      for k, v in before.items()
      if k != "change-report.md"
    }

  def test_stale_fix_is_reported_on_every_run(self: TestRun, repo: Path) -> None:
    """A stale fix keeps detect at exit 2 after the snapshot catches up."""
    fixes = [{"op": "set", "path": ["paths", "/gone", "get", "summary"], "from": "Old", "value": "x"}]
    (repo / "spec-fixes.json").write_text(json.dumps({"fixes": fixes}), encoding="utf-8")
    run(repo, upstream_routes())

    code = run(repo, upstream_routes())

    report = (repo / "change-report.md").read_text(encoding="utf-8")
    assert code == 2
    assert "No upstream changes." in report
    assert "1 fix(es) no longer match the raw spec" in report
    assert "fix 1 (set paths › /gone › get › summary): key '/gone' not found" in report

  def test_undecided_route_gap_is_work(self: TestRun, repo: Path) -> None:
    """A route difference with no recorded decision keeps detect at exit 2."""
    decisions = {k: v for k, v in FIXTURE_DECISIONS.items() if k != "POST /move/{id}/{organizationId}"}
    (repo / "route-decisions.json").write_text(json.dumps({"routes": decisions}), encoding="utf-8")
    run(repo, upstream_routes())

    code = run(repo, upstream_routes())

    report = (repo / "change-report.md").read_text(encoding="utf-8")
    assert code == 2
    assert "1 spec-vs-CLI route difference(s) or decision(s) need attention" in report
    assert "`POST /move/{id}/{organizationId}`: registered by bw serve, but not documented; needs a decision" in report
    assert "`GET /object/item/{id}`: documented, but bw serve registers no matching route. Decision: fixture:" in report

  def test_stale_decision_is_work(self: TestRun, repo: Path) -> None:
    """A recorded decision that matches no difference keeps detect at exit 2."""
    decisions = {**FIXTURE_DECISIONS, "POST /gone": "fixture: nothing registers this."}
    (repo / "route-decisions.json").write_text(json.dumps({"routes": decisions}), encoding="utf-8")
    run(repo, upstream_routes())

    code = run(repo, upstream_routes())

    assert code == 2
    assert "`POST /gone`: recorded decision matches no difference any more" in (repo
                                                                                / "change-report.md").read_text(encoding="utf-8")

  def test_behaviour_is_reported_without_counting_as_work(self: TestRun, repo: Path) -> None:
    """Recorded behaviour goes in the report and leaves an unchanged upstream at exit 0."""
    recorded = {"routes": FIXTURE_DECISIONS, "behaviour": {"GET /status": "fixture: answers 400."}}
    (repo / "route-decisions.json").write_text(json.dumps(recorded), encoding="utf-8")
    run(repo, upstream_routes())

    code = run(repo, upstream_routes())

    assert code == 0
    assert "`GET /status`: fixture: answers 400." in (repo / "change-report.md").read_text(encoding="utf-8")

  def test_missing_fixes_file_is_an_error(self: TestRun, repo: Path) -> None:
    """With no fixes file, detection stops rather than counting zero fixes."""
    (repo / "spec-fixes.json").unlink()

    assert run(repo, upstream_routes()) == 1
    assert "No such file or directory" in (repo / "change-report.md").read_text(encoding="utf-8")

  def test_old_format_fixes_file_is_an_error(self: TestRun, repo: Path) -> None:
    """A fixes file without a fixes list stops detection rather than passing."""
    (repo / "spec-fixes.json").write_text(json.dumps({"operations": []}), encoding="utf-8")

    assert run(repo, upstream_routes()) == 1
    assert "spec-fixes.json has no fixes list" in (repo / "change-report.md").read_text(encoding="utf-8")

  def test_reordered_keys_leave_the_snapshot_alone(self: TestRun, repo: Path) -> None:
    """Same content in a different key order rewrites nothing."""
    run(repo, upstream_routes())
    snapshot_file = repo / "vault-management-api-original.json"
    reordered = json.dumps(dict(reversed(list(fixture_spec().items()))), indent=2)
    snapshot_file.write_text(reordered, encoding="utf-8")

    code = run(repo, upstream_routes())

    assert code == 0
    assert snapshot_file.read_text(encoding="utf-8") == reordered

  def test_report_lists_stale_fixes_and_spec_changes(self: TestRun, repo: Path) -> None:
    """The report carries spec changes and fixes that no longer match."""
    old = fixture_spec()
    old["paths"]["/legacy"] = {"get": {"summary": "Old"}}
    (repo / "vault-management-api-original.json").write_text(json.dumps(old), encoding="utf-8")
    fixes: List[Dict[str, Any]] = [{"op": "set", "path": ["paths", "/legacy", "get", "summary"], "from": "Old", "value": "Legacy"}]
    (repo / "spec-fixes.json").write_text(json.dumps({"fixes": fixes}), encoding="utf-8")

    run(repo, upstream_routes())

    report = (repo / "change-report.md").read_text(encoding="utf-8")
    assert "Route removed: `GET /legacy`" in report
    assert "fix 1 (set paths › /legacy › get › summary): key '/legacy' not found" in report
    assert "## Regenerated" in report
    assert "## Work created" in report
