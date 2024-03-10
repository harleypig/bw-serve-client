# SendTemplate


## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**deletion_date** | **datetime** |  | [optional] 
**disabled** | **bool** |  | [optional] 
**expiration_date** | **datetime** |  | [optional] 
**file** | **str** |  | [optional] 
**hide_email** | **bool** |  | [optional] 
**max_access_count** | **int** |  | [optional] 
**name** | **str** |  | [optional] 
**notes** | **str** |  | [optional] 
**password** | **str** |  | [optional] 
**text** | [**SendText**](SendText.md) |  | [optional] 
**type** | **int** |  | [optional] 

## Example

```python
from bw_serve_client.models.send_template import SendTemplate

# TODO update the JSON string below
json = "{}"
# create an instance of SendTemplate from a JSON string
send_template_instance = SendTemplate.from_json(json)
# print the JSON string representation of the object
print SendTemplate.to_json()

# convert the object into a dict
send_template_dict = send_template_instance.to_dict()
# create an instance of SendTemplate from a dict
send_template_form_dict = send_template.from_dict(send_template_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


