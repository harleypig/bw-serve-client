#!/usr/bin/env python3

r"""Unified API Specification Tool for Bitwarden Vault Management API.

This script provides a unified interface for working with the Bitwarden Vault
Management API OpenAPI specification. It combines functionality from multiple
scripts into a single tool with subcommands.

Usage:
    python upstream/api-spec-tool.py <subcommand> [options]

Global Options:
    -q, --quiet    Suppress verbose output, only show errors and exit codes
    -d, --debug    Enable debug output with detailed logging

Subcommands:
    analyze    Analyze API structure and extract key information
    extract    Extract and format API routes

Exit Codes:
    0    Success
    1    General error (invalid arguments, file not found, etc.)
    2    Analysis error (malformed JSON, invalid API spec, etc.)
    3    Unexpected error (any other failure)

Examples:
    # Analyze the API structure
    python upstream/api-spec-tool.py analyze upstream/vault-management-api-original.json

    # Extract routes in markdown format
    python upstream/api-spec-tool.py extract --format markdown \\
    upstream/vault-management-api-original.json

    # Quiet mode - suppress verbose output
    python upstream/api-spec-tool.py analyze --quiet upstream/vault-management-api-original.json

    # Debug mode - show detailed logging
    python upstream/api-spec-tool.py analyze --debug upstream/vault-management-api-original.json
"""

import argparse
import json
import os
from pathlib import Path
import sys
from typing import Any, Dict, List, Set

# Type aliases for complex types
RouteInfo = Dict[str, Any]
RouteList = List[RouteInfo]
GroupedRoutes = Dict[str, RouteList]
OutputData = Dict[str, Dict[str, List[str]]]


class APISpecToolError(Exception):
  """Base exception for APISpecTool errors."""

  pass


class APISpecTool:
  """Unified tool for working with API specifications.

  This tool provides functionality for analyzing OpenAPI specifications and
  extracting their routes. It initializes with the script directory for relative
  path operations.
  """

  # ---------------------------------------------------------------------------
  def __init__(self: "APISpecTool", quiet: bool = False, debug: bool = False) -> None:
    self.script_dir = Path(__file__).parent
    self.quiet = quiet
    self.debug = debug

  # ---------------------------------------------------------------------------
  def _debug(self: "APISpecTool", message: str) -> None:
    """Print debug message if debug mode is enabled.

    Args:
        message: Debug message to print
    """
    if self.debug:
      print(f"[DEBUG] {message}", file=sys.stderr)

  # ---------------------------------------------------------------------------
  def load_json_file(self: "APISpecTool", file_path: str, description: str = "JSON file") -> Dict[str, Any]:
    """Load and parse a JSON file with error handling.

    Arguments:
        file_path: Path to the JSON file to load.
        description: Description of the file for error messages.

    Returns:
        Dict[str, Any]: The parsed JSON data as a dictionary.

    Raises:
        TypeError: When the JSON file does not contain a dictionary.
        FileNotFoundError: When the specified file does not exist.
        JSONDecodeError: When the file contains invalid JSON.
        APISpecToolError: When an unexpected error occurs while reading the file.
    """
    self._debug(f"Loading {description}: {file_path}")
    try:
      with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    except FileNotFoundError as e:
      self._debug(f"File not found: {file_path}")
      raise FileNotFoundError(f"{description} not found: {file_path}") from e

    except json.JSONDecodeError as e:
      self._debug(f"JSON decode error at position {e.pos}: {e}")
      raise json.JSONDecodeError(f"Invalid JSON in {description}: {e}", e.doc, e.pos) from e

    except Exception as e:
      self._debug(f"Unexpected error loading {description}: {type(e).__name__}: {e}")
      raise APISpecToolError(f"Error reading {description}: {e}") from e

    self._debug(f"Successfully loaded {description}, size: {len(str(data))} characters")

    if not isinstance(data, dict):
      self._debug(f"JSON file contains {type(data).__name__}, expected dict")
      raise TypeError(f"Expected JSON object (dict), got {type(data).__name__}")

    self._debug(f"JSON file validated as dictionary with {len(data)} top-level keys")
    return data

  # ---------------------------------------------------------------------------
  def analyze_api_structure(self: "APISpecTool", swagger_file: str) -> Dict[str, Any]:
    """Analyze the API structure and extract key information.

    Arguments:
        swagger_file: Path to the Swagger/OpenAPI specification file.

    Returns:
        Dict[str, Any]: Analysis results containing API information, authentication,
            server info, response patterns, and validation rules.
    """
    self._debug(f"Starting API structure analysis for: {swagger_file}")
    data = self.load_json_file(swagger_file, "swagger file")
    self._debug(f"Loaded swagger data with {len(data)} top-level keys: {list(data.keys())}")

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

  # ---------------------------------------------------------------------------
  def _extract_api_info(self: "APISpecTool", data: Dict[str, Any], analysis: Dict[str, Any]) -> None:
    """Extract API information from the spec."""
    self._debug("Extracting API info from spec")

    if 'info' in data:
      info_data = data['info']
      self._debug(f"Found info section with keys: {list(info_data.keys())}")

      analysis['api_info'] = {
        'title': info_data.get('title', ''),
        'description': info_data.get('description', ''),
        'version': info_data.get('version', ''),
        'openapi_version': data.get('openapi', '')
      }

      self._debug(f"Extracted API info: {analysis['api_info']}")

    else:
      self._debug("No 'info' section found in spec")

  # ---------------------------------------------------------------------------
  def _extract_authentication_info(self: "APISpecTool", data: Dict[str, Any], analysis: Dict[str, Any]) -> None:
    """Extract authentication information from the spec."""
    self._debug("Extracting authentication info from spec")

    if 'security' in data:
      self._debug(f"Found security section: {data['security']}")
      analysis['authentication'] = data['security']

    else:
      self._debug("No 'security' section found in spec")

    if 'components' in data and 'securitySchemes' in data['components']:
      schemes = data['components']['securitySchemes']
      self._debug(f"Found security schemes: {list(schemes.keys())}")
      analysis['authentication']['schemes'] = schemes

    else:
      self._debug("No security schemes found in components")

  # ---------------------------------------------------------------------------
  def _extract_server_info(self: "APISpecTool", data: Dict[str, Any], analysis: Dict[str, Any]) -> None:
    """Extract server information from the spec."""
    self._debug("Extracting server info from spec")

    if 'servers' in data:
      # Convert servers list to a more readable format
      servers = data['servers']
      self._debug(f"Found servers section with {len(servers) if isinstance(servers, list) else 'non-list'} entries")

      if isinstance(servers, list) and len(servers) > 0:
        primary_url = servers[0].get('url', '') if isinstance(servers[0], dict) else str(servers[0])
        self._debug(f"Primary server URL: {primary_url}")
        analysis['server_info'] = {'servers': servers, 'primary_url': primary_url, 'count': len(servers)}

      else:
        self._debug("Servers list is empty or not a list")
        analysis['server_info'] = {'servers': servers}

    elif 'host' in data:
      self._debug("Using legacy host/basePath format")
      analysis['server_info'] = {
        'host': data.get('host', ''),
        'basePath': data.get('basePath', ''),
        'schemes': data.get('schemes', [])
      }

    else:
      self._debug("No server information found in spec")

  # ---------------------------------------------------------------------------
  def _analyze_paths(
    self: "APISpecTool", data: Dict[str, Any], analysis: Dict[str, Any], error_codes: Set[str], tags: Set[str],
    response_patterns: Dict[str, Set[str]]
  ) -> None:
    """Analyze API paths and extract patterns."""
    self._debug("Analyzing API paths")

    if 'paths' not in data:
      self._debug("No 'paths' section found in spec")
      return

    paths = data['paths']
    self._debug(f"Found {len(paths)} paths to analyze")
    endpoint_count = 0

    for path, methods in paths.items():
      self._debug(f"Processing path: {path}")

      for method, details in methods.items():
        if method.upper() in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS']:
          self._debug(f"  Processing {method.upper()} method")
          self._process_endpoint(path, method, details, analysis, error_codes, tags, response_patterns)
          endpoint_count += 1

    self._debug(f"Processed {endpoint_count} endpoints total")

  # ---------------------------------------------------------------------------
  def _process_endpoint(
    self: "APISpecTool", path: str, method: str, details: Dict[str, Any], analysis: Dict[str, Any], error_codes: Set[str],
    tags: Set[str], response_patterns: Dict[str, Set[str]]
  ) -> None:
    """Process a single endpoint and extract its information."""
    self._debug(f"    Processing endpoint: {method.upper()} {path}")

    # Extract tags
    if 'tags' in details:
      tags.update(details['tags'])

    # Extract parameters
    self._extract_parameters(details, analysis)

    # Extract request body patterns
    self._extract_request_body_patterns(path, method, details, analysis)

    # Extract response patterns
    self._extract_response_patterns(path, method, details, analysis, error_codes, response_patterns)

  # ---------------------------------------------------------------------------
  def _extract_parameters(self: "APISpecTool", details: Dict[str, Any], analysis: Dict[str, Any]) -> None:
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

  # ---------------------------------------------------------------------------
  def _extract_request_body_patterns(
    self: "APISpecTool", path: str, method: str, details: Dict[str, Any], analysis: Dict[str, Any]
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

  # ---------------------------------------------------------------------------
  def _extract_response_patterns(
    self: "APISpecTool", path: str, method: str, details: Dict[str, Any], analysis: Dict[str, Any], error_codes: Set[str],
    response_patterns: Dict[str, Set[str]]
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
            analysis['examples'][example_key] = {'content_type': content_type, 'example': content_info['example']}

  # ---------------------------------------------------------------------------
  def _analyze_schemas(self: "APISpecTool", data: Dict[str, Any], analysis: Dict[str, Any]) -> None:
    """Analyze data schemas from the spec."""
    self._debug("Analyzing data schemas")

    if 'components' in data and 'schemas' in data['components']:
      schemas = data['components']['schemas']
      self._debug(f"Found {len(schemas)} schemas to analyze")

      for schema_name, schema_def in schemas.items():
        self._debug(f"  Analyzing schema: {schema_name}")

        analysis['data_models'][schema_name] = {
          'type': schema_def.get('type', 'object'),
          'properties': schema_def.get('properties', {}),
          'required': schema_def.get('required', []),
          'description': schema_def.get('description', '')
        }

    else:
      self._debug("No schemas found in components")

  # ---------------------------------------------------------------------------
  def _finalize_analysis(
    self: "APISpecTool", analysis: Dict[str, Any], error_codes: Set[str], tags: Set[str], response_patterns: Dict[str, Set[str]]
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

  # ---------------------------------------------------------------------------
  def _print_header(self: "APISpecTool") -> None:
    """Print the analysis header."""
    print("=" * 80)
    print("BITWARDEN VAULT MANAGEMENT API - LIBRARY DEVELOPMENT ANALYSIS")
    print("=" * 80)

  # ---------------------------------------------------------------------------
  def _print_api_info(self: "APISpecTool", analysis: Dict[str, Any]) -> None:
    """Print API information section."""
    print("\n📋 API INFORMATION:")
    print("-" * 40)

    for key, value in analysis['api_info'].items():
      print(f"  {key}: {value}")

  # ---------------------------------------------------------------------------
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

  # ---------------------------------------------------------------------------
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

  # ---------------------------------------------------------------------------
  def _print_response_patterns(self: "APISpecTool", analysis: Dict[str, Any]) -> None:
    """Print response patterns section."""
    print("\n📤 RESPONSE PATTERNS:")
    print("-" * 40)

    for status_code, content_types in analysis['response_patterns'].items():
      print(f"  {status_code}: {', '.join(content_types)}")

  # ---------------------------------------------------------------------------
  def _print_error_codes(self: "APISpecTool", analysis: Dict[str, Any]) -> None:
    """Print error codes section."""
    print("\n❌ ERROR CODES:")
    print("-" * 40)

    for code in analysis['error_codes']:
      print(f"  {code}")

  # ---------------------------------------------------------------------------
  def _print_tags(self: "APISpecTool", analysis: Dict[str, Any]) -> None:
    """Print API categories (tags) section."""
    print("\n🏷️  API CATEGORIES (TAGS):")
    print("-" * 40)

    for tag in analysis['tags']:
      print(f"  - {tag}")

  # ---------------------------------------------------------------------------
  def _print_parameter_patterns(self: "APISpecTool", analysis: Dict[str, Any]) -> None:
    """Print parameter patterns section."""
    print("\n📝 PARAMETER PATTERNS:")
    print("-" * 40)

    for param_type, params in analysis['parameter_patterns'].items():
      print(f"  {param_type.upper()} parameters:")

      for param in params[:5]:  # Show first 5 examples
        print(f"    - {param['name']} ({param['type']}) - "
              f"{param['description'][:50]}...")

      if len(params) > 5:
        print(f"    ... and {len(params) - 5} more")

  # ---------------------------------------------------------------------------
  def _print_request_body_patterns(self: "APISpecTool", analysis: Dict[str, Any]) -> None:
    """Print request body patterns section."""
    print("\n📦 REQUEST BODY PATTERNS:")
    print("-" * 40)

    for endpoint, body_info in list(analysis['request_body_patterns'].items())[:5]:
      print(f"  {endpoint}:")
      print(f"    Content-Types: {', '.join(body_info['content_types'])}")
      print(f"    Required: {body_info['required']}")

  # ---------------------------------------------------------------------------
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

  # ---------------------------------------------------------------------------
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

  # ---------------------------------------------------------------------------
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
    self._debug(f"Extracting routes from: {swagger_file}")
    data = self.load_json_file(swagger_file, "swagger file")
    routes: List[Dict[str, Any]] = []

    if 'paths' not in data:
      self._debug("No 'paths' section found in swagger file")
      print("Error: No 'paths' section found in swagger file.", file=sys.stderr)
      return routes

    paths = data['paths']
    self._debug(f"Found {len(paths)} paths to extract routes from")

    for path, methods in paths.items():
      self._debug(f"Processing path: {path}")

      for method, details in methods.items():
        if method.upper() in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS']:
          self._debug(f"  Extracting {method.upper()} method")

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
          self._debug(f"    Added route: {method.upper()} {path}")

    self._debug(f"Extracted {len(routes)} total routes")
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


# -----------------------------------------------------------------------------
def main() -> None:
  """Run the API spec tool with command line arguments.

  Exit codes:
      0: Success
      1: General error (invalid arguments, file not found, etc.)
      2: Analysis error (malformed JSON, invalid API spec, etc.)
      3: Unexpected error (any other failure)
  """
  parser = create_argument_parser()
  args = parser.parse_args()

  if not args.command:
    parser.print_help()
    sys.exit(1)

  # Initialize tool with debug and quiet flags
  tool = APISpecTool(quiet=getattr(args, 'quiet', False), debug=getattr(args, 'debug', False))

  if tool.debug:
    tool._debug(f"Starting api-spec-tool with command: {args.command}")
    tool._debug(f"Quiet mode: {tool.quiet}, Debug mode: {tool.debug}")

  try:
    _execute_command(tool, args)

  except FileNotFoundError as e:
    _handle_file_not_found_error(tool, args, e)

  except json.JSONDecodeError as e:
    _handle_json_decode_error(tool, args, e)

  except KeyError as e:
    _handle_key_error(tool, args, e)

  except Exception as e:
    _handle_general_error(tool, args, e)


# -----------------------------------------------------------------------------
def _execute_command(tool: APISpecTool, args: argparse.Namespace) -> None:
  """Execute the specified command."""
  if args.command == 'analyze':
    handle_analyze_command(tool, args)

  elif args.command == 'extract':
    handle_extract_command(tool, args)


# -----------------------------------------------------------------------------
def _handle_file_not_found_error(tool: APISpecTool, args: argparse.Namespace, e: FileNotFoundError) -> None:
  """Handle FileNotFoundError."""
  tool._debug(f"FileNotFoundError caught: {e}")

  if not getattr(args, 'quiet', False):
    print(f"Error: File not found: {e}", file=sys.stderr)

  sys.exit(1)


# -----------------------------------------------------------------------------
def _handle_json_decode_error(tool: APISpecTool, args: argparse.Namespace, e: json.JSONDecodeError) -> None:
  """Handle JSONDecodeError."""
  tool._debug(f"JSONDecodeError caught: {e}")

  if not getattr(args, 'quiet', False):
    print(f"Error: Invalid JSON: {e}", file=sys.stderr)

  sys.exit(2)


# -----------------------------------------------------------------------------
def _handle_key_error(tool: APISpecTool, args: argparse.Namespace, e: KeyError) -> None:
  """Handle KeyError."""
  tool._debug(f"KeyError caught: {e}")

  if not getattr(args, 'quiet', False):
    print(f"Error: Missing required field in API spec: {e}", file=sys.stderr)

  sys.exit(2)


# -----------------------------------------------------------------------------
def _handle_general_error(tool: APISpecTool, args: argparse.Namespace, e: Exception) -> None:
  """Handle general exceptions."""
  tool._debug(f"Exception caught: {type(e).__name__}: {e}")

  if not getattr(args, 'quiet', False):
    print(f"Error: {e}", file=sys.stderr)

  sys.exit(3)


# -----------------------------------------------------------------------------
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

  # Global options
  parser.add_argument('-q', '--quiet', action='store_true', help='Suppress verbose output, only show errors and exit codes')
  parser.add_argument('-d', '--debug', action='store_true', help='Enable debug output with detailed logging')

  subparsers = parser.add_subparsers(dest='command', help='Available subcommands')

  # Analyze subcommand
  analyze_parser = subparsers.add_parser('analyze', help='Analyze API structure')
  analyze_parser.add_argument('swagger_file', help='Path to the swagger JSON file')
  analyze_parser.add_argument('-q', '--quiet', action='store_true', help='Suppress verbose output, only show errors and exit codes')
  analyze_parser.add_argument('-d', '--debug', action='store_true', help='Enable debug output with detailed logging')

  # Extract subcommand
  extract_parser = subparsers.add_parser('extract', help='Extract and format API routes')
  extract_parser.add_argument('swagger_file', help='Path to the swagger JSON file')
  extract_parser.add_argument(
    '--format', '-f', choices=['markdown', 'text', 'json'], default='text', help='Output format (default: text)'
  )
  extract_parser.add_argument('--output', '-o', help='Output file (default: stdout)')
  extract_parser.add_argument('-q', '--quiet', action='store_true', help='Suppress verbose output, only show errors and exit codes')
  extract_parser.add_argument('-d', '--debug', action='store_true', help='Enable debug output with detailed logging')

  return parser


# -----------------------------------------------------------------------------
def handle_analyze_command(tool: APISpecTool, args: argparse.Namespace) -> None:
  """Handle the analyze command.

  Arguments:
      tool: APISpecTool instance to use for analysis.
      args: Parsed command line arguments.
  """
  tool._debug(f"Starting analyze command for file: {args.swagger_file}")
  analysis = tool.analyze_api_structure(args.swagger_file)
  tool._debug("Analysis completed, processing results")

  if not args.quiet:
    tool._debug("Printing detailed analysis (verbose mode)")
    tool.print_analysis(analysis)

  else:
    # In quiet mode, just print the summary
    tool._debug("Printing summary only (quiet mode)")

    # Count endpoints by using the extract_routes function
    routes = tool.extract_routes(args.swagger_file)
    endpoint_count = len(routes)
    tool._debug(f"Found {endpoint_count} endpoints total")
    print(f"API Analysis Complete: {endpoint_count} endpoints found")


# -----------------------------------------------------------------------------
def handle_extract_command(tool: APISpecTool, args: argparse.Namespace) -> None:
  """Handle the extract command.

  Arguments:
      tool: APISpecTool instance to use for extraction.
      args: Parsed command line arguments.
  """
  tool._debug(f"Starting extract command for file: {args.swagger_file}")
  tool._debug(f"Output format: {args.format}")

  if args.output:
    tool._debug(f"Output file: {args.output}")

  routes = tool.extract_routes(args.swagger_file)
  tool._debug(f"Extracted {len(routes)} routes")

  if args.format == 'markdown':
    tool._debug("Formatting as markdown")
    output = tool.format_markdown(routes)

  elif args.format == 'text':
    tool._debug("Formatting as text")
    output = tool.format_text(routes)

  elif args.format == 'json':
    tool._debug("Formatting as JSON")
    output = tool.format_json(routes)

  else:
    tool._debug(f"Unknown format: {args.format}")
    print(f"Error: Unknown format {args.format}", file=sys.stderr)
    sys.exit(1)

  if args.output:
    with os.fdopen(os.open(args.output, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o644), 'w', encoding='utf-8') as f:
      f.write(output)

    if not args.quiet:
      print(f"Routes extracted and saved to: {args.output}")

  else:
    print(output)


# -----------------------------------------------------------------------------
if __name__ == '__main__':
  main()
