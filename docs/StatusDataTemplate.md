# StatusDataTemplate


## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**last_sync** | **datetime** |  | [optional] 
**server_url** | **str** |  | [optional] 
**status** | **str** |  | [optional] 
**user_email** | **str** |  | [optional] 
**user_id** | **str** |  | [optional] 

## Example

```python
from bw_serve_client.models.status_data_template import StatusDataTemplate

# TODO update the JSON string below
json = "{}"
# create an instance of StatusDataTemplate from a JSON string
status_data_template_instance = StatusDataTemplate.from_json(json)
# print the JSON string representation of the object
print StatusDataTemplate.to_json()

# convert the object into a dict
status_data_template_dict = status_data_template_instance.to_dict()
# create an instance of StatusDataTemplate from a dict
status_data_template_form_dict = status_data_template.from_dict(status_data_template_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


