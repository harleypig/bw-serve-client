# bw_serve_client.LockUnlockApi

All URIs are relative to *http://localhost*

Method | HTTP request | Description
------------- | ------------- | -------------
[**lock_post**](LockUnlockApi.md#lock_post) | **POST** /lock | Lock your vault.
[**unlock_post**](LockUnlockApi.md#unlock_post) | **POST** /unlock | Unlock your vault.


# **lock_post**
> LockunlockSuccess lock_post()

Lock your vault.

Lock your vault. This action will destroy the session key required to authorize requests to most endpoints.

### Example

```python
import time
import os
import bw_serve_client
from bw_serve_client.models.lockunlock_success import LockunlockSuccess
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
    api_instance = bw_serve_client.LockUnlockApi(api_client)

    try:
        # Lock your vault.
        api_response = api_instance.lock_post()
        print("The response of LockUnlockApi->lock_post:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling LockUnlockApi->lock_post: %s\n" % e)
```



### Parameters
This endpoint does not need any parameter.

### Return type

[**LockunlockSuccess**](LockunlockSuccess.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Success returns confirmation that your vault is locked. |  -  |
**400** | Bad Request. |  -  |
**404** | Not Found. |  -  |
**500** | Internal Server Error. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **unlock_post**
> LockunlockSuccess unlock_post(unlock_post_request)

Unlock your vault.

Unlock your vault. This action will create the session key required to authorize requests to most endpoints.

### Example

```python
import time
import os
import bw_serve_client
from bw_serve_client.models.lockunlock_success import LockunlockSuccess
from bw_serve_client.models.unlock_post_request import UnlockPostRequest
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
    api_instance = bw_serve_client.LockUnlockApi(api_client)
    unlock_post_request = {"password":"myp@$$w0rd"} # UnlockPostRequest | The request body must contain an object containing your master password.

    try:
        # Unlock your vault.
        api_response = api_instance.unlock_post(unlock_post_request)
        print("The response of LockUnlockApi->unlock_post:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling LockUnlockApi->unlock_post: %s\n" % e)
```



### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **unlock_post_request** | [**UnlockPostRequest**](UnlockPostRequest.md)| The request body must contain an object containing your master password. | 

### Return type

[**LockunlockSuccess**](LockunlockSuccess.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Success will return confirmation that your vault is unlocked and a session key. You **do not** need to do anything with the session key to proceed. |  -  |
**400** | Bad Request. |  -  |
**404** | Not Found. |  -  |
**500** | Internal Server Error. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

