# bw_serve_client.SendApi

All URIs are relative to *http://localhost*

Method | HTTP request | Description
------------- | ------------- | -------------
[**list_object_send_get**](SendApi.md#list_object_send_get) | **GET** /list/object/send | Retrieve a list of Sends.
[**object_send_id_delete**](SendApi.md#object_send_id_delete) | **DELETE** /object/send/{id} | Delete a Send.
[**object_send_id_get**](SendApi.md#object_send_id_get) | **GET** /object/send/{id} | Retrieve a Send.
[**object_send_id_put**](SendApi.md#object_send_id_put) | **PUT** /object/send/{id} | Edit a Send.
[**object_send_post**](SendApi.md#object_send_post) | **POST** /object/send | Create a Send.
[**send_id_remove_password_post**](SendApi.md#send_id_remove_password_post) | **POST** /send/{id}/remove-password | Remove the password from a Send.


# **list_object_send_get**
> list_object_send_get(search=search)

Retrieve a list of Sends.

Retrieve a list of Sends. By default, this will return a list of all Send objects, however you can specify search terms as query parameters to narrow list results.<br><br>**Only Text Sends are supported.**

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
    api_instance = bw_serve_client.SendApi(api_client)
    search = 'search_example' # str | List all Sends that contain this search term. (optional)

    try:
        # Retrieve a list of Sends.
        api_instance.list_object_send_get(search=search)
    except Exception as e:
        print("Exception when calling SendApi->list_object_send_get: %s\n" % e)
```



### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **search** | **str**| List all Sends that contain this search term. | [optional] 

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
**200** | Success returns an array (in &#x60;\&quot;data\&quot;:[]&#x60;) of matching Sends as objects. If no Sends are found, an empty array is returned. |  -  |
**400** | Bad Request. |  -  |
**404** | Not Found. |  -  |
**500** | Internal Server Error. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **object_send_id_delete**
> object_send_id_delete(id)

Delete a Send.

Delete an existing Send by specifying the unique object identifier (e.g. `e813e187-70e3-4feb-950a-ae52010c4b56`) in the path.<br><br>**Only Text Sends are supported.**

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
    api_instance = bw_serve_client.SendApi(api_client)
    id = 'id_example' # str | Unique identifier of the Send to delete.

    try:
        # Delete a Send.
        api_instance.object_send_id_delete(id)
    except Exception as e:
        print("Exception when calling SendApi->object_send_id_delete: %s\n" % e)
```



### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **str**| Unique identifier of the Send to delete. | 

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
**200** | Success returns confirmation that the Send was deleted. |  -  |
**400** | Bad Request. |  -  |
**404** | Not Found. |  -  |
**500** | Internal Server Error. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **object_send_id_get**
> object_send_id_get(id)

Retrieve a Send.

Retrieve a Send by specifying the unique object identifier (e.g. `e813e187-70e3-4feb-950a-ae52010c4b56`) in the path.<br><br>**Only Text Sends are supported.**

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
    api_instance = bw_serve_client.SendApi(api_client)
    id = 'id_example' # str | Unique identifier of the Send to retrieve.

    try:
        # Retrieve a Send.
        api_instance.object_send_id_get(id)
    except Exception as e:
        print("Exception when calling SendApi->object_send_id_get: %s\n" % e)
```



### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **str**| Unique identifier of the Send to retrieve. | 

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
**200** | Success returns an object representing the retrieved Send in the &#x60;\&quot;data\&quot;:{}&#x60; property. |  -  |
**400** | Bad Request. |  -  |
**404** | Not Found. |  -  |
**500** | Internal Server Error. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **object_send_id_put**
> object_send_id_put(id, send_template)

Edit a Send.

Edit an existing Send by specifying the unique object identifier (e.g. `e813e187-70e3-4feb-950a-ae52010c4b56`) in the path and the new object contents in the request body.<br><br> **Only Text Sends are supported.**

### Example

```python
import time
import os
import bw_serve_client
from bw_serve_client.models.send_template import SendTemplate
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
    api_instance = bw_serve_client.SendApi(api_client)
    id = 'id_example' # str | Unique identifier of the Send to edit.
    send_template = {"deletionDate":"2022-03-21T19:06:53.810Z","disabled":false,"expirationDate":"2022-03-21T19:06:53.810Z","file":null,"hideEmail":true,"maxAccessCount":3,"name":"My Text Send","notes":"Notes for the text send.","password":"P@ssw0Rd","text":{"hidden":true,"text":"Secret Information"},"type":0} # SendTemplate | The request body must contain an object representing the edits to make to the Send.<br><br>**Include the full object in the request body**, not just the properties to edit, as the new object will replace the pre-existing Send object.

    try:
        # Edit a Send.
        api_instance.object_send_id_put(id, send_template)
    except Exception as e:
        print("Exception when calling SendApi->object_send_id_put: %s\n" % e)
```



### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **str**| Unique identifier of the Send to edit. | 
 **send_template** | [**SendTemplate**](SendTemplate.md)| The request body must contain an object representing the edits to make to the Send.&lt;br&gt;&lt;br&gt;**Include the full object in the request body**, not just the properties to edit, as the new object will replace the pre-existing Send object. | 

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
**200** | Success returns an object representing the edited Send in the &#x60;\&quot;data\&quot;:{}&#x60; property. |  -  |
**400** | Bad Request. |  -  |
**404** | Not Found. |  -  |
**500** | Internal Server Error. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **object_send_post**
> object_send_post(send_template)

Create a Send.

Create a Send.<br><br>**Only Text Sends are supported.**

### Example

```python
import time
import os
import bw_serve_client
from bw_serve_client.models.send_template import SendTemplate
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
    api_instance = bw_serve_client.SendApi(api_client)
    send_template = {"deletionDate":"2022-03-21T19:06:53.810Z","disabled":false,"expirationDate":"2022-03-21T19:06:53.810Z","file":null,"hideEmail":true,"maxAccessCount":3,"name":"My Text Send","notes":"Notes for the text send.","password":"P@ssw0Rd","text":{"hidden":true,"text":"Secret Information"},"type":0} # SendTemplate | The request body must contain an object representing the Send to create. Use `\"type\":0` to indicate text and provide the `\"text\":{}` object.

    try:
        # Create a Send.
        api_instance.object_send_post(send_template)
    except Exception as e:
        print("Exception when calling SendApi->object_send_post: %s\n" % e)
```



### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **send_template** | [**SendTemplate**](SendTemplate.md)| The request body must contain an object representing the Send to create. Use &#x60;\&quot;type\&quot;:0&#x60; to indicate text and provide the &#x60;\&quot;text\&quot;:{}&#x60; object. | 

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
**200** | Success returns an object representing the created Send in the &#x60;\&quot;data\&quot;:{}&#x60; property. |  -  |
**400** | Bad Request. |  -  |
**404** | Not Found. |  -  |
**500** | Internal Server Error. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **send_id_remove_password_post**
> send_id_remove_password_post(id)

Remove the password from a Send.

Remove the password from a Send.<br><br>**Only Text Sends are supported.**

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
    api_instance = bw_serve_client.SendApi(api_client)
    id = 'id_example' # str | Unique identifier of the Send.

    try:
        # Remove the password from a Send.
        api_instance.send_id_remove_password_post(id)
    except Exception as e:
        print("Exception when calling SendApi->send_id_remove_password_post: %s\n" % e)
```



### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **str**| Unique identifier of the Send. | 

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
**200** | Success returns an object representing the Send with &#x60;\&quot;passwordSet\&quot;:\&quot;false\&quot;&#x60; inside the object. |  -  |
**400** | Bad Request. |  -  |
**404** | Not Found. |  -  |
**500** | Internal Server Error. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

