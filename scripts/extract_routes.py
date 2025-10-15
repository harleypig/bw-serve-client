#!/usr/bin/env python3

"""Route Extraction Script for Bitwarden Vault Management API.

This script extracts API routes from the Bitwarden Vault Management API
swagger/OpenAPI specification file and generates formatted output for
documentation and comparison purposes.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

# Default values for command line arguments
DEFAULT_FORMAT = 'text'
DEFAULT_SWAGGER_FILE = 'docs/vault-management-api.json'
DEFAULT_OUTPUT = 'stdout'    # Represents stdout when None


def get_usage_text() -> str:
  """Generate usage text with dynamic script name and actual defaults."""
  script_name = Path(__file__).name
  return f"""Usage:
    {script_name} [options] [swagger_file]

Options:
    --format, -f    Output format: markdown, text, json
                    (default: {DEFAULT_FORMAT})
    --output, -o    Output file
                    (default: {DEFAULT_OUTPUT})
    --help, -h      Show this help message

Examples:
    {script_name} {DEFAULT_SWAGGER_FILE}
    {script_name} -o routes.txt {DEFAULT_SWAGGER_FILE}
    {script_name} -f json -o routes.json {DEFAULT_SWAGGER_FILE}
"""


class RouteExtractor:
  """Extract and format API routes from OpenAPI/Swagger specification."""

  def __init__(self, swagger_file: str):
    """Initialize with swagger file path."""
    self.swagger_file = Path(swagger_file)
    self.data = self._load_swagger_data()

  def _load_swagger_data(self) -> Dict[str, Any]:
    """Load and parse the swagger JSON file."""
    try:
      with open(self.swagger_file, 'r', encoding='utf-8') as f:
        return json.load(f)
    except FileNotFoundError:
      print(
        f"Error: Swagger file '{self.swagger_file}' not found.",
        file=sys.stderr
      )
      sys.exit(1)
    except json.JSONDecodeError as e:
      print(f"Error: Invalid JSON in swagger file: {e}", file=sys.stderr)
      sys.exit(1)

  def extract_routes(self) -> List[Dict[str, Any]]:
    """Extract all routes from the swagger data."""
    routes: List[Dict[str, Any]] = []

    if 'paths' not in self.data:
      print(
        "Error: No 'paths' section found in swagger file.", file=sys.stderr
      )
      return routes

    for path, methods in self.data['paths'].items():
      for method, details in methods.items():
        if method.upper() in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD',
                              'OPTIONS']:
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

      output.append("")      # Add blank line between sections

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

      output.append("")      # Add blank line between sections

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
    output_data = {}
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

  def generate_output(self, format_type: str = 'markdown') -> str:
    """Generate formatted output for the extracted routes."""
    routes = self.extract_routes()

    if format_type == 'markdown':
      return self.format_markdown(routes)
    elif format_type == 'text':
      return self.format_text(routes)
    elif format_type == 'json':
      return self.format_json(routes)
    else:
      raise ValueError(f"Unknown format type: {format_type}")


def main():
  """Main entry point for the script."""
  parser = argparse.ArgumentParser(
    description=
    "Extract API routes from Bitwarden Vault Management API swagger file",
    formatter_class=argparse.RawDescriptionHelpFormatter,
    epilog=get_usage_text()
  )

  parser.add_argument(
    'swagger_file',
    nargs='?',
    default=DEFAULT_SWAGGER_FILE,
    help=f'Path to the swagger JSON file (default: {DEFAULT_SWAGGER_FILE})'
  )

  parser.add_argument(
    '--format',
    '-f',
    choices=['markdown', 'text', 'json'],
    default=DEFAULT_FORMAT,
    help=f'Output format (default: {DEFAULT_FORMAT})'
  )

  parser.add_argument(
    '--output',
    '-o',
    type=str,
    help=f'Output file (default: {DEFAULT_OUTPUT})'
  )

  args = parser.parse_args()

  try:
    extractor = RouteExtractor(args.swagger_file)
    output = extractor.generate_output(args.format)

    if args.output:
      with open(args.output, 'w', encoding='utf-8') as f:
        f.write(output)
      print(f"Routes extracted and saved to: {args.output}")
    else:
      print(output)

  except Exception as e:
    print(f"Error: {e}", file=sys.stderr)
    sys.exit(1)


if __name__ == '__main__':
  main()
