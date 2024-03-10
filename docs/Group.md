# Group


## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**hide_passwords** | **bool** |  | [optional] 
**id** | **str** |  | [optional] 
**read_only** | **bool** |  | [optional] 

## Example

```python
from bw_serve_client.models.group import Group

# TODO update the JSON string below
json = "{}"
# create an instance of Group from a JSON string
group_instance = Group.from_json(json)
# print the JSON string representation of the object
print Group.to_json()

# convert the object into a dict
group_dict = group_instance.to_dict()
# create an instance of Group from a dict
group_form_dict = group.from_dict(group_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


