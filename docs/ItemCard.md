# ItemCard


## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**brand** | **str** |  | [optional] 
**cardholder_name** | **str** |  | [optional] 
**code** | **str** |  | [optional] 
**exp_month** | **str** |  | [optional] 
**exp_year** | **str** |  | [optional] 
**number** | **str** |  | [optional] 

## Example

```python
from bw_serve_client.models.item_card import ItemCard

# TODO update the JSON string below
json = "{}"
# create an instance of ItemCard from a JSON string
item_card_instance = ItemCard.from_json(json)
# print the JSON string representation of the object
print ItemCard.to_json()

# convert the object into a dict
item_card_dict = item_card_instance.to_dict()
# create an instance of ItemCard from a dict
item_card_form_dict = item_card.from_dict(item_card_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


