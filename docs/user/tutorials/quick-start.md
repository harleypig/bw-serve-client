# Quick Start Tutorial

Get up and running with `bw-serve-client` in just a few minutes!

## 🎯 What You'll Learn

By the end of this tutorial, you'll know how to:
- Connect to your Bitwarden server
- Make your first API call
- Handle basic errors
- Retrieve vault information

## ⚡ 5-Minute Setup

### Step 1: Install the Library

```bash
pip install bw-serve-client
```

### Step 2: Basic Connection

```python
from bw_serve_client import ApiClient

# Create a client instance
client = ApiClient(
    protocol="https",
    domain="your-bitwarden-server.com",
    port=443
)
```

### Step 3: Your First API Call

```python
# Test the connection
try:
    response = client.get("/health")
    print("✅ Connected successfully!")
    print(f"Server response: {response}")
except Exception as e:
    print(f"❌ Connection failed: {e}")
```

## 🔐 Adding Authentication

Most API calls require authentication. Here's how to set it up:

```python
from bw_serve_client import ApiClient

# Create client with authentication
client = ApiClient(
    protocol="https",
    domain="your-bitwarden-server.com",
    port=443
)

# Set authentication token
client.session.headers.update({
    'Authorization': f'Bearer your-auth-token'
})
```

## 📋 Common Operations

### Get Vault Items

```python
# Retrieve all vault items
try:
    items = client.get("/vault/items")
    print(f"Found {len(items)} items in your vault")
    
    for item in items:
        print(f"- {item.get('name', 'Unnamed Item')}")
        
except Exception as e:
    print(f"Error retrieving items: {e}")
```

### Create a New Item

```python
# Create a new login item
new_item = {
    "type": 1,  # Login type
    "name": "My New Login",
    "login": {
        "username": "user@example.com",
        "password": "secure-password"
    }
}

try:
    response = client.post("/vault/items", data=new_item)
    print(f"✅ Item created successfully!")
    print(f"Item ID: {response.get('id')}")
    
except Exception as e:
    print(f"❌ Failed to create item: {e}")
```

### Update an Existing Item

```python
# Update an item (you'll need the item ID)
item_id = "your-item-id"
updated_data = {
    "name": "Updated Item Name",
    "notes": "Updated notes"
}

try:
    response = client.put(f"/vault/items/{item_id}", data=updated_data)
    print("✅ Item updated successfully!")
    
except Exception as e:
    print(f"❌ Failed to update item: {e}")
```

### Delete an Item

```python
# Delete an item
item_id = "your-item-id"

try:
    client.delete(f"/vault/items/{item_id}")
    print("✅ Item deleted successfully!")
    
except Exception as e:
    print(f"❌ Failed to delete item: {e}")
```

## 🛡️ Error Handling

The library provides structured error handling:

```python
from bw_serve_client import ApiClient, BitwardenAPIError, AuthenticationError

client = ApiClient(protocol="https", domain="your-server.com")

try:
    response = client.get("/vault/items")
    
except AuthenticationError:
    print("❌ Authentication failed. Check your token.")
    
except BitwardenAPIError as e:
    print(f"❌ API Error: {e}")
    print(f"Status Code: {e.status_code}")
    
except Exception as e:
    print(f"❌ Unexpected error: {e}")
```

## 🔧 Configuration Options

### Custom Timeout and Retries

```python
client = ApiClient(
    protocol="https",
    domain="your-bitwarden-server.com",
    port=443,
    timeout=60,        # 60 second timeout
    max_retries=5      # Retry failed requests up to 5 times
)
```

### Custom User Agent

```python
client = ApiClient(
    protocol="https",
    domain="your-bitwarden-server.com",
    port=443,
    user_agent="MyApp/1.0.0"  # Custom user agent
)
```

### Using Context Manager

```python
# Automatically handle connection cleanup
with ApiClient(protocol="https", domain="your-server.com") as client:
    items = client.get("/vault/items")
    print(f"Retrieved {len(items)} items")
# Connection is automatically closed
```

## 📊 Complete Example

Here's a complete example that demonstrates the main features:

```python
from bw_serve_client import ApiClient, BitwardenAPIError

def main():
    # Create client
    client = ApiClient(
        protocol="https",
        domain="your-bitwarden-server.com",
        port=443,
        timeout=30,
        max_retries=3
    )
    
    # Set authentication
    client.session.headers.update({
        'Authorization': 'Bearer your-auth-token'
    })
    
    try:
        # Test connection
        print("Testing connection...")
        health = client.get("/health")
        print(f"✅ Server is healthy: {health}")
        
        # Get vault items
        print("\nRetrieving vault items...")
        items = client.get("/vault/items")
        print(f"✅ Found {len(items)} items")
        
        # Display first few items
        for i, item in enumerate(items[:3]):
            print(f"  {i+1}. {item.get('name', 'Unnamed')}")
        
        if len(items) > 3:
            print(f"  ... and {len(items) - 3} more items")
            
    except BitwardenAPIError as e:
        print(f"❌ API Error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()
```

## 🎉 Congratulations!

You've successfully:
- ✅ Installed the library
- ✅ Made your first API call
- ✅ Handled authentication
- ✅ Performed basic CRUD operations
- ✅ Implemented error handling

## 🚀 Next Steps

Ready to dive deeper? Check out:

1. **[Authentication Guide](../guides/authentication.md)** - Detailed authentication setup
2. **[API Reference](../api-reference/)** - Complete API documentation
3. **[Error Handling Guide](../guides/error-handling.md)** - Advanced error management
4. **[Vault Operations Guide](../guides/vault-operations.md)** - Working with vaults

## 🆘 Need Help?

- Check the [Troubleshooting Guide](../guides/troubleshooting.md)
- Review [Common Issues](../guides/common-issues.md)
- [Open an issue](https://github.com/harleypig/bw-serve-client/issues) on GitHub

---

*Ready for more? Explore the [API Reference](../api-reference/) to see all available methods!*