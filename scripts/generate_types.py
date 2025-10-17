#!/usr/bin/env python3

"""Generate Python types from Bitwarden Vault Management API OpenAPI specification.

This script generates Pydantic models and type definitions from the OpenAPI
specification, organizing them into logical modules based on their usage patterns.
"""

import argparse
import json
import sys
from pathlib import Path
from string import Template
from typing import Any, Dict, List, Set, Union, Optional
from datetime import datetime


class TypeGenerator:
  """Generate Python types from OpenAPI specification using templates."""

  def __init__(self, swagger_file: str, output_dir: str = "bw_serve_client/types"):
    """Initialize the type generator."""
    self.swagger_file = Path(swagger_file)
    self.output_dir = Path(output_dir)
    self.templates_dir = Path(__file__).parent / "templates"
    self.data = self._load_swagger_data()
    self.schemas = self.data.get('components', {}).get('schemas', {})

    # Load templates
    self.templates = self._load_templates()

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

  def _load_templates(self) -> Dict[str, Template]:
    """Load all template files."""
    templates = {}
    template_files = {
      'module': 'module_template.py',
      'init': 'init_template.py',
      'enum': 'enum_template.py',
      'model': 'model_template.py',
      'property': 'property_template.py',
      'imports': 'imports_template.py',
    }

    for name, filename in template_files.items():
      template_path = self.templates_dir / filename

      try:
        with open(template_path, 'r', encoding='utf-8') as f:
          templates[name] = Template(f.read())

      except FileNotFoundError:
        print(f"Error: Template file '{template_path}' not found.", file=sys.stderr)
        sys.exit(1)

    return templates

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

    # XXX: Use dicts for the simple return values so we don't have a stack of
    #      if/elif's.

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
    # XXX: Use dicts for the simple return values so we don't have a stack of
    #      if/elif's.

    # Handle special cases
    if schema_name == 'field':
      # Rename to avoid conflict with Pydantic Field
      return 'CustomField'

    elif schema_name == 'item.card':
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
      return ''.join(word.capitalize() for word in schema_name.split('_'))

  def _generate_enum_class(
    self, field_name: str, enum_values: List[Any], parent_class: str
  ) -> str:
    """Generate enum class for a field using template."""
    enum_name = f"{parent_class}{field_name.capitalize()}"

    # Generate enum values
    enum_value_lines = []

    for i, value in enumerate(enum_values):
      if isinstance(value, str):
        # Use the string value as the enum name
        enum_key = value.upper().replace(' ', '_').replace('-', '_')
        enum_value_lines.append(f'  {enum_key} = {repr(value)}')

      else:
        # Use a generic name for numeric values
        enum_value_lines.append(f'  VALUE_{i} = {repr(value)}')

    enum_values_str = '\n'.join(enum_value_lines)

    return self.templates['enum'].substitute(
      enum_name=enum_name, field_name=field_name, enum_values=enum_values_str
    )

  def _generate_pydantic_model(
    self, schema_name: str, schema: Dict[str, Any], module_name: str = ""
  ) -> str:
    """Generate Pydantic model code for a schema using templates."""
    class_name = self._get_class_name(schema_name)

    # Generate enum classes first
    properties = schema.get('properties', {})
    enum_classes = []

    for prop_name, prop_schema in properties.items():
      if 'enum' in prop_schema:
        enum_class = self._generate_enum_class(prop_name, prop_schema['enum'], class_name)
        enum_classes.append(enum_class)

    # Generate properties
    property_lines = []
    required_fields = set(schema.get('required', []))

    if not properties:
      property_lines.append("  pass")

    else:
      for prop_name, prop_schema in properties.items():
        # Generate field annotation
        field_type = self._python_type_from_openapi(prop_schema, module_name)

        # Make all fields optional by default for easier usage
        # Only make required if explicitly marked as required in OpenAPI
        is_required = prop_name in required_fields

        if not is_required:
          field_type = f'Optional[{field_type}]'

        # Add field description if available
        description = prop_schema.get('description', '')
        comment = f"  # {description}" if description else ""

        property_line = self.templates['property'].substitute(
          prop_name=prop_name, field_type=field_type, comment=comment
        )
        property_lines.append(property_line)

    properties_str = '\n'.join(property_lines)

    # Generate the main model class
    description = schema.get('description', f'{class_name} model')

    if not description.endswith('.'):
      description += '.'

    model_class = self.templates['model'].substitute(
      class_name=class_name, description=description, properties=properties_str
    )

    # Combine enum classes and model class
    if enum_classes:
      return '\n\n'.join(enum_classes) + '\n\n' + model_class

    else:
      return model_class

  def _generate_imports(self, types_used: Set[str], module_name: str) -> str:
    """Generate import statements for the types used using template."""
    # Generate TYPE_CHECKING imports
    type_checking_imports = []

    # XXX: The import names should be either generated from the swagger file,
    #      or pre-defined.

    if module_name != "global_types":
      type_checking_imports.append("if TYPE_CHECKING:")
      type_checking_imports.append(
        "  from .global_types import ("
        "Collection, CustomField, Folder, Group, Status, Uris"
        ")"
      )
      type_checking_imports.append("")

    if module_name != "item_types":
      type_checking_imports.append("if TYPE_CHECKING:")
      type_checking_imports.append(
        "  from .item_types import ("
        "ItemCard, ItemIdentity, ItemLogin, ItemSecureNote, ItemTemplate"
        ")"
      )
      type_checking_imports.append("")

    if module_name != "send_types":
      type_checking_imports.append("if TYPE_CHECKING:")
      type_checking_imports.append("  from .send_types import SendTemplate, SendText")
      type_checking_imports.append("")

    type_checking_str = '\n'.join(type_checking_imports)

    return self.templates['imports'].substitute(type_checking_imports=type_checking_str)

  def generate_global_types(self) -> str:
    """Generate global types module using template."""
    # Generate all classes (includes enum classes within the model generation)
    class_lines = []

    for schema_name in sorted(self.global_types):
      schema = self.schemas[schema_name]
      class_lines.append(self._generate_pydantic_model(schema_name, schema, "global_types"))

    model_classes_str = '\n\n'.join(class_lines)

    return self.templates['module'].substitute(
      module_docstring='Global types used across multiple API endpoints.',
      imports=self._generate_imports(set(self.global_types), "global_types"),
      enum_classes='',
      model_classes='\n' + model_classes_str
    )

  def generate_item_types(self) -> str:
    """Generate item-specific types module using template."""
    # Generate all classes (includes enum classes within the model generation)
    class_lines = []

    for schema_name in sorted(self.item_types):
      schema = self.schemas[schema_name]
      class_lines.append(self._generate_pydantic_model(schema_name, schema, "item_types"))

    model_classes_str = '\n\n'.join(class_lines)

    return self.templates['module'].substitute(
      module_docstring='Types specific to vault items and templates.',
      imports=self._generate_imports(set(self.item_types), "item_types"),
      enum_classes='',
      model_classes=model_classes_str
    )

  def generate_send_types(self) -> str:
    """Generate send-specific types module using template."""
    # Generate all classes (includes enum classes within the model generation)
    class_lines = []

    for schema_name in sorted(self.send_types):
      schema = self.schemas[schema_name]
      class_lines.append(self._generate_pydantic_model(schema_name, schema, "send_types"))

    model_classes_str = '\n\n'.join(class_lines)

    return self.templates['module'].substitute(
      module_docstring='Types for Bitwarden Send functionality.',
      imports=self._generate_imports(set(self.send_types), "send_types"),
      enum_classes='',
      model_classes=model_classes_str
    )

  def generate_response_types(self) -> str:
    """Generate response types module using template."""
    # Generate all classes (includes enum classes within the model generation)
    class_lines = []

    for schema_name in sorted(self.response_types):
      schema = self.schemas[schema_name]
      class_lines.append(
        self._generate_pydantic_model(schema_name, schema, "response_types")
      )

    model_classes_str = '\n\n'.join(class_lines)

    return self.templates['module'].substitute(
      module_docstring='API response wrapper types.',
      imports=self._generate_imports(set(self.response_types), "response_types"),
      enum_classes='',
      model_classes=model_classes_str
    )

  def generate_other_types(self) -> str:
    """Generate other types module using template."""
    # Generate all classes (includes enum classes within the model generation)
    class_lines = []

    for schema_name in sorted(self.other_types):
      schema = self.schemas[schema_name]
      class_lines.append(self._generate_pydantic_model(schema_name, schema, "other_types"))

    if class_lines:
      model_classes_str = '\n\n'.join(class_lines)
      return self.templates['module'].substitute(
        module_docstring='Additional utility types.',
        imports=self._generate_imports(set(self.other_types), "other_types"),
        enum_classes='',
        model_classes='\n' + model_classes_str
      )

    else:
      # Handle empty module case
      return self.templates['module'].substitute(
        module_docstring='Additional utility types.',
        imports=self._generate_imports(set(self.other_types), "other_types"),
        enum_classes='',
        model_classes=''
      )

  def generate_types_init(self) -> str:
    """Generate __init__.py for types package using template."""
    # XXX: These should be generated from data in the swagger file.

    # Generate imports
    import_lines = [
      'from .global_types import (  # noqa: F401',
      '  Collection,',
      '  CustomField,',
      '  CustomFieldType,',
      '  Folder,',
      '  Group,',
      '  Status,',
      '  Uris,',
      '  UrisMatch,',
      ')',
      'from .item_types import (  # noqa: F401',
      '  ItemCard,',
      '  ItemCardBrand,',
      '  ItemIdentity,',
      '  ItemLogin,',
      '  ItemSecureNote,',
      '  ItemSecureNoteType,',
      '  ItemTemplate,',
      '  ItemTemplateReprompt,',
      '  ItemTemplateType,',
      ')',
      '# other_types module is currently empty',
      'from .response_types import LockUnlockSuccess  # noqa: F401',
      'from .send_types import SendTemplate, SendText  # noqa: F401',
      '',
    ]

    # Add all class names to __all__
    all_classes = []

    for schema_name in self.schemas.keys():
      class_name = self._get_class_name(schema_name)
      all_classes.append(f"  '{class_name}',")

    all_classes_str = '\n'.join(sorted(all_classes))

    return self.templates['init'].substitute(
      imports='\n'.join(import_lines), all_classes=all_classes_str
    ) + '\n'

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
    # XXX: Convert this to a template.
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
