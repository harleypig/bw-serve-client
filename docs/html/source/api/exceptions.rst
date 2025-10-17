Exceptions
==========

Exception hierarchy for the bw-serve-client library.

Exception Classes
-----------------

Base Exception
~~~~~~~~~~~~~~

.. autoclass:: bw_serve_client.api_client.BitwardenAPIError
   :members:
   :undoc-members:
   :show-inheritance:

Authentication Errors
~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: bw_serve_client.api_client.AuthenticationError
   :members:
   :undoc-members:
   :show-inheritance:

Validation Errors
~~~~~~~~~~~~~~~~~

.. autoclass:: bw_serve_client.api_client.ValidationError
   :members:
   :undoc-members:
   :show-inheritance:

Not Found Errors
~~~~~~~~~~~~~~~~

.. autoclass:: bw_serve_client.api_client.NotFoundError
   :members:
   :undoc-members:
   :show-inheritance:

Server Errors
~~~~~~~~~~~~~

.. autoclass:: bw_serve_client.api_client.ServerError
   :members:
   :undoc-members:
   :show-inheritance:

Exception Usage
---------------

Here's how to handle exceptions in your code:

.. code-block:: python

   from bw_serve_client import ApiClient, BitwardenAPIError, AuthenticationError

   client = ApiClient(protocol="https", domain="your-server.com")

   try:
       response = client.get("/vault/items")
   except AuthenticationError:
       print("Authentication failed. Check your token.")
   except BitwardenAPIError as e:
       print(f"API Error: {e}")
       print(f"Status Code: {e.status_code}")
   except Exception as e:
       print(f"Unexpected error: {e}")
