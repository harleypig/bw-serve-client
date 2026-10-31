"""Simple tests for API Specification Tool."""

import importlib.util
import json
import os
import sys
import tempfile
from typing import Any, Dict

import pytest

# Import the tool from the upstream directory
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'upstream'))

spec = importlib.util.spec_from_file_location(
  "api_spect_tool", os.path.join(os.path.dirname(__file__), '..', 'upstream', 'api-spec-tool.py')
)
if spec is None or spec.loader is None:
  raise ImportError("Could not load api_spect_tool module")

api_spect_tool = importlib.util.module_from_spec(spec)
spec.loader.exec_module(api_spect_tool)

APISpecTool = api_spect_tool.APISpecTool


class TestAPISpecToolBasic:
  """Basic test cases for APISpecTool class."""

  def setup_method(self: "TestAPISpecToolBasic") -> None:
    """Set up test fixtures before each test method."""
    self.tool = APISpecTool()
    self.sample_swagger_data: Dict[str, Any] = {
      "openapi": "3.0.0",
      "info": {
        "title": "Test API",
        "description": "A test API",
        "version": "1.0.0"
      },
      "servers": [{
        "url": "https://api.example.com",
        "description": "Test server"
      }],
      "paths": {
        "/users": {
          "get": {
            "tags": ["users"],
            "summary": "Get users",
            "responses": {
              "200": {
                "description": "Success",
                "content": {
                  "application/json": {
                    "schema": {
                      "type": "array"
                    }
                  }
                }
              }
            }
          }
        }
      }
    }

  def test_init(self: "TestAPISpecToolBasic") -> None:
    """Test APISpecTool initialization."""
    tool = APISpecTool()  # act

    assert tool is not None

  def test_load_json_file_success(self: "TestAPISpecToolBasic") -> None:  # noqa: AAA01
    """Test successful JSON file loading."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:  # act
      json.dump(self.sample_swagger_data, f)
      temp_file = f.name

    try:
      result = self.tool.load_json_file(temp_file, "test file")
      assert result == self.sample_swagger_data
    finally:
      os.unlink(temp_file)

  def test_load_json_file_not_found(self: "TestAPISpecToolBasic") -> None:
    """Test JSON file loading when file doesn't exist."""
    with pytest.raises(FileNotFoundError):  # act
      self.tool.load_json_file("nonexistent.json", "test file")

  def test_analyze_api_structure(self: "TestAPISpecToolBasic") -> None:  # noqa: AAA01
    """Test API structure analysis."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:  # act
      json.dump(self.sample_swagger_data, f)
      temp_file = f.name

    try:
      analysis = self.tool.analyze_api_structure(temp_file)

      # Check basic structure
      assert 'api_info' in analysis
      assert 'authentication' in analysis
      assert 'server_info' in analysis
      assert 'response_patterns' in analysis
      assert 'error_codes' in analysis
      assert 'data_models' in analysis
      assert 'parameter_patterns' in analysis
      assert 'request_body_patterns' in analysis
      assert 'tags' in analysis
      assert 'examples' in analysis
      assert 'validation_rules' in analysis

      # Check specific values
      assert analysis['api_info']['title'] == "Test API"
      assert analysis['api_info']['version'] == "1.0.0"
      assert "users" in analysis['tags']
      assert "200" in analysis['error_codes']
    finally:
      os.unlink(temp_file)

  def test_extract_routes(self: "TestAPISpecToolBasic") -> None:  # noqa: AAA01
    """Test route extraction."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:  # act
      json.dump(self.sample_swagger_data, f)
      temp_file = f.name

    try:
      routes = self.tool.extract_routes(temp_file)

      # Check that routes were extracted
      assert len(routes) > 0

      # Check for expected routes
      route_paths = [route['path'] for route in routes]
      assert "/users" in route_paths
    finally:
      os.unlink(temp_file)

  def test_format_markdown(self: "TestAPISpecToolBasic") -> None:
    """Test markdown formatting."""
    routes = [{'path': '/users', 'method': 'GET', 'summary': 'Get users', 'tags': ['users']}]

    result = self.tool.format_markdown(routes)  # act

    assert "# users" in result
    assert "/users (GET)" in result

  def test_format_text(self: "TestAPISpecToolBasic") -> None:
    """Test text formatting."""
    routes = [{'path': '/users', 'method': 'GET', 'summary': 'Get users', 'tags': ['users']}]

    result = self.tool.format_text(routes)  # act

    assert "users" in result
    assert "/users (GET)" in result

  def test_format_json(self: "TestAPISpecToolBasic") -> None:
    """Test JSON formatting."""
    routes = [{'path': '/users', 'method': 'GET', 'summary': 'Get users', 'tags': ['users']}]

    result = self.tool.format_json(routes)  # act

    parsed = json.loads(result)
    assert 'users' in parsed
    assert '/users' in parsed['users']
    assert 'GET' in parsed['users']['/users']


if __name__ == '__main__':
  pytest.main([__file__])
