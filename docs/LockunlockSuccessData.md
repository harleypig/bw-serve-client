# LockunlockSuccessData


## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**message** | **str** |  | [optional] 
**no_color** | **bool** |  | [optional] 
**object** | **str** |  | [optional] 
**title** | **str** |  | [optional] 

## Example

```python
from bw_serve_client.models.lockunlock_success_data import LockunlockSuccessData

# TODO update the JSON string below
json = "{}"
# create an instance of LockunlockSuccessData from a JSON string
lockunlock_success_data_instance = LockunlockSuccessData.from_json(json)
# print the JSON string representation of the object
print LockunlockSuccessData.to_json()

# convert the object into a dict
lockunlock_success_data_dict = lockunlock_success_data_instance.to_dict()
# create an instance of LockunlockSuccessData from a dict
lockunlock_success_data_form_dict = lockunlock_success_data.from_dict(lockunlock_success_data_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


