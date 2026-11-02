"""The enumerated request fields allow exactly what the pinned bw CLI accepts.

Each expected set below was read from the Bitwarden source at the CLI
release in ``upstream/lock.json`` (#108): ``clients`` is bitwarden/clients
at that tag, ``sdk`` is bitwarden/sdk-internal at 4a9eb239, the
0.2.0-main.1126 build the release pins in its ``package.json``.

A CLI bump changes the lock file, which fails ``test_values_were_read_at_
the_locked_release`` until the cited files have been re-read at the new tag;
a value added or dropped there then fails the field's case here until the
spec fix and this table agree again.
"""

from __future__ import annotations

from enum import Enum
from enum import IntEnum
import json
from pathlib import Path
import types
from typing import Any, get_args, get_origin, Literal, TYPE_CHECKING, Union

from conftest import load_recorded
from pydantic import SecretStr
import pytest

from bw_serve_client._generated import models
from bw_serve_client.errors import ValidationError
from bw_serve_client.resource import Resource

if TYPE_CHECKING:
  from conftest import MakeClient
  import httpx
  from pydantic import BaseModel

LOCK = Path(__file__).resolve().parent.parent / "upstream" / "lock.json"

#: The CLI release the table below was read at.
READ_AT = "cli-v2026.10.1"

# model, field, allowed values, where they come from.
REQUEST_ENUMS = [
  pytest.param(
    models.ItemTemplateSchema,
    "type",
    {1, 2, 3, 4, 5, 6, 7, 8},
    id="item.type",
    # clients libs/common/src/vault/enums/cipher-type.ts;
    # sdk crates/bitwarden-vault/src/cipher/cipher.rs (CipherType).
  ),
  pytest.param(
    models.ItemTemplateSchema,
    "reprompt",
    {0, 1},
    id="item.reprompt",
    # clients libs/common/src/vault/enums/cipher-reprompt-type.ts;
    # sdk crates/bitwarden-vault/src/cipher/cipher.rs (CipherRepromptType).
  ),
  pytest.param(
    models.ItemSecureNoteSchema,
    "type",
    {0},
    id="item.secureNote.type",
    # clients libs/common/src/vault/enums/secure-note-type.enum.ts;
    # sdk crates/bitwarden-vault/src/cipher/secure_note.rs (SecureNoteType).
  ),
  pytest.param(
    models.UrisSchema,
    "match",
    {0, 1, 2, 3, 4, 5},
    id="item.login.uris.match",
    # clients libs/common/src/models/domain/domain-service.ts
    # (UriMatchStrategy); sdk crates/bitwarden-vault/src/cipher/login.rs
    # (UriMatchType).
  ),
  pytest.param(
    models.FieldSchema,
    "type",
    {0, 1, 2, 3},
    id="item.fields.type",
    # clients libs/common/src/vault/enums/field-type.enum.ts;
    # sdk crates/bitwarden-vault/src/cipher/field.rs (FieldType).
  ),
  pytest.param(
    models.SendTemplateSchema,
    "type",
    {0, 1},
    id="send.type",
    # clients libs/common/src/tools/send/types/send-type.ts has Item=2 as
    # well, but apps/cli/src/tools/send/commands/create.command.ts answers
    # it "not yet available" on every server, so it is left out.
  ),
  pytest.param(
    models.ObjectTemplateTypeGetParameters,
    "type",
    {
      "item",
      "item.field",
      "item.login",
      "item.login.uri",
      "item.card",
      "item.identity",
      "item.securenote",
      "item.bankaccount",
      "item.driverslicense",
      "item.passport",
      "folder",
      "collection",
      "item-collections",
      "org-collection",
    },
    id="template.type",
    # clients apps/cli/src/commands/get.command.ts (getTemplate).
  ),
  pytest.param(
    models.ArchiveObjectIdPostParameters,
    "object",
    {"item"},
    id="archive.object",
    # clients apps/cli/src/vault/archive.command.ts (run).
  ),
]


# -----------------------------------------------------------------------------
def _choices(model: type[BaseModel], field: str) -> tuple[Any, set[Any]]:
  """Find the enum or literal a field is restricted to.

  Args:
    model: A generated model.
    field: The field's python name.

  Returns:
    The restricting type, an Enum class or ``Literal[...]``, and its values.
  """
  annotation = model.model_fields[field].annotation

  if get_origin(annotation) in (Union, types.UnionType):
    [annotation] = [arg for arg in get_args(annotation) if arg is not type(None)]

  if isinstance(annotation, type) and issubclass(annotation, Enum):
    return annotation, {member.value for member in annotation}

  assert get_origin(annotation) is Literal, f"{model.__name__}.{field} is {annotation!r}, not an enum"

  return annotation, set(get_args(annotation))


# -----------------------------------------------------------------------------
def test_values_were_read_at_the_locked_release() -> None:
  """The table was read at the CLI release the lock file pins."""
  release = json.loads(LOCK.read_text(encoding="utf-8"))["cli"]["release"]  # act

  assert release == READ_AT, f"re-read every source cited in {Path(__file__).name} at {release}, then update READ_AT"


@pytest.mark.parametrize(("model", "field", "expected"), REQUEST_ENUMS)
def test_enum_allows_what_the_cli_accepts(model: type[BaseModel], field: str, expected: set[Any]) -> None:
  """Each enumerated request field allows exactly the cited values."""
  _, allowed = _choices(model, field)  # act

  assert allowed == expected


@pytest.mark.parametrize(("model", "field", "expected"), REQUEST_ENUMS)
def test_integer_enums_are_int_enums(model: type[BaseModel], field: str, expected: set[Any]) -> None:
  """An enum of numbers is an IntEnum, so its members compare as numbers."""
  restriction, _ = _choices(model, field)  # act

  if all(isinstance(value, int) for value in expected) and isinstance(restriction, type):
    assert issubclass(restriction, IntEnum), restriction.__name__


@pytest.mark.parametrize("brand", ["visa", "amex", "Mastercard", "Diners Club", "anything at all"])
def test_card_brand_is_free_text(brand: str) -> None:
  """A card brand is any string; the CLI stores it as entered.

  clients libs/common/src/models/export/card.export.ts declares
  ``brand?: string``; sdk crates/bitwarden-vault/src/cipher/card.rs holds
  ``brand: Option<String>``.
  """
  card = models.ItemCardSchema.model_validate({"brand": brand})  # act

  assert card.brand == brand


# -----------------------------------------------------------------------------
class TestUnknownItemType:
  """An unknown item type never reaches bw serve.

  With CLI 2026.10.1, ``"type": 99`` takes bw serve down against
  Vaultwarden and is stored as a login against Bitwarden Cloud (#108).
  """

  @pytest.mark.parametrize("item_type", [0, 9, 99, None])
  def test_refused_before_sending(
    self: TestUnknownItemType, make_client: MakeClient, sent: list[httpx.Request], item_type: int
  ) -> None:
    """The item body fails validation, and the transport sees nothing.

    A missing type is refused too: CipherExport.toView copies it unchecked.
    """
    resource = Resource(make_client())
    body = {"name": "Bad type"} if item_type is None else {"type": item_type, "name": "Bad type"}

    with pytest.raises(ValidationError, match=r"invalid body for POST /object/item: type: "):  # act
      resource._request("POST", "/object/item", body=(models.ItemTemplateSchema, body))

    assert sent == []

  def test_known_type_is_sent(self: TestUnknownItemType, make_client: MakeClient, sent: list[httpx.Request]) -> None:
    """The check above is not refusing everything: an SSH key goes out."""
    resource = Resource(make_client(json_body={"success": True, "data": None}))

    resource._request("POST", "/object/item", body=(models.ItemTemplateSchema, {"type": 5, "name": "Key"}))  # act

    [request] = sent
    assert json.loads(request.content) == {"type": 5, "name": "Key"}


# -----------------------------------------------------------------------------
#: Made-up values for the type 5-8 payloads; secret ones must be SecretStr.
PRIVATE_KEY = "made-up-ssh-private-key-9Tq4"

#: One body per newer item type, with the sub-object CipherExport.toView
#: reads for it (clients libs/common/src/models/export/cipher.export.ts).
NEWER_TYPES = [
  pytest.param(
    5, "sshKey", {
      "privateKey": PRIVATE_KEY,
      "publicKey": "ssh-ed25519 AAAA",
      "keyFingerprint": "SHA256:x"
    }, id="ssh-key"
  ),
  pytest.param(
    6, "bankAccount", {
      "bankName": "Bank",
      "accountNumber": "12345678",
      "pin": "1234",
      "iban": "GB00"
    }, id="bank-account"
  ),
  pytest.param(
    7, "driversLicense", {
      "firstName": "Jo",
      "licenseNumber": "D123",
      "expirationDate": "2030-01-01"
    }, id="drivers-license"
  ),
  pytest.param(8, "passport", {
    "surname": "Doe",
    "passportNumber": "X123",
    "issueDate": "2020-01-01"
  }, id="passport"),
]


class TestItemBodies:
  """Item bodies bw serve accepts are accepted (#108)."""

  @pytest.mark.parametrize(("item_type", "key", "data"), NEWER_TYPES)
  def test_newer_type_with_its_data_is_sent(
    self: TestItemBodies, make_client: MakeClient, sent: list[httpx.Request], item_type: int, key: str, data: dict[str, str]
  ) -> None:
    """A type 5-8 item with its sub-object validates and goes out whole."""
    resource = Resource(make_client(json_body={"success": True, "data": None}))
    body = {"type": item_type, "name": "Newer", key: data}

    resource._request("POST", "/object/item", body=(models.ItemTemplateSchema, body))  # act

    [request] = sent
    assert json.loads(request.content) == body

  def test_ssh_private_key_is_secret(self: TestItemBodies) -> None:
    """The private key is a SecretStr, so the model's repr hides it."""
    item = models.ItemTemplateSchema.model_validate({"type": 5, "sshKey": {"privateKey": PRIVATE_KEY}})  # act

    assert item.ssh_key is not None
    assert isinstance(item.ssh_key.private_key, SecretStr)
    assert PRIVATE_KEY not in repr(item)

  @pytest.mark.parametrize(
    ("case", "model"),
    [
      ("template-item", models.ItemTemplateSchema),
      ("template-item-login", models.ItemLoginSchema),
      ("template-org-collection", models.CollectionSchema),
      ("template-folder", models.FolderSchema),
    ],
  )
  def test_fetched_template_posts_back(self: TestItemBodies, case: str, model: type[BaseModel]) -> None:
    """What ``GET /object/template/{type}`` returns validates as a request body."""
    template = load_recorded(case)["response"]["body"]["data"]["template"]

    result = model.model_validate(template)  # act

    assert result.model_dump(by_alias=True, exclude_unset=True).keys() == template.keys()


# -----------------------------------------------------------------------------
class TestSendBodies:
  """A Send body omitting ``disabled`` still carries it."""

  def test_disabled_defaults_to_false(self: TestSendBodies, make_client: MakeClient, sent: list[httpx.Request]) -> None:
    """Vaultwarden answers 422 without ``disabled``, so false is sent.

    False is the CLI's own template value (clients
    apps/cli/src/tools/send/models/send.response.ts, ``template``).
    """
    resource = Resource(make_client(json_body={"success": True, "data": None}))
    body = {"name": "Text", "type": 0, "text": {"text": "hello"}, "deletionDate": "2030-01-01T00:00:00Z"}

    resource._request("POST", "/object/send", body=(models.SendTemplateSchema, body))  # act

    [request] = sent
    assert json.loads(request.content)["disabled"] is False
