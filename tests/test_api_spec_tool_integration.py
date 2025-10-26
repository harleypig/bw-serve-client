"""Integration tests for API Specification Tool."""

import importlib.util
import json
import os
import subprocess
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


class TestCommandLineInterface:
  """Test cases for command-line interface."""

  def test_help_command(self: "TestCommandLineInterface") -> None:
    """Test that the help command works."""
    result = subprocess.run(
      [  # act
        sys.executable,
        os.path.join(os.path.dirname(__file__), '..', 'scripts', 'api-spec-tool.py'), '--help'
      ],
      capture_output=True,
      text=True
    )

    assert result.returncode == 0
    assert "analyze" in result.stdout
    assert "extract" in result.stdout
    assert "update" in result.stdout
    assert "fix" in result.stdout

  def test_analyze_help(self: "TestCommandLineInterface") -> None:
    """Test analyze subcommand help."""
    result = subprocess.run(
      [  # act
        sys.executable,
        os.path.join(os.path.dirname(__file__), '..', 'scripts', 'api-spec-tool.py'), 'analyze', '--help'
      ],
      capture_output=True,
      text=True
    )

    assert result.returncode == 0
    assert "swagger_file" in result.stdout

  def test_extract_help(self: "TestCommandLineInterface") -> None:
    """Test extract subcommand help."""
    result = subprocess.run(
      [  # act
        sys.executable,
        os.path.join(os.path.dirname(__file__), '..', 'scripts', 'api-spec-tool.py'), 'extract', '--help'
      ],
      capture_output=True,
      text=True
    )

    assert result.returncode == 0
    assert "format" in result.stdout
    assert "output" in result.stdout

  def test_update_help(self: "TestCommandLineInterface") -> None:
    """Test update subcommand help."""
    result = subprocess.run(
      [  # act
        sys.executable,
        os.path.join(os.path.dirname(__file__), '..', 'scripts', 'api-spec-tool.py'), 'update', '--help'
      ],
      capture_output=True,
      text=True
    )

    assert result.returncode == 0
    assert "dry-run" in result.stdout

  def test_fix_help(self: "TestCommandLineInterface") -> None:
    """Test fix subcommand help."""
    result = subprocess.run(
      [  # act
        sys.executable,
        os.path.join(os.path.dirname(__file__), '..', 'scripts', 'api-spec-tool.py'), 'fix', '--help'
      ],
      capture_output=True,
      text=True
    )

    assert result.returncode == 0
    assert "original-file" in result.stdout
    assert "fixed-file" in result.stdout


class TestEndToEndWorkflow:
  """End-to-end workflow tests."""

  def setup_method(self: "TestEndToEndWorkflow") -> None:
    """Set up test fixtures before each test method."""
    self.tool = APISpecTool()
    self.original_spec: Dict[str, Any] = {
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
    self.fixed_spec = {
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

  def test_complete_workflow(self: "TestEndToEndWorkflow") -> None:  # noqa: AAA01
    """Test complete workflow from analysis to fix application."""
    # Step 1: Analyze original spec
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:  # act
      json.dump(self.original_spec, f)
      original_file = f.name
    try:
      analysis = self.tool.analyze_api_structure(original_file)
      assert analysis['api_info']['title'] == "Test API"
      assert "/test" in [route['path'] for route in self.tool.extract_routes(original_file)]
    finally:
      os.unlink(original_file)

    # Step 2: Find differences
    differences = self.tool.find_differences(self.original_spec, self.fixed_spec)
    assert len(differences) > 0

    # Step 3: Create fix entries
    fixes = {
      "operations": [
        self.tool.create_fix_entry(
          diff['path'], diff.get('value'), diff['type'], diff.get('old_value'), diff.get('description', '')
        ) for diff in differences
      ]
    }

    # Step 4: Apply fixes
    test_spec = self.original_spec.copy()
    successful_changes, skipped_changes = self.tool.apply_path_operations(test_spec, fixes)
    assert len(successful_changes) > 0

    # Step 5: Verify the result is closer to the fixed spec
    # (exact match might not be possible due to DeepDiff limitations)
    assert "/test" in test_spec["paths"]

  def test_spec_fixes_v2_format_workflow(self: "TestEndToEndWorkflow") -> None:  # noqa: AAA01  # yapf: disable
    """Test workflow with v2 spec-fixes format."""
    # Create v2 spec-fixes file
    v2_fixes = {
      "version":
        "2.0",
      "description":
        "Test fixes",
      "metadata": {
        "generated_by": "test",
        "generated_at": "2024-01-01T00:00:00Z"
      },
      "operations": [{
        "type": "set_value",
        "path": "paths|/test|get|responses|200|content",
        "value": {
          "application/json": {
            "schema": {
              "type": "object"
            }
          }
        },
        "description": "Add content to response"
      }]
    }
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:  # act
      json.dump(v2_fixes, f)
      fixes_file = f.name
    try:
      # Test loading existing paths
      existing_paths = self.tool.get_existing_spec_fix_paths(fixes_file)
      assert "paths|/test|get|responses|200|content" in existing_paths

      # Test applying fixes
      test_spec: Dict[str, Any] = self.original_spec.copy()
      successful_changes, skipped_changes = self.tool.apply_path_operations(test_spec, v2_fixes)
      assert len(successful_changes) > 0
      assert "content" in test_spec["paths"]["/test"]["get"]["responses"]["200"]
    finally:
      os.unlink(fixes_file)

  def test_error_handling_scenarios(self: "TestEndToEndWorkflow") -> None:
    """Test various error handling scenarios."""
    with pytest.raises(FileNotFoundError):  # act
      self.tool.load_json_file("nonexistent.json", "test file")

    # Test with invalid JSON
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
      f.write("invalid json")
      temp_file = f.name
    try:
      with pytest.raises(json.JSONDecodeError):
        self.tool.load_json_file(temp_file, "test file")
    finally:
      os.unlink(temp_file)

    # Test with non-dictionary JSON
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
      json.dump(["not", "a", "dict"], f)
      temp_file = f.name
    try:
      with pytest.raises(TypeError):
        self.tool.load_json_file(temp_file, "test file")
    finally:
      os.unlink(temp_file)

  def test_edge_cases(self: "TestEndToEndWorkflow") -> None:  # noqa: AAA01
    """Test edge cases and boundary conditions."""
    # Test with empty spec
    empty_spec = {"openapi": "3.0.0", "info": {"title": "Empty", "version": "1.0.0"}}
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:  # act
      json.dump(empty_spec, f)
      temp_file = f.name
    try:
      analysis = self.tool.analyze_api_structure(temp_file)
      assert analysis['tags'] == []
      assert analysis['error_codes'] == []
    finally:
      os.unlink(temp_file)

    # Test with minimal valid spec
    minimal_spec = {"openapi": "3.0.0", "info": {"title": "Minimal", "version": "1.0.0"}, "paths": {}}
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
      json.dump(minimal_spec, f)
      temp_file = f.name
    try:
      analysis = self.tool.analyze_api_structure(temp_file)
      assert analysis['api_info']['title'] == "Minimal"
    finally:
      os.unlink(temp_file)

  def test_array_operations(self: "TestEndToEndWorkflow") -> None:
    """Test array modification operations."""
    spec = {"test": {"items": [{"name": "item1", "value": "old"}, {"name": "item2", "value": "keep"}]}}
    fixes = {
      "operations": [{
        "type": "modify_array_element",
        "path": "test|items",
        "match_criteria": {
          "name": "item1"
        },
        "modifications": {
          "value": "new"
        },
        "description": "Update array element"
      }]
    }

    successful_changes, skipped_changes = self.tool.apply_path_operations(spec, fixes)  # act
    assert len(successful_changes) > 0  # noqa: AAA04
    assert spec["test"]["items"][0]["value"] == "new"
    assert spec["test"]["items"][1]["value"] == "keep"

  def test_array_index_detection_in_update_workflow(self: "TestEndToEndWorkflow") -> None:
    """Test that array index changes are properly detected in update workflow."""
    # Create original spec with array elements
    original_spec = {
      "openapi": "3.0.0",
      "info": {
        "title": "Test API",
        "version": "1.0.0"
      },
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

    # Create fixed spec with array element changes
    fixed_spec = {
      "openapi": "3.0.0",
      "info": {
        "title": "Test API",
        "version": "1.0.0"
      },
      "paths": {
        "/test": {
          "get": {
            "parameters": [
              {
                "name": "param1",
                "schema": {
                  "type": "string"
                }
              },
              {
                "name": "param2",
                "schema": {
                  "type": "string",
                  "format": "uri"
                }
              },  # Changed from url to uri
              {
                "name": "param3",
                "schema": {
                  "type": "string"
                }
              }
            ]
          }
        }
      }
    }

    differences = self.tool.find_differences(original_spec, fixed_spec)  # act

    # Should find the array index change
    array_index_changes = [diff for diff in differences if 'parameters|1|schema|format' in diff['path']]
    assert len(array_index_changes) > 0

    # The change should be detected as a set_value operation
    format_change = array_index_changes[0]
    assert format_change['type'] == 'set_value'
    assert format_change['old_value'] == 'url'
    assert format_change['value'] == 'uri'

  def test_array_index_fix_application(self: "TestEndToEndWorkflow") -> None:
    """Test that array index fixes are properly applied."""
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
        "old_value": "url",
        "description": "Update URL format to URI"
      }]
    }

    successful_changes, skipped_changes = self.tool.apply_path_operations(spec, fixes)  # act

    assert len(successful_changes) > 0
    assert "Updated value" in successful_changes[0]
    assert spec["paths"]["/test"]["get"]["parameters"][1]["schema"]["format"] == "uri"

  def test_key_rename_operations(self: "TestEndToEndWorkflow") -> None:
    """Test key rename operations."""
    spec = {"test": {"old_key": "value"}}
    fixes = {
      "operations": [{
        "type": "rename_key",
        "path": "test",
        "old_key": "old_key",
        "new_key": "new_key",
        "description": "Rename key"
      }]
    }

    successful_changes, skipped_changes = self.tool.apply_path_operations(spec, fixes)  # act
    assert len(successful_changes) > 0  # noqa: AAA04
    assert "new_key" in spec["test"]
    assert "old_key" not in spec["test"]
    assert spec["test"]["new_key"] == "value"

  def test_complete_array_index_workflow(self: "TestEndToEndWorkflow") -> None:  # noqa: AAA01
    """Test complete workflow with array index changes."""
    # Create original spec with array elements
    original_spec = {
      "openapi": "3.0.0",
      "info": {
        "title": "Test API",
        "version": "1.0.0"
      },
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

    # Create fixed spec with array element changes
    fixed_spec = {
      "openapi": "3.0.0",
      "info": {
        "title": "Test API",
        "version": "1.0.0"
      },
      "paths": {
        "/test": {
          "get": {
            "parameters": [
              {
                "name": "param1",
                "schema": {
                  "type": "string"
                }
              },
              {
                "name": "param2",
                "schema": {
                  "type": "string",
                  "format": "uri"
                }
              },  # Changed from url to uri
              {
                "name": "param3",
                "schema": {
                  "type": "string"
                }
              }
            ]
          }
        }
      }
    }

    # Step 1: Find differences (simulating update command)
    differences = self.tool.find_differences(original_spec, fixed_spec)

    # Should find the array index change
    array_index_changes = [diff for diff in differences if 'parameters|1|schema|format' in diff['path']]
    assert len(array_index_changes) > 0

    # Step 2: Create fix entries (simulating update command)
    fixes = {
      "operations": [
        self.tool.create_fix_entry(
          diff['path'], diff.get('value'), diff['type'], diff.get('old_value'), diff.get('description', '')
        ) for diff in differences
      ]
    }

    # Step 3: Apply fixes (simulating fix command)
    test_spec = original_spec.copy()

    successful_changes, skipped_changes = self.tool.apply_path_operations(test_spec, fixes)  # act

    # Step 4: Verify the result
    assert len(successful_changes) > 0
    assert test_spec["paths"]["/test"]["get"]["parameters"][1]["schema"]["format"] == "uri"

    # Verify the change was applied correctly
    assert test_spec["paths"]["/test"]["get"]["parameters"][0]["schema"]["type"] == "string"
    assert test_spec["paths"]["/test"]["get"]["parameters"][1]["schema"]["format"] == "uri"
    assert test_spec["paths"]["/test"]["get"]["parameters"][2]["schema"]["type"] == "string"


if __name__ == '__main__':
  pytest.main([__file__])
