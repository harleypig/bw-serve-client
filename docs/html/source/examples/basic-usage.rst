Basic Usage Examples
====================

This page contains basic usage examples for the bw-serve-client library.

Installation
~~~~~~~~~~~~

.. code-block:: bash

   pip install bw-serve-client

Simple Connection
~~~~~~~~~~~~~~~~~

.. code-block:: python

   from bw_serve_client import ApiClient

   # Create a client instance
   client = ApiClient(
       protocol="https",
       domain="your-bitwarden-server.com",
       port=443
   )

   # Test the connection
   try:
       response = client.get("/health")
       print("✅ Connected successfully!")
   except Exception as e:
       print(f"❌ Connection failed: {e}")

Authentication
~~~~~~~~~~~~~~

.. code-block:: python

   from bw_serve_client import ApiClient

   client = ApiClient(protocol="https", domain="your-server.com")

   # Set authentication token
   client.session.headers.update({
       'Authorization': 'Bearer your-auth-token'
   })

   # Now you can make authenticated requests
   items = client.get("/vault/items")

Basic CRUD Operations
~~~~~~~~~~~~~~~~~~~~~

Get Items
~~~~~~~~~

.. code-block:: python

   # Get all vault items
   items = client.get("/vault/items")
   print(f"Found {len(items)} items")

   # Get a specific item
   item = client.get("/vault/items/item-id")
   print(f"Item name: {item['name']}")

Create Item
~~~~~~~~~~~

.. code-block:: python

   # Create a new login item
   new_item = {
       "type": 1,  # Login type
       "name": "My New Login",
       "login": {
           "username": "user@example.com",
           "password": "secure-password"
       }
   }

   response = client.post("/vault/items", data=new_item)
   print(f"Created item with ID: {response['id']}")

Update Item
~~~~~~~~~~~

.. code-block:: python

   # Update an existing item
   item_id = "your-item-id"
   updated_data = {
       "name": "Updated Item Name",
       "notes": "Updated notes"
   }

   response = client.put(f"/vault/items/{item_id}", data=updated_data)
   print("Item updated successfully!")

Delete Item
~~~~~~~~~~~

.. code-block:: python

   # Delete an item
   item_id = "your-item-id"
   client.delete(f"/vault/items/{item_id}")
   print("Item deleted successfully!")

Error Handling
--------------

.. code-block:: python

   from bw_serve_client import ApiClient, BitwardenAPIError, AuthenticationError

   client = ApiClient(protocol="https", domain="your-server.com")

   try:
       response = client.get("/vault/items")
   except AuthenticationError:
       print("❌ Authentication failed. Check your token.")
   except BitwardenAPIError as e:
       print(f"❌ API Error: {e}")
       print(f"Status Code: {e.status_code}")
   except Exception as e:
       print(f"❌ Unexpected error: {e}")

Context Manager
---------------

.. code-block:: python

   # Use context manager for automatic cleanup
   with ApiClient(protocol="https", domain="your-server.com") as client:
       client.session.headers.update({
           'Authorization': 'Bearer your-token'
       })

       items = client.get("/vault/items")
       print(f"Retrieved {len(items)} items")
   # Connection is automatically closed

Configuration
-------------

.. code-block:: python

   # Custom configuration
   client = ApiClient(
       protocol="https",
       domain="your-bitwarden-server.com",
       port=443,
       timeout=60,        # 60 second timeout
       max_retries=5,     # Retry failed requests up to 5 times
       user_agent="MyApp/1.0.0"  # Custom user agent
   )

Complete Example
----------------

.. code-block:: python

   from bw_serve_client import ApiClient, BitwardenAPIError

   def main():
       # Create client
       client = ApiClient(
           protocol="https",
           domain="your-bitwarden-server.com",
           port=443,
           timeout=30,
           max_retries=3
       )

       # Set authentication
       client.session.headers.update({
           'Authorization': 'Bearer your-auth-token'
       })

       try:
           # Test connection
           print("Testing connection...")
           health = client.get("/health")
           print(f"✅ Server is healthy: {health}")

           # Get vault items
           print("\nRetrieving vault items...")
           items = client.get("/vault/items")
           print(f"✅ Found {len(items)} items")

           # Display first few items
           for i, item in enumerate(items[:3]):
               print(f"  {i+1}. {item.get('name', 'Unnamed')}")

           if len(items) > 3:
               print(f"  ... and {len(items) - 3} more items")

       except BitwardenAPIError as e:
           print(f"❌ API Error: {e}")
       except Exception as e:
           print(f"❌ Unexpected error: {e}")

   if __name__ == "__main__":
       main()
