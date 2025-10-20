#!/usr/bin/env python3

"""Automatically update spec-fixes.json.

Update spec-fixes.json with changes from vault-management-api-fixed.json that
are not already covered in the current spec-fixes.json file.

This script compares the original and fixed API spec files to find
differences, then adds any new changes to the spec-fixes.json file that aren't
already covered.

Usage:
    # Show what would be added without making changes
    python scripts/update-spec-fixes.py --dry-run

    # Apply changes to spec-fixes.json
    python scripts/update-spec-fixes.py

    # Use custom file paths
    python scripts/update-spec-fixes.py --original-file my-original.json --fixed-file my-fixed.json

Options:
    --dry-run        Show what would be added without making changes
    --output-file    Specify output file (default: scripts/spec-fixes.json)
    --original-file  Original API spec file (default: scripts/vault-management-api-original.json)
    --fixed-file     Fixed API spec file (default: scripts/vault-management-api-fixed.json)
"""

import argparse
import json
import os
import sys
from typing import Any, Dict, List, Set


def find_differences(obj1: Any, obj2: Any, path: str = '') -> List[Dict[str, Any]]:
  """Find all differences between two JSON objects, returning paths and values."""
  differences = []

  if isinstance(obj1, dict) and isinstance(obj2, dict):
    # Check for new keys in obj2
    for key in obj2:
      if key not in obj1:
        differences.append({
          'path': f'{path}|{key}' if path else key,
          'operation': 'add',
          'value': obj2[key]
        })
      elif obj1[key] != obj2[key]:
        if isinstance(obj1[key], dict) and isinstance(obj2[key], dict):
          # Recursively check nested objects
          differences.extend(
            find_differences(obj1[key], obj2[key], f'{path}|{key}' if path else key)
          )
        else:
          # Values are different
          differences.append({
            'path': f'{path}|{key}' if path else key,
            'operation': 'set_value',
            'value': obj2[key]
          })

  return differences


def get_existing_spec_fix_paths(spec_fixes_file: str) -> Set[str]:
  """Get all paths already covered in spec-fixes.json."""
  try:
    with open(spec_fixes_file, 'r') as f:
      spec_fixes = json.load(f)

    existing_paths = set()
    for fix in spec_fixes.get('path_operations', {}).get('fixes', []):
      if 'path' in fix:
        existing_paths.add(fix['path'])

    return existing_paths
  except FileNotFoundError:
    print(f"Warning: {spec_fixes_file} not found. Will create new file.")
    return set()
  except json.JSONDecodeError as e:
    print(f"Error parsing {spec_fixes_file}: {e}")
    return set()


def create_fix_entry(path: str, value: Any, operation: str = 'set_value') -> Dict[str, Any]:
  """Create a fix entry for the spec-fixes format."""
  # Determine description based on the path
  if 'description' in path:
    if 'components|schemas|' in path:
      schema_name = path.split('|')[2]
      prop_name = path.split('|')[-2] if 'properties' in path else 'schema'
      description = f"Add description to {schema_name} {prop_name} property"
    else:
      description = f"Add description to {path.split('|')[-1]}"
  elif 'title' in path:
    schema_name = path.split('|')[2]
    description = f"Add title to {schema_name} schema"
  else:
    description = f"Set value for {path}"

  return {"operation": operation, "path": path, "value": value, "description": description}


def main() -> None:
  """Main function to update spec-fixes.json with new changes from fixed API spec."""
  parser = argparse.ArgumentParser(description='Update spec-fixes.json with new changes')
  parser.add_argument(
    '--dry-run',
    action='store_true',
    help='Show what would be added without making changes'
  )
  parser.add_argument(
    '--output-file',
    default='scripts/spec-fixes.json',
    help='Output file path (default: scripts/spec-fixes.json)'
  )
  parser.add_argument(
    '--original-file',
    default='scripts/vault-management-api-original.json',
    help='Original API spec file'
  )
  parser.add_argument(
    '--fixed-file',
    default='scripts/vault-management-api-fixed.json',
    help='Fixed API spec file'
  )

  args = parser.parse_args()

  # Load the original and fixed files
  try:
    with open(args.original_file, 'r') as f:
      original = json.load(f)

    print(f"Loaded original file: {args.original_file}")
  except FileNotFoundError:
    print(f"Error: {args.original_file} not found")
    sys.exit(1)
  except json.JSONDecodeError as e:
    print(f"Error parsing {args.original_file}: {e}")
    sys.exit(1)

  try:
    with open(args.fixed_file, 'r') as f:
      fixed = json.load(f)

    print(f"Loaded fixed file: {args.fixed_file}")
  except FileNotFoundError:
    print(f"Error: {args.fixed_file} not found")
    sys.exit(1)
  except json.JSONDecodeError as e:
    print(f"Error parsing {args.fixed_file}: {e}")
    sys.exit(1)

  # Get existing spec-fix paths
  existing_paths = get_existing_spec_fix_paths(args.output_file)
  print(f"Found {len(existing_paths)} existing paths in spec-fixes")

  # Find all differences
  all_differences = []

  # Check paths section
  path_diffs = find_differences(original.get('paths', {}), fixed.get('paths', {}), 'paths')
  all_differences.extend(path_diffs)

  # Check components section
  comp_diffs = find_differences(
    original.get('components', {}), fixed.get('components', {}), 'components'
  )
  all_differences.extend(comp_diffs)

  print(f"Found {len(all_differences)} total differences")

  # Filter out differences that are already covered
  new_fixes = []
  for diff in all_differences:
    spec_path = diff['path']

    # Skip if already covered
    if spec_path in existing_paths:
      continue

    # Only include certain types of changes
    operation_valid = diff['operation'] in ['add', 'set_value']
    path_valid = (
      'description' in spec_path or 'title' in spec_path or 'schema' in spec_path
    )
    if operation_valid and path_valid:
      new_fixes.append(create_fix_entry(spec_path, diff['value'], diff['operation']))

  if not new_fixes:
    print("No new changes to add to spec-fixes.json")
    return

  print(f"\nFound {len(new_fixes)} new changes to add:")
  for fix in new_fixes:
    print(f"  - {fix['path']}: {fix['description']}")

  if args.dry_run:
    print("\nDry run complete. No changes made.")
    return

  # Load existing spec-fixes or create new structure
  try:
    with open(args.output_file, 'r') as f:
      spec_fixes = json.load(f)
  except FileNotFoundError:
    spec_fixes = {
      "path_operations": {
        "description": "Operations on JSON paths in the spec",
        "fixes": []
      }
    }

  # Add new fixes
  spec_fixes['path_operations']['fixes'].extend(new_fixes)

  # Write updated spec-fixes
  try:
    with os.fdopen(os.open(args.output_file, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o644),
                   'w') as f:
      json.dump(spec_fixes, f, indent=2)

    print(f"\nSuccessfully updated {args.output_file} with {len(new_fixes)} new fixes")
  except Exception as e:
    print(f"Error writing to {args.output_file}: {e}")
    sys.exit(1)


if __name__ == '__main__':
  main()
