"""Record bw serve payloads into tests/fixtures/serve/, one JSON file per case.

Everything runs in Docker: a throwaway Vaultwarden and an image holding the
pinned bw CLI share a private network, and only ``bw serve``'s port is
published, on 127.0.0.1. This script builds the image, starts both
containers, sends each case over HTTP, and removes the containers, the
network and (unless ``--keep-image``) the image again, whatever happens.

The account is made up and lives only inside the Vaultwarden container.
Before anything is written, every secret -- the master password, the
session key, the made-up item and Send passwords and TOTP seed, and the
values a case names with ``Case.secret`` (generated passwords, Send keys and
access URLs, attachment download URLs) -- is replaced with ``<redacted>``
wherever it appears, and a payload that still holds one is refused.

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
from typing import Any, NamedTuple, Optional, Union
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

# The item the field routes read, and the Send, carry made-up secrets of
# their own. They are redacted like the master password, so a fixture never
# shows the value even though no real vault ever held it.
FIELD_PASSWORD = "made-up-field-password-7c1e9a"
TOTP_SEED = "JBSWY3DPEHPK3PXPMADEUP7Q"
SEND_PASSWORD = "made-up-send-password-4b2d"

#: The file the attachment cases upload: name and text content.
ATTACHMENT = ("recorded-attachment.txt", "Made-up attachment for fixture recording.\n")

REDACTED = "<redacted>"

# Registration and login each run 600,000 PBKDF2 rounds before bw serve
# listens; three minutes is generous for that and still ends a broken run.
READY_TIMEOUT = 180

# A single docker command is local and quick; the build pulls and installs.
DOCKER_TIMEOUT = 120
BUILD_TIMEOUT = 900

#: Pulls placeholder values out of a response body.
Keep = Callable[[Any], dict[str, str]]

#: Pulls values to redact out of a successful response body.
Secret = Callable[[Any], list[str]]

#: A JSON request body: an object, or an array (the collection-id routes).
Body = Union[dict[str, Any], list[Any]]


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
    file: ``(filename, text)`` sent as the multipart ``file`` field.
    secret: Pulls values to redact out of a successful response body.
  """

  name: str
  description: str
  method: str
  path: str
  body: Optional[Body] = None
  raw: Optional[str] = None
  keep: Optional[Keep] = None
  file: Optional[tuple[str, str]] = None
  secret: Optional[Secret] = None


def _data_id(key: str) -> Keep:
  """Keep ``data.id`` of a response under ``key``.

  Args:
    key: Placeholder name later paths use.

  Returns:
    A ``Case.keep`` callable.
  """
  return lambda body: {key: body["data"]["id"]}


def _data_list_id(key: str) -> Keep:
  """Keep the id of the first entry of a list response under ``key``.

  Args:
    key: Placeholder name later paths use.

  Returns:
    A ``Case.keep`` callable.
  """
  return lambda body: {key: body["data"]["data"][0]["id"]}


def _data_fields(*names: str) -> Secret:
  """Redact the named members of a response's ``data``.

  Args:
    names: Members of ``data`` holding a secret.

  Returns:
    A ``Case.secret`` callable.
  """
  return lambda body: [body["data"][name] for name in names]


def _attachment_urls(body: Any) -> list[str]:
  """Redact every attachment download URL of an item response.

  Each URL carries a signed download token, short-lived but still a
  credential to the server that issued it.

  Args:
    body: The response body of a request that returns an item.

  Returns:
    The URLs.
  """
  return [attachment["url"] for attachment in body["data"]["attachments"]]


# A random id no vault holds, for the never-existed lookups.
NEVER_EXISTED = "7d3c0d52-31a6-4c47-9b0e-0b1d1c5c0a11"

#: The login the field routes read: the existing item, edited to carry a
#: made-up password and TOTP seed.
EDITED_LOGIN = {
  "type": 1,
  "name": "Recorded login",
  "folderId": "{folder_id}",
  "notes": "Made-up item for fixture recording.",
  "login": {
    "username": "someone@example.com",
    "password": FIELD_PASSWORD,
    "totp": TOTP_SEED,
    "uris": [{
      "match": None,
      "uri": "https://example.com/"
    }],
  },
}

#: A secure note, the simplest item, for the cases that only need one more.
SECURE_NOTE = {"type": 2, "notes": "Made-up note for fixture recording.", "secureNote": {"type": 0}}

#: A text Send. ``disabled`` is sent because Vaultwarden refuses a Send
#: without it (the send-create-no-disabled case); ``{deletion_date}`` is a
#: week from the run, inside the 31 days a server allows.
SEND = {
  "name": "Recorded send",
  "type": 0,
  "text": {
    "text": "Made-up send text.",
    "hidden": False
  },
  "deletionDate": "{deletion_date}",
  "password": SEND_PASSWORD,
  "disabled": False,
}

#: A collection in the organization register.js creates.
ORG_COLLECTION = {"organizationId": "{org_id}", "name": "Second collection", "externalId": None, "groups": [], "users": []}

CASES = (
  Case("status-locked", "Status while the vault is locked.", "GET", "/status"),
  Case("folders-list-locked", "A command refused because the vault is locked.", "GET", "/list/object/folders"),
  Case("unlock-wrong-password", "Unlock with the wrong master password.", "POST", "/unlock", {"password": "wrong-password"}),
  Case(
    "unlock",
    "Unlock with the master password; the session key is redacted.",
    "POST",
    "/unlock", {"password": PASSWORD},
    secret=_data_fields("raw")
  ),
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
  # Items, and the single-field reads of the login.
  Case("item-edit", "Edit the login to carry a password and a TOTP seed.", "PUT", "/object/item/{item_id}", EDITED_LOGIN),
  Case("item-field-username", "Read the login's username.", "GET", "/object/username/{item_id}"),
  Case("item-field-password", "Read the login's password; the value is redacted.", "GET", "/object/password/{item_id}"),
  Case("item-field-uri", "Read the login's first URI.", "GET", "/object/uri/{item_id}"),
  Case("item-field-totp", "Read the login's current TOTP code, which changes every run.", "GET", "/object/totp/{item_id}"),
  Case("item-field-notes", "Read the item's notes.", "GET", "/object/notes/{item_id}"),
  # bw asks the Have I Been Pwned range API, so this one needs the internet.
  Case("item-field-exposed", "How often the login's password appears in known breaches.", "GET", "/object/exposed/{item_id}"),
  Case("item-field-never-existed", "Read a field of an item the vault never held.", "GET", f"/object/password/{NEVER_EXISTED}"),
  Case("item-get-by-search", "Get an item by a search term that matches one item.", "GET", "/object/item/Recorded%20login"),
  Case(
    "item-create-note",
    "Create a secure note.",
    "POST",
    "/object/item", {
      **SECURE_NOTE, "name": "Recorded note"
    },
    keep=_data_id("note_id")
  ),
  Case("item-get-by-search-ambiguous", "Get an item by a search term that matches two.", "GET", "/object/item/Recorded"),
  # Archive and restore.
  Case("item-archive", "Archive the note.", "POST", "/archive/item/{note_id}"),
  Case("items-list-archived", "List archived items.", "GET", "/list/object/items?archived=true"),
  # bw serve has no unarchive route. Restoring an archived item answered
  # 200 here, but 400 "Cipher is not in trash." when sent straight after the
  # archive with no request between, so the list above stays before it.
  Case("item-restore-archived", "Restore an item that is archived, not in the trash.", "POST", "/restore/item/{note_id}"),
  Case("item-archive-never-existed", "Archive an item the vault never held.", "POST", f"/archive/item/{NEVER_EXISTED}"),
  Case("item-delete", "Delete the note, which moves it to the trash.", "DELETE", "/object/item/{note_id}"),
  Case("items-list-trash", "List the items in the trash.", "GET", "/list/object/items?trash=true"),
  Case("item-restore", "Restore the note from the trash.", "POST", "/restore/item/{note_id}"),
  Case("item-delete-permanent", "Delete the note permanently.", "DELETE", "/object/item/{note_id}?permanent=true"),
  # Attachments. The create response is the item, whose attachment URL
  # carries a download token.
  Case(
    "attachment-create",
    "Attach a small text file to the login, as multipart form data.",
    "POST",
    "/attachment?itemid={item_id}",
    keep=lambda body: {"attachment_id": body["data"]["attachments"][0]["id"]},
    file=ATTACHMENT,
    secret=_attachment_urls,
  ),
  Case(
    "attachment-get", "Download the attachment; the body is the file.", "GET", "/object/attachment/{attachment_id}?itemid={item_id}"
  ),
  Case("attachment-delete", "Delete the attachment.", "DELETE", "/object/attachment/{attachment_id}?itemid={item_id}"),
  Case(
    "attachment-get-deleted", "Download the attachment just deleted.", "GET", "/object/attachment/{attachment_id}?itemid={item_id}"
  ),
  # Send. The key and access URL are a Send's secret, so every payload
  # holding them is redacted.
  Case(
    "send-create-no-disabled", "Create a Send without the disabled member Vaultwarden requires.", "POST", "/object/send", {
      key: value
      for key, value in SEND.items()
      if key != "disabled"
    }
  ),
  Case(
    "send-create",
    "Create a password-protected text Send.",
    "POST",
    "/object/send",
    SEND,
    keep=_data_id("send_id"),
    secret=_data_fields("key", "accessUrl"),
  ),
  Case("send-get", "Get the Send just created.", "GET", "/object/send/{send_id}"),
  Case("sends-list-object", "List Sends through the object route.", "GET", "/list/object/send"),
  Case("sends-list", "List Sends through the send route.", "GET", "/send/list"),
  Case("send-remove-password", "Remove the Send's password.", "POST", "/send/{send_id}/remove-password"),
  Case(
    "send-edit", "Rename the Send and hide its text.", "PUT", "/object/send/{send_id}", {
      **SEND, "name": "Renamed send",
      "text": {
        "text": "Made-up send text.",
        "hidden": True
      }
    }
  ),
  Case("send-delete", "Delete the Send.", "DELETE", "/object/send/{send_id}"),
  Case("send-get-deleted", "Get the Send just deleted.", "GET", "/object/send/{send_id}"),
  # Utilities. A generated password or passphrase is a secret.
  Case("generate", "Generate a password with the default options.", "GET", "/generate", secret=_data_fields("data")),
  Case(
    "generate-minimums",
    "Generate a password with minimum digit and special counts, avoiding ambiguous characters.",
    "GET",
    "/generate?length=24&uppercase=true&lowercase=true&number=true&special=true&minNumber=3&minSpecial=3&ambiguous=true",
    secret=_data_fields("data"),
  ),
  Case(
    "generate-passphrase",
    "Generate a passphrase.",
    "GET",
    "/generate?passphrase=true&words=4&separator=-&capitalize=true&includeNumber=true",
    secret=_data_fields("data"),
  ),
  Case("template-item", "The item template.", "GET", "/object/template/item"),
  Case("template-item-login", "The login template.", "GET", "/object/template/item.login"),
  Case("template-folder", "The folder template.", "GET", "/object/template/folder"),
  Case("template-org-collection", "The organization collection template.", "GET", "/object/template/org-collection"),
  Case("template-item-collections", "The item-collections template.", "GET", "/object/template/item-collections"),
  Case("fingerprint", "The account's fingerprint phrase.", "GET", "/object/fingerprint/me"),
  # Organizations and collections. register.js creates the organization,
  # with one collection, before bw logs in.
  Case("organizations-list", "List organizations.", "GET", "/list/object/organizations", keep=_data_list_id("org_id")),
  Case("organization-get", "Get the organization.", "GET", "/object/organization/{org_id}"),
  Case("collections-list", "List collections.", "GET", "/list/object/collections", keep=_data_list_id("collection_id")),
  Case("collection-get", "Get the collection.", "GET", "/object/collection/{collection_id}"),
  Case(
    "org-collections-list", "List the organization's collections.", "GET", "/list/object/org-collections?organizationId={org_id}"
  ),
  Case("org-collections-list-no-org", "List organization collections without naming one.", "GET", "/list/object/org-collections"),
  Case(
    "org-collection-get", "Get the collection through the organization route.", "GET",
    "/object/org-collection/{collection_id}?organizationId={org_id}"
  ),
  Case(
    "org-collection-create",
    "Create a second collection.",
    "POST",
    "/object/org-collection?organizationId={org_id}",
    ORG_COLLECTION,
    keep=_data_id("new_collection_id"),
  ),
  Case(
    "org-collection-edit", "Rename the second collection.", "PUT",
    "/object/org-collection/{new_collection_id}?organizationId={org_id}", {
      **ORG_COLLECTION, "name": "Renamed collection"
    }
  ),
  Case("org-members-list", "List the organization's members.", "GET", "/list/object/org-members?organizationId={org_id}"),
  Case(
    "org-members-list-unknown-org", "List the members of an organization the account is not in.", "GET",
    f"/list/object/org-members?organizationId={NEVER_EXISTED}"
  ),
  Case(
    "org-member-confirm-unknown", "Confirm a member the organization does not have.", "POST",
    f"/confirm/org-member/{NEVER_EXISTED}?organizationId={{org_id}}"
  ),
  Case(
    "item-create-shared",
    "Create a note to move into the organization.",
    "POST",
    "/object/item", {
      **SECURE_NOTE, "name": "Shared note"
    },
    keep=_data_id("shared_id")
  ),
  Case("item-move", "Move the note into the organization's collection.", "POST", "/move/{shared_id}/{org_id}", ["{collection_id}"]),
  # bw serve's local vault can lag the move: once its response came back
  # with no organizationId, and the item-collections edit was refused as
  # outside any organization. The sync makes the edit deterministic.
  Case("sync-after-move", "Sync, so the local vault holds the moved note.", "POST", "/sync"),
  Case(
    "item-collections-edit", "Put the moved note in both collections.", "PUT", "/object/item-collections/{shared_id}",
    ["{collection_id}", "{new_collection_id}"]
  ),
  Case(
    "item-collections-not-in-org", "Set collections on an item outside any organization.", "PUT",
    "/object/item-collections/{item_id}", ["{collection_id}"]
  ),
  Case(
    "org-collection-delete", "Delete the second collection.", "DELETE",
    "/object/org-collection/{new_collection_id}?organizationId={org_id}"
  ),
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


def multipart(filename: str, text: str, boundary: str) -> bytes:
  """Encode one file as a ``multipart/form-data`` body, field ``file``.

  Args:
    filename: The file name the part declares.
    text: The file's content.
    boundary: The part boundary, which must not occur in ``text``.

  Returns:
    The body.
  """
  disposition = 'form-data; name="file"; filename="' + filename + '"'
  head = f"--{boundary}\r\nContent-Disposition: {disposition}\r\nContent-Type: text/plain\r\n\r\n"

  return (head + text + f"\r\n--{boundary}--\r\n").encode()


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

  if case.file is not None:
    boundary = f"bw-recorder-{uuid.uuid4().hex}"
    request = urllib.request.Request(base + path, method=case.method, data=multipart(*case.file, boundary))
    request.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")

  else:
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


def secrets_of(case: Case, status: int, body: Any) -> list[str]:
  """Collect the values a case's response holds that must be redacted.

  Args:
    case: The request.
    status: The response status.
    body: The parsed response body.

  Returns:
    The non-empty values ``case.secret`` names, or none when the case names
    none or failed. An empty string is dropped: replacing it would put the
    marker between every character of every payload.
  """
  if case.secret is None or status != 200:
    return []

  return [value for value in case.secret(body) if value]


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
    week_ahead = datetime.date.today() + datetime.timedelta(days=7)
    values = {"deletion_date": f"{week_ahead.isoformat()}T00:00:00.000Z"}
    secrets = [PASSWORD, FIELD_PASSWORD, TOTP_SEED, SEND_PASSWORD]
    records = []

    for case in CASES:
      try:
        path, data, status, body = send(base, case, values)

      except RuntimeError as e:
        raise RuntimeError(f"{e}\nbw container log:\n{container_logs(started[-1])}") from e

      secrets.extend(secrets_of(case, status, body))

      if case.keep is not None and status == 200:
        values.update(case.keep(body))

      request: dict[str, Any] = {
        "method": case.method,
        "path": path,
        "body": data if data is None or case.raw is not None else json.loads(data),
      }

      if case.file is not None:
        request["content_type"] = "multipart/form-data"
        request["body"] = {"file": {"filename": case.file[0], "content": case.file[1]}}

      records.append({
        "case": case.name,
        "description": case.description,
        "recorded": recorded,
        "request": request,
        "response": {
          "status": status,
          "body": body
        },
      })

    # Redact everything before writing anything, so a failure leaves no
    # partial set behind.
    redacted = [redact(r, secrets) for r in records]

  finally:
    # --volumes: the Vaultwarden image declares VOLUME /data, so each run
    # gets an anonymous volume that a plain rm would leave behind.
    for container in reversed(started):
      docker("rm", "--force", "--volumes", container, check=False)

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
