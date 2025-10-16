Data Models
===========

Data structures and models used by the bw-serve-client library.

.. note::
   This section documents the data structures used internally by the library.
   For information about the Bitwarden API data models, refer to the
   `Bitwarden Vault Management API documentation <https://bitwarden.com/help/vault-management-api/>`_.

Request/Response Data
---------------------

The library handles various data types for API requests and responses:

String Data
~~~~~~~~~~~

String data is passed through directly without serialization:

.. code-block:: python

   # String data is sent as-is
   client.post("/endpoint", data="raw string data")

Dictionary Data
~~~~~~~~~~~~~~~

Dictionary data is automatically serialized to JSON:

.. code-block:: python

   # Dictionary data is serialized to JSON
   data = {
       "name": "My Item",
       "type": 1,
       "login": {
           "username": "user@example.com",
           "password": "secure-password"
       }
   }
   client.post("/vault/items", data=data)

File Data
~~~~~~~~~

File data is handled as multipart form data:

.. code-block:: python

   # File uploads use multipart form data
   files = {
       "file": ("attachment.txt", open("attachment.txt", "rb"), "text/plain")
   }
   client.post("/vault/attachments", files=files)

Response Data
~~~~~~~~~~~~~

Response data is automatically deserialized based on content type:

.. code-block:: python

   # JSON responses are automatically parsed
   response = client.get("/vault/items")
   # response is a Python object (list, dict, etc.)

   # Non-JSON responses are returned as strings
   response = client.get("/vault/export")
   # response is a string