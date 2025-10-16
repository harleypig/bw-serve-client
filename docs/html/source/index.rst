Welcome to bw-serve-client's documentation!
============================================

**bw-serve-client** is a Python library for interacting with the Bitwarden Vault Management API. 
It provides a simple, intuitive interface for managing vaults, items, and attachments.

Quick Start
-----------

.. code-block:: python

   from bw_serve_client import ApiClient

   # Create a client instance
   client = ApiClient(
       protocol="https",
       domain="your-bitwarden-server.com",
       port=443
   )

   # Set authentication
   client.session.headers.update({
       'Authorization': 'Bearer your-auth-token'
   })

   # Make your first API call
   items = client.get("/vault/items")
   print(f"Found {len(items)} items in your vault")

Features
--------

* **Simple API** - Easy-to-use interface for Bitwarden Vault Management API
* **Type Safety** - Full type hints and mypy support
* **Error Handling** - Comprehensive error handling with custom exceptions
* **Retry Logic** - Built-in retry mechanism for failed requests
* **Context Manager** - Automatic resource cleanup
* **Logging** - Integrated logging support
* **Testing** - Comprehensive test suite with 100% coverage

Documentation
-------------

API Reference
~~~~~~~~~~~~~

.. toctree::
   :maxdepth: 2
   :caption: API Reference:

   api/api-client
   api/exceptions
   api/data-models

Examples
--------

.. toctree::
   :maxdepth: 1
   :caption: Examples:

   examples/basic-usage

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

