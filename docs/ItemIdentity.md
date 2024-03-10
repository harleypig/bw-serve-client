# ItemIdentity


## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**address1** | **str** |  | [optional] 
**address2** | **str** |  | [optional] 
**address3** | **str** |  | [optional] 
**city** | **str** |  | [optional] 
**company** | **str** |  | [optional] 
**country** | **str** |  | [optional] 
**email** | **str** |  | [optional] 
**first_name** | **str** |  | [optional] 
**last_name** | **str** |  | [optional] 
**license_number** | **str** |  | [optional] 
**middle_name** | **str** |  | [optional] 
**passport_number** | **str** |  | [optional] 
**phone** | **str** |  | [optional] 
**postal_code** | **str** |  | [optional] 
**ssn** | **str** |  | [optional] 
**state** | **str** |  | [optional] 
**title** | **str** |  | [optional] 
**username** | **str** |  | [optional] 

## Example

```python
from bw_serve_client.models.item_identity import ItemIdentity

# TODO update the JSON string below
json = "{}"
# create an instance of ItemIdentity from a JSON string
item_identity_instance = ItemIdentity.from_json(json)
# print the JSON string representation of the object
print ItemIdentity.to_json()

# convert the object into a dict
item_identity_dict = item_identity_instance.to_dict()
# create an instance of ItemIdentity from a dict
item_identity_form_dict = item_identity.from_dict(item_identity_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


