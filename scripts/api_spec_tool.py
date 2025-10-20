#!/usr/bin/env python3

"""Unified API Specification Tool for Bitwarden Vault Management API.

This script provides a unified interface for working with the Bitwarden Vault
Management API OpenAPI specification. It combines functionality from multiple
scripts into a single tool with subcommands.

Usage:
    python scripts/api_spec_tool.py <subcommand> [options]

Subcommands:
    analyze    Analyze API structure and extract key information
    extract    Extract and format API routes
    update     Update spec-fixes.json with new changes
    fix        Apply fixes to the OpenAPI specification

Examples:
    # Analyze the API structure
    python scripts/api_spec_tool.py analyze scripts/vault-management-api-original.json

    # Extract routes in markdown format
    python scripts/api_spec_tool.py extract --format markdown \\
        scripts/vault-management-api-original.json

    # Update spec-fixes with new changes (dry run)
    python scripts/api_spec_tool.py update --dry-run

    # Apply fixes to create a fixed specification
    python scripts/api_spec_tool.py fix
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Set
from deepdiff import DeepDiff


class APISpecTool:
    """Unified tool for working with API specifications."""

    def __init__(self) -> None:
        """Initialize the API spec tool."""
        self.script_dir = Path(__file__).parent

    def load_json_file(self, file_path: str, description: str = "JSON file") -> Dict[str, Any]:
        """Load and parse a JSON file with error handling."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if not isinstance(data, dict):
                    raise ValueError(
                        f"Expected JSON object (dict), got {type(data).__name__}"
                    )
                return data

        except FileNotFoundError:
            print(f"Error: {description} not found: {file_path}", file=sys.stderr)
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in {description}: {e}", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"Error reading {description}: {e}", file=sys.stderr)
            sys.exit(1)

    def analyze_api_structure(self, swagger_file: str) -> Dict[str, Any]:
        """Analyze the API structure and extract key information."""
        data = self.load_json_file(swagger_file, "swagger file")

        error_codes: Set[str] = set()
        tags: Set[str] = set()
        response_patterns: Dict[str, Set[str]] = {}

        analysis: Dict[str, Any] = {
            'api_info': {},
            'authentication': {},
            'server_info': {},
            'response_patterns': response_patterns,
            'error_codes': error_codes,
            'data_models': {},
            'parameter_patterns': {},
            'request_body_patterns': {},
            'tags': tags,
            'endpoint_categories': {},
            'examples': {},
            'validation_rules': {}
        }

        # Extract API info
        if 'info' in data:
            analysis['api_info'] = {
                'title': data['info'].get('title', ''),
                'description': data['info'].get('description', ''),
                'version': data['info'].get('version', ''),
                'openapi_version': data.get('openapi', '')
            }

        # Extract authentication info
        if 'security' in data:
            analysis['authentication'] = data['security']

        if 'components' in data and 'securitySchemes' in data['components']:
            analysis['authentication']['schemes'] = data['components'][
                'securitySchemes'
            ]

        # Extract server info
        if 'servers' in data:
            analysis['server_info'] = data['servers']
        elif 'host' in data:
            analysis['server_info'] = {
                'host': data.get('host', ''),
                'basePath': data.get('basePath', ''),
                'schemes': data.get('schemes', [])
            }

        # Analyze paths
        if 'paths' in data:
            for path, methods in data['paths'].items():
                for method, details in methods.items():
                    if method.upper() in [
                        'GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS'
                    ]:
                        # Extract tags
                        if 'tags' in details:
                            tags.update(details['tags'])

                        # Extract parameters
                        if 'parameters' in details:
                            for param in details['parameters']:
                                param_info = {
                                    'name': param.get('name', ''),
                                    'in': param.get('in', ''),
                                    'required': param.get('required', False),
                                    'type': param.get('schema', {}).get('type', ''),
                                    'format': param.get('schema', {}).get('format', ''),
                                    'description': param.get('description', '')
                                }
                                if param_info['in'] not in analysis['parameter_patterns']:
                                    analysis['parameter_patterns'][param_info['in']] = []

                                analysis['parameter_patterns'][param_info['in']].append(param_info)

                        # Extract request body patterns
                        if 'requestBody' in details:
                            req_body = details['requestBody']
                            content_types = list(req_body.get('content', {}).keys())
                            analysis['request_body_patterns'][f"{method.upper()} {path}"] = {
                                'content_types': content_types,
                                'required': req_body.get('required', False),
                                'description': req_body.get('description', '')
                            }

                        # Extract response patterns
                        if 'responses' in details:
                            for status_code, response in details['responses'].items():
                                error_codes.add(status_code)

                                if 'content' in response:
                                    content_types = list(response['content'].keys())
                                    if status_code not in response_patterns:
                                        response_patterns[status_code] = set()

                                    response_patterns[status_code].update(content_types)

                                    # Extract examples
                                    for content_type, content_info in response['content'].items():
                                        if 'example' in content_info:
                                            example_key = f"{method.upper()} {path} {status_code}"
                                            analysis['examples'][example_key] = {
                                                'content_type': content_type,
                                                'example': content_info['example']
                                            }

        # Analyze schemas
        if 'components' in data and 'schemas' in data['components']:
            for schema_name, schema_def in data['components']['schemas'].items():
                analysis['data_models'][schema_name] = {
                    'type': schema_def.get('type', 'object'),
                    'properties': schema_def.get('properties', {}),
                    'required': schema_def.get('required', []),
                    'description': schema_def.get('description', '')
                }

        # Convert sets to lists for JSON serialization
        analysis['error_codes'] = sorted(list(error_codes))
        analysis['tags'] = sorted(list(tags))
        for status_code in response_patterns:
            analysis['response_patterns'][status_code] = sorted(
                list(response_patterns[status_code])
            )

        return analysis

    def print_analysis(self, analysis: Dict[str, Any]) -> None:
        """Print the analysis results in a readable format."""
        print("=" * 80)
        print("BITWARDEN VAULT MANAGEMENT API - LIBRARY DEVELOPMENT ANALYSIS")
        print("=" * 80)

        # API Information
        print("\n📋 API INFORMATION:")
        print("-" * 40)
        for key, value in analysis['api_info'].items():
            print(f"  {key}: {value}")

        # Authentication
        print("\n🔐 AUTHENTICATION:")
        print("-" * 40)
        if analysis['authentication']:
            for key, value in analysis['authentication'].items():
                print(f"  {key}: {value}")
        else:
            print("  No explicit authentication schemes defined")
            print("  Note: This API likely uses session-based authentication via 'bw serve'")

        # Base URL
        print("\n🌐 SERVER CONFIGURATION:")
        print("-" * 40)
        if analysis['server_info']:
            for key, value in analysis['server_info'].items():
                print(f"  {key}: {value}")
        else:
            print("  No explicit server configuration")
            print("  Note: This API runs locally via 'bw serve' command")

        # Response Patterns
        print("\n📤 RESPONSE PATTERNS:")
        print("-" * 40)
        for status_code, content_types in analysis['response_patterns'].items():
            print(f"  {status_code}: {', '.join(content_types)}")

        # Error Codes
        print("\n❌ ERROR CODES:")
        print("-" * 40)
        for code in analysis['error_codes']:
            print(f"  {code}")

        # Tags (API Categories)
        print("\n🏷️  API CATEGORIES (TAGS):")
        print("-" * 40)
        for tag in analysis['tags']:
            print(f"  - {tag}")

        # Parameter Patterns
        print("\n📝 PARAMETER PATTERNS:")
        print("-" * 40)
        for param_type, params in analysis['parameter_patterns'].items():
            print(f"  {param_type.upper()} parameters:")
            for param in params[:5]:  # Show first 5 examples
                print(
                    f"    - {param['name']} ({param['type']}) - "
                    f"{param['description'][:50]}..."
                )

            if len(params) > 5:
                print(f"    ... and {len(params) - 5} more")

        # Request Body Patterns
        print("\n📦 REQUEST BODY PATTERNS:")
        print("-" * 40)
        for endpoint, body_info in list(analysis['request_body_patterns'].items())[:5]:
            print(f"  {endpoint}:")
            print(f"    Content-Types: {', '.join(body_info['content_types'])}")
            print(f"    Required: {body_info['required']}")

        # Data Models
        print("\n🏗️  DATA MODELS (SCHEMAS):")
        print("-" * 40)
        for model_name, model_info in list(analysis['data_models'].items())[:10]:
            print(f"  {model_name}:")
            print(f"    Type: {model_info['type']}")
            if model_info['properties']:
                prop_count = len(model_info['properties'])
                print(f"    Properties: {prop_count} fields")
                # Show a few key properties
                for prop_name, prop_info in list(model_info['properties'].items())[:3]:
                    prop_type = prop_info.get('type', 'unknown')
                    print(f"      - {prop_name}: {prop_type}")

                if prop_count > 3:
                    print(f"      ... and {prop_count - 3} more properties")

        # Key Examples
        print("\n💡 KEY EXAMPLES:")
        print("-" * 40)
        for example_key, example_info in list(analysis['examples'].items())[:3]:
            print(f"  {example_key}:")
            print(f"    Content-Type: {example_info['content_type']}")
            print(f"    Example: {str(example_info['example'])[:100]}...")

        print("\n" + "=" * 80)
        print("ANALYSIS COMPLETE")
        print("=" * 80)

    def extract_routes(self, swagger_file: str) -> List[Dict[str, Any]]:
        """Extract all routes from the swagger data."""
        data = self.load_json_file(swagger_file, "swagger file")
        routes: List[Dict[str, Any]] = []

        if 'paths' not in data:
            print("Error: No 'paths' section found in swagger file.", file=sys.stderr)
            return routes

        for path, methods in data['paths'].items():
            for method, details in methods.items():
                if method.upper() in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS']:
                    route_info = {
                        'path': path,
                        'method': method.upper(),
                        'summary': details.get('summary', ''),
                        'description': details.get('description', ''),
                        'tags': details.get('tags', []),
                        'parameters': details.get('parameters', []),
                        'responses': list(details.get('responses', {}).keys())
                    }
                    routes.append(route_info)

        return routes

    def format_markdown(self, routes: List[Dict[str, Any]]) -> str:
        """Format routes as markdown."""
        output = []

        # Group routes by tags
        grouped_routes: Dict[str, List[Dict[str, Any]]] = {}

        for route in routes:
            tags = route['tags'] if route['tags'] else ['Misc']

            for tag in tags:
                if tag not in grouped_routes:
                    grouped_routes[tag] = []

                grouped_routes[tag].append(route)

        # Sort tags and format output
        for tag in sorted(grouped_routes.keys()):
            output.append(f"# {tag}")

            # Group routes by path within each tag
            path_methods: Dict[str, List[str]] = {}

            for route in grouped_routes[tag]:
                path = route['path']
                method = route['method']

                if path not in path_methods:
                    path_methods[path] = []

                path_methods[path].append(method)

            # Sort methods alphabetically for each path
            for path in sorted(path_methods.keys()):
                methods = sorted(path_methods[path])
                methods_str = ','.join(methods)
                output.append(f"  {path} ({methods_str})")

            output.append("")  # Add blank line between sections

        return "\n".join(output)

    def format_text(self, routes: List[Dict[str, Any]]) -> str:
        """Format routes as plain text."""
        output = []

        # Group routes by tags
        grouped_routes: Dict[str, List[Dict[str, Any]]] = {}
        for route in routes:
            tags = route['tags'] if route['tags'] else ['Misc']

            for tag in tags:
                if tag not in grouped_routes:
                    grouped_routes[tag] = []

                grouped_routes[tag].append(route)

        # Sort tags and format output
        for tag in sorted(grouped_routes.keys()):
            output.append(f"{tag}")
            output.append("-" * len(tag))

            # Group routes by path within each tag
            path_methods: Dict[str, List[str]] = {}

            for route in grouped_routes[tag]:
                path = route['path']
                method = route['method']

                if path not in path_methods:
                    path_methods[path] = []

                path_methods[path].append(method)

            # Sort methods alphabetically for each path
            for path in sorted(path_methods.keys()):
                methods = sorted(path_methods[path])
                methods_str = ','.join(methods)
                output.append(f"  {path} ({methods_str})")

            output.append("")  # Add blank line between sections

        return "\n".join(output)

    def format_json(self, routes: List[Dict[str, Any]]) -> str:
        """Format routes as JSON."""
        # Group routes by tags
        grouped_routes: Dict[str, List[Dict[str, Any]]] = {}

        for route in routes:
            tags = route['tags'] if route['tags'] else ['Misc']

            for tag in tags:
                if tag not in grouped_routes:
                    grouped_routes[tag] = []

                grouped_routes[tag].append(route)

        # Create simplified output structure
        output_data: Dict[str, Dict[str, List[str]]] = {}

        for tag in sorted(grouped_routes.keys()):
            # Group routes by path within each tag
            path_methods: Dict[str, List[str]] = {}

            for route in grouped_routes[tag]:
                path = route['path']
                method = route['method']

                if path not in path_methods:
                    path_methods[path] = []

                path_methods[path].append(method)

            # Sort methods alphabetically for each path
            for path in sorted(path_methods.keys()):
                methods = sorted(path_methods[path])

                if tag not in output_data:
                    output_data[tag] = {}

                output_data[tag][path] = methods

        return json.dumps(output_data, indent=2, ensure_ascii=False)

    def find_differences(self, obj1: Any, obj2: Any, path: str = '') -> List[Dict[str, Any]]:
        """Find all differences between two JSON objects using DeepDiff."""
        differences = []

        # Use DeepDiff to find all differences
        diff = DeepDiff(obj1, obj2, ignore_order=True, exclude_paths=["root['info']"])

        # Process dictionary item additions
        if 'dictionary_item_added' in diff:
            for key_path in diff['dictionary_item_added']:
                # Get the value at this path from obj2
                value = self.get_value_at_deepdiff_path(obj2, key_path)
                pipe_path = self.convert_deepdiff_path_to_pipes(key_path, path)
                differences.append({
                    'path': pipe_path,
                    'operation': 'add',
                    'value': value
                })

        # Process dictionary item changes
        if 'values_changed' in diff:
            for key_path, change in diff['values_changed'].items():
                pipe_path = self.convert_deepdiff_path_to_pipes(key_path, path)
                differences.append({
                    'path': pipe_path,
                    'operation': 'set_value',
                    'value': change['new_value']
                })

        return differences

    def get_value_at_deepdiff_path(self, obj: Any, path: str) -> Any:
        """Get value at a DeepDiff path in the object."""
        # Convert DeepDiff path to actual object navigation
        if path.startswith("root['"):
            # Remove "root['" prefix and "']" suffix, then split by "']['"
            path_parts = path[6:-2].split("']['")
            current = obj
            for part in path_parts:
                if isinstance(current, dict) and part in current:
                    current = current[part]
                else:
                    return None

            return current

        return None

    def convert_deepdiff_path_to_pipes(self, key_path: str, base_path: str = '') -> str:
        """Convert DeepDiff path format to pipe-separated format."""
        # DeepDiff uses "root['key1']['key2'][3]['key3']" format, convert to "key1|key2|3|key3"
        if key_path.startswith("root['"):
            # Simple approach: replace common patterns
            pipe_path = key_path
            # Remove "root['" prefix and "']" suffix
            pipe_path = pipe_path[6:-2]
            # Replace "']['" with "|"
            pipe_path = pipe_path.replace("']['", "|")
            # Handle array indices by replacing "][" with "|"
            pipe_path = pipe_path.replace("][", "|")
            # Remove any remaining brackets and quotes
            pipe_path = pipe_path.replace("[", "").replace("]", "").replace("'", "")
        else:
            # Fallback for other formats
            pipe_path = key_path.replace("['", "|").replace("']", "").replace("root", "")
            if pipe_path.startswith('|'):
                pipe_path = pipe_path[1:]

        # Prepend base path if provided
        if base_path:
            pipe_path = f"{base_path}|{pipe_path}"

        return pipe_path

    def get_existing_spec_fix_paths(self, spec_fixes_file: str) -> Set[str]:
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

    def create_fix_entry(
        self, path: str, value: Any, operation: str = 'set_value'
    ) -> Dict[str, Any]:
        """Create a fix entry for the spec-fixes format."""
        # Map 'add' operation to 'add_if_missing' since that's what the fix script supports
        if operation == 'add':
            operation = 'add_if_missing'

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

        return {
            "operation": operation,
            "path": path,
            "value": value,
            "description": description
        }

    def get_value_at_spec_path(self, spec: Dict[str, Any], path: str) -> Any:
        """Get value at a pipe-separated path in the spec."""
        parts = path.split('|')
        current = spec

        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None

        return current

    def set_value_at_path(self, spec: Dict[str, Any], path: str, value: Any) -> None:
        """Set value at a pipe-separated path in the spec."""
        parts = path.split('|')
        current = spec

        # Navigate to the parent of the target
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}

            current = current[part]

        # Set the final value
        current[parts[-1]] = value

    def path_exists(self, spec: Dict[str, Any], path: str) -> bool:
        """Check if a pipe-separated path exists in the spec."""
        return self.get_value_at_spec_path(spec, path) is not None

    def rename_key_at_path(
        self, spec: Dict[str, Any], parent_path: str, old_key: str, new_key: str
    ) -> bool:
        """Rename a key at the specified parent path."""
        parent = self.get_value_at_spec_path(spec, parent_path)

        if isinstance(parent, dict) and old_key in parent:
            parent[new_key] = parent.pop(old_key)
            return True

        return False

    def modify_array_element(
        self, spec: Dict[str, Any], array_path: str, match_criteria: Dict[str, Any],
        modifications: Dict[str, Any]
    ) -> bool:
        """Modify a specific element in an array by matching criteria."""
        array = self.get_value_at_spec_path(spec, array_path)

        if not isinstance(array, list):
            return False

        # Find the element that matches all criteria
        for element in array:
            if isinstance(element, dict):
                # Check if this element matches all criteria
                matches = all(
                    element.get(key) == value for key, value in match_criteria.items()
                )

                if matches:
                    # Apply modifications to this element
                    for key, value in modifications.items():
                        element[key] = value

                    return True

        return False

    def apply_path_operations(self, spec: Dict[str, Any], fixes: Dict[str, Any]) -> List[str]:
        """Apply path-based operations to the spec."""
        changes_made = []
        operations = fixes.get("path_operations", {}).get("fixes", [])

        for op in operations:
            operation = op["operation"]
            path = op["path"]
            description = op.get("description", "")

            if operation == "rename_key":
                success = self.rename_key_at_path(spec, path, op["old_key"], op["new_key"])

                if success:
                    changes_made.append(f"Renamed key: {description}")
                else:
                    changes_made.append(f"Key not found (skipped): {description}")

            elif operation == "set_value":
                if self.path_exists(spec, path):
                    current_value = self.get_value_at_spec_path(spec, path)

                    if current_value != op["value"]:
                        self.set_value_at_path(spec, path, op["value"])
                        changes_made.append(f"Updated value: {description}")
                    else:
                        changes_made.append(f"Value unchanged (already correct): {description}")
                else:
                    self.set_value_at_path(spec, path, op["value"])
                    changes_made.append(f"Added new value: {description}")

            elif operation == "add_if_missing":
                if not self.path_exists(spec, path):
                    self.set_value_at_path(spec, path, op["value"])
                    changes_made.append(f"Added missing: {description}")
                else:
                    changes_made.append(f"Already exists (skipped): {description}")

            elif operation == "modify_array_element":
                match_criteria = op.get("match_criteria", {})
                modifications = op.get("modifications", {})

                success = self.modify_array_element(spec, path, match_criteria, modifications)

                if success:
                    changes_made.append(f"Modified array element: {description}")
                else:
                    changes_made.append(f"Array element not found (skipped): {description}")

            else:
                changes_made.append(f"Unknown operation {operation!r}: {description}")

        return changes_made


def main() -> None:
    """Main entry point for the API spec tool."""
    parser = argparse.ArgumentParser(
        description="Unified API Specification Tool for Bitwarden Vault Management API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    subparsers = parser.add_subparsers(dest='command', help='Available subcommands')

    # Analyze subcommand
    analyze_parser = subparsers.add_parser('analyze', help='Analyze API structure')
    analyze_parser.add_argument('swagger_file', help='Path to the swagger JSON file')

    # Extract subcommand
    extract_parser = subparsers.add_parser('extract', help='Extract and format API routes')
    extract_parser.add_argument('swagger_file', help='Path to the swagger JSON file')
    extract_parser.add_argument(
        '--format', '-f',
        choices=['markdown', 'text', 'json'],
        default='text',
        help='Output format (default: text)'
    )
    extract_parser.add_argument(
        '--output', '-o',
        help='Output file (default: stdout)'
    )

    # Update subcommand
    update_parser = subparsers.add_parser('update', help='Update spec-fixes.json with new changes')
    update_parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be added without making changes'
    )
    update_parser.add_argument(
        '--output-file',
        default='scripts/spec-fixes.json',
        help='Output file path (default: scripts/spec-fixes.json)'
    )
    update_parser.add_argument(
        '--original-file',
        default='scripts/vault-management-api-original.json',
        help='Original API spec file'
    )
    update_parser.add_argument(
        '--fixed-file',
        default='scripts/vault-management-api-fixed.json',
        help='Fixed API spec file'
    )

    # Fix subcommand
    fix_parser = subparsers.add_parser('fix', help='Apply fixes to the OpenAPI specification')
    fix_parser.add_argument(
        '--original-file',
        default='scripts/vault-management-api-original.json',
        help='Original API spec file'
    )
    fix_parser.add_argument(
        '--fixed-file',
        default='scripts/vault-management-api-fixed.json',
        help='Fixed API spec file'
    )
    fix_parser.add_argument(
        '--fixes-file',
        default='scripts/spec-fixes.json',
        help='Fixes configuration file'
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    tool = APISpecTool()

    try:
        if args.command == 'analyze':
            analysis = tool.analyze_api_structure(args.swagger_file)
            tool.print_analysis(analysis)

        elif args.command == 'extract':
            routes = tool.extract_routes(args.swagger_file)

            if args.format == 'markdown':
                output = tool.format_markdown(routes)
            elif args.format == 'text':
                output = tool.format_text(routes)
            elif args.format == 'json':
                output = tool.format_json(routes)
            else:
                print(f"Error: Unknown format {args.format}", file=sys.stderr)
                sys.exit(1)

            if args.output:
                with os.fdopen(os.open(args.output, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o644),
                               'w', encoding='utf-8') as f:
                    f.write(output)
                print(f"Routes extracted and saved to: {args.output}")
            else:
                print(output)

        elif args.command == 'update':
            # Load the original and fixed files
            original = tool.load_json_file(args.original_file, "original spec file")
            fixed = tool.load_json_file(args.fixed_file, "fixed spec file")

            print(f"Loaded original file: {args.original_file}")
            print(f"Loaded fixed file: {args.fixed_file}")

            # Get existing spec-fix paths
            existing_paths = tool.get_existing_spec_fix_paths(args.output_file)
            print(f"Found {len(existing_paths)} existing paths in spec-fixes")

            # Find all differences using DeepDiff
            print("Analyzing differences...")
            all_differences = tool.find_differences(original, fixed)
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
                # Skip paths with array indices since the fix script doesn't support them
                has_array_index = any(
                    part.isdigit() for part in spec_path.split('|')
                )

                if operation_valid and path_valid and not has_array_index:
                    new_fixes.append(
                        tool.create_fix_entry(spec_path, diff['value'], diff['operation'])
                    )

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
            with os.fdopen(os.open(args.output_file, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o644),
                           'w') as f:
                json.dump(spec_fixes, f, indent=2)

            print(f"\nSuccessfully updated {args.output_file} with {len(new_fixes)} new fixes")

        elif args.command == 'fix':
            # Load files
            original_spec = tool.load_json_file(args.original_file, "original spec file")
            fixes_config = tool.load_json_file(args.fixes_file, "fixes configuration file")

            print("📖 Loading files...")
            print(f"   Original spec: {args.original_file}")
            print(f"   Fixes config: {args.fixes_file}")

            # Apply fixes to a copy of the original spec
            print("🔧 Applying OpenAPI spec fixes...")
            fixed_spec_data = original_spec.copy()
            changes_made = tool.apply_path_operations(fixed_spec_data, fixes_config)

            # Write fixed specification
            print(f"💾 Writing fixed spec: {args.fixed_file}")

            with os.fdopen(os.open(args.fixed_file, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o644),
                           'w') as f:
                json.dump(fixed_spec_data, f, indent=2)

            # Print summary
            if changes_made:
                print(f"\n✅ Applied {len(changes_made)} fixes:")
                for change in changes_made:
                    print(f"   • {change}")
            else:
                print("\n⚠️  No fixes were applied")

            print(f"\n🎉 Fixed specification written to: {args.fixed_file}")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
