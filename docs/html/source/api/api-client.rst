API client
==========

One :class:`ApiClient` connects to one running ``bw serve`` and is shared
by every resource class. Its ``get``, ``post``, ``put`` and ``delete``
methods send a request as given, without validation; use a resource class
where one covers the route.

.. autoclass:: bw_serve_client.api_client.ApiClient
   :members:
   :exclude-members: session
