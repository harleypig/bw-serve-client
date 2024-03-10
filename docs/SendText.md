# SendText


## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**hidden** | **bool** |  | [optional] 
**text** | **str** |  | [optional] 

## Example

```python
from bw_serve_client.models.send_text import SendText

# TODO update the JSON string below
json = "{}"
# create an instance of SendText from a JSON string
send_text_instance = SendText.from_json(json)
# print the JSON string representation of the object
print SendText.to_json()

# convert the object into a dict
send_text_dict = send_text_instance.to_dict()
# create an instance of SendText from a dict
send_text_form_dict = send_text.from_dict(send_text_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


