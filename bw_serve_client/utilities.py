"""Utilities domain class for the Bitwarden Vault Management API.

The generator, template and fingerprint routes of the ``Miscellaneous``
tag in the API spec. One method per route::

  GET /object/template/{type} - Utilities.template
  GET /object/fingerprint/me  - Utilities.fingerprint
  GET /generate               - Utilities.generate
"""

from __future__ import annotations

from typing import Any, Optional, TYPE_CHECKING, Union

from ._generated.models import GenerateGetParameters
from ._generated.models import ObjectTemplateTypeGetParameters
from ._generated.models import SecretStringResponseSchema
from ._generated.models import StringResponseSchema
from ._generated.models import TemplateResponseSchema
from .resource import Resource
from .resource import route

if TYPE_CHECKING:
  from pydantic import SecretStr


class Utilities(Resource):
  """Generate passwords, and fetch object templates and the fingerprint phrase.

  bw serve refuses ``template`` and ``fingerprint`` while the vault is
  locked, which is a :class:`~bw_serve_client.errors.UserError`;
  ``generate`` works either way. Construction, logging and error handling are :class:`Resource`'s. Every
  method returns what the error handler returned, in place of its result,
  when a failure is handled without raising.
  """

  # ---------------------------------------------------------------------------
  @route("GET", "/object/template/{type}")
  def template(self: Utilities, object_type: str) -> Any:
    """Retrieve a JSON template for any object.

    Templates can be used to guide you in creation of new objects.

    Args:
        object_type: One of ``item``, ``item.field``, ``item.login``,
            ``item.login.uri``, ``item.card``, ``item.identity``,
            ``item.securenote``, ``item.bankaccount``,
            ``item.driverslicense``, ``item.passport``, ``folder``,
            ``collection``, ``item-collections`` or ``org-collection``;
            anything else is refused before sending.

    Returns:
        The template: a dict for every type but ``item-collections``,
        whose template is a list of collection ids.
    """
    result = self._request(
      "GET",
      "/object/template/{type}",
      path_params=(ObjectTemplateTypeGetParameters, {
        "type": object_type
      }),
      response_type=TemplateResponseSchema
    )

    return self._member(result, TemplateResponseSchema, "template")

  # ---------------------------------------------------------------------------
  @route("GET", "/object/fingerprint/me")
  def fingerprint(self: Utilities) -> Union[str, None, Any]:
    """Retrieve your fingerprint phrase.

    Returns:
        Your account's fingerprint phrase, words joined by hyphens.
    """
    result = self._request("GET", "/object/fingerprint/me", response_type=StringResponseSchema)

    return self._member(result, StringResponseSchema, "data")

  # ---------------------------------------------------------------------------
  @route("GET", "/generate")
  def generate(
    self: Utilities,
    *,
    length: Optional[int] = None,
    uppercase: Optional[bool] = None,
    lowercase: Optional[bool] = None,
    number: Optional[bool] = None,
    special: Optional[bool] = None,
    min_number: Optional[int] = None,
    min_special: Optional[int] = None,
    avoid_ambiguous: Optional[bool] = None,
    passphrase: Optional[bool] = None,
    words: Optional[int] = None,
    separator: Optional[str] = None,
    capitalize: Optional[bool] = None,
    include_number: Optional[bool] = None,
  ) -> Union[SecretStr, None, Any]:
    """Generate a password or passphrase.

    With no arguments, a 14-character password of upper and lower case
    letters and digits. ``None`` leaves an option to bw serve's default.

    The four character sets are all-or-named: naming none gets upper,
    lower and digits, but naming any turns off every one not named --
    ``special=True`` alone gives a password of special characters only.
    bw serve raises a ``length`` under 5 to 5 and ``words`` under 3 to 3,
    and uses only the first character of ``separator``, reading
    ``"space"`` and ``"empty"`` as a space and as nothing.

    ``avoid_ambiguous`` leaves out the characters easily mistaken for one
    another -- ``I``, ``O``, ``l``, ``0`` and ``1``. It is sent as the
    spec's ``ambiguous``, which avoids them when true.

    Args:
        length: Number of characters in the password.
        uppercase: Include uppercase letters in the password.
        lowercase: Include lowercase letters in the password.
        number: Include digits in the password.
        special: Include special characters in the password.
        min_number: Fewest digits the password may hold.
        min_special: Fewest special characters the password may hold.
        avoid_ambiguous: Leave out easily mistaken characters.
        passphrase: Generate a passphrase instead of a password.
        words: Number of words in the passphrase.
        separator: Character between the passphrase's words.
        capitalize: Title-case the passphrase.
        include_number: Include a digit in the passphrase.

    Returns:
        The password or passphrase.
    """
    query = {
      "length": length,
      "uppercase": uppercase,
      "lowercase": lowercase,
      "number": number,
      "special": special,
      "minNumber": min_number,
      "minSpecial": min_special,
      "ambiguous": avoid_ambiguous,
      "passphrase": passphrase,
      "words": words,
      "separator": separator,
      "capitalize": capitalize,
      "includeNumber": include_number,
    }

    result = self._request("GET", "/generate", query=(GenerateGetParameters, query), response_type=SecretStringResponseSchema)

    return self._member(result, SecretStringResponseSchema, "data")
