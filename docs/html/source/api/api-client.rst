API Client
==========

The main client class for interacting with the Bitwarden Vault Management API.

.. autoclass:: bw_serve_client.api_client.ApiClient
   :members:
   :undoc-members:
   :show-inheritance:

   .. automethod:: __init__

   .. automethod:: get

   .. automethod:: post

   .. automethod:: put

   .. automethod:: delete

   .. automethod:: close

   .. automethod:: __enter__

   .. automethod:: __exit__

Private Methods
~~~~~~~~~~~~~~~

.. automethod:: bw_serve_client.api_client.ApiClient._make_request
   :noindex:

.. automethod:: bw_serve_client.api_client.ApiClient._serialize_data
   :noindex:

.. automethod:: bw_serve_client.api_client.ApiClient._deserialize_data
   :noindex:

.. automethod:: bw_serve_client.api_client.ApiClient._handle_error
   :noindex:

.. automethod:: bw_serve_client.api_client.ApiClient._setup_default_logger
   :noindex: