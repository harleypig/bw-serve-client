"""The base class of the generated custom-field models.

``codegen`` makes ``FieldSchema`` and ``FieldResponseSchema`` subclasses of
:class:`CustomField` (``base-class-map`` in ``pyproject.toml``), so it must
not import the generated models.
"""

from __future__ import annotations

from pydantic import BaseModel
from pydantic import model_validator
from pydantic import SecretStr

#: The custom-field type Bitwarden masks.
HIDDEN = 1


class CustomField(BaseModel):
  """A custom field whose value is a ``SecretStr`` when the field is hidden.

  A hidden field (``type`` 1) holds a secret, so its ``value`` is wrapped in
  ``SecretStr`` and shows in no repr, str or log record; read it with
  ``get_secret_value()``. Text, boolean and linked fields keep a plain
  ``str``. A request sends the real value: ``ApiClient`` reveals it as it
  sends.

  The wrapping runs on validation, so a field built with
  ``model_construct`` or changed by assignment or ``model_copy`` afterwards
  is not wrapped.
  """

  # ---------------------------------------------------------------------------
  @model_validator(mode="after")
  def _hide_hidden_value(self: CustomField) -> CustomField:
    """Wrap a hidden field's value in ``SecretStr``.

    Returns:
        The model, its value wrapped when the field is hidden.
    """
    # Through __dict__: the fields are the subclass's, so this base cannot
    # name them to a type checker.
    fields = self.__dict__

    if fields.get("type") == HIDDEN and isinstance(fields.get("value"), str):
      fields["value"] = SecretStr(fields["value"])

    return self
