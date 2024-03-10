# LockunlockSuccess


## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**data** | [**LockunlockSuccessData**](LockunlockSuccessData.md) |  | [optional] 
**success** | **bool** |  | [optional] 

## Example

```python
from bw_serve_client.models.lockunlock_success import LockunlockSuccess

# TODO update the JSON string below
json = "{}"
# create an instance of LockunlockSuccess from a JSON string
lockunlock_success_instance = LockunlockSuccess.from_json(json)
# print the JSON string representation of the object
print LockunlockSuccess.to_json()

# convert the object into a dict
lockunlock_success_dict = lockunlock_success_instance.to_dict()
# create an instance of LockunlockSuccess from a dict
lockunlock_success_form_dict = lockunlock_success.from_dict(lockunlock_success_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


