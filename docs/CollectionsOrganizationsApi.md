# bw_serve_client.CollectionsOrganizationsApi

All URIs are relative to *http://localhost*

Method | HTTP request | Description
------------- | ------------- | -------------
[**confirm_org_member_id_post**](CollectionsOrganizationsApi.md#confirm_org_member_id_post) | **POST** /confirm/org-member/{id} | Confirm a member to a specified Organization.
[**list_object_collections_get**](CollectionsOrganizationsApi.md#list_object_collections_get) | **GET** /list/object/collections | List Collections from all member Organizations.
[**list_object_org_collections_get**](CollectionsOrganizationsApi.md#list_object_org_collections_get) | **GET** /list/object/org-collections | List Collections from a specified Organization.
[**list_object_org_members_get**](CollectionsOrganizationsApi.md#list_object_org_members_get) | **GET** /list/object/org-members | List members of a specified Organization.
[**list_object_organizations_get**](CollectionsOrganizationsApi.md#list_object_organizations_get) | **GET** /list/object/organizations | List Organizations of which you are a member.
[**object_org_collection_id_delete**](CollectionsOrganizationsApi.md#object_org_collection_id_delete) | **DELETE** /object/org-collection/{id} | Delete a Collection from a specified Organization.
[**object_org_collection_id_get**](CollectionsOrganizationsApi.md#object_org_collection_id_get) | **GET** /object/org-collection/{id} | Retrieve a Collection from a specified Organization.
[**object_org_collection_id_put**](CollectionsOrganizationsApi.md#object_org_collection_id_put) | **PUT** /object/org-collection/{id} | Edit a Collection in a specified Organization.
[**object_org_collection_post**](CollectionsOrganizationsApi.md#object_org_collection_post) | **POST** /object/org-collection | Create a Collection for a specified Organization.


# **confirm_org_member_id_post**
> confirm_org_member_id_post(id, organization_id)

Confirm a member to a specified Organization.

Confirm a member to a specified Organization by specifying a user identifier (e.g. `6b39c966-c776-4ba9-9489-ae320149af01`) in the path and the Organization identifier (e.g. `b64d6e40-adf2-4f46-b4d2-acd40147548a`) as a query parameter.

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
    api_instance = bw_serve_client.CollectionsOrganizationsApi(api_client)
    id = 'id_example' # str | A unique identifier for the user to confirm.
    organization_id = 'organization_id_example' # str | A unique identifier for the Organization.

    try:
        # Confirm a member to a specified Organization.
        api_instance.confirm_org_member_id_post(id, organization_id)
    except Exception as e:
        print("Exception when calling CollectionsOrganizationsApi->confirm_org_member_id_post: %s\n" % e)
```



### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **str**| A unique identifier for the user to confirm. | 
 **organization_id** | **str**| A unique identifier for the Organization. | 

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
**200** | Success returns confirmation that the user is confirmed to the Organization. |  -  |
**400** | Bad Request. |  -  |
**404** | Not Found. |  -  |
**500** | Internal Server Error. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **list_object_collections_get**
> list_object_collections_get(search=search)

List Collections from all member Organizations.

List Collections from all Organizations of which you are a member. Collections you do not have access to will not be listed.<br><br>By default, this will return a list of all Collections, however you can specify search terms as query parameters to narrow list results.

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
    api_instance = bw_serve_client.CollectionsOrganizationsApi(api_client)
    search = 'search_example' # str | List only Collections that contain this search term. (optional)

    try:
        # List Collections from all member Organizations.
        api_instance.list_object_collections_get(search=search)
    except Exception as e:
        print("Exception when calling CollectionsOrganizationsApi->list_object_collections_get: %s\n" % e)
```



### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **search** | **str**| List only Collections that contain this search term. | [optional] 

### Return type

void (empty response body)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: applcation/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Success returns an array (in &#x60;\&quot;data\&quot;:&#x60;) of Collections as objects. If no Collections are found, an empty array is returned. |  -  |
**400** | Bad Request. |  -  |
**404** | Not Found. |  -  |
**500** | Internal Server Error. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **list_object_org_collections_get**
> list_object_org_collections_get(organization_id, search=search)

List Collections from a specified Organization.

List existing Collections from a specified Organization by specifying an Organization idenfitier as a query parameter. Collections you do not have access to will not be listed.<br><br>By default, this will return a list of all Collections, however you can specify search terms as additional query parameters to narrow list results.

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
    api_instance = bw_serve_client.CollectionsOrganizationsApi(api_client)
    organization_id = 'organization_id_example' # str | Unique identifier of the Organization.
    search = 'search_example' # str | List only Collections that contain this search term. (optional)

    try:
        # List Collections from a specified Organization.
        api_instance.list_object_org_collections_get(organization_id, search=search)
    except Exception as e:
        print("Exception when calling CollectionsOrganizationsApi->list_object_org_collections_get: %s\n" % e)
```



### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **organization_id** | **str**| Unique identifier of the Organization. | 
 **search** | **str**| List only Collections that contain this search term. | [optional] 

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
**200** | Success returns an array (in &#x60;\&quot;data\&quot;:&#x60;) of matching Collections as objects. If no Collections are found, an empty array is returned. |  -  |
**400** | Bad Request. |  -  |
**404** | Not Found. |  -  |
**500** | Internal Server Error. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **list_object_org_members_get**
> list_object_org_members_get(organization_id)

List members of a specified Organization.

List members of a specified Organization by specifying an Organization identifier as a query parameter.

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
    api_instance = bw_serve_client.CollectionsOrganizationsApi(api_client)
    organization_id = 'organization_id_example' # str | Unique identifier of the Organization.

    try:
        # List members of a specified Organization.
        api_instance.list_object_org_members_get(organization_id)
    except Exception as e:
        print("Exception when calling CollectionsOrganizationsApi->list_object_org_members_get: %s\n" % e)
```



### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **organization_id** | **str**| Unique identifier of the Organization. | 

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
**200** | Success returns an array of users that are members of the specified Organization. If no users are found, an empty array is returned. |  -  |
**400** | Bad Request. |  -  |
**404** | Not Found. |  -  |
**500** | Internal Server Error. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **list_object_organizations_get**
> list_object_organizations_get(search=search)

List Organizations of which you are a member.

List Organizations of which you are a member. By default, this will return a list of all Organizations, however you can specify search terms as query parameters to narrow list results.

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
    api_instance = bw_serve_client.CollectionsOrganizationsApi(api_client)
    search = 'search_example' # str | List only Organizations that contain this search term. (optional)

    try:
        # List Organizations of which you are a member.
        api_instance.list_object_organizations_get(search=search)
    except Exception as e:
        print("Exception when calling CollectionsOrganizationsApi->list_object_organizations_get: %s\n" % e)
```



### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **search** | **str**| List only Organizations that contain this search term. | [optional] 

### Return type

void (empty response body)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: applcation/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Success returns an array (in &#x60;\&quot;data\&quot;:&#x60;) of Organizations as objects. If no Collections are found, an empty array is returned. |  -  |
**400** | Bad Request. |  -  |
**404** | Not Found. |  -  |
**500** | Internal Server Error. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **object_org_collection_id_delete**
> object_org_collection_id_delete(id, organization_id)

Delete a Collection from a specified Organization.

Delete an existing Collection from a specified Organization by specifying the unique Collection identifier (e.g. `3a84be8d-12e7-4223-98cd-ae0000eabdec`) in the path and an Organization identifier as a query parameter.<br><br>Deleting a Collection **will not** delete the items in it.

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
    api_instance = bw_serve_client.CollectionsOrganizationsApi(api_client)
    id = 'id_example' # str | Unique identifier of the Collection.
    organization_id = 'organization_id_example' # str | Unique identifier of the Organization.

    try:
        # Delete a Collection from a specified Organization.
        api_instance.object_org_collection_id_delete(id, organization_id)
    except Exception as e:
        print("Exception when calling CollectionsOrganizationsApi->object_org_collection_id_delete: %s\n" % e)
```



### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **str**| Unique identifier of the Collection. | 
 **organization_id** | **str**| Unique identifier of the Organization. | 

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
**200** | Success returns confirmation that the Collection was deleted. |  -  |
**400** | Bad Request. |  -  |
**404** | Not Found. |  -  |
**500** | Internal Server Error. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **object_org_collection_id_get**
> object_org_collection_id_get(id, organization_id)

Retrieve a Collection from a specified Organization.

Retrieve an existing collection from a specified Organization by specifying the unique Collection identifier (e.g. `3a84be8d-12e7-4223-98cd-ae0000eabdec`) in the path and an Organization identifier as a query parameter .

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
    api_instance = bw_serve_client.CollectionsOrganizationsApi(api_client)
    id = 'id_example' # str | Unique identifier of the Collection.
    organization_id = 'organization_id_example' # str | Unique identifier of the Organization.

    try:
        # Retrieve a Collection from a specified Organization.
        api_instance.object_org_collection_id_get(id, organization_id)
    except Exception as e:
        print("Exception when calling CollectionsOrganizationsApi->object_org_collection_id_get: %s\n" % e)
```



### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **str**| Unique identifier of the Collection. | 
 **organization_id** | **str**| Unique identifier of the Organization. | 

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
**200** | Success returns a JSON object representing the retrieved Collection in the &#x60;\&quot;data\&quot;:&#x60; property. |  -  |
**400** | Bad Request. |  -  |
**404** | Not Found. |  -  |
**500** | Internal Server Request. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **object_org_collection_id_put**
> object_org_collection_id_put(id, organization_id, collection=collection)

Edit a Collection in a specified Organization.

Edit an existing Collection in a specified Organization by specifying the unique collection identifier (e.g. `3a84be8d-12e7-4223-98cd-ae0000eabdec`) in the path, an Organization identifier as a query parameter, and Collection information in the request body.

### Example

```python
import time
import os
import bw_serve_client
from bw_serve_client.models.collection import Collection
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
    api_instance = bw_serve_client.CollectionsOrganizationsApi(api_client)
    id = 'id_example' # str | Unique identifier of the Collection.
    organization_id = 'organization_id_example' # str | Unique identifier of the Organization.
    collection = {"externalid":null,"groups":[{"hidePasswords":false,"id":"c4e31257-f3e1-4b13-895a-ae2700f9884e","readOnly":false}],"name":"Shared Logins","organizationId":"3c89a31d-f1cc-4673-8d5a-ae2700f9860d"} # Collection | The request body must contain an object representing the Collection to edit. Specifying `\"groups\":` is optional. (optional)

    try:
        # Edit a Collection in a specified Organization.
        api_instance.object_org_collection_id_put(id, organization_id, collection=collection)
    except Exception as e:
        print("Exception when calling CollectionsOrganizationsApi->object_org_collection_id_put: %s\n" % e)
```



### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **str**| Unique identifier of the Collection. | 
 **organization_id** | **str**| Unique identifier of the Organization. | 
 **collection** | [**Collection**](Collection.md)| The request body must contain an object representing the Collection to edit. Specifying &#x60;\&quot;groups\&quot;:&#x60; is optional. | [optional] 

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
**200** | Success returns an object representing the edited Collection. |  -  |
**400** | Bad Request. |  -  |
**404** | Not Found. |  -  |
**500** | Internal Server Request. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **object_org_collection_post**
> object_org_collection_post(organization_id, collection=collection)

Create a Collection for a specified Organization.

Create a collection for a specified Organization by specifying a unique Organization identifier as a query parameter and Collection information in the request body, including its `\"name\":` and an array of `\"groups\":` to add it to.

### Example

```python
import time
import os
import bw_serve_client
from bw_serve_client.models.collection import Collection
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
    api_instance = bw_serve_client.CollectionsOrganizationsApi(api_client)
    organization_id = 'organization_id_example' # str | Unique identifier of the Organization.
    collection = {"externalid":null,"groups":[{"hidePasswords":false,"id":"c4e31257-f3e1-4b13-895a-ae2700f9884e","readOnly":false}],"name":"Shared Logins","organizationId":"3c89a31d-f1cc-4673-8d5a-ae2700f9860d"} # Collection | The request body must contain an object representing the Collection to add. Specifying `\"groups\":` is optional. (optional)

    try:
        # Create a Collection for a specified Organization.
        api_instance.object_org_collection_post(organization_id, collection=collection)
    except Exception as e:
        print("Exception when calling CollectionsOrganizationsApi->object_org_collection_post: %s\n" % e)
```



### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **organization_id** | **str**| Unique identifier of the Organization. | 
 **collection** | [**Collection**](Collection.md)| The request body must contain an object representing the Collection to add. Specifying &#x60;\&quot;groups\&quot;:&#x60; is optional. | [optional] 

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
**200** | Success returns an object representing the created Collection. |  -  |
**400** | Bad Request. |  -  |
**404** | Not Found. |  -  |
**500** | Internal Server Error. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

