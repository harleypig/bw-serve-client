Models
======

The request and response models, generated from Bitwarden's OpenAPI spec
for the Vault Management API. They are pydantic 2 models; import any of
them from the package itself::

   from bw_serve_client import FolderSchema

Fields that hold secrets are ``SecretStr``, so they do not print; call
``get_secret_value()`` to read one. Each model's fields are listed under
it, by their Python names; the JSON name, where it differs, is the
field's alias.

.. automodule:: bw_serve_client._generated.models
   :members:
   :exclude-members: model_config
