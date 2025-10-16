#!/usr/bin/env python3

"""Analyze API structure to extract key information for library development.

This script analyzes the Bitwarden Vault Management API OpenAPI specification
to extract essential information needed for creating a Python client library.
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Set, Union


def analyze_api_structure(swagger_file: str) -> Dict[str, Any]:
  """Analyze the API structure and extract key information."""
  try:
    with open(swagger_file, 'r', encoding='utf-8') as f:
      data = json.load(f)
  except FileNotFoundError:
    print(f"Error: Swagger file '{swagger_file}' not found.", file=sys.stderr)
    sys.exit(1)
  except json.JSONDecodeError as e:
    print(f"Error: Invalid JSON in swagger file: {e}", file=sys.stderr)
    sys.exit(1)

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
    analysis['authentication']['schemes'] = data['components']['securitySchemes']

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
        if method.upper() in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS']:
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


def print_analysis(analysis: Dict[str, Any]) -> None:
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
    print("  Note: This API likely uses session-based authentication via "
          "'bw serve'")

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
    for param in params[:5]:                               # Show first 5 examples
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


def main():
  """Main entry point."""
  if len(sys.argv) != 2:
    print("Usage: python analyze_api_structure.py <swagger_file>")
    sys.exit(1)

  swagger_file = sys.argv[1]
  analysis = analyze_api_structure(swagger_file)
  print_analysis(analysis)


if __name__ == '__main__':
  main()
