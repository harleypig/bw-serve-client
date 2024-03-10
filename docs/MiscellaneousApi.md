# bw_serve_client.MiscellaneousApi

All URIs are relative to *http://localhost*

Method | HTTP request | Description
------------- | ------------- | -------------
[**generate_get**](MiscellaneousApi.md#generate_get) | **GET** /generate | Generate a password or passphrase.
[**object_fingerprint_me_get**](MiscellaneousApi.md#object_fingerprint_me_get) | **GET** /object/fingerprint/me | Retrieve your fingerprint phrase.
[**object_template_type_get**](MiscellaneousApi.md#object_template_type_get) | **GET** /object/template/{type} | Retrieve a JSON template for any object.
[**status_get**](MiscellaneousApi.md#status_get) | **GET** /status | Get the status of the Bitwarden CLI.
[**sync_post**](MiscellaneousApi.md#sync_post) | **POST** /sync | Sync your vault.


# **generate_get**
> generate_get(length=length, uppercase=uppercase, lowercase=lowercase, number=number, special=special, passphrase=passphrase, words=words, separator=separator, capitalize=capitalize, include_number=include_number)

Generate a password or passphrase.

Generate a password or passphrase. By default, `/generate` will generate a 14-character password with uppercase characters, lowercase characters, and numbers.

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
    api_instance = bw_serve_client.MiscellaneousApi(api_client)
    length = 56 # int | Number of characters in the **password**. (optional)
    uppercase = True # bool | Include uppercase characters in the **password**. (optional)
    lowercase = True # bool | Include lowercase characters in the **password**. (optional)
    number = True # bool | Include numbers in the **password**. (optional)
    special = True # bool | Include special characters in the **password**. (optional)
    passphrase = True # bool | Generate passphrase (by default, `/generate` will generate a password). (optional)
    words = 56 # int | Number of words in the **passphrase**. (optional)
    separator = 'separator_example' # str | Separator character in the **passphrase**. (optional)
    capitalize = True # bool | Title-case the **passphrase**. (optional)
    include_number = True # bool | Include numbers in the **passphrase**. (optional)

    try:
        # Generate a password or passphrase.
        api_instance.generate_get(length=length, uppercase=uppercase, lowercase=lowercase, number=number, special=special, passphrase=passphrase, words=words, separator=separator, capitalize=capitalize, include_number=include_number)
    except Exception as e:
        print("Exception when calling MiscellaneousApi->generate_get: %s\n" % e)
```



### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **length** | **int**| Number of characters in the **password**. | [optional] 
 **uppercase** | **bool**| Include uppercase characters in the **password**. | [optional] 
 **lowercase** | **bool**| Include lowercase characters in the **password**. | [optional] 
 **number** | **bool**| Include numbers in the **password**. | [optional] 
 **special** | **bool**| Include special characters in the **password**. | [optional] 
 **passphrase** | **bool**| Generate passphrase (by default, &#x60;/generate&#x60; will generate a password). | [optional] 
 **words** | **int**| Number of words in the **passphrase**. | [optional] 
 **separator** | **str**| Separator character in the **passphrase**. | [optional] 
 **capitalize** | **bool**| Title-case the **passphrase**. | [optional] 
 **include_number** | **bool**| Include numbers in the **passphrase**. | [optional] 

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
**200** | Success returns an object containing the generated password or passphrase. |  -  |
**400** | Bad Request. |  -  |
**404** | Not Found. |  -  |
**500** | Internal Server Error. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **object_fingerprint_me_get**
> object_fingerprint_me_get()

Retrieve your fingerprint phrase.

Retrieve your fingerprint phrase.

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
    api_instance = bw_serve_client.MiscellaneousApi(api_client)

    try:
        # Retrieve your fingerprint phrase.
        api_instance.object_fingerprint_me_get()
    except Exception as e:
        print("Exception when calling MiscellaneousApi->object_fingerprint_me_get: %s\n" % e)
```



### Parameters
This endpoint does not need any parameter.

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
**200** | Success returns an object containing your account fingerprint phrase. |  -  |
**400** | Bad Request. |  -  |
**404** | Not Found. |  -  |
**500** | Internal Server Error. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **object_template_type_get**
> object_template_type_get(type)

Retrieve a JSON template for any object.

Retreive a JSON template for any object, including vault items, sends, folders, and more. Templates can be used to guide you in creation of new objects.

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
    api_instance = bw_serve_client.MiscellaneousApi(api_client)
    type = 'type_example' # str | 

    try:
        # Retrieve a JSON template for any object.
        api_instance.object_template_type_get(type)
    except Exception as e:
        print("Exception when calling MiscellaneousApi->object_template_type_get: %s\n" % e)
```



### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **type** | **str**|  | 

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
**200** | Success returns an object containing the template for the specified type. |  -  |
**400** | Bad Request. |  -  |
**404** | Not Found. |  -  |
**500** | Internal Server Error. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **status_get**
> Status status_get()

Get the status of the Bitwarden CLI.

Get the current `serverURL`, `lastSync`, `userEmail`, `userID`, and `status` of your Bitwarden CLI client.

### Example

```python
import time
import os
import bw_serve_client
from bw_serve_client.models.status import Status
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
    api_instance = bw_serve_client.MiscellaneousApi(api_client)

    try:
        # Get the status of the Bitwarden CLI.
        api_response = api_instance.status_get()
        print("The response of MiscellaneousApi->status_get:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling MiscellaneousApi->status_get: %s\n" % e)
```



### Parameters
This endpoint does not need any parameter.

### Return type

[**Status**](Status.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Success returns an object containing status information about your Bitwarden CLI client. |  -  |
**400** | Bad Request. |  -  |
**404** | Not Found. |  -  |
**500** | Internal Server Error. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **sync_post**
> sync_post()

Sync your vault.

Sync your vault.

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
    api_instance = bw_serve_client.MiscellaneousApi(api_client)

    try:
        # Sync your vault.
        api_instance.sync_post()
    except Exception as e:
        print("Exception when calling MiscellaneousApi->sync_post: %s\n" % e)
```



### Parameters
This endpoint does not need any parameter.

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
**200** | Success returns an object confirming successful sync. |  -  |
**400** | Bad Request. |  -  |
**404** | Not Found. |  -  |
**500** | Internal Server Error. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

