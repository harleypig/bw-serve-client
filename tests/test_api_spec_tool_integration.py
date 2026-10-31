"""Integration tests for API Specification Tool."""

import importlib.util
import json
import os
import subprocess
import sys
import tempfile

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


class TestCommandLineInterface:
  """Test cases for command-line interface."""

  def test_help_command(self: "TestCommandLineInterface") -> None:
    """Test that the help command works."""
    result = subprocess.run(
      [  # act
        sys.executable,
        os.path.join(os.path.dirname(__file__), '..', 'upstream', 'api-spec-tool.py'), '--help'
      ],
      capture_output=True,
      text=True
    )

    assert result.returncode == 0
    assert "{analyze,extract}" in result.stdout

  def test_analyze_help(self: "TestCommandLineInterface") -> None:
    """Test analyze subcommand help."""
    result = subprocess.run(
      [  # act
        sys.executable,
        os.path.join(os.path.dirname(__file__), '..', 'upstream', 'api-spec-tool.py'), 'analyze', '--help'
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
        os.path.join(os.path.dirname(__file__), '..', 'upstream', 'api-spec-tool.py'), 'extract', '--help'
      ],
      capture_output=True,
      text=True
    )

    assert result.returncode == 0
    assert "format" in result.stdout
    assert "output" in result.stdout


class TestLoadAndAnalyzeErrors:
  """Error handling and edge cases for loading and analyzing a spec."""

  def setup_method(self: "TestLoadAndAnalyzeErrors") -> None:
    """Set up test fixtures before each test method."""
    self.tool = APISpecTool()

  def test_error_handling_scenarios(self: "TestLoadAndAnalyzeErrors") -> None:
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

  def test_edge_cases(self: "TestLoadAndAnalyzeErrors") -> None:  # noqa: AAA01
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


if __name__ == '__main__':
  pytest.main([__file__])
