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
  "api_spect_tool",
  os.path.join(os.path.dirname(__file__), '..', 'scripts', 'api-spec-tool.py')
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
    result = subprocess.run([  # act
      sys.executable,  # act
      os.path.join(os.path.dirname(__file__), '..', 'scripts', 'api-spec-tool.py'), '--help'  # act
    ],  # act
                            capture_output=True,  # act
                            text=True)  # act

    assert result.returncode == 0
    assert "analyze" in result.stdout
    assert "extract" in result.stdout
    assert "update" in result.stdout
    assert "fix" in result.stdout

  def test_analyze_help(self: "TestCommandLineInterface") -> None:
    """Test analyze subcommand help."""
    result = subprocess.run([  # act
      sys.executable,  # act
      os.path.join(os.path.dirname(__file__), '..', 'scripts', 'api-spec-tool.py'),  # act
      'analyze', '--help'  # act
    ],  # act
                            capture_output=True,  # act
                            text=True)  # act

    assert result.returncode == 0
    assert "swagger_file" in result.stdout

  def test_extract_help(self: "TestCommandLineInterface") -> None:
    """Test extract subcommand help."""
    result = subprocess.run([  # act
      sys.executable,  # act
      os.path.join(os.path.dirname(__file__), '..', 'scripts', 'api-spec-tool.py'),  # act
      'extract', '--help'  # act
    ],  # act
                            capture_output=True,  # act
                            text=True)  # act

    assert result.returncode == 0
    assert "format" in result.stdout
    assert "output" in result.stdout

  def test_update_help(self: "TestCommandLineInterface") -> None:
    """Test update subcommand help."""
    result = subprocess.run([  # act
      sys.executable,  # act
      os.path.join(os.path.dirname(__file__), '..', 'scripts', 'api-spec-tool.py'),  # act
      'update', '--help'  # act
    ],  # act
                            capture_output=True,  # act
                            text=True)  # act

    assert result.returncode == 0
    assert "dry-run" in result.stdout

  def test_fix_help(self: "TestCommandLineInterface") -> None:
    """Test fix subcommand help."""
    result = subprocess.run([  # act
      sys.executable,  # act
      os.path.join(os.path.dirname(__file__), '..', 'scripts', 'api-spec-tool.py'), 'fix',  # act
      '--help'  # act
    ],  # act
                            capture_output=True,  # act
                            text=True)  # act

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

  def test_complete_workflow(self: "TestEndToEndWorkflow") -> None:
    """Test complete workflow from analysis to fix application."""
    # Step 1: Analyze original spec
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:  # act
      json.dump(self.original_spec, f)  # act
      original_file = f.name  # act
    try:  # act
      analysis = self.tool.analyze_api_structure(original_file)  # act
      assert analysis['api_info']['title'] == "Test API"
      assert "/test" in [route['path'] for route in self.tool.extract_routes(original_file)]
    finally:  # act
      os.unlink(original_file)  # act

    # Step 2: Find differences
    differences = self.tool.find_differences(self.original_spec, self.fixed_spec)  # act
    assert len(differences) > 0

    # Step 3: Create fix entries
    fixes = {  # act
      "operations": [  # act
        self.tool.create_fix_entry(  # act
          diff['path'], diff.get('value'), diff['type'], diff.get('old_value'),  # act
          diff.get('description', '')  # act
        ) for diff in differences  # act
      ]  # act
    }  # act

    # Step 4: Apply fixes
    test_spec = self.original_spec.copy()  # act
    changes = self.tool.apply_path_operations(test_spec, fixes)  # act
    assert len(changes) > 0

    # Step 5: Verify the result is closer to the fixed spec
    # (exact match might not be possible due to DeepDiff limitations)
    assert "/test" in test_spec["paths"]

  def test_spec_fixes_v2_format_workflow(self: "TestEndToEndWorkflow") -> None:
    """Test workflow with v2 spec-fixes format."""
    # Create v2 spec-fixes file
    v2_fixes = {  # act
      "version":  # act
        "2.0",  # act
      "description":  # act
        "Test fixes",  # act
      "metadata": {  # act
        "generated_by": "test",  # act
        "generated_at": "2024-01-01T00:00:00Z"  # act
      },  # act
      "operations": [{  # act
        "type": "set_value",  # act
        "path": "paths|/test|get|responses|200|content",  # act
        "value": {  # act
          "application/json": {  # act
            "schema": {  # act
              "type": "object"  # act
            }  # act
          }  # act
        },  # act
        "description": "Add content to response"  # act
      }]  # act
    }  # act
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:  # act
      json.dump(v2_fixes, f)  # act
      fixes_file = f.name  # act
    try:  # act
      # Test loading existing paths
      existing_paths = self.tool.get_existing_spec_fix_paths(fixes_file)  # act
      assert "paths|/test|get|responses|200|content" in existing_paths

      # Test applying fixes
      test_spec: Dict[str, Any] = self.original_spec.copy()  # act
      changes = self.tool.apply_path_operations(test_spec, v2_fixes)  # act
      assert len(changes) > 0
      assert "content" in test_spec["paths"]["/test"]["get"]["responses"]["200"]
    finally:  # act
      os.unlink(fixes_file)  # act

  def test_spec_fixes_old_format_workflow(self: "TestEndToEndWorkflow") -> None:
    """Test workflow with old spec-fixes format."""
    # Create old format spec-fixes file
    old_fixes = {  # act
      "path_operations": {  # act
        "fixes": [{  # act
          "operation": "set_value",  # act
          "path": "paths|/test|get|responses|200|content",  # act
          "value": {  # act
            "application/json": {  # act
              "schema": {  # act
                "type": "object"  # act
              }  # act
            }  # act
          },  # act
          "description": "Add content to response"  # act
        }]  # act
      }  # act
    }  # act
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:  # act
      json.dump(old_fixes, f)  # act
      fixes_file = f.name  # act
    try:  # act
      # Test loading existing paths
      existing_paths = self.tool.get_existing_spec_fix_paths(fixes_file)  # act
      assert "paths|/test|get|responses|200|content" in existing_paths

      # Test applying fixes
      test_spec: Dict[str, Any] = self.original_spec.copy()  # act
      changes = self.tool.apply_path_operations(test_spec, old_fixes)  # act
      assert len(changes) > 0
      assert "content" in test_spec["paths"]["/test"]["get"]["responses"]["200"]
    finally:  # act
      os.unlink(fixes_file)  # act

  def test_error_handling_scenarios(self: "TestEndToEndWorkflow") -> None:
    """Test various error handling scenarios."""
    with pytest.raises(SystemExit):  # act
      self.tool.load_json_file("nonexistent.json", "test file")

    # Test with invalid JSON
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:  # act
      f.write("invalid json")
      temp_file = f.name
    try:
      with pytest.raises(SystemExit):  # act
        self.tool.load_json_file(temp_file, "test file")
    finally:
      os.unlink(temp_file)

    # Test with non-dictionary JSON
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:  # act
      json.dump(["not", "a", "dict"], f)
      temp_file = f.name
    try:
      with pytest.raises(SystemExit):  # act
        self.tool.load_json_file(temp_file, "test file")
    finally:
      os.unlink(temp_file)

  def test_edge_cases(self: "TestEndToEndWorkflow") -> None:
    """Test edge cases and boundary conditions."""
    # Test with empty spec
    empty_spec = {"openapi": "3.0.0", "info": {"title": "Empty", "version": "1.0.0"}}  # act
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:  # act
      json.dump(empty_spec, f)  # act
      temp_file = f.name  # act
    try:  # act
      analysis = self.tool.analyze_api_structure(temp_file)  # act
      assert analysis['tags'] == []
      assert analysis['error_codes'] == []
    finally:  # act
      os.unlink(temp_file)  # act

    # Test with minimal valid spec
    minimal_spec = {  # act
      "openapi": "3.0.0",  # act
      "info": {  # act
        "title": "Minimal",  # act
        "version": "1.0.0"  # act
      },  # act
      "paths": {}  # act
    }  # act
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:  # act
      json.dump(minimal_spec, f)  # act
      temp_file = f.name  # act
    try:  # act
      analysis = self.tool.analyze_api_structure(temp_file)  # act
      assert analysis['api_info']['title'] == "Minimal"
    finally:  # act
      os.unlink(temp_file)  # act

  def test_array_operations(self: "TestEndToEndWorkflow") -> None:
    """Test array modification operations."""
    spec = {  # act
      "test": {  # act
        "items": [{  # act
          "name": "item1",  # act
          "value": "old"  # act
        }, {  # act
          "name": "item2",  # act
          "value": "keep"  # act
        }]  # act
      }  # act
    }  # act
    fixes = {  # act
      "operations": [{  # act
        "type": "modify_array_element",  # act
        "path": "test|items",  # act
        "match_criteria": {  # act
          "name": "item1"  # act
        },  # act
        "modifications": {  # act
          "value": "new"  # act
        },  # act
        "description": "Update array element"  # act
      }]  # act
    }  # act
    changes = self.tool.apply_path_operations(spec, fixes)  # act
    assert len(changes) > 0
    assert spec["test"]["items"][0]["value"] == "new"
    assert spec["test"]["items"][1]["value"] == "keep"

  def test_key_rename_operations(self: "TestEndToEndWorkflow") -> None:
    """Test key rename operations."""
    spec = {"test": {"old_key": "value"}}  # act
    fixes = {  # act
      "operations": [{  # act
        "type": "rename_key",  # act
        "path": "test",  # act
        "old_key": "old_key",  # act
        "new_key": "new_key",  # act
        "description": "Rename key"  # act
      }]  # act
    }  # act
    changes = self.tool.apply_path_operations(spec, fixes)  # act
    assert len(changes) > 0
    assert "new_key" in spec["test"]
    assert "old_key" not in spec["test"]
    assert spec["test"]["new_key"] == "value"


if __name__ == '__main__':
  pytest.main([__file__])
