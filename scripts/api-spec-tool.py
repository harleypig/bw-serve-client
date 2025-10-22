#!/usr/bin/env python3

r"""Unified API Specification Tool for Bitwarden Vault Management API.

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
import hashlib
import json
import os
from pathlib import Path
import sys
from typing import Any, Dict, List, Set, Tuple

from deepdiff import DeepDiff

# Type aliases for complex types
RouteInfo = Dict[str, Any]
RouteList = List[RouteInfo]
GroupedRoutes = Dict[str, RouteList]
OutputData = Dict[str, Dict[str, List[str]]]


class APISpecTool:
  """Unified tool for working with API specifications.

  This tool provides functionality for analyzing, extracting, updating, and fixing
  OpenAPI specifications. It initializes with the script directory for relative
  path operations.
  """

  # ---------------------------------------------------------------------------
  def __init__(self: "APISpecTool") -> None:
    self.script_dir = Path(__file__).parent

  # ---------------------------------------------------------------------------
  def load_json_file(self: "APISpecTool",
                     file_path: str,
                     description: str = "JSON file") -> Dict[str, Any]:
    """Load and parse a JSON file with error handling.

    Arguments:
        file_path: Path to the JSON file to load.
        description: Description of the file for error messages.

    Returns:
        Dict[str, Any]: The parsed JSON data as a dictionary.

    Raises:
        TypeError: When the JSON file does not contain a dictionary.
    """
    try:
      with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

      if not isinstance(data, dict):
        raise TypeError(f"Expected JSON object (dict), got {type(data).__name__}")

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

  # ---------------------------------------------------------------------------
  def analyze_api_structure(self: "APISpecTool", swagger_file: str) -> Dict[str, Any]:
    """Analyze the API structure and extract key information.

    Arguments:
        swagger_file: Path to the Swagger/OpenAPI specification file.

    Returns:
        Dict[str, Any]: Analysis results containing API information, authentication,
            server info, response patterns, and validation rules.
    """
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

    self._extract_api_info(data, analysis)
    self._extract_authentication_info(data, analysis)
    self._extract_server_info(data, analysis)
    self._analyze_paths(data, analysis, error_codes, tags, response_patterns)
    self._analyze_schemas(data, analysis)
    self._finalize_analysis(analysis, error_codes, tags, response_patterns)

    return analysis

  def _extract_api_info(
    self: "APISpecTool", data: Dict[str, Any], analysis: Dict[str, Any]
  ) -> None:
    """Extract API information from the spec."""
    if 'info' in data:
      analysis['api_info'] = {
        'title': data['info'].get('title', ''),
        'description': data['info'].get('description', ''),
        'version': data['info'].get('version', ''),
        'openapi_version': data.get('openapi', '')
      }

  def _extract_authentication_info(
    self: "APISpecTool", data: Dict[str, Any], analysis: Dict[str, Any]
  ) -> None:
    """Extract authentication information from the spec."""
    if 'security' in data:
      analysis['authentication'] = data['security']

    if 'components' in data and 'securitySchemes' in data['components']:
      analysis['authentication']['schemes'] = data['components']['securitySchemes']

  def _extract_server_info(
    self: "APISpecTool", data: Dict[str, Any], analysis: Dict[str, Any]
  ) -> None:
    """Extract server information from the spec."""
    if 'servers' in data:
      analysis['server_info'] = data['servers']
    elif 'host' in data:
      analysis['server_info'] = {
        'host': data.get('host', ''),
        'basePath': data.get('basePath', ''),
        'schemes': data.get('schemes', [])
      }

  def _analyze_paths(
    self: "APISpecTool", data: Dict[str, Any], analysis: Dict[str, Any],
    error_codes: Set[str], tags: Set[str], response_patterns: Dict[str, Set[str]]
  ) -> None:
    """Analyze API paths and extract patterns."""
    if 'paths' not in data:
      return

    for path, methods in data['paths'].items():
      for method, details in methods.items():
        if method.upper() in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS']:
          self._process_endpoint(
            path, method, details, analysis, error_codes, tags, response_patterns
          )

  def _process_endpoint(
    self: "APISpecTool", path: str, method: str, details: Dict[str, Any],
    analysis: Dict[str, Any], error_codes: Set[str], tags: Set[str],
    response_patterns: Dict[str, Set[str]]
  ) -> None:
    """Process a single endpoint and extract its information."""
    # Extract tags
    if 'tags' in details:
      tags.update(details['tags'])

    # Extract parameters
    self._extract_parameters(details, analysis)

    # Extract request body patterns
    self._extract_request_body_patterns(path, method, details, analysis)

    # Extract response patterns
    self._extract_response_patterns(
      path, method, details, analysis, error_codes, response_patterns
    )

  def _extract_parameters(
    self: "APISpecTool", details: Dict[str, Any], analysis: Dict[str, Any]
  ) -> None:
    """Extract parameter information from endpoint details."""
    if 'parameters' not in details:
      return

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

  def _extract_request_body_patterns(
    self: "APISpecTool", path: str, method: str, details: Dict[str, Any],
    analysis: Dict[str, Any]
  ) -> None:
    """Extract request body patterns from endpoint details."""
    if 'requestBody' not in details:
      return

    req_body = details['requestBody']
    content_types = list(req_body.get('content', {}).keys())
    analysis['request_body_patterns'][f"{method.upper()} {path}"] = {
      'content_types': content_types,
      'required': req_body.get('required', False),
      'description': req_body.get('description', '')
    }

  def _extract_response_patterns(
    self: "APISpecTool", path: str, method: str, details: Dict[str, Any],
    analysis: Dict[str, Any], error_codes: Set[str], response_patterns: Dict[str, Set[str]]
  ) -> None:
    """Extract response patterns from endpoint details."""
    if 'responses' not in details:
      return

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

  def _analyze_schemas(
    self: "APISpecTool", data: Dict[str, Any], analysis: Dict[str, Any]
  ) -> None:
    """Analyze data schemas from the spec."""
    if 'components' in data and 'schemas' in data['components']:
      for schema_name, schema_def in data['components']['schemas'].items():
        analysis['data_models'][schema_name] = {
          'type': schema_def.get('type', 'object'),
          'properties': schema_def.get('properties', {}),
          'required': schema_def.get('required', []),
          'description': schema_def.get('description', '')
        }

  def _finalize_analysis(
    self: "APISpecTool", analysis: Dict[str, Any], error_codes: Set[str], tags: Set[str],
    response_patterns: Dict[str, Set[str]]
  ) -> None:
    """Finalize analysis by converting sets to lists for JSON serialization.

    Arguments:
        analysis: The analysis dictionary to finalize.
        error_codes: Set of error codes found in the API.
        tags: Set of tags found in the API.
        response_patterns: Dictionary mapping status codes to sets of response patterns.
    """
    analysis['error_codes'] = sorted(error_codes)
    analysis['tags'] = sorted(tags)
    for status_code in response_patterns:
      analysis['response_patterns'][status_code] = sorted(response_patterns[status_code])

  # ---------------------------------------------------------------------------
  def print_analysis(self: "APISpecTool", analysis: Dict[str, Any]) -> None:
    """Print the analysis results in a readable format.

    Arguments:
        analysis: The analysis dictionary to print.
    """
    self._print_header()
    self._print_api_info(analysis)
    self._print_authentication(analysis)
    self._print_server_config(analysis)
    self._print_response_patterns(analysis)
    self._print_error_codes(analysis)
    self._print_tags(analysis)
    self._print_parameter_patterns(analysis)
    self._print_request_body_patterns(analysis)
    self._print_data_models(analysis)
    self._print_examples(analysis)
    self._print_footer()

  def _print_header(self: "APISpecTool") -> None:
    """Print the analysis header."""
    print("=" * 80)
    print("BITWARDEN VAULT MANAGEMENT API - LIBRARY DEVELOPMENT ANALYSIS")
    print("=" * 80)

  def _print_api_info(self: "APISpecTool", analysis: Dict[str, Any]) -> None:
    """Print API information section."""
    print("\n📋 API INFORMATION:")
    print("-" * 40)
    for key, value in analysis['api_info'].items():
      print(f"  {key}: {value}")

  def _print_authentication(self: "APISpecTool", analysis: Dict[str, Any]) -> None:
    """Print authentication section."""
    print("\n🔐 AUTHENTICATION:")
    print("-" * 40)
    if analysis['authentication']:
      for key, value in analysis['authentication'].items():
        print(f"  {key}: {value}")
    else:
      print("  No explicit authentication schemes defined")
      print("  Note: This API likely uses session-based authentication via 'bw serve'")

  def _print_server_config(self: "APISpecTool", analysis: Dict[str, Any]) -> None:
    """Print server configuration section."""
    print("\n🌐 SERVER CONFIGURATION:")
    print("-" * 40)
    if analysis['server_info']:
      for key, value in analysis['server_info'].items():
        print(f"  {key}: {value}")
    else:
      print("  No explicit server configuration")
      print("  Note: This API runs locally via 'bw serve' command")

  def _print_response_patterns(self: "APISpecTool", analysis: Dict[str, Any]) -> None:
    """Print response patterns section."""
    print("\n📤 RESPONSE PATTERNS:")
    print("-" * 40)
    for status_code, content_types in analysis['response_patterns'].items():
      print(f"  {status_code}: {', '.join(content_types)}")

  def _print_error_codes(self: "APISpecTool", analysis: Dict[str, Any]) -> None:
    """Print error codes section."""
    print("\n❌ ERROR CODES:")
    print("-" * 40)
    for code in analysis['error_codes']:
      print(f"  {code}")

  def _print_tags(self: "APISpecTool", analysis: Dict[str, Any]) -> None:
    """Print API categories (tags) section."""
    print("\n🏷️  API CATEGORIES (TAGS):")
    print("-" * 40)
    for tag in analysis['tags']:
      print(f"  - {tag}")

  def _print_parameter_patterns(self: "APISpecTool", analysis: Dict[str, Any]) -> None:
    """Print parameter patterns section."""
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

  def _print_request_body_patterns(self: "APISpecTool", analysis: Dict[str, Any]) -> None:
    """Print request body patterns section."""
    print("\n📦 REQUEST BODY PATTERNS:")
    print("-" * 40)
    for endpoint, body_info in list(analysis['request_body_patterns'].items())[:5]:
      print(f"  {endpoint}:")
      print(f"    Content-Types: {', '.join(body_info['content_types'])}")
      print(f"    Required: {body_info['required']}")

  def _print_data_models(self: "APISpecTool", analysis: Dict[str, Any]) -> None:
    """Print data models section."""
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

  def _print_examples(self: "APISpecTool", analysis: Dict[str, Any]) -> None:
    """Print key examples section.

    Arguments:
        analysis: The analysis dictionary containing examples to print.
    """
    print("\n💡 KEY EXAMPLES:")
    print("-" * 40)
    for example_key, example_info in list(analysis['examples'].items())[:3]:
      print(f"  {example_key}:")
      print(f"    Content-Type: {example_info['content_type']}")
      print(f"    Example: {str(example_info['example'])[:100]}...")

  def _print_footer(self: "APISpecTool") -> None:
    """Print the analysis footer."""
    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)

  # ---------------------------------------------------------------------------
  def extract_routes(self: "APISpecTool", swagger_file: str) -> List[Dict[str, Any]]:
    """Extract all routes from the swagger data.

    Arguments:
        swagger_file: Path to the Swagger/OpenAPI specification file.

    Returns:
        List[Dict[str, Any]]: List of route dictionaries containing path, method,
            and operation details.
    """
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

  # ---------------------------------------------------------------------------
  def format_markdown(self: "APISpecTool", routes: RouteList) -> str:
    """Format routes as markdown.

    Arguments:
        routes: List of route dictionaries to format.

    Returns:
        str: Formatted markdown string containing all routes grouped by tags.
    """
    output = []

    # Group routes by tags
    grouped_routes: GroupedRoutes = {}

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

  # ---------------------------------------------------------------------------
  def format_text(self: "APISpecTool", routes: RouteList) -> str:
    """Format routes as plain text.

    Arguments:
        routes: List of route dictionaries to format.

    Returns:
        str: Formatted plain text string containing all routes grouped by tags.
    """
    output = []

    # Group routes by tags
    grouped_routes: GroupedRoutes = {}
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

  # ---------------------------------------------------------------------------
  def format_json(self: "APISpecTool", routes: RouteList) -> str:
    """Format routes as JSON.

    Arguments:
        routes: List of route dictionaries to format.

    Returns:
        str: JSON string containing all routes grouped by tags.
    """
    # Group routes by tags
    grouped_routes: GroupedRoutes = {}

    for route in routes:
      tags = route['tags'] if route['tags'] else ['Misc']

      for tag in tags:
        if tag not in grouped_routes:
          grouped_routes[tag] = []

        grouped_routes[tag].append(route)

    # Create simplified output structure
    output_data: OutputData = {}

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

  # ---------------------------------------------------------------------------
  def create_content_hash(self: "APISpecTool", obj: Any) -> str:
    """Create a content-based hash for an object.
    
    Arguments:
        obj: The object to hash.
        
    Returns:
        str: A hash string representing the object's content.
    """
    # Convert to JSON string with sorted keys for consistent hashing
    json_str = json.dumps(obj, sort_keys=True, separators=(',', ':'))
    return hashlib.md5(json_str.encode('utf-8')).hexdigest()

  # ---------------------------------------------------------------------------
  def find_array_element_mappings(self: "APISpecTool", 
                                  old_array: List[Any], 
                                  new_array: List[Any]) -> Dict[int, int]:
    """Find mappings between old and new array elements based on content hash.
    
    Arguments:
        old_array: The original array.
        new_array: The modified array.
        
    Returns:
        Dict[int, int]: Mapping from old index to new index, or -1 if element was removed.
    """
    # Create hash maps for both arrays
    old_hashes = {i: self.create_content_hash(item) for i, item in enumerate(old_array)}
    new_hashes = {i: self.create_content_hash(item) for i, item in enumerate(new_array)}
    
    # Create reverse mapping from hash to index
    old_hash_to_index = {hash_val: idx for idx, hash_val in old_hashes.items()}
    new_hash_to_index = {hash_val: idx for idx, hash_val in new_hashes.items()}
    
    # Map old indices to new indices
    mapping = {}
    for old_idx, old_hash in old_hashes.items():
      if old_hash in new_hash_to_index:
        mapping[old_idx] = new_hash_to_index[old_hash]
      else:
        mapping[old_idx] = -1  # Element was removed
    
    return mapping

  # ---------------------------------------------------------------------------
  def find_differences(self: "APISpecTool",
                       obj1: Any,
                       obj2: Any,
                       path: str = '') -> List[Dict[str, Any]]:
    """Find all differences between two JSON objects using DeepDiff.

    Arguments:
        obj1: First object to compare.
        obj2: Second object to compare.
        path: Base path for the comparison.

    Returns:
        List[Dict[str, Any]]: List of difference dictionaries containing change
            details and descriptions.
    """
    differences = []

    # Use DeepDiff to find all differences
    diff = DeepDiff(obj1, obj2, ignore_order=True, exclude_paths=["root['info']"])

    # Process different types of changes
    differences.extend(self._process_dictionary_additions(diff, obj2, path))
    differences.extend(self._process_dictionary_removals(diff, path))
    differences.extend(self._process_value_changes(diff, path))
    differences.extend(self._process_type_changes(diff, path))
    differences.extend(self._process_iterable_additions(diff, path))
    differences.extend(self._process_iterable_removals(diff, path))

    return differences

  # ---------------------------------------------------------------------------
  def find_differences_with_array_tracking(self: "APISpecTool",
                                          obj1: Any,
                                          obj2: Any,
                                          path: str = '') -> List[Dict[str, Any]]:
    """Find differences with intelligent array element tracking.

    This method extends the basic difference finding to handle array position
    changes by using content-based hashing to track elements across changes.

    Arguments:
        obj1: First object to compare.
        obj2: Second object to compare.
        path: Base path for the comparison.

    Returns:
        List[Dict[str, Any]]: List of difference dictionaries with array tracking.
    """
    differences = []
    
    # First, get basic differences
    basic_differences = self.find_differences(obj1, obj2, path)
    
    # Also find array-specific differences by comparing arrays directly
    array_differences = self._find_array_differences(obj1, obj2, path)
    
    # Combine all differences
    all_differences = basic_differences + array_differences
    
    # Process each difference to handle array position changes
    for diff in all_differences:
      if self._is_array_path(diff['path']):
        # Handle array-specific differences
        array_diffs = self._process_array_differences(obj1, obj2, diff, path)
        differences.extend(array_diffs)
      else:
        differences.append(diff)
    
    return differences

  def _find_array_differences(self: "APISpecTool", obj1: Any, obj2: Any, path: str) -> List[Dict[str, Any]]:
    """Find differences specifically in arrays by comparing them element by element.
    
    Arguments:
        obj1: First object to compare.
        obj2: Second object to compare.
        path: Base path for the comparison.
        
    Returns:
        List[Dict[str, Any]]: List of array-specific differences.
    """
    differences = []
    
    if isinstance(obj1, dict) and isinstance(obj2, dict):
      for key in set(obj1.keys()) | set(obj2.keys()):
        if key in obj1 and key in obj2:
          if isinstance(obj1[key], list) and isinstance(obj2[key], list):
            # Both are arrays - compare them
            array_diffs = self._compare_arrays(obj1[key], obj2[key], f"{path}|{key}" if path else key)
            differences.extend(array_diffs)
          else:
            # Recurse into nested objects
            nested_diffs = self._find_array_differences(obj1[key], obj2[key], f"{path}|{key}" if path else key)
            differences.extend(nested_diffs)
    
    return differences

  def _compare_arrays(self: "APISpecTool", old_array: List[Any], new_array: List[Any], array_path: str) -> List[Dict[str, Any]]:
    """Compare two arrays and find differences with position tracking.
    
    Arguments:
        old_array: Original array.
        new_array: Modified array.
        array_path: Path to the array.
        
    Returns:
        List[Dict[str, Any]]: List of array differences.
    """
    differences = []
    
    # Find element mappings
    mappings = self.find_array_element_mappings(old_array, new_array)
    
    # Check for added items
    old_hashes = {self.create_content_hash(item) for item in old_array}
    new_hashes = {self.create_content_hash(item) for item in new_array}
    
    added_hashes = new_hashes - old_hashes
    removed_hashes = old_hashes - new_hashes
    
    # Process added items - but check for field modifications first
    for new_idx, item in enumerate(new_array):
      item_hash = self.create_content_hash(item)
      if item_hash in added_hashes:
        # Check if this might be a field modification of an existing item
        is_field_mod = False
        for old_idx, old_item in enumerate(old_array):
          if self._is_field_modification(old_item, item):
            # This is a field modification, not an addition
            field_diffs = self._find_field_differences(old_item, item, f"{array_path}|{new_idx}")
            differences.extend(field_diffs)
            is_field_mod = True
            break
        
        if not is_field_mod:
          differences.append({
            'path': f"{array_path}|{new_idx}",
            'type': 'add_array_item',
            'value': item,
            'description': f"Add new array item at position {new_idx}: {str(item)[:50]}...",
            'content_hash': item_hash,
            'array_tracking': True
          })
    
    # Process removed items - but check for field modifications first
    for old_idx, item in enumerate(old_array):
      item_hash = self.create_content_hash(item)
      if item_hash in removed_hashes:
        # Check if this might be a field modification of an existing item
        is_field_mod = False
        for new_idx, new_item in enumerate(new_array):
          if self._is_field_modification(item, new_item):
            # This is a field modification, not a removal
            # We already handled this in the added items section
            is_field_mod = True
            break
        
        if not is_field_mod:
          differences.append({
            'path': f"{array_path}|{old_idx}",
            'type': 'remove_array_item',
            'value': item,
            'description': f"Remove array item from position {old_idx}: {str(item)[:50]}...",
            'content_hash': item_hash,
            'array_tracking': True
          })
    
    # Process moved/changed items
    for old_idx, new_idx in mappings.items():
      if new_idx != -1:  # Item wasn't removed
        old_item = old_array[old_idx]
        new_item = new_array[new_idx]
        
        if self.create_content_hash(old_item) != self.create_content_hash(new_item):
          # Item content changed - check if it's a field modification or complete replacement
          if self._is_field_modification(old_item, new_item):
            # Generate field-level differences instead of replacing the entire item
            field_diffs = self._find_field_differences(old_item, new_item, f"{array_path}|{new_idx}")
            differences.extend(field_diffs)
          else:
            # Complete item replacement
            differences.append({
              'path': f"{array_path}|{new_idx}",
              'type': 'set_value',
              'value': new_item,
              'old_value': old_item,
              'description': f"Update array item at position {new_idx}: {str(new_item)[:50]}...",
              'content_hash': self.create_content_hash(new_item),
              'old_content_hash': self.create_content_hash(old_item),
              'array_tracking': True
            })
        elif old_idx != new_idx:
          # Item moved but content unchanged - we might want to track this
          differences.append({
            'path': f"{array_path}|{new_idx}",
            'type': 'move_array_item',
            'value': new_item,
            'old_position': old_idx,
            'new_position': new_idx,
            'description': f"Array item moved from position {old_idx} to {new_idx}: {str(new_item)[:50]}...",
            'content_hash': self.create_content_hash(new_item),
            'array_tracking': True
          })
    
    return differences

  def _is_field_modification(self: "APISpecTool", old_item: Any, new_item: Any) -> bool:
    """Check if the change is a field modification within the same object structure.
    
    Arguments:
        old_item: Original item.
        new_item: Modified item.
        
    Returns:
        bool: True if this is a field modification, False if it's a complete replacement.
    """
    # Both items must be dictionaries for field modification
    if not isinstance(old_item, dict) or not isinstance(new_item, dict):
      return False
    
    # Check if they have the same keys (allowing for additions/removals)
    old_keys = set(old_item.keys())
    new_keys = set(new_item.keys())
    
    # If more than 50% of keys changed, treat as complete replacement
    common_keys = old_keys & new_keys
    if len(common_keys) < max(len(old_keys), len(new_keys)) * 0.5:
      return False
    
    # Check if most values are the same (allowing for a few field changes)
    same_values = 0
    total_values = 0
    
    for key in common_keys:
      if old_item[key] == new_item[key]:
        same_values += 1
      total_values += 1
    
    # If more than 70% of values are the same, treat as field modification
    return total_values > 0 and (same_values / total_values) > 0.7

  def _find_field_differences(self: "APISpecTool", old_item: Any, new_item: Any, base_path: str) -> List[Dict[str, Any]]:
    """Find field-level differences within an object.
    
    Arguments:
        old_item: Original item.
        new_item: Modified item.
        base_path: Base path for the object.
        
    Returns:
        List[Dict[str, Any]]: List of field-level differences.
    """
    differences = []
    
    if not isinstance(old_item, dict) or not isinstance(new_item, dict):
      return differences
    
    # Check for changed fields
    all_keys = set(old_item.keys()) | set(new_item.keys())
    
    for key in all_keys:
      old_value = old_item.get(key)
      new_value = new_item.get(key)
      
      if old_value != new_value:
        field_path = f"{base_path}|{key}"
        
        if key in old_item and key in new_item:
          # Field changed - check if it's a nested object
          if isinstance(old_value, dict) and isinstance(new_value, dict):
            # Recursively find differences in nested objects
            nested_diffs = self._find_field_differences(old_value, new_value, field_path)
            differences.extend(nested_diffs)
          else:
            # Simple field change
            differences.append({
              'path': field_path,
              'type': 'set_value',
              'value': new_value,
              'old_value': old_value,
              'description': f"Update field '{key}': {str(new_value)[:50]}...",
              'array_tracking': True
            })
        elif key in new_item:
          # Field added
          differences.append({
            'path': field_path,
            'type': 'set_value',
            'value': new_value,
            'description': f"Add field '{key}': {str(new_value)[:50]}...",
            'array_tracking': True
          })
        elif key in old_item:
          # Field removed
          differences.append({
            'path': field_path,
            'type': 'delete_value',
            'old_value': old_value,
            'description': f"Remove field '{key}'",
            'array_tracking': True
          })
    
    return differences

  def _is_array_path(self: "APISpecTool", path: str) -> bool:
    """Check if a path contains array indices.
    
    Arguments:
        path: Pipe-separated path string.
        
    Returns:
        bool: True if the path contains array indices.
    """
    parts = path.split('|')
    return any(part.isdigit() for part in parts)

  def _process_array_differences(self: "APISpecTool", 
                                obj1: Any, 
                                obj2: Any, 
                                diff: Dict[str, Any], 
                                base_path: str) -> List[Dict[str, Any]]:
    """Process differences that involve arrays with position tracking.
    
    Arguments:
        obj1: Original object.
        obj2: Modified object.
        diff: The difference dictionary to process.
        base_path: Base path for the comparison.
        
    Returns:
        List[Dict[str, Any]]: List of processed difference dictionaries.
    """
    differences = []
    path = diff['path']
    
    # Extract array path and index
    array_path, array_index = self._extract_array_path_and_index(path)
    if array_path is None:
      # Not an array path, return original diff
      return [diff]
    
    # Get the arrays
    old_array = self.get_value_at_spec_path(obj1, array_path)
    new_array = self.get_value_at_spec_path(obj2, array_path)
    
    if not isinstance(old_array, list) or not isinstance(new_array, list):
      return [diff]
    
    # Find element mappings
    mappings = self.find_array_element_mappings(old_array, new_array)
    
    # Process based on operation type
    if diff['type'] == 'add_array_item':
      differences.extend(self._process_array_item_addition(diff, mappings, old_array, new_array))
    elif diff['type'] == 'remove_array_item':
      differences.extend(self._process_array_item_removal(diff, mappings, old_array, new_array))
    elif diff['type'] == 'set_value':
      differences.extend(self._process_array_value_change(diff, mappings, old_array, new_array))
    else:
      differences.append(diff)
    
    return differences

  def _extract_array_path_and_index(self: "APISpecTool", path: str) -> Tuple[str, int]:
    """Extract array path and index from a full path.
    
    Arguments:
        path: Pipe-separated path string.
        
    Returns:
        Tuple[str, int]: Array path and index, or (None, -1) if not an array path.
    """
    parts = path.split('|')
    
    # Find the last numeric part (array index)
    for i in range(len(parts) - 1, -1, -1):
      if parts[i].isdigit():
        array_path = '|'.join(parts[:i])
        array_index = int(parts[i])
        return array_path, array_index
    
    return None, -1

  def _process_array_item_addition(self: "APISpecTool", 
                                  diff: Dict[str, Any], 
                                  mappings: Dict[int, int], 
                                  old_array: List[Any], 
                                  new_array: List[Any]) -> List[Dict[str, Any]]:
    """Process array item addition with position tracking.
    
    Arguments:
        diff: The original difference dictionary.
        mappings: Element mappings from old to new indices.
        old_array: Original array.
        new_array: Modified array.
        
    Returns:
        List[Dict[str, Any]]: List of processed differences.
    """
    differences = []
    
    # Find items that were added (not in old array)
    old_hashes = {self.create_content_hash(item) for item in old_array}
    new_hashes = {self.create_content_hash(item) for item in new_array}
    
    added_hashes = new_hashes - old_hashes
    
    for new_idx, item in enumerate(new_array):
      item_hash = self.create_content_hash(item)
      if item_hash in added_hashes:
        # This is a new item
        array_path = diff['path'].rsplit('|', 1)[0]  # Remove the index part
        new_path = f"{array_path}|{new_idx}"
        
        differences.append({
          'path': new_path,
          'type': 'add_array_item',
          'value': item,
          'description': f"Add new array item at position {new_idx}: {str(item)[:50]}...",
          'content_hash': self.create_content_hash(item),
          'array_tracking': True
        })
    
    return differences

  def _process_array_item_removal(self: "APISpecTool", 
                                 diff: Dict[str, Any], 
                                 mappings: Dict[int, int], 
                                 old_array: List[Any], 
                                 new_array: List[Any]) -> List[Dict[str, Any]]:
    """Process array item removal with position tracking.
    
    Arguments:
        diff: The original difference dictionary.
        mappings: Element mappings from old to new indices.
        old_array: Original array.
        new_array: Modified array.
        
    Returns:
        List[Dict[str, Any]]: List of processed differences.
    """
    differences = []
    
    # Find items that were removed (not in new array)
    old_hashes = {self.create_content_hash(item) for item in old_array}
    new_hashes = {self.create_content_hash(item) for item in new_array}
    
    removed_hashes = old_hashes - new_hashes
    
    for old_idx, item in enumerate(old_array):
      item_hash = self.create_content_hash(item)
      if item_hash in removed_hashes:
        # This item was removed
        array_path = diff['path'].rsplit('|', 1)[0]  # Remove the index part
        
        differences.append({
          'path': f"{array_path}|{old_idx}",
          'type': 'remove_array_item',
          'value': item,
          'description': f"Remove array item from position {old_idx}: {str(item)[:50]}...",
          'content_hash': self.create_content_hash(item),
          'array_tracking': True
        })
    
    return differences

  def _process_array_value_change(self: "APISpecTool", 
                                 diff: Dict[str, Any], 
                                 mappings: Dict[int, int], 
                                 old_array: List[Any], 
                                 new_array: List[Any]) -> List[Dict[str, Any]]:
    """Process array value changes with position tracking.
    
    Arguments:
        diff: The original difference dictionary.
        mappings: Element mappings from old to new indices.
        old_array: Original array.
        new_array: Modified array.
        
    Returns:
        List[Dict[str, Any]]: List of processed differences.
    """
    differences = []
    
    # Find items that changed (same position but different content)
    for old_idx, new_idx in mappings.items():
      if new_idx != -1:  # Item wasn't removed
        old_item = old_array[old_idx]
        new_item = new_array[new_idx]
        
        if self.create_content_hash(old_item) != self.create_content_hash(new_item):
          # Item content changed
          array_path = diff['path'].rsplit('|', 1)[0]  # Remove the index part
          new_path = f"{array_path}|{new_idx}"
          
          differences.append({
            'path': new_path,
            'type': 'set_value',
            'value': new_item,
            'old_value': old_item,
            'description': f"Update array item at position {new_idx}: {str(new_item)[:50]}...",
            'content_hash': self.create_content_hash(new_item),
            'old_content_hash': self.create_content_hash(old_item),
            'array_tracking': True
          })
    
    return differences

  def _process_dictionary_additions(self: "APISpecTool", diff: Any, obj2: Any,
                                    path: str) -> List[Dict[str, Any]]:
    """Process dictionary item additions."""
    differences = []
    if 'dictionary_item_added' in diff:
      for key_path in diff['dictionary_item_added']:
        value = self.get_value_at_deepdiff_path(obj2, key_path)
        pipe_path = self.convert_deepdiff_path_to_pipes(key_path, path)
        differences.append({
          'path': pipe_path,
          'type': 'add_if_missing',
          'value': value,
          'description': f"Add missing value at {pipe_path}"
        })

    return differences

  def _process_dictionary_removals(self: "APISpecTool", diff: Any,
                                   path: str) -> List[Dict[str, Any]]:
    """Process dictionary item removals."""
    differences = []
    if 'dictionary_item_removed' in diff:
      for key_path in diff['dictionary_item_removed']:
        pipe_path = self.convert_deepdiff_path_to_pipes(key_path, path)
        differences.append({
          'path': pipe_path,
          'type': 'delete_value',
          'description': f"Remove value at {pipe_path}"
        })

    return differences

  def _process_value_changes(self: "APISpecTool", diff: Any,
                             path: str) -> List[Dict[str, Any]]:
    """Process value changes."""
    differences = []
    if 'values_changed' in diff:
      for key_path, change in diff['values_changed'].items():
        pipe_path = self.convert_deepdiff_path_to_pipes(key_path, path)

        differences.append({
          'path': pipe_path,
          'type': 'set_value',
          'value': change['new_value'],
          'old_value': change['old_value'],
          'description': f"Update value at {pipe_path}"
        })

    return differences

  def _process_type_changes(self: "APISpecTool", diff: Any,
                            path: str) -> List[Dict[str, Any]]:
    """Process type changes."""
    differences = []
    if 'type_changes' in diff:
      for key_path, change in diff['type_changes'].items():
        pipe_path = self.convert_deepdiff_path_to_pipes(key_path, path)
        differences.append({
          "path": pipe_path,
          "type": "set_value",
          "value": change["new_value"],
          "old_value": change["old_value"],
          "description":
            f"Change type at {pipe_path} from "
            f"{type(change['old_value']).__name__} to "
            f"{type(change['new_value']).__name__}"
        })

    return differences

  def _process_iterable_additions(self: "APISpecTool", diff: Any,
                                  path: str) -> List[Dict[str, Any]]:
    """Process iterable item additions.

    Arguments:
        diff: DeepDiff object containing the differences.
        path: Base path for the differences.

    Returns:
        List[Dict[str, Any]]: List of difference dictionaries for added items.
    """
    differences = []
    if 'iterable_item_added' in diff:
      for key_path, items in diff['iterable_item_added'].items():
        pipe_path = self.convert_deepdiff_path_to_pipes(key_path, path)
        for item in items:
          # Check if this is actually an array item addition or object property addition
          # If the item is a simple string and the path ends with a pipe, it's likely
          # a property name being added to an object within an array, not an array item
          if isinstance(item, str) and pipe_path.endswith('|'):
            # Skip these as they're likely object property additions, not array items
            continue

          # Generate a more descriptive description
          item_desc = str(item)[:50] + "..." if len(str(item)) > 50 else str(item)
          description = f"Add array item to {pipe_path}: {item_desc}"

          differences.append({
            'path': pipe_path,
            'type': 'add_array_item',
            'value': item,
            'description': description
          })

    return differences

  def _process_iterable_removals(self: "APISpecTool", diff: Any,
                                 path: str) -> List[Dict[str, Any]]:
    """Process iterable item removals.

    Arguments:
        diff: DeepDiff object containing the differences.
        path: Base path for the differences.

    Returns:
        List[Dict[str, Any]]: List of difference dictionaries for removed items.
    """
    differences = []
    if 'iterable_item_removed' in diff:
      for key_path, items in diff['iterable_item_removed'].items():
        pipe_path = self.convert_deepdiff_path_to_pipes(key_path, path)
        for item in items:
          # Check if this is actually an array item removal or object property removal
          # If the item is a simple string and the path ends with a pipe, it's likely
          # a property name being removed from an object within an array, not an array item
          if isinstance(item, str) and pipe_path.endswith('|'):
            # Skip these as they're likely object property removals, not array items
            continue

          # Generate a more descriptive description
          item_desc = str(item)[:50] + "..." if len(str(item)) > 50 else str(item)
          description = f"Remove array item from {pipe_path}: {item_desc}"

          differences.append({
            'path': pipe_path,
            'type': 'remove_array_item',
            'value': item,
            'description': description
          })

    return differences

  # ---------------------------------------------------------------------------
  def get_value_at_deepdiff_path(self: "APISpecTool", obj: Any, path: str) -> Any:
    """Get value at a DeepDiff path in the object.

    Arguments:
        obj: The object to navigate.
        path: DeepDiff path string to follow.

    Returns:
        Any: The value at the specified path, or None if the path doesn't exist.
    """
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

  # ---------------------------------------------------------------------------
  def convert_deepdiff_path_to_pipes(
    self: "APISpecTool", key_path: str, base_path: str = ''
  ) -> str:
    """Convert DeepDiff path format to pipe-separated format.

    Arguments:
        key_path: DeepDiff path string to convert.
        base_path: Optional base path to prepend to the result.

    Returns:
        str: Pipe-separated path string (e.g., "key1|key2|3|key3").
    """
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
      return f"{base_path}|{pipe_path}"

    return pipe_path

  # ---------------------------------------------------------------------------
  def get_existing_spec_fix_paths(self: "APISpecTool", spec_fixes_file: str) -> Set[str]:
    """Get all paths already covered in spec-fixes.json.

    Arguments:
        spec_fixes_file: Path to the spec-fixes.json file.

    Returns:
        Set[str]: Set of existing paths from the spec-fixes file.
    """
    try:
      with open(spec_fixes_file, 'r') as f:
        spec_fixes = json.load(f)

      existing_paths = set()

      # Handle v2 format
      if "operations" in spec_fixes:
        for fix in spec_fixes["operations"]:
          if 'path' in fix:
            existing_paths.add(fix['path'])

      return existing_paths
    except FileNotFoundError:
      print(f"Warning: {spec_fixes_file} not found. Will create new file.")
      return set()
    except json.JSONDecodeError as e:
      print(f"Error parsing {spec_fixes_file}: {e}")
      return set()

  # ---------------------------------------------------------------------------
  def create_fix_entry(
    self: "APISpecTool",
    path: str,
    value: Any,
    operation_type: str = 'set_value',
    old_value: Any = None,
    description: str | None = None
  ) -> Dict[str, Any]:
    """Create a fix entry for the spec-fixes format.

    Arguments:
        path: The path where the fix should be applied.
        value: The value to set (for set_value operations).
        operation_type: Type of operation ('set_value', 'add_if_missing', etc.).
        old_value: Previous value (for comparison operations).
        description: Optional description of the fix.

    Returns:
        Dict[str, Any]: Fix entry dictionary with type, path, description,
            and optional value/old_value fields.
    """
    # Generate description if not provided
    if description is None:
      if operation_type == 'add_if_missing':
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
          description = f"Add missing value at {path}"
      elif operation_type == 'delete_value':
        description = f"Remove value at {path}"
      elif operation_type == 'set_value':
        description = f"Update value at {path}"
      else:
        description = f"{operation_type} at {path}"

    # Create the base entry
    entry = {"type": operation_type, "path": path, "description": description}

    # Add value if it exists
    if value is not None:
      entry["value"] = value

    # Add old_value if it exists (for set_value operations)
    if old_value is not None:
      entry["old_value"] = old_value

    return entry

  # ---------------------------------------------------------------------------
  def create_array_aware_fix_entry(
    self: "APISpecTool",
    path: str,
    value: Any,
    operation_type: str = 'set_value',
    old_value: Any = None,
    description: str | None = None,
    content_hash: str | None = None
  ) -> Dict[str, Any]:
    """Create a fix entry with array position tracking support.

    Arguments:
        path: The path where the fix should be applied.
        value: The value to set (for set_value operations).
        operation_type: Type of operation ('set_value', 'add_if_missing', etc.).
        old_value: Previous value (for comparison operations).
        description: Optional description of the fix.
        content_hash: Content hash for array element tracking.

    Returns:
        Dict[str, Any]: Fix entry dictionary with array tracking support.
    """
    # Create the base entry
    entry = self.create_fix_entry(path, value, operation_type, old_value, description)
    
    # Add content hash for array elements
    if content_hash:
      entry["content_hash"] = content_hash
    
    # Add array tracking metadata
    if self._is_array_path(path):
      entry["array_tracking"] = True
      array_path, array_index = self._extract_array_path_and_index(path)
      if array_path:
        entry["array_path"] = array_path
        entry["array_index"] = array_index
    
    return entry

  # ---------------------------------------------------------------------------
  def get_value_at_spec_path(self: "APISpecTool", spec: Dict[str, Any], path: str) -> Any:
    """Get value at a pipe-separated path in the spec.

    Arguments:
        spec: The specification dictionary to navigate.
        path: Pipe-separated path string to follow.

    Returns:
        Any: The value at the specified path, or None if the path doesn't exist.
    """
    parts = path.split('|')
    current = spec

    for part in parts:
      if part.isdigit() and isinstance(current, list):
        # Array index
        index = int(part)
        if 0 <= index < len(current):
          current = current[index]
        else:
          return None
      else:
        # Dictionary key
        if isinstance(current, dict) and part in current:
          current = current[part]
        else:
          return None

    return current

  # ---------------------------------------------------------------------------
  def set_value_at_path(
    self: "APISpecTool", spec: Dict[str, Any], path: str, value: Any
  ) -> None:
    """Set value at a pipe-separated path in the spec.

    Arguments:
        spec: The specification dictionary to modify.
        path: Pipe-separated path string where to set the value.
        value: The value to set at the specified path.
    """
    parts = path.split('|')
    current = spec

    # Navigate to the parent of the target
    for part in parts[:-1]:
      # Check if this part is an array index (only if current is a list)
      if part.isdigit() and isinstance(current, list):
        # Convert to integer and access array element
        index = int(part)
        if 0 <= index < len(current):
          current = current[index]
        else:
          raise IndexError(f"Array index {index} out of range")
      else:
        # Regular dictionary key
        if part not in current:
          current[part] = {}
        current = current[part]

    # Set the final value
    final_key = parts[-1]
    if final_key.isdigit() and isinstance(current, list):
      # Final part is an array index
      index = int(final_key)
      if 0 <= index < len(current):
        current[index] = value
      else:
        raise IndexError(f"Array index {index} out of range")
    else:
      # Final part is a dictionary key
      current[final_key] = value

  # ---------------------------------------------------------------------------
  def path_exists(self: "APISpecTool", spec: Dict[str, Any], path: str) -> bool:
    """Check if a pipe-separated path exists in the spec.

    Arguments:
        spec: The specification dictionary to check.
        path: Pipe-separated path string to check.

    Returns:
        bool: True if the path exists, False otherwise.
    """
    return self.get_value_at_spec_path(spec, path) is not None

  # ---------------------------------------------------------------------------
  def rename_key_at_path(
    self: "APISpecTool", spec: Dict[str, Any], parent_path: str, old_key: str, new_key: str
  ) -> bool:
    """Rename a key at the specified parent path.

    Arguments:
        spec: The specification dictionary to modify.
        parent_path: Pipe-separated path to the parent object.
        old_key: The current key name to rename.
        new_key: The new key name.

    Returns:
        bool: True if the key was successfully renamed, False otherwise.
    """
    parent = self.get_value_at_spec_path(spec, parent_path)

    if isinstance(parent, dict) and old_key in parent:
      parent[new_key] = parent.pop(old_key)
      return True

    return False

  # ---------------------------------------------------------------------------
  def modify_array_element(
    self: "APISpecTool", spec: Dict[str, Any], array_path: str,
    match_criteria: Dict[str, Any], modifications: Dict[str, Any]
  ) -> bool:
    """Modify a specific element in an array by matching criteria.

    Arguments:
        spec: The specification dictionary to modify.
        array_path: Pipe-separated path to the array.
        match_criteria: Dictionary of criteria to match elements.
        modifications: Dictionary of modifications to apply.

    Returns:
        bool: True if the element was successfully modified, False otherwise.
    """
    array = self.get_value_at_spec_path(spec, array_path)

    if not isinstance(array, list):
      return False

    # Find the element that matches all criteria
    for element in array:
      if isinstance(element, dict):
        # Check if this element matches all criteria
        matches = all(element.get(key) == value for key, value in match_criteria.items())

        if matches:
          # Apply modifications to this element
          for key, value in modifications.items():
            element[key] = value

          return True

    return False

  # -------------------------------------------------------------------------
  def apply_path_operations(
    self: "APISpecTool", spec: Dict[str, Any], fixes: Dict[str, Any]
  ) -> tuple[List[str], List[str]]:
    """Apply path-based operations to the spec.

    Arguments:
        spec: The specification dictionary to modify.
        fixes: Dictionary containing the fixes to apply.

    Returns:
        tuple[List[str], List[str]]: Tuple of (successful_changes, skipped_changes).
    """
    successful_changes: List[str] = []
    skipped_changes: List[str] = []

    # Handle both old and new format
    operations = self._get_operations_from_fixes(fixes)
    if not operations:
      return successful_changes, skipped_changes

    for op in operations:
      operation_type = op.get("type", op.get("operation", "unknown"))
      path = op["path"]
      description = op.get("description", "")

      change_msg = self._apply_single_operation(spec, operation_type, op, path, description)

      # Categorize messages based on their content
      if any(skip_indicator in change_msg.lower() for skip_indicator in
             ['skipped', 'already exists', 'not found', 'unchanged', 'no changes', 'already in correct position']):
        skipped_changes.append(change_msg)
      else:
        successful_changes.append(change_msg)

    return successful_changes, skipped_changes

  def _get_operations_from_fixes(self: "APISpecTool",
                                 fixes: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract operations from fixes configuration.

    Returns:
        List[Dict[str, Any]]: List of operation dictionaries from the fixes config.
    """
    if "operations" in fixes:
      operations = fixes["operations"]
      if isinstance(operations, list):
        return operations
      else:
        return []
    else:
      return []

  def _apply_single_operation(
    self: "APISpecTool", spec: Dict[str, Any], operation_type: str, op: Dict[str, Any],
    path: str, description: str
  ) -> str:
    """Apply a single operation and return a status message."""
    # Check if this is an array-aware operation
    if op.get('array_tracking', False):
      return self._apply_array_aware_operation(spec, op, path, description)
    
    # Regular operations
    if operation_type == "rename_key":
      return self._apply_rename_key(spec, op, description)
    elif operation_type == "set_value":
      return self._apply_set_value(spec, op, path, description)
    elif operation_type == "add_if_missing":
      return self._apply_add_if_missing(spec, op, path, description)
    elif operation_type == "delete_value":
      return self._apply_delete_value(spec, path, description)
    elif operation_type == "modify_array_element":
      return self._apply_modify_array_element(spec, op, description)
    elif operation_type == "add_array_item":
      return self._apply_add_array_item(spec, op, path, description)
    elif operation_type == "remove_array_item":
      return self._apply_remove_array_item(spec, op, path, description)
    elif operation_type == "move_array_item":
      return self._apply_move_array_item(spec, op, path, description)
    else:
      return f"Unknown operation {operation_type!r}: {description}"

  def _apply_rename_key(
    self: "APISpecTool", spec: Dict[str, Any], op: Dict[str, Any], description: str
  ) -> str:
    """Apply rename_key operation."""
    success = self.rename_key_at_path(spec, op["path"], op["old_key"], op["new_key"])
    if success:
      return f"Renamed key: {description}"
    else:
      return f"Key not found (skipped): {description}"

  def _apply_set_value(
    self: "APISpecTool", spec: Dict[str, Any], op: Dict[str, Any], path: str,
    description: str
  ) -> str:
    """Apply set_value operation."""
    if self.path_exists(spec, path):
      current_value = self.get_value_at_spec_path(spec, path)
      if current_value != op["value"]:
        self.set_value_at_path(spec, path, op["value"])
        return f"Updated value: {description}"
      else:
        return f"Value unchanged (already correct): {description}"
    else:
      self.set_value_at_path(spec, path, op["value"])
      return f"Added new value: {description}"

  def _apply_add_if_missing(
    self: "APISpecTool", spec: Dict[str, Any], op: Dict[str, Any], path: str,
    description: str
  ) -> str:
    """Apply add_if_missing operation."""
    if not self.path_exists(spec, path):
      self.set_value_at_path(spec, path, op["value"])
      return f"Added missing: {description}"
    else:
      return f"Already exists (skipped): {description}"

  def _apply_delete_value(
    self: "APISpecTool", spec: Dict[str, Any], path: str, description: str
  ) -> str:
    """Apply delete_value operation."""
    if not self.path_exists(spec, path):
      return f"Value not found for deletion (skipped): {description}"

    # Navigate to parent and remove the key
    parts = path.split('|')
    if len(parts) <= 1:
      return f"Cannot delete root value (skipped): {description}"

    parent_path = '|'.join(parts[:-1])
    key_to_remove = parts[-1]
    parent = self.get_value_at_spec_path(spec, parent_path)

    if isinstance(parent, dict) and key_to_remove in parent:
      del parent[key_to_remove]
      return f"Deleted value: {description}"
    else:
      return f"Key not found for deletion (skipped): {description}"

  def _apply_modify_array_element(
    self: "APISpecTool", spec: Dict[str, Any], op: Dict[str, Any], description: str
  ) -> str:
    """Apply modify_array_element operation."""
    match_criteria = op.get("match_criteria", {})
    modifications = op.get("modifications", {})
    success = self.modify_array_element(spec, op["path"], match_criteria, modifications)

    if success:
      return f"Modified array element: {description}"
    else:
      return f"Array element not found (skipped): {description}"

  def _apply_add_array_item(
    self: "APISpecTool", spec: Dict[str, Any], op: Dict[str, Any], path: str,
    description: str
  ) -> str:
    """Apply add_array_item operation."""
    array = self.get_value_at_spec_path(spec, path)
    if isinstance(array, list):
      array.append(op["value"])
      return f"Added array item: {description}"
    else:
      return f"Path is not an array (skipped): {description}"

  def _apply_remove_array_item(
    self: "APISpecTool", spec: Dict[str, Any], op: Dict[str, Any], path: str,
    description: str
  ) -> str:
    """Apply remove_array_item operation."""
    array = self.get_value_at_spec_path(spec, path)
    if isinstance(array, list) and op["value"] in array:
      array.remove(op["value"])
      return f"Removed array item: {description}"
    else:
      return f"Array item not found (skipped): {description}"

  def _apply_move_array_item(
    self: "APISpecTool", spec: Dict[str, Any], op: Dict[str, Any], path: str,
    description: str
  ) -> str:
    """Apply move_array_item operation."""
    array = self.get_value_at_spec_path(spec, path)
    if not isinstance(array, list):
      return f"Path is not an array (skipped): {description}"
    
    # For move operations, we don't need to do anything since the array
    # is already in the correct order in the target specification
    # This operation is mainly for tracking/documentation purposes
    return f"Array item already in correct position (skipped): {description}"

  def _apply_array_aware_operation(
    self: "APISpecTool", spec: Dict[str, Any], op: Dict[str, Any], path: str,
    description: str
  ) -> str:
    """Apply array-aware operations using content hashing.
    
    Arguments:
        spec: The specification dictionary to modify.
        op: The operation dictionary.
        path: The path where the operation should be applied.
        description: Description of the operation.
        
    Returns:
        str: Status message for the operation.
    """
    if not op.get('array_tracking', False):
      # Fall back to regular operation
      return self._apply_single_operation(spec, op.get('type', 'set_value'), op, path, description)
    
    # Extract array path from the operation path
    array_path, array_index = self._extract_array_path_and_index(path)
    if not array_path:
      return f"Array path not found (skipped): {description}"
    
    array = self.get_value_at_spec_path(spec, array_path)
    if not isinstance(array, list):
      return f"Path is not an array (skipped): {description}"
    
    content_hash = op.get('content_hash')
    operation_type = op.get('type', 'set_value')
    
    if operation_type == 'add_array_item':
      # Add the item to the array
      array.append(op['value'])
      return f"Added array item: {description}"
    
    elif operation_type == 'remove_array_item':
      # Find and remove item by content hash
      for i, item in enumerate(array):
        if self.create_content_hash(item) == content_hash:
          array.pop(i)
          return f"Removed array item: {description}"
      return f"Array item not found (skipped): {description}"
    
    elif operation_type == 'set_value':
      # Find and update item by content hash
      for i, item in enumerate(array):
        if self.create_content_hash(item) == content_hash:
          array[i] = op['value']
          return f"Updated array item: {description}"
      return f"Array item not found (skipped): {description}"
    
    elif operation_type == 'move_array_item':
      # For move operations, the array is already in the correct order
      # in the target specification, so we just verify the item exists
      for item in array:
        if self.create_content_hash(item) == content_hash:
          return f"Array item already in correct position (skipped): {description}"
      return f"Array item not found (skipped): {description}"
    
    else:
      return f"Unknown array operation {operation_type}: {description}"


# -----------------------------------------------------------------------------
def main() -> None:
  """Run the API spec tool with command line arguments."""
  parser = create_argument_parser()
  args = parser.parse_args()

  if not args.command:
    parser.print_help()
    sys.exit(1)

  tool = APISpecTool()

  try:
    if args.command == 'analyze':
      handle_analyze_command(tool, args)
    elif args.command == 'extract':
      handle_extract_command(tool, args)
    elif args.command == 'update':
      handle_update_command(tool, args)
    elif args.command == 'fix':
      handle_fix_command(tool, args)

  except Exception as e:
    print(f"Error: {e}", file=sys.stderr)
    sys.exit(1)


def create_argument_parser() -> argparse.ArgumentParser:
  """Create and configure the argument parser.

  Returns:
      argparse.ArgumentParser: Configured argument parser with all subcommands.
  """
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
    '--format',
    '-f',
    choices=['markdown', 'text', 'json'],
    default='text',
    help='Output format (default: text)'
  )
  extract_parser.add_argument('--output', '-o', help='Output file (default: stdout)')

  # Update subcommand
  update_parser = subparsers.add_parser(
    'update', help='Update spec-fixes.json with new changes'
  )
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
    '--fixes-file', default='scripts/spec-fixes.json', help='Fixes configuration file'
  )

  return parser


def handle_analyze_command(tool: APISpecTool, args: argparse.Namespace) -> None:
  """Handle the analyze command.

  Arguments:
      tool: APISpecTool instance to use for analysis.
      args: Parsed command line arguments.
  """
  analysis = tool.analyze_api_structure(args.swagger_file)
  tool.print_analysis(analysis)


def handle_extract_command(tool: APISpecTool, args: argparse.Namespace) -> None:
  """Handle the extract command.

  Arguments:
      tool: APISpecTool instance to use for extraction.
      args: Parsed command line arguments.
  """
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
    with os.fdopen(os.open(args.output, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o644), 'w',
                   encoding='utf-8') as f:
      f.write(output)

    print(f"Routes extracted and saved to: {args.output}")
  else:
    print(output)


def handle_update_command(tool: APISpecTool, args: argparse.Namespace) -> None:
  """Handle the update command.

  Arguments:
      tool: APISpecTool instance to use for analysis.
      args: Parsed command line arguments.
  """
  # Load the original and fixed files
  original = tool.load_json_file(args.original_file, "original spec file")
  fixed = tool.load_json_file(args.fixed_file, "fixed spec file")

  print(f"Loaded original file: {args.original_file}")
  print(f"Loaded fixed file: {args.fixed_file}")

  # Get existing spec-fix paths
  existing_paths = tool.get_existing_spec_fix_paths(args.output_file)
  print(f"Found {len(existing_paths)} existing paths in spec-fixes")

  # Find all differences using DeepDiff with array tracking
  print("Analyzing differences...")
  all_differences = tool.find_differences_with_array_tracking(original, fixed)
  print(f"Found {len(all_differences)} total differences")

  # Filter out differences that are already covered
  new_fixes = _filter_new_fixes(tool, all_differences, existing_paths)

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
  spec_fixes = _load_or_create_spec_fixes(args)

  # Add new fixes
  _add_new_fixes(spec_fixes, new_fixes, args)

  # Sort operations by path for consistent output
  _sort_operations_by_path(spec_fixes)

  # Write updated spec-fixes
  with os.fdopen(os.open(args.output_file, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o644),
                 'w') as f:
    json.dump(spec_fixes, f, indent=2)

  print(f"\nSuccessfully updated {args.output_file} with {len(new_fixes)} new fixes")


def _filter_new_fixes(
  tool: APISpecTool, all_differences: List[Dict[str, Any]], existing_paths: Set[str]
) -> List[Dict[str, Any]]:
  """Filter out differences that are already covered."""
  new_fixes = []
  for diff in all_differences:
    spec_path = diff['path']

    # Skip if already covered
    if spec_path in existing_paths:
      continue

    # Include all types of changes (more comprehensive)
    operation_type = diff['type']
    value = diff.get('value')
    old_value = diff.get('old_value')
    description = diff.get('description')

    # Handle array indices with content-based tracking
    if diff.get('array_tracking', False):
      content_hash = diff.get('content_hash')
      old_content_hash = diff.get('old_content_hash')
      new_fixes.append(
        tool.create_array_aware_fix_entry(
          spec_path, value, operation_type, old_value, description or "", content_hash
        )
      )
    else:
      new_fixes.append(
        tool.create_fix_entry(spec_path, value, operation_type, old_value, description or "")
      )

  return new_fixes


def _load_or_create_spec_fixes(args: argparse.Namespace) -> Dict[str, Any]:
  """Load existing spec-fixes or create new structure."""
  try:
    with open(args.output_file, 'r') as f:
      return json.load(f)  # type: ignore[no-any-return]
  except FileNotFoundError:
    return {
      "version":
        "3.1",  # Version 3.1 adds improved skip operation categorization and better output organization
      "description":
        "Machine-focused OpenAPI specification fixes with array position tracking and improved operation categorization generated by DeepDiff analysis",
      "metadata": {
        "generated_by": "api_spec_tool.py",
        "generated_at": "2024-01-01T00:00:00Z",
        "original_spec": args.original_file,
        "fixed_spec": args.fixed_file,
        "features": ["array_position_tracking", "content_based_hashing", "element_mapping", "skip_operation_categorization"]
      },
      "operations": []
    }


def _add_new_fixes(
  spec_fixes: Dict[str, Any], new_fixes: List[Dict[str, Any]], args: argparse.Namespace
) -> None:
  """Add new fixes to the spec-fixes structure.

  Arguments:
      spec_fixes: The spec-fixes dictionary to update.
      new_fixes: List of new fixes to add.
      args: Parsed command line arguments.
  """
  # Add new fixes to operations
  spec_fixes["operations"].extend(new_fixes)


def _sort_operations_by_path(spec_fixes: Dict[str, Any]) -> None:
  """Sort operations by path for consistent output."""
  if "operations" in spec_fixes and isinstance(spec_fixes["operations"], list):
    spec_fixes["operations"].sort(key=lambda op: op.get("path", ""))


def handle_fix_command(tool: APISpecTool, args: argparse.Namespace) -> None:
  """Handle the fix command.

  Arguments:
      tool: APISpecTool instance to use for fixing.
      args: Parsed command line arguments.
  """
  # Load files
  original_spec = tool.load_json_file(args.original_file, "original spec file")
  fixes_config = tool.load_json_file(args.fixes_file, "fixes configuration file")

  print("📖 Loading files...")
  print(f"   Original spec: {args.original_file}")
  print(f"   Fixes config: {args.fixes_file}")

  # Apply fixes to a copy of the original spec
  print("🔧 Applying OpenAPI spec fixes...")
  fixed_spec_data = original_spec.copy()
  successful_changes, skipped_changes = tool.apply_path_operations(
    fixed_spec_data, fixes_config
  )

  # Write fixed specification
  print(f"💾 Writing fixed spec: {args.fixed_file}")

  with os.fdopen(os.open(args.fixed_file, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o644),
                 'w') as f:
    json.dump(fixed_spec_data, f, indent=2)

  # Print summary - successful changes first
  if successful_changes:
    print(f"\n✅ Applied {len(successful_changes)} fixes:")
    for change in successful_changes:
      print(f"   • {change}")
  else:
    print("\n⚠️  No fixes were applied")

  # Print skipped changes last for easier cleanup
  if skipped_changes:
    print(
      f"\n⏭️  Skipped {len(skipped_changes)} operations (already exist/no changes needed):"
    )
    for change in skipped_changes:
      print(f"   • {change}")

  print(f"\n🎉 Fixed specification written to: {args.fixed_file}")


if __name__ == '__main__':
  main()
