"""Tests for API Specification Tool quiet mode and exit codes."""

import importlib.util
import json
import os
import subprocess
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


class TestQuietModeFunctionality:
  """Test cases for quiet mode functionality."""

  def setup_method(self: "TestQuietModeFunctionality") -> None:
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

  def test_analyze_command_quiet_mode(self: "TestQuietModeFunctionality") -> None:
    """Test analyze command in quiet mode."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
      json.dump(self.sample_swagger_data, f)
      temp_file = f.name

    try:
      result = subprocess.run([  # act
        sys.executable,
        os.path.join(os.path.dirname(__file__), '..', 'upstream', 'api-spec-tool.py'),
        'analyze', '-q', temp_file
      ],
                              capture_output=True,
                              text=True)

      # Should exit with success code
      assert result.returncode == 0

      # Should only print the concise summary, not verbose output
      assert "API Analysis Complete: 1 endpoints found" in result.stdout
      assert "API Analysis Complete" not in result.stdout or result.stdout.count("API Analysis Complete") == 1

      # Should not contain verbose analysis details
      assert "API Info:" not in result.stdout
      assert "Authentication:" not in result.stdout
      assert "Server Info:" not in result.stdout

    finally:
      os.unlink(temp_file)

  def test_analyze_command_verbose_mode(self: "TestQuietModeFunctionality") -> None:
    """Test analyze command in verbose mode (default)."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
      json.dump(self.sample_swagger_data, f)
      temp_file = f.name

    try:
      result = subprocess.run([  # act
        sys.executable,
        os.path.join(os.path.dirname(__file__), '..', 'upstream', 'api-spec-tool.py'),
        'analyze', temp_file
      ],
                              capture_output=True,
                              text=True)

      # Should exit with success code
      assert result.returncode == 0

      # Should contain verbose analysis details
      assert "📋 API INFORMATION:" in result.stdout
      assert "🔐 AUTHENTICATION:" in result.stdout
      assert "🌐 SERVER CONFIGURATION:" in result.stdout

    finally:
      os.unlink(temp_file)

  def test_extract_command_quiet_mode(self: "TestQuietModeFunctionality") -> None:
    """Test extract command in quiet mode."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
      json.dump(self.sample_swagger_data, f)
      temp_file = f.name

    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as output_file:
      output_path = output_file.name

    try:
      result = subprocess.run([  # act
        sys.executable,
        os.path.join(os.path.dirname(__file__), '..', 'upstream', 'api-spec-tool.py'),
        'extract', '-q', temp_file, '-o', output_path
      ],
                              capture_output=True,
                              text=True)

      # Should exit with success code
      assert result.returncode == 0

      # Should not print success message in quiet mode
      assert "Routes extracted and saved to:" not in result.stdout

      # Should still create the output file
      assert os.path.exists(output_path)

    finally:
      os.unlink(temp_file)
      if os.path.exists(output_path):
        os.unlink(output_path)

  def test_extract_command_verbose_mode(self: "TestQuietModeFunctionality") -> None:
    """Test extract command in verbose mode (default)."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
      json.dump(self.sample_swagger_data, f)
      temp_file = f.name

    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as output_file:
      output_path = output_file.name

    try:
      result = subprocess.run([  # act
        sys.executable,
        os.path.join(os.path.dirname(__file__), '..', 'upstream', 'api-spec-tool.py'),
        'extract', temp_file, '-o', output_path
      ],
                              capture_output=True,
                              text=True)

      # Should exit with success code
      assert result.returncode == 0

      # Should print success message in verbose mode
      assert "Routes extracted and saved to:" in result.stdout

    finally:
      os.unlink(temp_file)
      if os.path.exists(output_path):
        os.unlink(output_path)


class TestExitCodes:
  """Test cases for exit codes."""

  def test_success_exit_code(self: "TestExitCodes") -> None:
    """Test that successful operations return exit code 0."""
    sample_data = {"openapi": "3.0.0", "info": {"title": "Test API", "version": "1.0.0"}, "paths": {}}

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
      json.dump(sample_data, f)
      temp_file = f.name

    try:
      result = subprocess.run([  # act
        sys.executable,
        os.path.join(os.path.dirname(__file__), '..', 'upstream', 'api-spec-tool.py'),
        'analyze', temp_file
      ],
                              capture_output=True,
                              text=True)

      assert result.returncode == 0

    finally:
      os.unlink(temp_file)

  def test_general_error_exit_code_file_not_found(self: "TestExitCodes") -> None:
    """Test that file not found errors return exit code 1."""
    result = subprocess.run([  # act
      sys.executable,
      os.path.join(os.path.dirname(__file__), '..', 'upstream', 'api-spec-tool.py'),
      'analyze', 'nonexistent.json'
    ],
                            capture_output=True,
                            text=True)

    assert result.returncode == 1

  def test_general_error_exit_code_quiet_mode(self: "TestExitCodes") -> None:
    """Test that file not found errors return exit code 1 in quiet mode."""
    result = subprocess.run([  # act
      sys.executable,
      os.path.join(os.path.dirname(__file__), '..', 'upstream', 'api-spec-tool.py'),
      'analyze', '-q', 'nonexistent.json'
    ],
                            capture_output=True,
                            text=True)

    assert result.returncode == 1
    # In quiet mode, should not print error message
    assert "Error: File not found:" not in result.stdout
    assert "Error: File not found:" not in result.stderr

  def test_analysis_error_exit_code_invalid_json(self: "TestExitCodes") -> None:
    """Test that invalid JSON errors return exit code 2."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
      f.write("invalid json content")
      temp_file = f.name

    try:
      result = subprocess.run([  # act
        sys.executable,
        os.path.join(os.path.dirname(__file__), '..', 'upstream', 'api-spec-tool.py'),
        'analyze', temp_file
      ],
                              capture_output=True,
                              text=True)

      assert result.returncode == 2

    finally:
      os.unlink(temp_file)

  def test_analysis_error_exit_code_quiet_mode(self: "TestExitCodes") -> None:
    """Test that invalid JSON errors return exit code 2 in quiet mode."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
      f.write("invalid json content")
      temp_file = f.name

    try:
      result = subprocess.run([  # act
        sys.executable,
        os.path.join(os.path.dirname(__file__), '..', 'upstream', 'api-spec-tool.py'),
        'analyze', '-q', temp_file
      ],
                              capture_output=True,
                              text=True)

      assert result.returncode == 2
      # In quiet mode, should not print error message
      assert "Error: Invalid JSON:" not in result.stdout
      assert "Error: Invalid JSON:" not in result.stderr

    finally:
      os.unlink(temp_file)

  def test_analysis_error_exit_code_non_dict_json(self: "TestExitCodes") -> None:
    """Test that non-dictionary JSON errors return exit code 3."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
      json.dump(["not", "a", "dict"], f)
      temp_file = f.name

    try:
      result = subprocess.run([  # act
        sys.executable,
        os.path.join(os.path.dirname(__file__), '..', 'upstream', 'api-spec-tool.py'),
        'analyze', temp_file
      ],
                              capture_output=True,
                              text=True)

      assert result.returncode == 3

    finally:
      os.unlink(temp_file)

  def test_no_command_exit_code(self: "TestExitCodes") -> None:
    """Test that no command provided returns exit code 1."""
    result = subprocess.run(
      [  # act
        sys.executable, os.path.join(os.path.dirname(__file__), '..', 'upstream', 'api-spec-tool.py')
      ],
      capture_output=True,
      text=True
    )

    assert result.returncode == 1

  def test_invalid_command_exit_code(self: "TestExitCodes") -> None:
    """Test that invalid command returns exit code 2."""
    result = subprocess.run(
      [  # act
        sys.executable,
        os.path.join(os.path.dirname(__file__), '..', 'upstream', 'api-spec-tool.py'), 'invalid_command'
      ],
      capture_output=True,
      text=True
    )

    assert result.returncode == 2

  def test_help_command_exit_code(self: "TestExitCodes") -> None:
    """Test that help command returns exit code 0."""
    result = subprocess.run(
      [  # act
        sys.executable,
        os.path.join(os.path.dirname(__file__), '..', 'upstream', 'api-spec-tool.py'), '--help'
      ],
      capture_output=True,
      text=True
    )

    assert result.returncode == 0

  def test_subcommand_help_exit_code(self: "TestExitCodes") -> None:
    """Test that subcommand help returns exit code 0."""
    result = subprocess.run(
      [  # act
        sys.executable,
        os.path.join(os.path.dirname(__file__), '..', 'upstream', 'api-spec-tool.py'), 'analyze', '--help'
      ],
      capture_output=True,
      text=True
    )

    assert result.returncode == 0


class TestQuietModeErrorHandling:
  """Test cases for error handling in quiet mode."""

  def test_quiet_mode_suppresses_all_error_messages(self: "TestQuietModeErrorHandling") -> None:
    """Test that quiet mode suppresses all error messages."""
    result = subprocess.run([  # act
      sys.executable,
      os.path.join(os.path.dirname(__file__), '..', 'upstream', 'api-spec-tool.py'),
      'analyze', '-q', 'nonexistent.json'
    ],
                            capture_output=True,
                            text=True)

    assert result.returncode == 1
    assert result.stdout == ""
    assert result.stderr == ""

  def test_quiet_mode_suppresses_json_error_messages(self: "TestQuietModeErrorHandling") -> None:
    """Test that quiet mode suppresses JSON error messages."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
      f.write("invalid json")
      temp_file = f.name

    try:
      result = subprocess.run([  # act
        sys.executable,
        os.path.join(os.path.dirname(__file__), '..', 'upstream', 'api-spec-tool.py'),
        'analyze', '-q', temp_file
      ],
                              capture_output=True,
                              text=True)

      assert result.returncode == 2
      assert result.stdout == ""
      assert result.stderr == ""

    finally:
      os.unlink(temp_file)

  def test_verbose_mode_shows_error_messages(self: "TestQuietModeErrorHandling") -> None:
    """Test that verbose mode shows error messages."""
    result = subprocess.run([  # act
      sys.executable,
      os.path.join(os.path.dirname(__file__), '..', 'upstream', 'api-spec-tool.py'),
      'analyze', 'nonexistent.json'
    ],
                            capture_output=True,
                            text=True)

    assert result.returncode == 1
    assert "Error: File not found:" in result.stderr

  def test_quiet_mode_still_creates_output_files(self: "TestQuietModeErrorHandling") -> None:
    """Test that quiet mode still creates output files when successful."""
    sample_data = {
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

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
      json.dump(sample_data, f)
      temp_file = f.name

    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as output_file:
      output_path = output_file.name

    try:
      result = subprocess.run([  # act
        sys.executable,
        os.path.join(os.path.dirname(__file__), '..', 'upstream', 'api-spec-tool.py'),
        'extract', '-q', temp_file, '-o', output_path
      ],
                              capture_output=True,
                              text=True)

      assert result.returncode == 0
      assert os.path.exists(output_path)

      # Verify the file was created and has content
      with open(output_path, 'r') as f:
        content = f.read()
        assert len(content) > 0

    finally:
      os.unlink(temp_file)
      if os.path.exists(output_path):
        os.unlink(output_path)


if __name__ == '__main__':
  pytest.main([__file__])
