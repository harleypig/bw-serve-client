"""Simple tests for API Specification Tool."""

import importlib.util
import json
import os
import sys
import tempfile
from typing import Any, Dict

import pytest

# Import the tool from the scripts directory
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

spec = importlib.util.spec_from_file_location(
  "api_spect_tool", os.path.join(os.path.dirname(__file__), '..', 'scripts', 'api-spec-tool.py')
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

  def test_find_differences(self: "TestAPISpecToolBasic") -> None:
    """Test finding differences between two objects."""
    obj1 = {"a": 1, "b": 2}
    obj2 = {"a": 1, "b": 3, "c": 4}

    differences = self.tool.find_differences(obj1, obj2)  # act

    # Should find changes and additions
    assert len(differences) > 0

    # Check for specific difference types
    diff_types = [diff['type'] for diff in differences]
    assert 'set_value' in diff_types or 'add_if_missing' in diff_types

  def test_create_fix_entry(self: "TestAPISpecToolBasic") -> None:
    """Test creating fix entries."""
    fix_entry = self.tool.create_fix_entry(  # act
      path="test|path",
      value="test_value",
      operation_type="set_value",
      description="Test fix"
    )

    assert fix_entry['path'] == "test|path"
    assert fix_entry['value'] == "test_value"
    assert fix_entry['type'] == "set_value"
    assert fix_entry['description'] == "Test fix"

  def test_path_exists(self: "TestAPISpecToolBasic") -> None:
    """Test path existence checking."""
    spec = {"test": {"nested": {"value": "test"}}}  # act

    assert self.tool.path_exists(spec, "test|nested|value")
    assert not self.tool.path_exists(spec, "test|nonexistent")
    assert not self.tool.path_exists(spec, "nonexistent|path")

  def test_get_value_at_spec_path(self: "TestAPISpecToolBasic") -> None:
    """Test getting values at spec paths."""
    spec = {"test": {"nested": {"value": "test"}}}  # act

    assert self.tool.get_value_at_spec_path(spec, "test|nested|value") == "test"
    assert self.tool.get_value_at_spec_path(spec, "test|nested") == {"value": "test"}

  def test_set_value_at_path(self: "TestAPISpecToolBasic") -> None:
    """Test setting values at spec paths."""
    spec: Dict[str, Any] = {"test": {"nested": {}}}

    self.tool.set_value_at_path(spec, "test|nested|new_key", "new_value")  # act

    assert spec["test"]["nested"]["new_key"] == "new_value"

  def test_set_value_at_path_with_array_index(self: "TestAPISpecToolBasic") -> None:
    """Test setting values at paths with array indices."""
    spec: Dict[str, Any] = {
      "paths": {
        "/test": {
          "get": {
            "parameters": [{
              "name": "param1",
              "schema": {
                "type": "string"
              }
            }, {
              "name": "param2",
              "schema": {
                "type": "string"
              }
            }, {
              "name": "param3",
              "schema": {
                "type": "string"
              }
            }]
          }
        }
      }
    }

    self.tool.set_value_at_path(spec, "paths|/test|get|parameters|1|schema|format", "uri")  # act

    assert spec["paths"]["/test"]["get"]["parameters"][1]["schema"]["format"] == "uri"

  def test_get_value_at_spec_path_with_array_index(self: "TestAPISpecToolBasic") -> None:
    """Test getting values at paths with array indices."""
    spec: Dict[str, Any] = {
      "paths": {
        "/test": {
          "get": {
            "parameters": [{
              "name": "param1",
              "schema": {
                "type": "string"
              }
            }, {
              "name": "param2",
              "schema": {
                "type": "string",
                "format": "uri"
              }
            }, {
              "name": "param3",
              "schema": {
                "type": "string"
              }
            }]
          }
        }
      }
    }

    result = self.tool.get_value_at_spec_path(spec, "paths|/test|get|parameters|1|schema|format")  # act

    assert result == "uri"

  def test_path_exists_with_array_index(self: "TestAPISpecToolBasic") -> None:
    """Test path existence checking with array indices."""
    spec: Dict[str, Any] = {
      "paths": {
        "/test": {
          "get": {
            "parameters": [{
              "name": "param1",
              "schema": {
                "type": "string"
              }
            }, {
              "name": "param2",
              "schema": {
                "type": "string",
                "format": "uri"
              }
            }]
          }
        }
      }
    }

    # act
    assert self.tool.path_exists(spec, "paths|/test|get|parameters|1|schema|format")
    assert not self.tool.path_exists(spec, "paths|/test|get|parameters|2|schema|format")
    assert not self.tool.path_exists(spec, "paths|/test|get|parameters|1|schema|nonexistent")

  def test_apply_path_operations_set_value(self: "TestAPISpecToolBasic") -> None:
    """Test applying set_value operations."""
    spec = {"test": {"nested": {"value": "old"}}}
    fixes = {"operations": [{"type": "set_value", "path": "test|nested|value", "value": "new", "description": "Update value"}]}

    successful_changes, skipped_changes = self.tool.apply_path_operations(spec, fixes)  # act

    assert len(successful_changes) > 0
    assert "Updated value" in successful_changes[0]
    assert spec["test"]["nested"]["value"] == "new"

  def test_apply_path_operations_set_value_with_array_index(self: "TestAPISpecToolBasic") -> None:
    """Test applying set_value operations with array indices."""
    spec: Dict[str, Any] = {
      "paths": {
        "/test": {
          "get": {
            "parameters": [{
              "name": "param1",
              "schema": {
                "type": "string"
              }
            }, {
              "name": "param2",
              "schema": {
                "type": "string",
                "format": "url"
              }
            }, {
              "name": "param3",
              "schema": {
                "type": "string"
              }
            }]
          }
        }
      }
    }
    fixes = {
      "operations": [{
        "type": "set_value",
        "path": "paths|/test|get|parameters|1|schema|format",
        "value": "uri",
        "description": "Update URL format to URI"
      }]
    }

    successful_changes, skipped_changes = self.tool.apply_path_operations(spec, fixes)  # act

    assert len(successful_changes) > 0
    assert "Updated value" in successful_changes[0]
    assert spec["paths"]["/test"]["get"]["parameters"][1]["schema"]["format"] == "uri"

  def test_apply_path_operations_add_if_missing(self: "TestAPISpecToolBasic") -> None:
    """Test applying add_if_missing operations."""
    spec = {"test": {"existing": "value"}}
    fixes = {"operations": [{"type": "add_if_missing", "path": "test|new_key", "value": "new_value", "description": "Add new key"}]}

    successful_changes, skipped_changes = self.tool.apply_path_operations(spec, fixes)  # act

    assert len(successful_changes) > 0
    assert "Added missing" in successful_changes[0]
    assert spec["test"]["new_key"] == "new_value"

  def test_apply_path_operations_delete_value(self: "TestAPISpecToolBasic") -> None:
    """Test applying delete_value operations."""
    spec = {"test": {"to_delete": "value", "keep": "value"}}
    fixes = {"operations": [{"type": "delete_value", "path": "test|to_delete", "description": "Delete key"}]}

    successful_changes, skipped_changes = self.tool.apply_path_operations(spec, fixes)  # act

    assert len(successful_changes) > 0
    assert "Deleted value" in successful_changes[0]
    assert "to_delete" not in spec["test"]
    assert "keep" in spec["test"]

  def test_get_existing_spec_fix_paths_v2_format(  # noqa: AAA01
    self: "TestAPISpecToolBasic"
  ) -> None:
    """Test getting existing spec fix paths from v2 format."""
    v2_fixes = {
      "version": "2.0",
      "operations": [{
        "path": "test|path1",
        "type": "set_value"
      }, {
        "path": "test|path2",
        "type": "add_if_missing"
      }]
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:  # act
      json.dump(v2_fixes, f)
      temp_file = f.name

    try:
      paths = self.tool.get_existing_spec_fix_paths(temp_file)
      assert "test|path1" in paths
      assert "test|path2" in paths
    finally:
      os.unlink(temp_file)

  def test_get_existing_spec_fix_paths_file_not_found(self: "TestAPISpecToolBasic") -> None:
    """Test getting existing spec fix paths when file doesn't exist."""
    paths = self.tool.get_existing_spec_fix_paths("nonexistent.json")  # act

    assert paths == set()

  def test_rename_key_at_path(self: "TestAPISpecToolBasic") -> None:
    """Test renaming keys at paths."""
    spec = {"test": {"old_key": "value"}}

    success = self.tool.rename_key_at_path(spec, "test", "old_key", "new_key")  # act

    assert success
    assert "new_key" in spec["test"]
    assert "old_key" not in spec["test"]
    assert spec["test"]["new_key"] == "value"

  def test_rename_key_at_path_not_found(self: "TestAPISpecToolBasic") -> None:
    """Test renaming keys when the key doesn't exist."""
    spec = {"test": {"existing_key": "value"}}

    success = self.tool.rename_key_at_path(spec, "test", "nonexistent", "new_key")  # act

    assert not success
    assert "existing_key" in spec["test"]
    assert "new_key" not in spec["test"]

  def test_modify_array_element(self: "TestAPISpecToolBasic") -> None:
    """Test modifying array elements."""
    spec = {"test": {"items": [{"name": "item1", "value": "old"}, {"name": "item2", "value": "keep"}]}}
    match_criteria = {"name": "item1"}
    modifications = {"value": "new"}

    success = self.tool.modify_array_element(  # act
      spec, "test|items", match_criteria, modifications
    )

    assert success
    assert spec["test"]["items"][0]["value"] == "new"
    assert spec["test"]["items"][1]["value"] == "keep"

  def test_modify_array_element_not_found(self: "TestAPISpecToolBasic") -> None:
    """Test modifying array elements when no match is found."""
    spec = {"test": {"items": [{"name": "item1", "value": "old"}]}}
    match_criteria = {"name": "nonexistent"}
    modifications = {"value": "new"}

    success = self.tool.modify_array_element(  # act
      spec, "test|items", match_criteria, modifications
    )

    assert not success
    assert spec["test"]["items"][0]["value"] == "old"

  def test_full_workflow_integration(self: "TestAPISpecToolBasic") -> None:
    """Test a complete workflow from analysis to fix application."""
    # Create test data
    original_spec = {
      "openapi": "3.0.0",
      "info": {
        "title": "Test API",
        "version": "1.0.0"
      },
      "paths": {
        "/test": {
          "get": {
            "responses": {
              "200": {
                "description": "Success"
              }
            }
          }
        }
      }
    }
    fixed_spec = {
      "openapi": "3.0.0",
      "info": {
        "title": "Test API",
        "version": "1.0.0"
      },
      "paths": {
        "/test": {
          "get": {
            "responses": {
              "200": {
                "description": "Success",
                "content": {
                  "application/json": {
                    "schema": {
                      "type": "object"
                    }
                  }
                }
              }
            }
          }
        }
      }
    }

    differences = self.tool.find_differences(original_spec, fixed_spec)  # act

    assert len(differences) > 0

    # Create fix entries
    fixes = {
      "operations": [
        self.tool.create_fix_entry(
          diff['path'], diff.get('value'), diff['type'], diff.get('old_value'), diff.get('description', '')
        ) for diff in differences
      ]
    }

    # Apply fixes
    test_spec = original_spec.copy()
    successful_changes, skipped_changes = self.tool.apply_path_operations(test_spec, fixes)

    # Verify changes were applied
    assert len(successful_changes) > 0
    # The exact structure might vary, but we should have some changes
    assert "/test" in test_spec["paths"]


if __name__ == '__main__':
  pytest.main([__file__])
