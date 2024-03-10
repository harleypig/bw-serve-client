# bw_serve_client.FoldersApi

All URIs are relative to *http://localhost*

Method | HTTP request | Description
------------- | ------------- | -------------
[**list_object_folders_get**](FoldersApi.md#list_object_folders_get) | **GET** /list/object/folders | Retrieve a list of folders in your vault.
[**object_folder_id_delete**](FoldersApi.md#object_folder_id_delete) | **DELETE** /object/folder/{id} | Delete a folder from your vault.
[**object_folder_id_get**](FoldersApi.md#object_folder_id_get) | **GET** /object/folder/{id} | Retrieve a folder from your vault.
[**object_folder_id_put**](FoldersApi.md#object_folder_id_put) | **PUT** /object/folder/{id} | Edit a folder in your vault.
[**object_folder_post**](FoldersApi.md#object_folder_post) | **POST** /object/folder | Add a folder to your vault.


# **list_object_folders_get**
> list_object_folders_get(search=search)

Retrieve a list of folders in your vault.

Retrieve a list of folders in your vault. By default, this will return a list of all folders, however you can specify search terms as query parameters to narrow list results.

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
    api_instance = bw_serve_client.FoldersApi(api_client)
    search = 'search_example' # str | List all folders that contain this search term. (optional)

    try:
        # Retrieve a list of folders in your vault.
        api_instance.list_object_folders_get(search=search)
    except Exception as e:
        print("Exception when calling FoldersApi->list_object_folders_get: %s\n" % e)
```



### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **search** | **str**| List all folders that contain this search term. | [optional] 

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
**200** | Success returns an array (in &#x60;\&quot;data\&quot;:[]&#x60;) of matching folders as objects. If no folders are found, an empty array is returned. |  -  |
**400** | Bad Request. |  -  |
**404** | Not Found. |  -  |
**500** | Internal Server Error. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **object_folder_id_delete**
> object_folder_id_delete(id)

Delete a folder from your vault.

Delete an existing folder from your vault by specifying the unique folder identifier (e.g. `3a84be8d-12e7-4223-98cd-ae0000eabdec`) in the path.<br><br>Deleting a folder **will not** delete the items in it.

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
    api_instance = bw_serve_client.FoldersApi(api_client)
    id = 'id_example' # str | Unique identifier of the item to retrieve.

    try:
        # Delete a folder from your vault.
        api_instance.object_folder_id_delete(id)
    except Exception as e:
        print("Exception when calling FoldersApi->object_folder_id_delete: %s\n" % e)
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
**200** | Success returns confirmation that the folder was deleted. |  -  |
**400** | Bad Request. |  -  |
**404** | Not Found. |  -  |
**500** | Internal Server Error. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **object_folder_id_get**
> object_folder_id_get(id)

Retrieve a folder from your vault.

Retrieve an existing folder from your vault by specifying the unique folder identifier (e.g. `3a84be8d-12e7-4223-98cd-ae0000eabdec`) in the path.

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
    api_instance = bw_serve_client.FoldersApi(api_client)
    id = 'id_example' # str | Unique identifier of the item to retrieve.

    try:
        # Retrieve a folder from your vault.
        api_instance.object_folder_id_get(id)
    except Exception as e:
        print("Exception when calling FoldersApi->object_folder_id_get: %s\n" % e)
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
**200** | Success returns an object containing the folder&#39;s &#x60;\&quot;id\&quot;:&#x60; and &#x60;\&quot;name\&quot;:&#x60;. |  -  |
**400** | Bad Request. |  -  |
**404** | Not Found. |  -  |
**500** | Internal Server Error. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **object_folder_id_put**
> object_folder_id_put(id, folder)

Edit a folder in your vault.

Edit an existing folder in your vault by specifying the unique folder identifier (e.g. `3a84be8d-12e7-4223-98cd-ae0000eabdec`) in the path and the new folder `\"name\":` in the request body.

### Example

```python
import time
import os
import bw_serve_client
from bw_serve_client.models.folder import Folder
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
    api_instance = bw_serve_client.FoldersApi(api_client)
    id = 'id_example' # str | Unique identifier of the item to edit.
    folder = {"name":"My Folder's New Name"} # Folder | 

    try:
        # Edit a folder in your vault.
        api_instance.object_folder_id_put(id, folder)
    except Exception as e:
        print("Exception when calling FoldersApi->object_folder_id_put: %s\n" % e)
```



### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **str**| Unique identifier of the item to edit. | 
 **folder** | [**Folder**](Folder.md)|  | 

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
**200** | Success returns an object containing the folder&#39;s pre-existing &#x60;\&quot;id\&quot;:&#x60; and its new &#x60;\&quot;name\&quot;:&#x60;. |  -  |
**400** | Bad Request. |  -  |
**404** | Not Found. |  -  |
**500** | Internal Server Error. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **object_folder_post**
> object_folder_post(folder)

Add a folder to your vault.

Add a folder to your vault.

### Example

```python
import time
import os
import bw_serve_client
from bw_serve_client.models.folder import Folder
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
    api_instance = bw_serve_client.FoldersApi(api_client)
    folder = {"name":"My Folder of Items"} # Folder | The request body must contain an object representing the name for the folder to add.

    try:
        # Add a folder to your vault.
        api_instance.object_folder_post(folder)
    except Exception as e:
        print("Exception when calling FoldersApi->object_folder_post: %s\n" % e)
```



### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **folder** | [**Folder**](Folder.md)| The request body must contain an object representing the name for the folder to add. | 

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
**200** | Success returns an object containing a generated folder &#x60;\&quot;id\&quot;:&#x60; and its &#x60;\&quot;name\&quot;:&#x60;. |  -  |
**400** | Bad Request. |  -  |
**404** | Not Found. |  -  |
**500** | Internal Server Error. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

