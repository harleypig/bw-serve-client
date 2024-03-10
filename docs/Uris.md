# Uris


## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**match** | **int** |  | [optional] 
**uri** | **str** |  | [optional] 

## Example

```python
from bw_serve_client.models.uris import Uris

# TODO update the JSON string below
json = "{}"
# create an instance of Uris from a JSON string
uris_instance = Uris.from_json(json)
# print the JSON string representation of the object
print Uris.to_json()

# convert the object into a dict
uris_dict = uris_instance.to_dict()
# create an instance of Uris from a dict
uris_form_dict = uris.from_dict(uris_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


