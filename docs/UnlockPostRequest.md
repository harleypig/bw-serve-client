# UnlockPostRequest


## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**password** | **str** |  | [optional] 

## Example

```python
from bw_serve_client.models.unlock_post_request import UnlockPostRequest

# TODO update the JSON string below
json = "{}"
# create an instance of UnlockPostRequest from a JSON string
unlock_post_request_instance = UnlockPostRequest.from_json(json)
# print the JSON string representation of the object
print UnlockPostRequest.to_json()

# convert the object into a dict
unlock_post_request_dict = unlock_post_request_instance.to_dict()
# create an instance of UnlockPostRequest from a dict
unlock_post_request_form_dict = unlock_post_request.from_dict(unlock_post_request_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


