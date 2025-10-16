#!/usr/bin/env python3

"""Example demonstrating usage of generated types from Bitwarden Vault Management API.

This example shows how to use the generated Pydantic models for type-safe
interaction with the Bitwarden Vault Management API.
"""

from typing import List, Optional
from uuid import UUID

# Import the generated types
from bw_serve_client.types import (
    # Global types
    Collection, Field, Folder, Group, Status, Uris,
    # Item types
    ItemCard, ItemIdentity, ItemLogin, ItemSecureNote, ItemTemplate,
    # Enums
    FieldType, UrisMatch, ItemCardBrand, ItemSecureNoteType,
    ItemTemplateReprompt, ItemTemplateType
)


def create_login_item() -> ItemTemplate:
    """Create a login item template with proper typing."""
    # Create a login item with proper field types
    login_item = ItemTemplate(
        name="Example Login",
        type=ItemTemplateType.VALUE_0,  # Login type
        favorite=True,
        notes="This is an example login item",
        login=ItemLogin(
            username="user@example.com",
            password="secure_password",
            totp="JBSWY3DPEHPK3PXP"
        ),
        fields=[
            Field(
                name="Custom Field",
                type=FieldType.VALUE_0,  # Text field type
                value="Custom value"
            )
        ]
    )
    return login_item


def create_identity_item() -> ItemTemplate:
    """Create an identity item template."""
    identity_item = ItemTemplate(
        name="John Doe Identity",
        type=ItemTemplateType.VALUE_1,  # Identity type
        identity=ItemIdentity(
            firstName="John",
            lastName="Doe",
            email="john.doe@example.com",
            phone="+1-555-0123",
            address1="123 Main St",
            city="Anytown",
            state="CA",
            postalCode="12345",
            country="US"
        )
    )
    return identity_item


def create_card_item() -> ItemTemplate:
    """Create a credit card item template."""
    card_item = ItemTemplate(
        name="Visa Credit Card",
        type=ItemTemplateType.VALUE_2,  # Card type
        card=ItemCard(
            brand=ItemCardBrand.VISA,
            cardholderName="John Doe",
            number="4111111111111111",
            expMonth="12",
            expYear="2025",
            code="123"
        )
    )
    return card_item


def create_secure_note() -> ItemTemplate:
    """Create a secure note item template."""
    secure_note = ItemTemplate(
        name="Secret Note",
        type=ItemTemplateType.VALUE_3,  # Secure note type
        secureNote=ItemSecureNote(
            type=ItemSecureNoteType.VALUE_0
        ),
        notes="This is a secure note with sensitive information"
    )
    return secure_note


def create_collection() -> Collection:
    """Create a collection with groups."""
    collection = Collection(
        name="Work Items",
        organizationId=UUID("12345678-1234-1234-1234-123456789012"),
        groups=[
            Group(
                id=UUID("87654321-4321-4321-4321-210987654321"),
                hidePasswords=False,
                readOnly=False
            )
        ]
    )
    return collection


def create_folder() -> Folder:
    """Create a folder for organizing items."""
    folder = Folder(name="Personal Items")
    return folder


def demonstrate_type_validation():
    """Demonstrate type validation and error handling."""
    print("🔍 Demonstrating type validation...")
    
    try:
        # This should work fine
        valid_item = ItemTemplate(
            name="Valid Item",
            type=ItemTemplateType.VALUE_0,
            favorite=True
        )
        print(f"✅ Valid item created: {valid_item.name}")
        
        # This should also work (optional fields)
        minimal_item = ItemTemplate(name="Minimal Item")
        print(f"✅ Minimal item created: {minimal_item.name}")
        
    except Exception as e:
        print(f"❌ Validation error: {e}")


def main():
    """Main example function."""
    print("🚀 Bitwarden Vault Management API Types Example")
    print("=" * 50)
    
    # Create different types of items
    print("\n📝 Creating different item types...")
    
    login_item = create_login_item()
    print(f"✅ Login item: {login_item.name} (type: {login_item.type})")
    
    identity_item = create_identity_item()
    print(f"✅ Identity item: {identity_item.name} (type: {identity_item.type})")
    
    card_item = create_card_item()
    print(f"✅ Card item: {card_item.name} (type: {card_item.type})")
    
    secure_note = create_secure_note()
    print(f"✅ Secure note: {secure_note.name} (type: {secure_note.type})")
    
    # Create organizational structures
    print("\n📁 Creating organizational structures...")
    
    collection = create_collection()
    print(f"✅ Collection: {collection.name}")
    
    folder = create_folder()
    print(f"✅ Folder: {folder.name}")
    
    # Demonstrate type validation
    print("\n🔍 Type validation demonstration...")
    demonstrate_type_validation()
    
    print("\n🎉 Example completed successfully!")
    print("\n💡 Key benefits of using generated types:")
    print("   - Type safety and IDE autocompletion")
    print("   - Automatic validation of API data")
    print("   - Clear documentation of data structures")
    print("   - Easy serialization/deserialization")


if __name__ == "__main__":
    main()