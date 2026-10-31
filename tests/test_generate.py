"""Tests for generating bw_serve_client/_generated/ (codegen/generate.py)."""

from __future__ import annotations

import ast
import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Any, Dict, TYPE_CHECKING

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "codegen"))

import generate  # noqa: E402 - importable only once codegen/ is on the path.

if TYPE_CHECKING:
  from pytest_mock import MockerFixture

DANGLING = {"$ref": "#/components/parameters/gone"}
NAMELESS = {"in": "query"}

LONG = "Lock your vault. This action will destroy the session key required to authorize requests to most endpoints, " * 3


def spec() -> Dict[str, Any]:
  """Build a small spec: a request-only schema, and response-only ones by ref and inline.

  Returns:
      Dict[str, Any]: The spec.
  """
  return {
    "paths": {
      "/object/folder": {
        "post": {
          "summary": "Add a folder.",
          "description": LONG,
          "requestBody": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/folder"
                }
              }
            }
          },
          "responses": {
            "200": {
              "content": {
                "application/json": {
                  "schema": {
                    "$ref": "#/components/schemas/status"
                  }
                }
              }
            }
          },
        },
        "x-ignored": {},
      },
      "/object/folder/{id}": {
        "delete": {
          "parameters": [{
            "name": "id",
            "in": "path",
            "required": True
          }, {
            "name": "force",
            "in": "query"
          }],
          "responses": {
            "200": {
              "content": {
                "application/json": {
                  "schema": {
                    "title": "DeletedSchema",
                    "properties": {
                      "ok": {
                        "type": "boolean"
                      }
                    }
                  }
                }
              }
            }
          },
        }
      },
    },
    "components": {
      "schemas": {
        "folder": {
          "title": "FolderSchema",
          "properties": {
            "name": {
              "type": "string"
            }
          }
        },
        "status": {
          "title": "StatusSchema",
          "properties": {
            "data": {
              "title": "StatusDataSchema",
              "properties": {
                "template": {
                  "$ref": "#/components/schemas/status"
                }
              }
            }
          },
        },
      }
    },
  }


def run_module(source: str) -> Dict[str, Any]:
  """Execute generated source and return its namespace.

  Arguments:
      source: The module's source.

  Returns:
      Dict[str, Any]: The module's globals.
  """
  with tempfile.TemporaryDirectory() as scratch:
    path = Path(scratch) / "generated_under_test.py"
    path.write_text(source, encoding="utf-8")
    found = importlib.util.spec_from_file_location(path.stem, path)
    assert found is not None
    assert found.loader is not None
    module = importlib.util.module_from_spec(found)

    # dataclasses looks the defining module up in sys.modules.
    sys.modules[path.stem] = module
    try:
      found.loader.exec_module(module)

    finally:
      del sys.modules[path.stem]

  return module.__dict__


class TestResponseModels:
  """Which models ignore unknown fields."""

  def test_only_response_models_are_named(self: TestResponseModels) -> None:
    """Response schemas, by ref, nested and inline, are named; request schemas are not."""
    assert generate.response_models(spec()) == ["DeletedSchema", "StatusDataSchema", "StatusSchema"]

  def test_untitled_response_object_stops_generation(self: TestResponseModels) -> None:
    """A response object with no title gets a name no override can match."""
    untitled = spec()
    del untitled["paths"]["/object/folder/{id}"]["delete"]["responses"]["200"]["content"]["application/json"]["schema"]["title"]

    with pytest.raises(generate.GenerateError, match="no title.*ok"):
      generate.response_models(untitled)

  def test_shared_model_stops_generation(self: TestResponseModels) -> None:
    """A model a request and a response both use has no answer under #22."""
    shared = spec()
    shared["paths"]["/object/folder"]["post"]["responses"]["200"]["content"]["application/json"]["schema"] = {
      "$ref": "#/components/schemas/folder"
    }

    with pytest.raises(generate.GenerateError, match="FolderSchema"):
      generate.response_models(shared)


class TestRoutes:
  """The route list module."""

  def test_every_operation_becomes_a_route(self: TestRoutes) -> None:
    """Method, path, parameters, summary and description carry over, in spec order."""
    namespace = run_module(generate.render_routes(spec()))

    routes = namespace["ROUTES"]
    parameter = namespace["Parameter"]
    assert [(route.method, route.path) for route in routes] == [("POST", "/object/folder"), ("DELETE", "/object/folder/{id}")]
    assert routes[0].summary == "Add a folder."
    assert routes[1].summary == ""
    assert routes[1].parameters == (parameter("id", "path", True), parameter("force", "query", False))
    assert namespace["__all__"] == ["Parameter", "Route", "ROUTES"]

  def test_long_text_round_trips(self: TestRoutes) -> None:
    """A description split across literals is the spec's text exactly."""
    source = generate.render_routes(spec())

    assert run_module(source)["ROUTES"][0].description == LONG
    assert max(len(line) for line in source.splitlines()) <= 132

  @pytest.mark.parametrize(
    "text", ["", "short", LONG, "a" * 300, "line one\nline two " * 20, "a\tb " * 40, "\n" * 100, "it's \\ \"q\" " * 30]
  )
  def test_literal_is_exact_and_fits(self: TestRoutes, text: str) -> None:
    """Any string, tabs and escapes included, evaluates back to itself in literals that fit."""
    source = generate.literal(text, "    ")

    assert ast.literal_eval(source.strip()) == text
    assert max(len(line) for line in source.splitlines()) <= generate.CHUNK + len("      ")

  def test_splits_between_words(self: TestRoutes) -> None:
    """Text of short words, escapes included, splits only at whitespace."""
    chunks = generate._chunks("it's \\ \"q\" " * 30)  # noqa: SF01 - the splitting rule is what is under test.

    assert len(chunks) > 1
    assert all(chunk.endswith(" ") for chunk in chunks[:-1])


class TestParameters:
  """Parameters from the path and the operation, with references resolved."""

  def test_path_level_and_references(self: TestParameters) -> None:
    """Path parameters come first, a reference resolves, and the operation's own replaces a same-named one."""
    raw = spec()
    item = raw["paths"]["/object/folder/{id}"]
    item["parameters"] = [{"name": "id", "in": "path", "description": "old"}, {"$ref": "#/components/parameters/session"}]
    raw["components"]["parameters"] = {"session": {"name": "session", "in": "header", "required": True}}

    found = generate.parameters(raw, "/object/folder/{id}", item["delete"])

    assert [(p["name"], p["in"], p.get("required")) for p in found] == [("id", "path", True), ("session", "header", True),
                                                                        ("force", "query", None)]

  @pytest.mark.parametrize(("parameter", "message"), [(DANGLING, "does not resolve"), (NAMELESS, "no name or location")])
  def test_bad_parameter_stops_generation(self: TestParameters, parameter: Dict[str, Any], message: str) -> None:
    """A dangling reference or a nameless parameter is a named error, not a crash."""
    raw = spec()
    raw["paths"]["/object/folder/{id}"]["parameters"] = [parameter]

    with pytest.raises(generate.GenerateError, match=message):
      generate.render_routes(raw)


class TestInit:
  """The package's __init__.py."""

  def test_reexports_models_and_routes(self: TestInit) -> None:
    """Every model and the route list are imported and listed in __all__."""
    source = generate.render_init(["FolderSchema", "StatusSchema"])

    assert "from .models import FolderSchema\n" in source
    assert "from .routes import ROUTES\n" in source
    assert source.endswith('__all__ = ["FolderSchema", "StatusSchema", "Parameter", "Route", "ROUTES"]\n')

  def test_name_clash_stops_generation(self: TestInit) -> None:
    """A model named like a route list export would shadow it."""
    with pytest.raises(generate.GenerateError, match="Route"):
      generate.render_init(["Route"])


class TestGenerateModels:
  """Running the generator and adding __all__."""

  @pytest.fixture
  def models(self: TestGenerateModels, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Point the models module into a temporary directory."""
    path = tmp_path / "models.py"
    monkeypatch.setattr(generate, "MODELS", path)
    return path

  def generator(self: TestGenerateModels, models: Path, code: int = 0) -> Any:
    """Stand in for datamodel-code-generator, writing two classes.

    Arguments:
        models: Where the generator writes.
        code: The exit code to return.

    Returns:
        Any: A replacement for subprocess.run.
    """

    def run(args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
      assert kwargs["cwd"] == generate.ROOT
      template = Path(args[args.index("--extra-template-data") + 1]).read_text(encoding="utf-8")
      models.write_text(f"# {template}\nclass FolderSchema:\n  pass\n\n\nclass StatusSchema:\n  pass\n", encoding="utf-8")
      return subprocess.CompletedProcess(args, code, "", "boom" if code else "")

    return run

  def test_overrides_reach_the_generator_and_all_is_added(self: TestGenerateModels, models: Path, mocker: MockerFixture) -> None:
    """The ignore overrides are passed in, and __all__ lists the classes in order."""
    mocker.patch.object(generate.subprocess, "run", side_effect=self.generator(models))

    names = generate.generate_models(["StatusSchema"])

    source = models.read_text(encoding="utf-8")
    assert names == ["FolderSchema", "StatusSchema"]
    assert """{"StatusSchema": {"config": {"extra": "'ignore'"}}}""" in source
    assert source.endswith('\n\n__all__ = ["FolderSchema", "StatusSchema"]\n')

  def test_override_for_a_missing_model_stops_generation(self: TestGenerateModels, models: Path, mocker: MockerFixture) -> None:
    """A response title with no generated class means its override did nothing."""
    mocker.patch.object(generate.subprocess, "run", side_effect=self.generator(models))

    with pytest.raises(generate.GenerateError, match="GoneSchema"):
      generate.generate_models(["GoneSchema"])

  def test_generator_failure_stops_generation(self: TestGenerateModels, models: Path, mocker: MockerFixture) -> None:
    """A failing generator is an error carrying its output."""
    mocker.patch.object(generate.subprocess, "run", side_effect=self.generator(models, code=1))

    with pytest.raises(generate.GenerateError, match="exited 1: boom"):
      generate.generate_models([])


class TestMain:
  """The command line."""

  def test_error_exits_1(
    self: TestMain, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
  ) -> None:
    """A spec that cannot be read exits 1 and says why."""
    monkeypatch.setattr(generate, "PATCHED_SPEC", tmp_path / "missing.json")

    assert generate.main() == 1
    assert "generate: error:" in capsys.readouterr().err
