# bw_serve_client.AttachmentsFieldsApi

All URIs are relative to *http://localhost*

Method | HTTP request | Description
------------- | ------------- | -------------
[**attachment_post**](AttachmentsFieldsApi.md#attachment_post) | **POST** /attachment | Attach a file to an existing vault item.
[**object_attachment_id_delete**](AttachmentsFieldsApi.md#object_attachment_id_delete) | **DELETE** /object/attachment/{id} | Delete an attachment.
[**object_attachment_id_get**](AttachmentsFieldsApi.md#object_attachment_id_get) | **GET** /object/attachment/{id} | Retrieve an attachment.
[**object_exposed_id_get**](AttachmentsFieldsApi.md#object_exposed_id_get) | **GET** /object/exposed/{id} | Retrieve the number of times a password has been exposed for a login item.
[**object_notes_id_get**](AttachmentsFieldsApi.md#object_notes_id_get) | **GET** /object/notes/{id} | Retrieve the notes of an item.
[**object_password_id_get**](AttachmentsFieldsApi.md#object_password_id_get) | **GET** /object/password/{id} | Retrieve the password of a login item.
[**object_totp_id_get**](AttachmentsFieldsApi.md#object_totp_id_get) | **GET** /object/totp/{id} | Retrieve the TOTP code of a login item.
[**object_uri_id_get**](AttachmentsFieldsApi.md#object_uri_id_get) | **GET** /object/uri/{id} | Retrieve the URI of a login item.
[**object_username_id_get**](AttachmentsFieldsApi.md#object_username_id_get) | **GET** /object/username/{id} | Retrieve the username of a login item.


# **attachment_post**
> attachment_post(id, file=file)

Attach a file to an existing vault item.

Attach a file to an existing vault item by specifying a unique object identifier (e.g. `3a84be8d-12e7-4223-98cd-ae0000eabdec`) in the path and the file in the request body.

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
    api_instance = bw_serve_client.AttachmentsFieldsApi(api_client)
    id = 'id_example' # str | Unique identifier of the item to attach a file to.
    file = None # bytearray |  (optional)

    try:
        # Attach a file to an existing vault item.
        api_instance.attachment_post(id, file=file)
    except Exception as e:
        print("Exception when calling AttachmentsFieldsApi->attachment_post: %s\n" % e)
```



### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **str**| Unique identifier of the item to attach a file to. | 
 **file** | **bytearray**|  | [optional] 

### Return type

void (empty response body)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: multipart/form-data
 - **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Success returns the item object with new objects in an &#x60;\&quot;attachments\&quot;:[]&#x60; array. |  -  |
**400** | Bad Request. |  -  |
**404** | Not Found. |  -  |
**500** | Internal Server Error. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **object_attachment_id_delete**
> object_attachment_id_delete(id, itemid)

Delete an attachment.

Delete an attachment by specifying the attachment id (e.g. `o4lrz575u84koanvu9f5gqv9a9ab92gf`) in the path and item id (e.g. `ba624b21-1c8a-43b3-a713-ae0000eabdec`) as a query parameter.

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
    api_instance = bw_serve_client.AttachmentsFieldsApi(api_client)
    id = 'id_example' # str | Unique identifier of the attachment.
    itemid = 'itemid_example' # str | Unique identifier of the item the file is attached to.

    try:
        # Delete an attachment.
        api_instance.object_attachment_id_delete(id, itemid)
    except Exception as e:
        print("Exception when calling AttachmentsFieldsApi->object_attachment_id_delete: %s\n" % e)
```



### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **str**| Unique identifier of the attachment. | 
 **itemid** | **str**| Unique identifier of the item the file is attached to. | 

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
**200** | Success returns confirmation that the attachment was deleted. |  -  |
**400** | Bad Request. |  -  |
**404** | Not Found. |  -  |
**500** | Internal Server Error. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **object_attachment_id_get**
> object_attachment_id_get(id, itemid)

Retrieve an attachment.

Retreive an attachment by specifying the attachment id (e.g. `o4lrz575u84koanvu9f5gqv9a9ab92gf`) in the path and item id (e.g. `ba624b21-1c8a-43b3-a713-ae0000eabdec`) as a query parameter.<br><br>If you're retrieving any file type other than plaintext, we recommend posting the request through a browser window for immediate download.

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
    api_instance = bw_serve_client.AttachmentsFieldsApi(api_client)
    id = 'id_example' # str | Unique identifier of the attachment.
    itemid = 'itemid_example' # str | Unique identifier of the item the file is attached to.

    try:
        # Retrieve an attachment.
        api_instance.object_attachment_id_get(id, itemid)
    except Exception as e:
        print("Exception when calling AttachmentsFieldsApi->object_attachment_id_get: %s\n" % e)
```



### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **str**| Unique identifier of the attachment. | 
 **itemid** | **str**| Unique identifier of the item the file is attached to. | 

### Return type

void (empty response body)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: Not defined

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Success returns the attached file. |  -  |
**400** | Bad Request. |  -  |
**404** | Not Found. |  -  |
**500** | Internal Server Error. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **object_exposed_id_get**
> object_exposed_id_get(id)

Retrieve the number of times a password has been exposed for a login item.

Retrieve the number of times a password has been exposed for a login item by specifying the item's unique object identifier (e.g. `3a84be8d-12e7-4223-98cd-ae0000eabdec`) in the path.

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
    api_instance = bw_serve_client.AttachmentsFieldsApi(api_client)
    id = 'id_example' # str | Unique identifier of the item.

    try:
        # Retrieve the number of times a password has been exposed for a login item.
        api_instance.object_exposed_id_get(id)
    except Exception as e:
        print("Exception when calling AttachmentsFieldsApi->object_exposed_id_get: %s\n" % e)
```



### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **str**| Unique identifier of the item. | 

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
**200** | Success returns an object containing the number of times the item&#39;s password has been exposed. |  -  |
**400** | Bad Request. |  -  |
**404** | Not Found. |  -  |
**500** | Internal Server Error. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **object_notes_id_get**
> object_notes_id_get(id)

Retrieve the notes of an item.

Retrieve the notes of an item by specifying the item's unique object identifier (e.g. `3a84be8d-12e7-4223-98cd-ae0000eabdec`) in the path.

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
    api_instance = bw_serve_client.AttachmentsFieldsApi(api_client)
    id = 'id_example' # str | Unique identifier of the item.

    try:
        # Retrieve the notes of an item.
        api_instance.object_notes_id_get(id)
    except Exception as e:
        print("Exception when calling AttachmentsFieldsApi->object_notes_id_get: %s\n" % e)
```



### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **str**| Unique identifier of the item. | 

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
**200** | Success returns an object containing the notes for the item. |  -  |
**400** | Bad Request. |  -  |
**404** | Not Found. |  -  |
**500** | Internal Server Error. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **object_password_id_get**
> object_password_id_get(id)

Retrieve the password of a login item.

Retrieve the password of a login item by specifying the item's unique object identifier (e.g. `3a84be8d-12e7-4223-98cd-ae0000eabdec`) in the path.

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
    api_instance = bw_serve_client.AttachmentsFieldsApi(api_client)
    id = 'id_example' # str | Unique identifier of the item.

    try:
        # Retrieve the password of a login item.
        api_instance.object_password_id_get(id)
    except Exception as e:
        print("Exception when calling AttachmentsFieldsApi->object_password_id_get: %s\n" % e)
```



### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **str**| Unique identifier of the item. | 

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
**200** | Success returns an object containing password of the item. |  -  |
**400** | Bad Request. |  -  |
**404** | Not Found. |  -  |
**500** | Internal Server Error. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **object_totp_id_get**
> object_totp_id_get(id)

Retrieve the TOTP code of a login item.

Retrieve the TOTP code of a login item by specifying the item's unique object identifier (e.g. `3a84be8d-12e7-4223-98cd-ae0000eabdec`) in the path.

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
    api_instance = bw_serve_client.AttachmentsFieldsApi(api_client)
    id = 'id_example' # str | Unique identifier of the item.

    try:
        # Retrieve the TOTP code of a login item.
        api_instance.object_totp_id_get(id)
    except Exception as e:
        print("Exception when calling AttachmentsFieldsApi->object_totp_id_get: %s\n" % e)
```



### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **str**| Unique identifier of the item. | 

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
**200** | Success returns an object containing the current TOTP code for the item. |  -  |
**400** | Bad Request. |  -  |
**404** | Not Found. |  -  |
**500** | Internal Server Error. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **object_uri_id_get**
> object_uri_id_get(id)

Retrieve the URI of a login item.

Retrieve the URI of a login item by specifying the item's unique object identifier (e.g. `3a84be8d-12e7-4223-98cd-ae0000eabdec`) in the path.

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
    api_instance = bw_serve_client.AttachmentsFieldsApi(api_client)
    id = 'id_example' # str | Unique identifier of the item.

    try:
        # Retrieve the URI of a login item.
        api_instance.object_uri_id_get(id)
    except Exception as e:
        print("Exception when calling AttachmentsFieldsApi->object_uri_id_get: %s\n" % e)
```



### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **str**| Unique identifier of the item. | 

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
**200** | Success returns an object containing the first URI for the item. |  -  |
**400** | Bad Request. |  -  |
**404** | Not Found. |  -  |
**500** | Internal Server Error. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **object_username_id_get**
> object_username_id_get(id)

Retrieve the username of a login item.

Retrieve the username of a login item by specifying the item's unique object identifier (e.g. `3a84be8d-12e7-4223-98cd-ae0000eabdec`) in the path.

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
    api_instance = bw_serve_client.AttachmentsFieldsApi(api_client)
    id = 'id_example' # str | Unique identifier of the item.

    try:
        # Retrieve the username of a login item.
        api_instance.object_username_id_get(id)
    except Exception as e:
        print("Exception when calling AttachmentsFieldsApi->object_username_id_get: %s\n" % e)
```



### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **str**| Unique identifier of the item. | 

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
**200** | Success returns an object containing username of the item. |  -  |
**400** | Bad Request. |  -  |
**404** | Not Found. |  -  |
**500** | Internal Server Error. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

