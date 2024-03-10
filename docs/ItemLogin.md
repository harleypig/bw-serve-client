# ItemLogin


## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**password** | **str** |  | [optional] 
**totp** | **str** |  | [optional] 
**uris** | [**Uris**](Uris.md) |  | [optional] 
**username** | **str** |  | [optional] 

## Example

```python
from bw_serve_client.models.item_login import ItemLogin

# TODO update the JSON string below
json = "{}"
# create an instance of ItemLogin from a JSON string
item_login_instance = ItemLogin.from_json(json)
# print the JSON string representation of the object
print ItemLogin.to_json()

# convert the object into a dict
item_login_dict = item_login_instance.to_dict()
# create an instance of ItemLogin from a dict
item_login_form_dict = item_login.from_dict(item_login_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


