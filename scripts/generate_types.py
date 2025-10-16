#!/usr/bin/env python3

"""Generate Python types from Bitwarden Vault Management API OpenAPI specification.

This script generates Pydantic models and type definitions from the OpenAPI
specification, organizing them into logical modules based on their usage patterns.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Set, Union, Optional
from datetime import datetime


class TypeGenerator:
  """Generate Python types from OpenAPI specification."""

  def __init__(self, swagger_file: str, output_dir: str = "bw_serve_client/types"):
    """Initialize the type generator."""
    self.swagger_file = Path(swagger_file)
    self.output_dir = Path(output_dir)
    self.data = self._load_swagger_data()
    self.schemas = self.data.get('components', {}).get('schemas', {})

    # Categorize schemas
    self.global_types: List[str] = []
    self.item_types: List[str] = []
    self.response_types: List[str] = []
    self.send_types: List[str] = []
    self.other_types: List[str] = []

    self._categorize_schemas()

  def _load_swagger_data(self) -> Dict[str, Any]:
    """Load and parse the swagger JSON file."""
    try:
      with open(self.swagger_file, 'r', encoding='utf-8') as f:
        return json.load(f)
    except FileNotFoundError:
      print(f"Error: Swagger file '{self.swagger_file}' not found.", file=sys.stderr)
      sys.exit(1)
    except json.JSONDecodeError as e:
      print(f"Error: Invalid JSON in swagger file: {e}", file=sys.stderr)
      sys.exit(1)

  def _categorize_schemas(self) -> None:
    """Categorize schemas based on their usage patterns."""
    for name, schema in self.schemas.items():
      if name.startswith('item.'):
        self.item_types.append(name)
      elif name.startswith('send.'):
        self.send_types.append(name)
      elif name.endswith('.success') or name.endswith('.error'):
        self.response_types.append(name)
      elif name in ['collection', 'field', 'folder', 'group', 'status', 'uris']:
        self.global_types.append(name)
      else:
        self.other_types.append(name)

  def _python_type_from_openapi(self, schema: Dict[str, Any], module_name: str = "") -> str:
    """Convert OpenAPI type to Python type annotation."""
    if 'type' not in schema:
      return 'Any'

    openapi_type = schema['type']
    format_type = schema.get('format', '')

    # Handle enums - return the base type, not the enum class
    if 'enum' in schema:
      enum_values = schema['enum']
      if all(isinstance(v, int) for v in enum_values):
        return 'int'
      elif all(isinstance(v, str) for v in enum_values):
        return 'str'
      else:
        return 'Union[' + ', '.join(str(type(v).__name__) for v in enum_values) + ']'

    if openapi_type == 'string':
      if format_type == 'uuid':
        return 'UUID'
      elif format_type == 'date':
        return 'date'
      elif format_type == 'date-time':
        return 'datetime'
      else:
        return 'str'
    elif openapi_type == 'integer':
      return 'int'
    elif openapi_type == 'number':
      return 'float'
    elif openapi_type == 'boolean':
      return 'bool'
    elif openapi_type == 'array':
      items = schema.get('items', {})
      if '$ref' in items:
        ref_name = items['$ref'].split('/')[-1]
        class_name = self._get_class_name(ref_name)
        # Use string annotation for forward references
        return f'List["{class_name}"]'
      else:
        item_type = self._python_type_from_openapi(items, module_name)
        return f'List[{item_type}]'
    elif openapi_type == 'object':
      return 'Dict[str, Any]'
    else:
      return 'Any'

  def _get_class_name(self, schema_name: str) -> str:
    """Convert schema name to Python class name."""
    # Handle special cases
    if schema_name == 'item.card':
      return 'ItemCard'
    elif schema_name == 'item.identity':
      return 'ItemIdentity'
    elif schema_name == 'item.login':
      return 'ItemLogin'
    elif schema_name == 'item.secureNote':
      return 'ItemSecureNote'
    elif schema_name == 'item.template':
      return 'ItemTemplate'
    elif schema_name == 'send.template':
      return 'SendTemplate'
    elif schema_name == 'send.text':
      return 'SendText'
    elif schema_name == 'lockunlock.success':
      return 'LockUnlockSuccess'
    else:
      # Convert snake_case to PascalCase
      return ''.join(word.capitalize() for word in schema_name.split('_'))

  def _generate_enum_class(
    self, field_name: str, enum_values: List[Any], parent_class: str
  ) -> str:
    """Generate enum class for a field."""
    enum_name = f"{parent_class}{field_name.capitalize()}"

    lines = []
    lines.append(f"class {enum_name}(Enum):")

    for i, value in enumerate(enum_values):
      if isinstance(value, str):
        # Use the string value as the enum name
        enum_key = value.upper().replace(' ', '_').replace('-', '_')
        lines.append(f'    {enum_key} = {repr(value)}')
      else:
        # Use a generic name for numeric values
        lines.append(f'    VALUE_{i} = {repr(value)}')

    return '\n'.join(lines)

  def _generate_pydantic_model(
    self, schema_name: str, schema: Dict[str, Any], module_name: str = ""
  ) -> str:
    """Generate Pydantic model code for a schema."""
    class_name = self._get_class_name(schema_name)

    lines = []

    # Generate enum classes first
    properties = schema.get('properties', {})
    enum_classes = []

    for prop_name, prop_schema in properties.items():
      if 'enum' in prop_schema:
        enum_class = self._generate_enum_class(prop_name, prop_schema['enum'], class_name)
        enum_classes.append(enum_class)

    if enum_classes:
      lines.extend(enum_classes)
      lines.append("")

    # Generate the main model class
    lines.append(f"class {class_name}(BaseModel):")

    # Add docstring
    description = schema.get('description', f'{class_name} model')
    lines.append(f'    """{description}"""')
    lines.append("")

    # Add properties
    required_fields = set(schema.get('required', []))

    if not properties:
      lines.append("    pass")
    else:
      for prop_name, prop_schema in properties.items():
        # Generate field annotation
        field_type = self._python_type_from_openapi(prop_schema, module_name)

        # Handle optional fields
        is_required = prop_name in required_fields
        if not is_required:
          field_type = f'Optional[{field_type}]'

        # Add field description if available
        description = prop_schema.get('description', '')
        if description:
          lines.append(f"    {prop_name}: {field_type}  # {description}")
        else:
          lines.append(f"    {prop_name}: {field_type}")

    return '\n'.join(lines)

  def _generate_imports(self, types_used: Set[str], module_name: str) -> List[str]:
    """Generate import statements for the types used."""
    imports = [
      "from typing import Any, Dict, List, Optional, Union, TYPE_CHECKING",
      "from datetime import date, datetime",
      "from uuid import UUID",
      "from enum import Enum",
      "from pydantic import BaseModel, Field",
      "",
    ]

    # Add TYPE_CHECKING imports to avoid circular imports
    if module_name != "global_types":
      imports.append("if TYPE_CHECKING:")
      imports.append(
        "    from .global_types import Collection, Field, Folder, Group, Status, Uris"
      )
      imports.append("")

    if module_name != "item_types":
      imports.append("if TYPE_CHECKING:")
      imports.append(
        "    from .item_types import ("
        "        ItemCard, ItemIdentity, ItemLogin, ItemSecureNote, ItemTemplate"
        "    )"
      )
      imports.append("")

    if module_name != "send_types":
      imports.append("if TYPE_CHECKING:")
      imports.append("    from .send_types import SendTemplate, SendText")
      imports.append("")

    return imports

  def generate_global_types(self) -> str:
    """Generate global types module."""
    lines = []
    lines.extend(self._generate_imports(set(self.global_types), "global_types"))
    lines.append("")

    for schema_name in sorted(self.global_types):
      schema = self.schemas[schema_name]
      lines.append(self._generate_pydantic_model(schema_name, schema, "global_types"))
      lines.append("")

    return '\n'.join(lines)

  def generate_item_types(self) -> str:
    """Generate item-specific types module."""
    lines = []
    lines.extend(self._generate_imports(set(self.item_types), "item_types"))
    lines.append("")

    for schema_name in sorted(self.item_types):
      schema = self.schemas[schema_name]
      lines.append(self._generate_pydantic_model(schema_name, schema, "item_types"))
      lines.append("")

    return '\n'.join(lines)

  def generate_send_types(self) -> str:
    """Generate send-specific types module."""
    lines = []
    lines.extend(self._generate_imports(set(self.send_types), "send_types"))
    lines.append("")

    for schema_name in sorted(self.send_types):
      schema = self.schemas[schema_name]
      lines.append(self._generate_pydantic_model(schema_name, schema, "send_types"))
      lines.append("")

    return '\n'.join(lines)

  def generate_response_types(self) -> str:
    """Generate response types module."""
    lines = []
    lines.extend(self._generate_imports(set(self.response_types), "response_types"))
    lines.append("")

    for schema_name in sorted(self.response_types):
      schema = self.schemas[schema_name]
      lines.append(self._generate_pydantic_model(schema_name, schema, "response_types"))
      lines.append("")

    return '\n'.join(lines)

  def generate_other_types(self) -> str:
    """Generate other types module."""
    lines = []
    lines.extend(self._generate_imports(set(self.other_types), "other_types"))
    lines.append("")

    for schema_name in sorted(self.other_types):
      schema = self.schemas[schema_name]
      lines.append(self._generate_pydantic_model(schema_name, schema, "other_types"))
      lines.append("")

    return '\n'.join(lines)

  def generate_types_init(self) -> str:
    """Generate __init__.py for types package."""
    lines = [
      '"""Type definitions for Bitwarden Vault Management API.',
      '',
      'This package contains Pydantic models generated from the OpenAPI',
      'specification for the Bitwarden Vault Management API.',
      '"""',
      '',
      'from .global_types import *',
      'from .item_types import *',
      'from .send_types import *',
      'from .response_types import *',
      'from .other_types import *',
      '',
      '__all__ = [',
    ]

    # Add all class names to __all__
    all_classes = []
    for schema_name in self.schemas.keys():
      class_name = self._get_class_name(schema_name)
      all_classes.append(f"    '{class_name}',")

    lines.extend(sorted(all_classes))
    lines.append(']')

    return '\n'.join(lines)

  def generate_all_types(self) -> None:
    """Generate all type modules."""
    # Create output directory
    self.output_dir.mkdir(parents=True, exist_ok=True)

    # Generate individual modules
    modules = {
      'global_types.py': self.generate_global_types(),
      'item_types.py': self.generate_item_types(),
      'send_types.py': self.generate_send_types(),
      'response_types.py': self.generate_response_types(),
      'other_types.py': self.generate_other_types(),
      '__init__.py': self.generate_types_init(),
    }

    for filename, content in modules.items():
      output_file = self.output_dir / filename
      with open(output_file, 'w', encoding='utf-8') as f:
        f.write(content)
      print(f"Generated: {output_file}")

  def print_summary(self) -> None:
    """Print summary of generated types."""
    print("\n" + "=" * 60)
    print("TYPES GENERATION SUMMARY")
    print("=" * 60)
    print(f"Total schemas processed: {len(self.schemas)}")
    print(f"Global types: {len(self.global_types)}")
    print(f"Item types: {len(self.item_types)}")
    print(f"Send types: {len(self.send_types)}")
    print(f"Response types: {len(self.response_types)}")
    print(f"Other types: {len(self.other_types)}")
    print(f"Output directory: {self.output_dir}")
    print("=" * 60)


def main():
  """Main entry point."""
  parser = argparse.ArgumentParser(
    description=
    "Generate Python types from Bitwarden Vault Management API OpenAPI specification"
  )

  parser.add_argument(
    'swagger_file',
    nargs='?',
    default='docs/vault-management-api.json',
    help='Path to the swagger JSON file'
  )

  parser.add_argument(
    '--output-dir',
    '-o',
    default='bw_serve_client/types',
    help='Output directory for generated types (default: bw_serve_client/types)'
  )

  args = parser.parse_args()

  try:
    generator = TypeGenerator(args.swagger_file, args.output_dir)
    generator.generate_all_types()
    generator.print_summary()

  except Exception as e:
    print(f"Error: {e}", file=sys.stderr)
    sys.exit(1)


if __name__ == '__main__':
  main()
