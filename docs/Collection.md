# Collection


## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**external_id** | **str** |  | [optional] 
**groups** | [**List[Group]**](Group.md) |  | [optional] 
**name** | **str** |  | [optional] 
**organization_id** | **str** |  | [optional] 

## Example

```python
from bw_serve_client.models.collection import Collection

# TODO update the JSON string below
json = "{}"
# create an instance of Collection from a JSON string
collection_instance = Collection.from_json(json)
# print the JSON string representation of the object
print Collection.to_json()

# convert the object into a dict
collection_dict = collection_instance.to_dict()
# create an instance of Collection from a dict
collection_form_dict = collection.from_dict(collection_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


