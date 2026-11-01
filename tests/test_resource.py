"""Tests for the Resource base class."""

from __future__ import annotations

import json
import logging
from typing import Any, TYPE_CHECKING
from uuid import uuid4

from pydantic import BaseModel
import pytest

from bw_serve_client._generated.models import FolderSchema
from bw_serve_client._generated.models import ListObjectFoldersGetParameters
from bw_serve_client._generated.models import MoveItemRequestSchema
from bw_serve_client._generated.models import ObjectFolderIdGetParameters
from bw_serve_client.errors import DefaultErrorHandler
from bw_serve_client.errors import ExternalServiceError
from bw_serve_client.errors import UserError
from bw_serve_client.errors import ValidationError
from bw_serve_client.resource import declared_routes
from bw_serve_client.resource import Resource
from bw_serve_client.resource import route
from bw_serve_client.resource import routed_methods
from bw_serve_client.resource import RouteKey

if TYPE_CHECKING:
  from conftest import MakeClient
  from conftest import ReturningHandler
  import httpx

FOLDER_ID = "3a84be8d-12e7-4223-98cd-ae0000eabdec"


class Thing(BaseModel):
  """A response payload for the tests to parse into.

  Attributes:
    id: Identifier.
    name: Display name.
  """

  id: str
  name: str


def _ok(data: object) -> dict[str, object]:
  """Wrap a payload the way bw serve does on success.

  Args:
    data: The ``data`` member.

  Returns:
    The response body.
  """
  return {"success": True, "data": data}


# -----------------------------------------------------------------------------
class TestConstruction:
  """Logger and handler defaults."""

  def test_inherits_client_logger_and_handler(self: TestConstruction, make_client: MakeClient) -> None:
    """With neither given, the client's logger and handler are used."""
    client = make_client()

    resource = Resource(client)  # act

    assert resource.client is client
    assert resource.logger is client.logger
    assert resource.error_handler is client.error_handler

  def test_uses_injected_logger_and_handler(
    self: TestConstruction, make_client: MakeClient, returning_handler: ReturningHandler
  ) -> None:
    """Injected objects replace the client's."""
    logger = logging.getLogger("test.resource.injected")

    resource = Resource(make_client(), logger=logger, error_handler=returning_handler)  # act

    assert resource.logger is logger
    assert resource.error_handler is returning_handler


# -----------------------------------------------------------------------------
class TestValidation:
  """Path, query and body are validated before anything is sent."""

  def test_valid_path_params_fill_the_template(self: TestValidation, make_client: MakeClient, sent: list[httpx.Request]) -> None:
    """A validated path parameter is formatted into the path."""
    resource = Resource(make_client(json_body=_ok({"id": FOLDER_ID, "name": "Notes"})))

    resource._request("GET", "/object/folder/{id}", path_params=(ObjectFolderIdGetParameters, {"id": FOLDER_ID}))  # act

    [request] = sent
    assert request.url.path == f"/object/folder/{FOLDER_ID}"

  def test_none_query_fields_are_omitted(self: TestValidation, make_client: MakeClient, sent: list[httpx.Request]) -> None:
    """A query field that is None is not sent."""
    resource = Resource(make_client(json_body=_ok(None)))

    resource._request("GET", "/list/object/folders", query=(ListObjectFoldersGetParameters, {"search": None}))  # act

    [request] = sent
    assert request.url.query == b""

  def test_query_fields_are_sent(self: TestValidation, make_client: MakeClient, sent: list[httpx.Request]) -> None:
    """A set query field is sent as a query parameter."""
    resource = Resource(make_client(json_body=_ok(None)))

    resource._request("GET", "/list/object/folders", query=(ListObjectFoldersGetParameters, {"search": "Notes"}))  # act

    [request] = sent
    assert request.url.params["search"] == "Notes"

  @pytest.mark.parametrize(
    "kwargs",
    [
      {
        "path_params": (ObjectFolderIdGetParameters, {
          "id": "not-a-uuid"
        })
      },
      {
        "query": (ListObjectFoldersGetParameters, {
          "search": 5
        })
      },
      {
        "body": (FolderSchema, {
          "name": "x",
          "unexpected": True
        })
      },
    ],
    ids=["path", "query", "body"],
  )
  def test_invalid_input_raises_before_sending(
    self: TestValidation, make_client: MakeClient, sent: list[httpx.Request], kwargs: dict[str, Any]
  ) -> None:
    """Input that fails its model is a ValidationError, and nothing is sent."""
    resource = Resource(make_client())

    with pytest.raises(ValidationError, match="invalid") as exc_info:  # act
      resource._request("POST", "/object/folder/{id}", **kwargs)

    # The pydantic error holds the input, which can be a secret (#30).
    assert exc_info.value.__cause__ is None
    assert exc_info.value.__context__ is None
    assert sent == []

  def test_invalid_input_with_returning_handler(
    self: TestValidation, make_client: MakeClient, sent: list[httpx.Request], returning_handler: ReturningHandler
  ) -> None:
    """A handler that returns has its value come back, and nothing is sent."""
    resource = Resource(make_client(), error_handler=returning_handler)

    result = resource._request("GET", "/object/folder/{id}", path_params=(ObjectFolderIdGetParameters, {"id": "nope"}))  # act

    assert result is returning_handler.result
    [(category, _, status_code, cause)] = returning_handler.calls
    assert category is ValidationError
    assert status_code is None
    assert cause is None
    assert sent == []


# -----------------------------------------------------------------------------
class TestRequestBody:
  """The body is built in the content type the API expects."""

  def test_body_is_sent_as_json(self: TestRequestBody, make_client: MakeClient, sent: list[httpx.Request]) -> None:
    """A validated body goes out as JSON."""
    resource = Resource(make_client(json_body=_ok(None)))

    resource._request("POST", "/object/folder", body=(FolderSchema, {"name": "Notes"}))  # act

    [request] = sent
    assert request.headers["Content-Type"] == "application/json"
    assert json.loads(request.content) == {"name": "Notes"}

  def test_body_with_files_is_sent_as_multipart(self: TestRequestBody, make_client: MakeClient, sent: list[httpx.Request]) -> None:
    """With files, the body fields ride along as multipart form fields."""
    resource = Resource(make_client(json_body=_ok(None)))

    resource._request("POST", "/attachment", body=(FolderSchema, {"name": "Notes"}), files={"file": ("a.txt", b"hello")})  # act

    [request] = sent
    assert request.headers["Content-Type"].startswith("multipart/form-data; boundary=")
    assert b'name="name"' in request.content
    assert b'filename="a.txt"' in request.content

  def test_root_model_body_is_sent_as_the_bare_array(
    self: TestRequestBody, make_client: MakeClient, sent: list[httpx.Request]
  ) -> None:
    """A RootModel body takes its root value and sends it as is."""
    resource = Resource(make_client(json_body=_ok(None)))

    resource._request("POST", "/move/x/y", body=(MoveItemRequestSchema, [FOLDER_ID]))  # act

    [request] = sent
    assert request.headers["Content-Type"] == "application/json"
    assert json.loads(request.content) == [FOLDER_ID]

  def test_root_model_body_is_validated(self: TestRequestBody, make_client: MakeClient, sent: list[httpx.Request]) -> None:
    """Each element of a RootModel body is validated, and a failure names its position."""
    resource = Resource(make_client(json_body=_ok(None)))

    with pytest.raises(ValidationError, match=r"invalid body for POST /move/x/y: 1: "):
      resource._request("POST", "/move/x/y", body=(MoveItemRequestSchema, [FOLDER_ID, "not-a-uuid"]))

    assert sent == []

  def test_no_body_sends_nothing(self: TestRequestBody, make_client: MakeClient, sent: list[httpx.Request]) -> None:
    """Without a body, the request has none."""
    resource = Resource(make_client(json_body=_ok(None)))

    resource._request("DELETE", "/object/folder/{id}", path_params=(ObjectFolderIdGetParameters, {"id": FOLDER_ID}))  # act

    [request] = sent
    assert request.content == b""


# -----------------------------------------------------------------------------
class TestResponseParsing:
  """The response's data member is parsed into the response type."""

  def test_parses_into_model(self: TestResponseParsing, make_client: MakeClient) -> None:
    """A single object parses into the model."""
    resource = Resource(make_client(json_body=_ok({"id": "1", "name": "Notes"})))

    result = resource._request("GET", "/thing", response_type=Thing)  # act

    assert result == Thing(id="1", name="Notes")

  def test_unwraps_list_envelope(self: TestResponseParsing, make_client: MakeClient) -> None:
    """A list envelope is unwrapped and each item parsed."""
    items = [{"id": "1", "name": "a"}, {"id": "2", "name": "b"}]
    resource = Resource(make_client(json_body=_ok({"object": "list", "data": items})))

    result = resource._request("GET", "/things", response_type=list[Thing])  # act

    assert result == [Thing(id="1", name="a"), Thing(id="2", name="b")]

  def test_bytes_returns_the_raw_body(self: TestResponseParsing, make_client: MakeClient) -> None:
    """A bytes response type returns the body itself, with no envelope."""
    resource = Resource(make_client(text_body="file content, not an envelope"))

    result = resource._request("GET", "/object/attachment/x", response_type=bytes)  # act

    assert result == b"file content, not an envelope"

  def test_no_response_type_returns_none(self: TestResponseParsing, make_client: MakeClient) -> None:
    """Without a response type the body is not read."""
    resource = Resource(make_client(text_body="not json at all"))

    result = resource._request("DELETE", "/thing")  # act

    assert result is None

  @pytest.mark.parametrize(
    ("body", "match"),
    [
      ({
        "text_body": "<html>oops</html>"
      }, "no data member"),
      ({
        "json_body": {
          "success": True
        }
      }, "no data member"),
      ({
        "json_body": _ok({"id": "1"})
      }, "does not match"),
    ],
    ids=["not-json", "no-data", "wrong-shape"],
  )
  def test_unparseable_2xx_is_external_service_error(
    self: TestResponseParsing, make_client: MakeClient, body: dict[str, Any], match: str
  ) -> None:
    """A 2xx body that cannot be parsed is the service's fault."""
    resource = Resource(make_client(**body))

    with pytest.raises(ExternalServiceError, match=match) as exc_info:  # act
      resource._request("GET", "/thing", response_type=Thing)

    assert exc_info.value.status_code == 200

  def test_unparseable_2xx_with_returning_handler(
    self: TestResponseParsing, make_client: MakeClient, returning_handler: ReturningHandler
  ) -> None:
    """A returning handler's value replaces the parse result."""
    resource = Resource(make_client(json_body=_ok({"id": "1"})), error_handler=returning_handler)

    result = resource._request("GET", "/thing", response_type=Thing)  # act

    assert result is returning_handler.result
    [(category, _, _, cause)] = returning_handler.calls
    assert category is ExternalServiceError
    assert cause is None


# -----------------------------------------------------------------------------
class TestMember:
  """_member takes one member of a parsed response and passes anything else through."""

  def test_returns_the_member_of_the_model(self: TestMember) -> None:
    """A parsed response yields the named member."""
    result = Resource._member(Thing(id="1", name="Notes"), Thing, "name")  # act

    assert result == "Notes"

  @pytest.mark.parametrize("handled", [None, "handled", {"name": "not a Thing"}])
  def test_passes_a_handler_value_through(self: TestMember, handled: Any) -> None:
    """Whatever the error handler returned comes back untouched."""
    result = Resource._member(handled, Thing, "name")  # act

    assert result is handled


# -----------------------------------------------------------------------------
class TestStatusHandling:
  """Error statuses become domain errors through the resource's handler."""

  @pytest.mark.parametrize(
    ("status", "message", "category"),
    [
      (400, "Bad request.", ValidationError),
      (400, "Vault is locked.", UserError),
      (404, "Not Found", ValidationError),
      (500, "Internal Server Error", ExternalServiceError),
    ],
  )
  def test_error_status_raises_domain_error(
    self: TestStatusHandling, make_client: MakeClient, status: int, message: str, category: type[Exception]
  ) -> None:
    """Each error status raises its category with the server's message."""
    resource = Resource(make_client(status=status, json_body={"success": False, "message": message}))

    with pytest.raises(category, match=message):  # act
      resource._request("GET", "/thing", response_type=Thing)

  def test_resource_handler_is_used_not_the_clients(
    self: TestStatusHandling, make_client: MakeClient, returning_handler: ReturningHandler
  ) -> None:
    """The resource's handler gets the failure even though the client's would raise."""
    client = make_client(status=500, json_body={"success": False, "message": "boom"})
    assert isinstance(client.error_handler, DefaultErrorHandler)
    resource = Resource(client, error_handler=returning_handler)

    result = resource._request("GET", "/thing", response_type=Thing)  # act

    assert result is returning_handler.result
    assert returning_handler.calls == [(ExternalServiceError, "boom", 500, None)]

  def test_logs_through_the_resource_logger(
    self: TestStatusHandling, make_client: MakeClient, caplog: pytest.LogCaptureFixture
  ) -> None:
    """The request is logged at debug on the resource's logger."""
    resource = Resource(make_client(json_body=_ok(None)), logger=logging.getLogger("test.resource.log"))

    with caplog.at_level(logging.DEBUG, logger="test.resource.log"):  # act
      resource._request("GET", "/object/folder/{id}", path_params=(ObjectFolderIdGetParameters, {"id": str(uuid4())}))

    assert any(r.name == "test.resource.log" and r.message.startswith("GET /object/folder/") for r in caplog.records)


# -----------------------------------------------------------------------------
class TestRouteDeclaration:
  """The @route decorator and the functions that read it back."""

  def test_records_the_route_and_returns_the_function(self: TestRouteDeclaration) -> None:
    """The function comes back unchanged, carrying its route."""

    def method() -> str:
      return "called"

    decorated = route("GET", "/status")(method)  # act

    assert decorated is method
    assert decorated() == "called"
    assert declared_routes(decorated) == (RouteKey("GET", "/status"),)

  def test_stacked_routes_are_all_recorded(self: TestRouteDeclaration) -> None:
    """A method serving two routes declares both, outermost first."""

    @route("GET", "/list/object/send")
    @route("GET", "/send/list")
    def method() -> None:
      """Serve both."""

    assert declared_routes(method) == (RouteKey("GET", "/list/object/send"), RouteKey("GET", "/send/list"))

  def test_undecorated_function_declares_nothing(self: TestRouteDeclaration) -> None:
    """A plain function, or any other object, has no routes."""
    assert declared_routes(len) == ()
    assert declared_routes(None) == ()

  def test_route_key_spells_method_and_path(self: TestRouteDeclaration) -> None:
    """Spell a route the way the exclusion list keys it: METHOD /path."""
    assert str(RouteKey("PUT", "/object/folder/{id}")) == "PUT /object/folder/{id}"

  def test_routed_methods_reads_only_the_class_namespace(self: TestRouteDeclaration) -> None:
    """Declared methods are listed by the class defining them, never by a subclass."""

    class Base:

      @route("POST", "/lock")
      def lock(self: Base) -> None:
        """Lock."""

      def helper(self: Base) -> None:
        """Do nothing; no route is declared."""

    class Child(Base):

      @route("POST", "/unlock")
      def unlock(self: Child) -> None:
        """Unlock."""

    assert routed_methods(Base) == {"lock": (RouteKey("POST", "/lock"),)}
    assert routed_methods(Child) == {"unlock": (RouteKey("POST", "/unlock"),)}
