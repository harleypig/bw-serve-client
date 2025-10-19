#!/usr/bin/env python3

"""Fix OpenAPI specification for Bitwarden Vault Management API.

This script applies systematic fixes to the original Bitwarden OpenAPI spec
to make it suitable for code generation with datamodel-code-generator.

Usage:
    python scripts/fix_openapi_spec.py
"""

import json
import re
import sys
from pathlib import Path
from typing import Dict, Any, List, Union


class OpenAPISpecFixer:
  """Applies systematic fixes to OpenAPI specifications."""

  def __init__(self, fixes_config_path: str):
    """Initialize with fixes configuration.

        Args:
            fixes_config_path: Path to JSON file containing fix configurations
        """
    with open(fixes_config_path) as f:
      self.fixes = json.load(f)
    self.changes_made = []

  def _get_value_at_path(self, spec: Dict[str, Any], path: str) -> Any:
    """Get value at a dot-separated path in the spec.

        Args:
            spec: OpenAPI specification dictionary
            path: Dot-separated path like "paths./object/item/{id}.get.responses"

        Returns:
            Value at the path, or None if path doesn't exist
        """
    parts = path.split('.')
    current = spec

    for part in parts:
      if isinstance(current, dict) and part in current:
        current = current[part]
      else:
        return None

    return current

  def _set_value_at_path(self, spec: Dict[str, Any], path: str, value: Any) -> None:
    """Set value at a dot-separated path in the spec.

        Args:
            spec: OpenAPI specification dictionary
            path: Dot-separated path like "paths./object/item/{id}.get.responses"
            value: Value to set
        """
    parts = path.split('.')
    current = spec

    # Navigate to the parent of the target
    for part in parts[:-1]:
      if part not in current:
        current[part] = {}
      current = current[part]

    # Set the final value
    current[parts[-1]] = value

  def _path_exists(self, spec: Dict[str, Any], path: str) -> bool:
    """Check if a dot-separated path exists in the spec.

        Args:
            spec: OpenAPI specification dictionary
            path: Dot-separated path

        Returns:
            True if path exists, False otherwise
        """
    return self._get_value_at_path(spec, path) is not None

  def _rename_key_at_path(
    self, spec: Dict[str, Any], parent_path: str, old_key: str, new_key: str
  ) -> bool:
    """Rename a key at the specified parent path.

        Args:
            spec: OpenAPI specification dictionary
            parent_path: Path to the parent object containing the key
            old_key: Current key name
            new_key: New key name

        Returns:
            True if rename was successful, False if old_key doesn't exist
        """
    parent = self._get_value_at_path(spec, parent_path)
    if isinstance(parent, dict) and old_key in parent:
      parent[new_key] = parent.pop(old_key)
      return True
    return False

  def apply_path_operations(self, spec: Dict[str, Any]) -> Dict[str, Any]:
    """Apply path-based operations to the spec.

        Args:
            spec: OpenAPI specification dictionary

        Returns:
            Modified specification
        """
    operations = self.fixes.get("path_operations", {}).get("fixes", [])

    for op in operations:
      operation = op["operation"]
      path = op["path"]
      description = op.get("description", "")

      if operation == "rename_key":
        success = self._rename_key_at_path(spec, path, op["old_key"], op["new_key"])
        if success:
          self.changes_made.append(f"Renamed key: {description}")
        else:
          self.changes_made.append(f"Key not found (skipped): {description}")

      elif operation == "set_value":
        if self._path_exists(spec, path):
          current_value = self._get_value_at_path(spec, path)
          if current_value != op["value"]:
            self._set_value_at_path(spec, path, op["value"])
            self.changes_made.append(f"Updated value: {description}")
          else:
            self.changes_made.append(f"Value unchanged (already correct): {description}")
        else:
          self._set_value_at_path(spec, path, op["value"])
          self.changes_made.append(f"Added new value: {description}")

      elif operation == "add_if_missing":
        if not self._path_exists(spec, path):
          self._set_value_at_path(spec, path, op["value"])
          self.changes_made.append(f"Added missing: {description}")
        else:
          self.changes_made.append(f"Already exists (skipped): {description}")

      else:
        self.changes_made.append(f"Unknown operation '{operation}': {description}")

    return spec

  def apply_all_fixes(self, spec: Dict[str, Any]) -> Dict[str, Any]:
    """Apply all configured fixes to the specification.

        Args:
            spec: Original OpenAPI specification

        Returns:
            Fixed specification
        """
    print("🔧 Applying OpenAPI spec fixes...")

    spec = self.apply_path_operations(spec)

    return spec

  def print_summary(self):
    """Print summary of changes made."""
    if self.changes_made:
      print(f"\n✅ Applied {len(self.changes_made)} fixes:")
      for change in self.changes_made:
        print(f"   • {change}")
    else:
      print("\n⚠️  No fixes were applied")


def main():
  """Main function to fix the OpenAPI specification."""
  script_dir = Path(__file__).parent

  # File paths
  original_spec = script_dir / "vault-management-api.json"
  fixed_spec = script_dir / "vault-management-api-fixed.json"
  fixes_config = script_dir / "spec-fixes.json"

  # Check if files exist
  if not original_spec.exists():
    print(f"❌ Original spec not found: {original_spec}")
    sys.exit(1)

  if not fixes_config.exists():
    print(f"❌ Fixes config not found: {fixes_config}")
    sys.exit(1)

  try:
    # Load original specification
    print(f"📖 Loading original spec: {original_spec}")
    with open(original_spec) as f:
      spec = json.load(f)

    # Apply fixes
    fixer = OpenAPISpecFixer(str(fixes_config))
    fixed_spec_data = fixer.apply_all_fixes(spec)

    # Write fixed specification
    print(f"💾 Writing fixed spec: {fixed_spec}")
    with open(fixed_spec, 'w') as f:
      json.dump(fixed_spec_data, f, indent=2)

    # Print summary
    fixer.print_summary()
    print(f"\n🎉 Fixed specification written to: {fixed_spec}")

  except json.JSONDecodeError as e:
    print(f"❌ JSON parsing error: {e}")
    sys.exit(1)
  except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)


if __name__ == "__main__":
  main()
