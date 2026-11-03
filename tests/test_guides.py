"""The code on the docs site's guide pages runs against the current API.

Every ``.. code-block:: python`` in ``docs/html/source/guides/`` compiles.
The two tutorials are run: each one's Python blocks, joined in page order,
are executed against a fake ``bw serve`` behind an ``httpx.MockTransport``,
and the fake's end state and the printed output are checked. Nothing here
talks to a real ``bw serve``.
"""

from __future__ import annotations

import json
from pathlib import Path
import re
import textwrap
from typing import Any, Optional
import uuid

import httpx
import pytest

GUIDES = Path(__file__).resolve().parents[1] / "docs" / "html" / "source" / "guides"

_DIRECTIVE = re.compile(r"^\.\. code-block:: (\w+)\s*$")


# -----------------------------------------------------------------------------
def _blocks(path: Path, language: str = "python") -> list[str]:
  """Return the body of each code block of one language, dedented.

  Args:
    path: An RST page.
    language: The ``code-block`` language to collect.

  Returns:
    Each block's source, in page order.
  """
  lines = path.read_text().splitlines()
  blocks = []
  index = 0

  while index < len(lines):
    match = _DIRECTIVE.match(lines[index])
    index += 1

    if match is None or match.group(1) != language:
      continue

    body = []

    # The body is every indented or blank line up to the next line that
    # starts in column one; option lines (":caption:") are not used here.
    while index < len(lines) and (not lines[index].strip() or lines[index].startswith(" ")):
      body.append(lines[index])
      index += 1

    blocks.append(textwrap.dedent("\n".join(body)).strip() + "\n")

  return blocks


# -----------------------------------------------------------------------------
def _run(source: str, path: Path) -> dict[str, Any]:
  """Execute guide code as a module that is not ``__main__``.

  Args:
    source: The code.
    path: The page it came from, for tracebacks.

  Returns:
    The module namespace after execution.
  """
  namespace: dict[str, Any] = {"__name__": "guide"}
  # The code is this repo's own docs, which is what the test exists to run.
  exec(compile(source, str(path), "exec"), namespace)  # nosec B102  # noqa: DUO105,DUO110,SCS101
  return namespace


class FakeServe:
  """An in-memory ``bw serve``: just the routes the tutorials call.

  Response shapes follow the recordings in ``tests/fixtures/serve/``.

  Attributes:
    locked: Answer every vault route with the locked-vault 400.
    forbidden: Answer every route with the Host check's 403.
    unreachable: Fail every request as a refused connection would.
    folders: Folder id to name.
    items: Item id to its stored JSON.
    sent: Each request as ``(method, path, body)``.
    ORGANIZATION: The id of the one organization.
    COLLECTION: The id of its one collection, "Tutorial collection".
  """

  ORGANIZATION = "f64481e2-dc5d-48cf-8db1-e6d5331fe910"
  COLLECTION = "b88b7b2c-a25d-40f7-a56f-afb8c03ccb5b"

  def __init__(self: FakeServe) -> None:
    self.locked = False
    self.forbidden = False
    self.unreachable = False
    self.folders: dict[str, str] = {}
    self.items: dict[str, dict[str, Any]] = {}
    self.sent: list[tuple[str, str, Any]] = []

  # ---------------------------------------------------------------------------
  @staticmethod
  def _ok(data: Any = None) -> httpx.Response:
    """Wrap ``data`` in bw serve's success envelope.

    Args:
      data: The ``data`` member, or ``None`` for a bare success.

    Returns:
      A 200 response.
    """
    body: dict[str, Any] = {"success": True}

    if data is not None:
      body["data"] = data

    return httpx.Response(200, json=body)

  # ---------------------------------------------------------------------------
  @staticmethod
  def _listed(entries: list[Any]) -> httpx.Response:
    """Wrap entries in bw serve's list envelope.

    Args:
      entries: The listed objects.

    Returns:
      A 200 response.
    """
    return FakeServe._ok({"object": "list", "data": entries})

  # ---------------------------------------------------------------------------
  def __call__(self: FakeServe, request: httpx.Request) -> httpx.Response:
    """Answer one request.

    Args:
      request: The request the client sent.

    Returns:
      The response.

    Raises:
      ConnectError: When the fake is unreachable.
    """
    path = request.url.path
    body = json.loads(request.content) if request.content else None
    self.sent.append((request.method, path, body))

    if self.unreachable:
      raise httpx.ConnectError("[Errno 2] No such file or directory")

    if self.forbidden:
      return httpx.Response(403, text="Forbidden")

    if path == "/status":
      template = {
        "serverUrl": "https://vault.example.com",
        "userEmail": "someone@example.com",
        "status": "locked" if self.locked else "unlocked"
      }
      return self._ok({"object": "template", "template": template})

    if self.locked:
      return httpx.Response(400, json={"success": False, "message": "Vault is locked."})

    return self._vault(request.method, path, body, request.url.params)

  # ---------------------------------------------------------------------------
  def _vault(self: FakeServe, method: str, path: str, body: Any, params: httpx.QueryParams) -> httpx.Response:
    """Answer a route that needs the vault unlocked.

    Args:
      method: HTTP method.
      path: Request path.
      body: Parsed JSON body, or ``None``.
      params: Query parameters.

    Returns:
      The response; a 404 for a route the fake does not know.
    """
    parts = path.strip("/").split("/")
    answer = None

    if (method, parts[0]) == ("POST", "sync"):
      answer = self._ok({"object": "message", "title": "Syncing complete."})

    elif method == "GET" and parts[0] == "list":
      answer = self._list(parts[2], params)

    elif parts[0] == "object":
      answer = self._object(method, parts[1], parts[2] if len(parts) > 2 else None, body)

    elif (method, parts[0]) == ("POST", "move"):
      self.items[parts[1]].update(organizationId=parts[2], collectionIds=body)
      answer = self._ok(self.items[parts[1]])

    return answer or httpx.Response(404, text=f"the fake has no route {method} {path}")

  # ---------------------------------------------------------------------------
  def _list(self: FakeServe, kind: str, params: httpx.QueryParams) -> Optional[httpx.Response]:
    """Answer ``GET /list/object/<kind>``.

    Args:
      kind: ``folders``, ``items`` or ``collections``.
      params: Query parameters.

    Returns:
      The response, or ``None`` for a kind the fake does not know.
    """
    if kind == "folders":
      folders = [{"object": "folder", "id": key, "name": name} for key, name in self.folders.items()]
      return self._listed([*folders, {"object": "folder", "id": "", "name": "No Folder"}])

    if kind == "items":
      folder_id = params.get("folderid")
      return self._listed([item for item in self.items.values() if folder_id is None or item.get("folderId") == folder_id])

    if kind == "collections":
      collection = {
        "object": "collection",
        "id": self.COLLECTION,
        "organizationId": self.ORGANIZATION,
        "name": "Tutorial collection"
      }
      return self._listed([collection] if params.get("search", "") in collection["name"] else [])

    return None

  # ---------------------------------------------------------------------------
  def _object(self: FakeServe, method: str, kind: str, object_id: Optional[str], body: Any) -> Optional[httpx.Response]:
    """Answer ``/object/<kind>`` and ``/object/<kind>/<id>``.

    Args:
      method: HTTP method.
      kind: ``folder`` or ``item``.
      object_id: The id in the path, if any.
      body: Parsed JSON body, or ``None``.

    Returns:
      The response, or ``None`` for a route the fake does not know.
    """
    store: dict[str, Any] = self.folders if kind == "folder" else self.items

    if method == "POST":
      new_id = str(uuid.uuid4())
      stored = {**body, "object": kind, "id": new_id} if kind == "item" else {"object": kind, "id": new_id, "name": body["name"]}
      store[new_id] = stored if kind == "item" else body["name"]
      return self._ok(stored)

    if method == "GET" and kind == "item" and object_id is not None:
      return self._ok(self.items[object_id])

    if method == "DELETE" and object_id is not None:
      store.pop(object_id)
      return self._ok()

    return None


# -----------------------------------------------------------------------------
@pytest.fixture
def fake(monkeypatch: pytest.MonkeyPatch) -> FakeServe:
  """Route every transport ``ApiClient`` builds, TCP or socket, to a fake.

  Args:
    monkeypatch: Restores ``httpx.HTTPTransport`` afterwards.

  Returns:
    The fake server.
  """
  server = FakeServe()

  def transport(**kwargs: Any) -> httpx.MockTransport:  # noqa: U100 - takes HTTPTransport's keywords, and needs none.
    return httpx.MockTransport(server)

  monkeypatch.setattr(httpx, "HTTPTransport", transport)
  return server  # noqa: R504 - transport closes over it, which the check does not see.


# -----------------------------------------------------------------------------
def _pages() -> list[Path]:
  """Return every guide page.

  Returns:
    The ``.rst`` files under ``guides/``, sorted.
  """
  return sorted(GUIDES.glob("*.rst"))


# -----------------------------------------------------------------------------
def test_guides_are_found() -> None:
  """The page list is derived, so it must hold the known pages and their code."""
  names = {path.name for path in _pages()}

  assert {"organise-items.rst", "script-over-socket.rst", "troubleshooting.rst"} <= names
  assert all(_blocks(path) for path in _pages())


# -----------------------------------------------------------------------------
@pytest.mark.parametrize("path", _pages(), ids=lambda path: path.name)
def test_every_block_compiles(path: Path) -> None:
  """Each Python block on each guide page is valid Python on its own."""
  for block in _blocks(path):
    compile(block, str(path), "exec")  # noqa: DUO110 - compiled to check the syntax, never run.


# -----------------------------------------------------------------------------
class TestOrganiseItems:
  """The create-and-organise tutorial does what its page says.

  Attributes:
    PAGE: The tutorial's page.
  """

  PAGE = GUIDES / "organise-items.rst"

  def test_runs_end_to_end(self: TestOrganiseItems, fake: FakeServe, capsys: pytest.CaptureFixture[str]) -> None:
    """Folder, login, read back, move and clean up all happen, in order."""
    _run("".join(_blocks(self.PAGE)), self.PAGE)  # act

    routes = [(method, path.split("/")[1]) for method, path, _ in fake.sent]
    output = capsys.readouterr().out
    assert ("POST", "move") in routes
    assert "Moved to organization " + FakeServe.ORGANIZATION in output
    assert fake.items == {}
    assert fake.folders == {}

  @pytest.mark.usefixtures("fake")
  def test_shows_the_output_the_page_claims(self: TestOrganiseItems, capsys: pytest.CaptureFixture[str]) -> None:
    """Every line of the page's sample output is printed, secrets masked."""
    _run("".join(_blocks(self.PAGE)), self.PAGE)  # act

    printed = capsys.readouterr().out.splitlines()
    claimed = _blocks(self.PAGE, "text")[0]
    assert claimed.splitlines()
    assert all(line in printed for line in claimed.splitlines())

  def test_hidden_value_is_sent_but_never_printed(
    self: TestOrganiseItems, fake: FakeServe, capsys: pytest.CaptureFixture[str]
  ) -> None:
    """The hidden field reaches bw serve in the clear and the output masked."""
    _run("".join(_blocks(self.PAGE)), self.PAGE)  # act

    added = next(body for method, path, body in fake.sent if (method, path) == ("POST", "/object/item"))
    assert added["fields"][0] == {"name": "Recovery code", "value": "TUTORIAL-1234-5678", "type": 1}
    assert "TUTORIAL-1234-5678" not in capsys.readouterr().out


# -----------------------------------------------------------------------------
class TestScriptOverSocket:
  """The socket tutorial's script exits with the status its table gives.

  Attributes:
    PAGE: The tutorial's page.
  """

  PAGE = GUIDES / "script-over-socket.rst"

  def _main(self: TestScriptOverSocket) -> Any:
    """Load the page's first block, the script, and return its ``main``.

    Returns:
      The script's ``main``.
    """
    return _run(_blocks(self.PAGE)[0], self.PAGE)["main"]

  @pytest.mark.usefixtures("fake")
  def test_whole_page_runs(self: TestScriptOverSocket, capsys: pytest.CaptureFixture[str]) -> None:
    """Every block runs together, the returned-error variant included."""
    namespace = _run("".join(_blocks(self.PAGE)), self.PAGE)

    status = namespace["main"]()  # act

    assert status == 0
    assert "1 folders" in capsys.readouterr().out

  def test_counts_logins_per_folder(self: TestScriptOverSocket, fake: FakeServe, capsys: pytest.CaptureFixture[str]) -> None:
    """Logins are counted under their folder's name; other items are not."""
    fake.folders["9725df6a-c6b5-43c8-af66-875309714845"] = "Work"
    fake.items = {
      "1": {
        "id": str(uuid.uuid4()),
        "type": 1,
        "folderId": "9725df6a-c6b5-43c8-af66-875309714845"
      },
      "2": {
        "id": str(uuid.uuid4()),
        "type": 1,
        "folderId": "9725df6a-c6b5-43c8-af66-875309714845"
      },
      "3": {
        "id": str(uuid.uuid4()),
        "type": 1
      },
      "4": {
        "id": str(uuid.uuid4()),
        "type": 2
      },
    }

    status = self._main()()  # act

    assert status == 0
    assert capsys.readouterr().out.splitlines() == ["    2  Work", "    1  No Folder"]

  @pytest.mark.parametrize(("failure", "expected"), [("locked", 1), ("unreachable", 2), ("forbidden", 3)])
  def test_failure_exit_status(self: TestScriptOverSocket, fake: FakeServe, failure: str, expected: int) -> None:
    """A locked vault, no server and a refused Host each get their own status."""
    setattr(fake, failure, True)

    status = self._main()()  # act

    assert status == expected

  def test_connects_to_the_socket(self: TestScriptOverSocket, fake: FakeServe, monkeypatch: pytest.MonkeyPatch) -> None:
    """The script connects to the socket named in ``BW_SERVE_SOCKET``."""
    seen: list[Optional[str]] = []
    monkeypatch.setattr(httpx, "HTTPTransport", lambda **kwargs: seen.append(kwargs.get("uds")) or httpx.MockTransport(fake))
    monkeypatch.setenv("BW_SERVE_SOCKET", "/run/user/1000/bw.sock")

    self._main()()  # act

    assert seen == ["/run/user/1000/bw.sock"]
