# bw_serve_client.VaultItemsApi

All URIs are relative to *http://localhost*

Method | HTTP request | Description
------------- | ------------- | -------------
[**list_object_items_get**](VaultItemsApi.md#list_object_items_get) | **GET** /list/object/items | Retrieve a list of items in your vault.
[**object_item_id_delete**](VaultItemsApi.md#object_item_id_delete) | **DELETE** /object/item/{id} | Delete an item from your vault.
[**object_item_id_get**](VaultItemsApi.md#object_item_id_get) | **GET** /object/item/{id} | Retrieve an item from your vault.
[**object_item_id_put**](VaultItemsApi.md#object_item_id_put) | **PUT** /object/item/{id} | Edit an item in your Vault.
[**object_item_post**](VaultItemsApi.md#object_item_post) | **POST** /object/item | Add a new item to your vault.
[**restore_item_id_post**](VaultItemsApi.md#restore_item_id_post) | **POST** /restore/item/{id} | Restore a deleted item.


# **list_object_items_get**
> list_object_items_get(organization_id=organization_id, collection_id=collection_id, folderid=folderid, url=url, trash=trash, search=search)

Retrieve a list of items in your vault.

Retrieve a list of existing items in your vault. By default, this will return a list of all existing items in your vault, however you can specify filters or search terms as query parameters to narrow list results.<br><br>Using multiple filters will perform a logical `OR` operation. Using filters **and** search terms will perform a logical `AND` operation.

### Example

```python
import time
import os
import bw_serve_client
from bw_serve_client.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to http://localhost
# See configuration.py for a list of all supported configuration parameters.
configuration = bw_serve_client.Configuration(
    host = "http://localhost"
)


# Enter a context with an instance of the API client
with bw_serve_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = bw_serve_client.VaultItemsApi(api_client)
    organization_id = 'organization_id_example' # str | List all items with this unique Organization identifier. (optional)
    collection_id = 'collection_id_example' # str | List all items with this unique collection identifier. (optional)
    folderid = 'folderid_example' # str | List all items with this unique folder identifier. (optional)
    url = 'url_example' # str | List all items with this URL/URI value. (optional)
    trash = True # bool | List all items in the trash. This query parameter is not a true boolean, in that `?trash`, `?trash=true`, and `?trash=false` will all be interpretted as a request to list items in the trash. (optional)
    search = 'search_example' # str | List all items that contain this search term. (optional)

    try:
        # Retrieve a list of items in your vault.
        api_instance.list_object_items_get(organization_id=organization_id, collection_id=collection_id, folderid=folderid, url=url, trash=trash, search=search)
    except Exception as e:
        print("Exception when calling VaultItemsApi->list_object_items_get: %s\n" % e)
```



### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **organization_id** | **str**| List all items with this unique Organization identifier. | [optional] 
 **collection_id** | **str**| List all items with this unique collection identifier. | [optional] 
 **folderid** | **str**| List all items with this unique folder identifier. | [optional] 
 **url** | **str**| List all items with this URL/URI value. | [optional] 
 **trash** | **bool**| List all items in the trash. This query parameter is not a true boolean, in that &#x60;?trash&#x60;, &#x60;?trash&#x3D;true&#x60;, and &#x60;?trash&#x3D;false&#x60; will all be interpretted as a request to list items in the trash. | [optional] 
 **search** | **str**| List all items that contain this search term. | [optional] 

### Return type

void (empty response body)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Success returns an array (in &#x60;\&quot;data\&quot;:[]&#x60;) of matching vault items as objects. If no items are found, an empty array is returned. |  -  |
**400** | Bad Request. |  -  |
**404** | Not Found. |  -  |
**500** | Internal Server Error. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **object_item_id_delete**
> object_item_id_delete(id)

Delete an item from your vault.

Delete an existing item from your vault by specifying the unique object identifier (e.g. `3a84be8d-12e7-4223-98cd-ae0000eabdec`) in the path.

### Example

```python
import time
import os
import bw_serve_client
from bw_serve_client.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to http://localhost
# See configuration.py for a list of all supported configuration parameters.
configuration = bw_serve_client.Configuration(
    host = "http://localhost"
)


# Enter a context with an instance of the API client
with bw_serve_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = bw_serve_client.VaultItemsApi(api_client)
    id = 'id_example' # str | Unique identifier of the item to delete.

    try:
        # Delete an item from your vault.
        api_instance.object_item_id_delete(id)
    except Exception as e:
        print("Exception when calling VaultItemsApi->object_item_id_delete: %s\n" % e)
```



### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **str**| Unique identifier of the item to delete. | 

### Return type

void (empty response body)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Success returns confirmation that the item was sent to the trash. |  -  |
**400** | Bad Request. |  -  |
**404** | Not Found. |  -  |
**500** | Internal Server Error. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **object_item_id_get**
> object_item_id_get(id)

Retrieve an item from your vault.

Retrieve an existing item from your vault by specifying a unique object identifier (e.g. `3a84be8d-12e7-4223-98cd-ae0000eabdec`) in the path.

### Example

```python
import time
import os
import bw_serve_client
from bw_serve_client.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to http://localhost
# See configuration.py for a list of all supported configuration parameters.
configuration = bw_serve_client.Configuration(
    host = "http://localhost"
)


# Enter a context with an instance of the API client
with bw_serve_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = bw_serve_client.VaultItemsApi(api_client)
    id = 'id_example' # str | Unique identifier of the item to retrieve.

    try:
        # Retrieve an item from your vault.
        api_instance.object_item_id_get(id)
    except Exception as e:
        print("Exception when calling VaultItemsApi->object_item_id_get: %s\n" % e)
```



### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **str**| Unique identifier of the item to retrieve. | 

### Return type

void (empty response body)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Success returns an object representing the retrieved item in the &#x60;\&quot;data\&quot;:{}&#x60; property. |  -  |
**400** | Bad Request. |  -  |
**404** | Not Found. |  -  |
**500** | Internal Server Error. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **object_item_id_put**
> object_item_id_put(id, item_template)

Edit an item in your Vault.

Edit an existing login, card, secure note, or identity in your Vault by specifying a unique object identifier (e.g. `3a84be8d-12e7-4223-98cd-ae0000eabdec`) in the path and the new object contents in the request body.

### Example

```python
import time
import os
import bw_serve_client
from bw_serve_client.models.item_template import ItemTemplate
from bw_serve_client.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to http://localhost
# See configuration.py for a list of all supported configuration parameters.
configuration = bw_serve_client.Configuration(
    host = "http://localhost"
)


# Enter a context with an instance of the API client
with bw_serve_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = bw_serve_client.VaultItemsApi(api_client)
    id = 'id_example' # str | Unique identifier of the item to edit.
    item_template = {"card":{"brand":"visa","cardholderName":"John Doe","code":"123","expMonth":"04","expYear":"2023","number":"4242424242424242"},"collectionIds":"c4e31257-f3e1-4b13-895a-ae2700f9884e","favorite":true,"fields":[],"folderId":null,"name":"Company Credit Card","notes":null,"organizationId":"3c89a31d-f1cc-4673-8d5a-ae2700f9860d","reprompt":1,"type":3} # ItemTemplate | The request body must contain an object representing the edits to make to the item.<br><br>**Include the full object in the request body**, not just the properties to edit, as the new object will replace the pre-existing object.

    try:
        # Edit an item in your Vault.
        api_instance.object_item_id_put(id, item_template)
    except Exception as e:
        print("Exception when calling VaultItemsApi->object_item_id_put: %s\n" % e)
```



### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **str**| Unique identifier of the item to edit. | 
 **item_template** | [**ItemTemplate**](ItemTemplate.md)| The request body must contain an object representing the edits to make to the item.&lt;br&gt;&lt;br&gt;**Include the full object in the request body**, not just the properties to edit, as the new object will replace the pre-existing object. | 

### Return type

void (empty response body)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Success returns an object representing the edited item in the &#x60;\&quot;data\&quot;:{}&#x60; property. |  -  |
**400** | Bad Request. |  -  |
**404** | Not Found. |  -  |
**500** | Internal Server Error. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **object_item_post**
> object_item_post(item_template)

Add a new item to your vault.

Add a new login, card, secure note, or identity to your vault.

### Example

```python
import time
import os
import bw_serve_client
from bw_serve_client.models.item_template import ItemTemplate
from bw_serve_client.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to http://localhost
# See configuration.py for a list of all supported configuration parameters.
configuration = bw_serve_client.Configuration(
    host = "http://localhost"
)


# Enter a context with an instance of the API client
with bw_serve_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = bw_serve_client.VaultItemsApi(api_client)
    item_template = {"card":{"brand":"visa","cardholderName":"John Doe","code":"123","expMonth":"04","expYear":"2023","number":"4242424242424242"},"collectionIds":"c4e31257-f3e1-4b13-895a-ae2700f9884e","favorite":true,"fields":[],"folderId":null,"name":"Company Credit Card","notes":null,"organizationId":"3c89a31d-f1cc-4673-8d5a-ae2700f9860d","reprompt":0,"type":3} # ItemTemplate | The request body must contain an object representing the item to add to your Vault. Indicate [item type](https://bitwarden.com/help/cli/#item-types) with `\"type\":` and only provide data in the appropriate type's object (e.g. `\"login\":{}` or `\"identity\":{}`). See the **Examples** for help.

    try:
        # Add a new item to your vault.
        api_instance.object_item_post(item_template)
    except Exception as e:
        print("Exception when calling VaultItemsApi->object_item_post: %s\n" % e)
```



### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **item_template** | [**ItemTemplate**](ItemTemplate.md)| The request body must contain an object representing the item to add to your Vault. Indicate [item type](https://bitwarden.com/help/cli/#item-types) with &#x60;\&quot;type\&quot;:&#x60; and only provide data in the appropriate type&#39;s object (e.g. &#x60;\&quot;login\&quot;:{}&#x60; or &#x60;\&quot;identity\&quot;:{}&#x60;). See the **Examples** for help. | 

### Return type

void (empty response body)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Success returns an object representing the created item in the &#x60;\&quot;data\&quot;:{}&#x60; property. |  -  |
**400** | Bad Request. |  -  |
**404** | Not Found. |  -  |
**500** | Internal Server Error. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **restore_item_id_post**
> restore_item_id_post(id)

Restore a deleted item.

Restore an item that was sent to the trash by specifying the unique object identifier (e.g. `3a84be8d-12e7-4223-98cd-ae0000eabdec`) in the path.

### Example

```python
import time
import os
import bw_serve_client
from bw_serve_client.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to http://localhost
# See configuration.py for a list of all supported configuration parameters.
configuration = bw_serve_client.Configuration(
    host = "http://localhost"
)


# Enter a context with an instance of the API client
with bw_serve_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = bw_serve_client.VaultItemsApi(api_client)
    id = 'id_example' # str | Unique identifier of the item to restore.

    try:
        # Restore a deleted item.
        api_instance.restore_item_id_post(id)
    except Exception as e:
        print("Exception when calling VaultItemsApi->restore_item_id_post: %s\n" % e)
```



### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **str**| Unique identifier of the item to restore. | 

### Return type

void (empty response body)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Success returns confirmation that the item was restored. |  -  |
**400** | Bad Request. |  -  |
**404** | Not Found. |  -  |
**500** | Internal Server Error. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

