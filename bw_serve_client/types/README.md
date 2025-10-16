# Generated Types for Bitwarden Vault Management API

This directory contains Pydantic models automatically generated from the Bitwarden Vault Management API OpenAPI specification. These types provide type safety and validation for all API data structures.

## Module Organization

The types are organized into logical modules based on their usage patterns:

### `global_types.py`
Core types used across multiple API endpoints:
- `Collection` - Organization collections
- `Field` - Custom fields for items
- `Folder` - Item folders
- `Group` - Collection groups
- `Status` - API response status
- `Uris` - URI matching configuration

### `item_types.py`
Types specific to vault items:
- `ItemCard` - Credit card information
- `ItemIdentity` - Identity/personal information
- `ItemLogin` - Login credentials
- `ItemSecureNote` - Secure notes
- `ItemTemplate` - Complete item template

### `send_types.py`
Types for Bitwarden Send functionality:
- `SendTemplate` - Send item template
- `SendText` - Text-based send items

### `response_types.py`
API response wrapper types:
- `LockUnlockSuccess` - Lock/unlock operation responses

## Usage

```python
from bw_serve_client.types import ItemTemplate, ItemLogin, Field, FieldType

# Create a login item with type safety
login_item = ItemTemplate(
    name="My Login",
    type=ItemTemplateType.VALUE_0,  # Login type
    login=ItemLogin(
        username="user@example.com",
        password="secure_password"
    ),
    fields=[
        Field(
            name="Custom Field",
            type=FieldType.VALUE_0,  # Text field
            value="Custom value"
        )
    ]
)
```

## Type Safety Features

- **Enum Validation**: All enum values are properly typed and validated
- **Optional Fields**: Non-required fields are marked as `Optional`
- **UUID Support**: Proper UUID type handling for identifiers
- **Forward References**: Circular dependencies handled with string annotations
- **Pydantic Validation**: Automatic validation of data types and constraints

## Regeneration

To regenerate these types from the OpenAPI specification:

```bash
python scripts/generate_types.py
```

The script will:
1. Parse the OpenAPI specification
2. Generate Pydantic models with proper type annotations
3. Handle enums and validation constraints
4. Organize types into logical modules
5. Generate proper imports and exports

## Dependencies

These types require:
- `pydantic>=2.0.0` - For model validation and serialization
- `typing` - For type annotations
- `uuid` - For UUID type support
- `enum` - For enum definitions