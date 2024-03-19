from bw_serve_client.api_client import ApiClient
from bw_serve_client.configuration import Configuration

# Create a configuration instance
config = Configuration()
config.host = "http://localhost:8181"

# Create an instance of the API client
client = ApiClient(configuration=config)


def get_items():
    # The endpoint to list items
    endpoint = "/list/object/items"

    # Make a GET request to the server
    response = client.request(
        method="GET",
        url=client.configuration.host + endpoint,
        _preload_content=False
    )

    # Check if the request was successful
    if response.status == 200:
        # Parse the JSON response and return it
        return response.data
    else:
        # Return None if the request failed
        return None


# The main function to execute when the script runs
if __name__ == "__main__":
    # Get the list of items from the vault
    items = get_items()

    # Check if we got a response
    if items:
        # Print the items if we did
        print("Items retrieved from the vault:")
        for item in items['data']:
            print(item)
    else:
        # Print an error message if we did not
        print("Failed to retrieve items from the vault.")
