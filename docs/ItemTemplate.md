# ItemTemplate


## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**card** | [**ItemCard**](ItemCard.md) |  | [optional] 
**collection_ids** | **List[str]** |  | [optional] 
**favorite** | **bool** |  | [optional] 
**fields** | [**List[Field]**](Field.md) |  | [optional] 
**folder_id** | **str** |  | [optional] 
**identity** | [**ItemIdentity**](ItemIdentity.md) |  | [optional] 
**login** | [**ItemLogin**](ItemLogin.md) |  | [optional] 
**name** | **str** |  | [optional] 
**notes** | **str** |  | [optional] 
**organization_id** | **str** |  | [optional] 
**reprompt** | **int** |  | [optional] 
**secure_note** | [**ItemSecureNote**](ItemSecureNote.md) |  | [optional] 
**type** | [**Int**](Int.md) |  | [optional] 

## Example

```python
from bw_serve_client.models.item_template import ItemTemplate

# TODO update the JSON string below
json = "{}"
# create an instance of ItemTemplate from a JSON string
item_template_instance = ItemTemplate.from_json(json)
# print the JSON string representation of the object
print ItemTemplate.to_json()

# convert the object into a dict
item_template_dict = item_template_instance.to_dict()
# create an instance of ItemTemplate from a dict
item_template_form_dict = item_template.from_dict(item_template_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


