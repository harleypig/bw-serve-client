"""Record bw serve payloads into tests/fixtures/serve/, one JSON file per case.

Everything runs in Docker: a throwaway Vaultwarden and an image holding the
pinned bw CLI share a private network, and only ``bw serve``'s port is
published, on 127.0.0.1. This script builds the image, starts both
containers, sends each case over HTTP, and removes the containers, the
network and (unless ``--keep-image``) the image again, whatever happens.

The account is made up and lives only inside the Vaultwarden container.
Before anything is written, the master password and the session key are
replaced with ``<redacted>`` wherever they appear, and a payload that still
holds either is refused.

Usage, from the repository root::

    python tests/fixtures/recorder/record.py [--port 8087] [--keep-image]

The CLI version comes from ``upstream/lock.json``, so re-running after the
pin moves records against the new release.
"""

from __future__ import annotations

import argparse
from collections.abc import Callable
import datetime
import json
from pathlib import Path
import subprocess
import sys
import time
from typing import Any, NamedTuple, Optional
import urllib.error
import urllib.request
import uuid

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
OUT = HERE.parent / "serve"

VAULTWARDEN_IMAGE = "vaultwarden/server:1.37.4"

# Made-up credentials for a server that exists for one run. Nothing here is
# a real account; the password is still redacted from every payload.
EMAIL = "fixture-recorder@example.com"
PASSWORD = "not-a-real-password-0f6c2d"

REDACTED = "<redacted>"

# Registration and login each run 600,000 PBKDF2 rounds before bw serve
# listens; three minutes is generous for that and still ends a broken run.
READY_TIMEOUT = 180

# A single docker command is local and quick; the build pulls and installs.
DOCKER_TIMEOUT = 120
BUILD_TIMEOUT = 900

#: Pulls placeholder values out of a response body.
Keep = Callable[[Any], dict[str, str]]


# -----------------------------------------------------------------------------
class Case(NamedTuple):
  """One request to record.

  Attributes:
    name: File stem of the payload, ``tests/fixtures/serve/<name>.json``.
    description: What the case shows.
    method: HTTP method.
    path: Path, with ``{name}`` placeholders filled from earlier responses.
    body: JSON request body, or None.
    raw: A raw request body sent instead of ``body``, or None.
    keep: Pulls a value out of the response body to fill later paths.
  """

  name: str
  description: str
  method: str
  path: str
  body: Optional[dict[str, Any]] = None
  raw: Optional[str] = None
  keep: Optional[Keep] = None


def _data_id(key: str) -> Keep:
  """Keep ``data.id`` of a response under ``key``.

  Args:
    key: Placeholder name later paths use.

  Returns:
    A ``Case.keep`` callable.
  """
  return lambda body: {key: body["data"]["id"]}


# A random id no vault holds, for the never-existed lookup.
NEVER_EXISTED = "7d3c0d52-31a6-4c47-9b0e-0b1d1c5c0a11"

CASES = (
  Case("status-locked", "Status while the vault is locked.", "GET", "/status"),
  Case("folders-list-locked", "A command refused because the vault is locked.", "GET", "/list/object/folders"),
  Case("unlock-wrong-password", "Unlock with the wrong master password.", "POST", "/unlock", {"password": "wrong-password"}),
  Case("unlock", "Unlock with the master password; the session key is redacted.", "POST", "/unlock", {"password": PASSWORD}),
  Case("status-unlocked", "Status once unlocked.", "GET", "/status"),
  Case("folder-create", "Create a folder.", "POST", "/object/folder", {"name": "Recorded folder"}, keep=_data_id("folder_id")),
  Case("folder-get", "Get the folder just created.", "GET", "/object/folder/{folder_id}"),
  Case("folder-edit", "Rename the folder.", "PUT", "/object/folder/{folder_id}", {"name": "Renamed folder"}),
  Case("folders-list", "List folders, which includes the built-in No Folder entry.", "GET", "/list/object/folders"),
  Case(
    "item-create",
    "Create a login item in the folder.",
    "POST",
    "/object/item",
    {
      "type": 1,
      "name": "Recorded login",
      "folderId": "{folder_id}",
      "notes": "Made-up item for fixture recording.",
      "login": {
        "username": "someone@example.com",
        "password": "made-up-item-password",
        "uris": [{
          "match": None,
          "uri": "https://example.com/"
        }],
      },
    },
    keep=_data_id("item_id"),
  ),
  Case("items-list-before-sync", "List items straight after creating one.", "GET", "/list/object/items"),
  Case("sync", "Sync the vault with the server.", "POST", "/sync"),
  Case("items-list", "List items after a sync.", "GET", "/list/object/items"),
  Case("item-get", "Get the item just created.", "GET", "/object/item/{item_id}"),
  # An attempt at a 5xx, kept as recorded whatever comes back. Not a case:
  # POST /object/item with "type": 99, which kills bw serve 2026.10.1
  # outright ("invalid value: 99, expected one of: 1, ..., 8") so there is
  # no response to record, and every case after it would fail.
  Case("attachment-no-file", "Add an attachment with no file.", "POST", "/attachment?itemid={item_id}"),
  Case("folder-delete", "Delete the folder.", "DELETE", "/object/folder/{folder_id}"),
  Case("folder-get-deleted", "Get the folder just deleted.", "GET", "/object/folder/{folder_id}"),
  Case("folder-get-never-existed", "Get a folder id the vault never held.", "GET", f"/object/folder/{NEVER_EXISTED}"),
  Case("folder-get-not-a-uuid", "Get a folder by an id that is not a UUID.", "GET", "/object/folder/not-a-uuid"),
  Case("folder-create-empty-name", "Create a folder with an empty name.", "POST", "/object/folder", {"name": ""}),
  Case("folder-create-no-body", "Create a folder with no body at all.", "POST", "/object/folder"),
  Case("folder-create-malformed-json", "Create a folder with a body that is not JSON.", "POST", "/object/folder", raw="{not json"),
  Case("unknown-route", "A path bw serve has no route for.", "GET", "/no/such/route"),
  Case("lock", "Lock the vault.", "POST", "/lock"),
)


# -----------------------------------------------------------------------------
def docker(*args: str, timeout: int = DOCKER_TIMEOUT, check: bool = True) -> str:
  """Run one docker command.

  Args:
    args: Arguments after ``docker``.
    timeout: Seconds before the command is killed.
    check: Raise on a non-zero exit.

  Returns:
    The command's standard output, stripped.

  Raises:
    RuntimeError: The command failed and ``check`` is set.
  """
  result = subprocess.run(["docker", *args], capture_output=True, text=True, timeout=timeout, check=False)

  if check and result.returncode != 0:
    raise RuntimeError(f"docker {args[0]} failed ({result.returncode}): {result.stderr.strip()}")

  return result.stdout.strip()


def env_args(env: dict[str, str]) -> list[str]:
  """Spell environment variables as ``docker run`` arguments.

  Args:
    env: Variable names and values.

  Returns:
    ``--env NAME=value`` for each, flattened.
  """
  return [arg for name, value in env.items() for arg in ("--env", f"{name}={value}")]


def cli_version() -> str:
  """Read the pinned CLI version from upstream/lock.json.

  Returns:
    The version without its ``cli-v`` tag prefix, e.g. ``2026.10.1``.
  """
  release = json.loads((REPO / "upstream" / "lock.json").read_text())["cli"]["release"]
  return release.removeprefix("cli-v")


# -----------------------------------------------------------------------------
def _fill_value(value: Any, values: dict[str, str]) -> Any:
  """Fill ``{name}`` placeholders in every string of a JSON value.

  Args:
    value: A JSON body, or any part of one.
    values: Placeholders kept from earlier responses.

  Returns:
    The value with its strings filled.
  """
  if isinstance(value, str):
    return value.format_map(values)

  if isinstance(value, dict):
    return {key: _fill_value(item, values) for key, item in value.items()}

  if isinstance(value, list):
    return [_fill_value(item, values) for item in value]

  return value


def fill(case: Case, values: dict[str, str]) -> tuple[str, Optional[str]]:
  """Fill a case's placeholders from the values earlier cases kept.

  Placeholders are ``{name}`` in the path and in any string of the JSON
  body; a raw body is sent as written.

  Args:
    case: The request.
    values: Placeholders kept from earlier responses.

  Returns:
    The filled path, and the request body to send, or None for no body.

  Raises:
    RuntimeError: A placeholder has no value, because the case that keeps
      it failed or has not run. Sending an empty value instead would
      record a different request than the case describes.
  """
  try:
    path = case.path.format_map(values)
    body = None if case.body is None else json.dumps(_fill_value(case.body, values))

  except KeyError as e:
    raise RuntimeError(f"{case.name}: no value for {{{e.args[0]}}}; the case that keeps it failed or has not run") from e

  if case.raw is not None:
    return path, case.raw

  return path, body


def send(base: str, case: Case, values: dict[str, str]) -> tuple[str, Optional[str], int, Any]:
  """Send one case to bw serve.

  Args:
    base: ``http://127.0.0.1:<port>``.
    case: The request.
    values: Placeholders kept from earlier responses.

  Returns:
    The filled path, the request body as sent, the status, and the response
    body (parsed JSON, or the text when it is not JSON).

  Raises:
    RuntimeError: A placeholder has no value, or bw serve closed the
      connection without answering.
  """
  path, data = fill(case, values)

  request = urllib.request.Request(base + path, method=case.method, data=None if data is None else data.encode())

  if data is not None:
    request.add_header("Content-Type", "application/json")

  try:
    with urllib.request.urlopen(request, timeout=60) as response:  # noqa: S310 - fixed http://127.0.0.1 base.
      status, text = response.status, response.read().decode()

  except urllib.error.HTTPError as e:
    status, text = e.code, e.read().decode()

  except (urllib.error.URLError, ConnectionError) as e:
    raise RuntimeError(f"{case.name}: {case.method} {path} got no response ({e})") from e

  try:
    body: Any = json.loads(text)

  except json.JSONDecodeError:
    body = text

  return path, data, status, body


def container_logs(container: str) -> str:
  """Read a container's log, both streams.

  Args:
    container: Container id or name.

  Returns:
    Its standard output and standard error, which ``docker logs`` replays
    on its own two streams.
  """
  logs = subprocess.run(["docker", "logs", container], capture_output=True, text=True, timeout=DOCKER_TIMEOUT, check=False)
  return logs.stdout + logs.stderr


def wait_ready(base: str, container: str) -> None:
  """Wait until bw serve answers, or fail if its container exits.

  Args:
    base: ``http://127.0.0.1:<port>``.
    container: The bw container's id, checked for an early exit.

  Raises:
    RuntimeError: The container exited or the timeout passed.
  """
  deadline = time.monotonic() + READY_TIMEOUT

  while time.monotonic() < deadline:
    if docker("inspect", "-f", "{{.State.Running}}", container) != "true":
      raise RuntimeError(f"bw container exited before serving:\n{container_logs(container)}")

    try:
      with urllib.request.urlopen(base + "/status", timeout=5):  # noqa: S310 - fixed http://127.0.0.1 base.
        return

    except (urllib.error.URLError, ConnectionError):
      time.sleep(2)

  raise RuntimeError(f"bw serve did not answer within {READY_TIMEOUT}s")


def redact(record: dict[str, Any], secrets: list[str]) -> dict[str, Any]:
  """Replace every secret, wherever it appears, with ``<redacted>``.

  Args:
    record: One payload, as it will be written.
    secrets: Exact strings to remove.

  Returns:
    The redacted payload.

  Raises:
    RuntimeError: A secret survived, which would mean it was escaped in a
      way plain replacement does not reach.
  """
  text = json.dumps(record)

  for secret in secrets:
    text = text.replace(secret, REDACTED)

  if any(secret in text for secret in secrets):
    raise RuntimeError(f"{record['case']}: a secret survived redaction")

  return json.loads(text)


def write_payloads(out: Path, redacted: list[dict[str, Any]]) -> None:
  """Replace every payload in ``out`` with this run's.

  The old ``*.json`` files go first, so a case renamed or removed since the
  last run leaves no stale payload behind.

  Args:
    out: The payload directory.
    redacted: Every case's payload, already redacted.
  """
  texts = {f"{r['case']}.json": json.dumps(r, indent=2, sort_keys=True) + "\n" for r in redacted}

  out.mkdir(exist_ok=True)

  for stale in out.glob("*.json"):
    stale.unlink()

  for name, text in texts.items():
    (out / name).write_text(text)


# -----------------------------------------------------------------------------
def record(port: int, keep_image: bool) -> list[str]:
  """Run every case against fresh containers and write the payloads.

  Args:
    port: Host port, on 127.0.0.1, that bw serve is published on.
    keep_image: Leave the built recorder image in place.

  Returns:
    One ``name status`` line per case written.

  Raises:
    RuntimeError: A case got no response or lacked a placeholder value; the
      bw container's log is attached.
  """
  version = cli_version()
  run_id = uuid.uuid4().hex[:8]
  image = f"bw-serve-recorder:{version}"
  network = f"bw-recorder-{run_id}"
  vaultwarden = f"bw-recorder-vw-{run_id}"
  certs = f"bw-recorder-certs-{run_id}"
  started: list[str] = []
  network_made = volume_made = False

  try:
    docker("build", "--quiet", "--build-arg", f"BW_CLI_VERSION={version}", "-t", image, str(HERE), timeout=BUILD_TIMEOUT)

    docker("network", "create", network)
    network_made = True

    # The bw CLI accepts only an https server, so Vaultwarden serves TLS
    # with a CA minted for this run, which only the bw container trusts.
    docker("volume", "create", certs)
    volume_made = True

    docker(
      "run", "--rm", "--user", "root", "--volume", f"{certs}:/certs", "--entrypoint", "/bin/sh", image, "/recorder/certs.sh",
      vaultwarden
    )

    shared = ["run", "--detach", "--network", network, "--volume", f"{certs}:/certs:ro"]

    vaultwarden_env = {
      # The server is meant to vanish with its container, which
      # Vaultwarden refuses to start for unless told so.
      "I_REALLY_WANT_VOLATILE_STORAGE": "true",
      "SIGNUPS_ALLOWED": "true",
      "WEB_VAULT_ENABLED": "false",
      "ROCKET_PORT": "443",
      "ROCKET_TLS": '{certs="/certs/server.crt",key="/certs/server.key"}',
      "DOMAIN": f"https://{vaultwarden}",
    }
    started.append(docker(*shared, "--name", vaultwarden, *env_args(vaultwarden_env), VAULTWARDEN_IMAGE))

    cli_env = {
      "NODE_EXTRA_CA_CERTS": "/certs/ca.crt",
      "VW_URL": f"https://{vaultwarden}",
      "BW_EMAIL": EMAIL,
      "BW_PASSWORD": PASSWORD,
    }
    published = ["--publish", f"127.0.0.1:{port}:8087"]
    started.append(docker(*shared, "--name", f"bw-recorder-cli-{run_id}", *published, *env_args(cli_env), image))

    base = f"http://127.0.0.1:{port}"
    wait_ready(base, started[-1])

    recorded = {
      "cli": version,
      "server": VAULTWARDEN_IMAGE,
      "date": datetime.date.today().isoformat(),
    }
    values: dict[str, str] = {}
    secrets = [PASSWORD]
    records = []

    for case in CASES:
      try:
        path, data, status, body = send(base, case, values)

      except RuntimeError as e:
        raise RuntimeError(f"{e}\nbw container log:\n{container_logs(started[-1])}") from e

      if case.name == "unlock" and status == 200:
        secrets.append(body["data"]["raw"])

      if case.keep is not None and status == 200:
        values.update(case.keep(body))

      records.append({
        "case": case.name,
        "description": case.description,
        "recorded": recorded,
        "request": {
          "method": case.method,
          "path": path,
          "body": data if data is None or case.raw is not None else json.loads(data),
        },
        "response": {
          "status": status,
          "body": body
        },
      })

    # Redact everything before writing anything, so a failure leaves no
    # partial set behind.
    redacted = [redact(r, secrets) for r in records]

  finally:
    for container in reversed(started):
      docker("rm", "--force", container, check=False)

    if network_made:
      docker("network", "rm", network, check=False)

    if volume_made:
      docker("volume", "rm", certs, check=False)

    if not keep_image:
      docker("image", "rm", image, check=False)

  # Reached only when every case answered and every payload redacted, so a
  # failed run never clears the payloads already on disk.
  write_payloads(OUT, redacted)

  return [f"{r['case']} {r['response']['status']}" for r in redacted]


def main() -> int:
  """Parse arguments and record.

  Returns:
    The process exit status.
  """
  parser = argparse.ArgumentParser(description="Record bw serve payloads into tests/fixtures/serve/.")
  parser.add_argument("--port", type=int, default=8087, help="127.0.0.1 port for bw serve (default 8087)")
  parser.add_argument("--keep-image", action="store_true", help="leave the built recorder image in place")
  args = parser.parse_args()

  for line in record(args.port, args.keep_image):
    print(line)

  return 0


if __name__ == "__main__":
  sys.exit(main())
