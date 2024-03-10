# StatusData


## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**object** | **str** |  | [optional] 
**template** | [**StatusDataTemplate**](StatusDataTemplate.md) |  | [optional] 

## Example

```python
from bw_serve_client.models.status_data import StatusData

# TODO update the JSON string below
json = "{}"
# create an instance of StatusData from a JSON string
status_data_instance = StatusData.from_json(json)
# print the JSON string representation of the object
print StatusData.to_json()

# convert the object into a dict
status_data_dict = status_data_instance.to_dict()
# create an instance of StatusData from a dict
status_data_form_dict = status_data.from_dict(status_data_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


