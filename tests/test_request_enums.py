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

  @pytest.mark.parametrize("item_type", [0, 9, 99])
  def test_refused_before_sending(
    self: TestUnknownItemType, make_client: MakeClient, sent: list[httpx.Request], item_type: int
  ) -> None:
    """The item body fails validation, and the transport sees nothing."""
    resource = Resource(make_client())
    body = {"type": item_type, "name": "Bad type"}

    with pytest.raises(ValidationError, match=r"invalid body for POST /object/item: type: "):  # act
      resource._request("POST", "/object/item", body=(models.ItemTemplateSchema, body))

    assert sent == []

  def test_known_type_is_sent(self: TestUnknownItemType, make_client: MakeClient, sent: list[httpx.Request]) -> None:
    """The check above is not refusing everything: an SSH key goes out."""
    resource = Resource(make_client(json_body={"success": True, "data": None}))

    resource._request("POST", "/object/item", body=(models.ItemTemplateSchema, {"type": 5, "name": "Key"}))  # act

    [request] = sent
    assert json.loads(request.content) == {"type": 5, "name": "Key"}
