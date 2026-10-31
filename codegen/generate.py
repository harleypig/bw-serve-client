#!/usr/bin/env python3

"""Generate ``bw_serve_client/_generated/`` from the patched spec.

Writes three modules, each with an ``__all__``:

- ``models.py``: the pydantic v2 models, by datamodel-code-generator, with
  its settings from ``pyproject.toml``.
- ``routes.py``: one ``Route`` per operation in the spec.
- ``__init__.py``: re-exports both.

Request models reject unknown fields and response models ignore them (#22).
``pyproject.toml`` sets ``forbid`` for every model, and this passes the
generator a per-class ``ignore`` for each model a response uses. A model both
a request and a response use has no answer under #22, so it stops the build.

Usage: ``python codegen/generate.py``. Exits 1, naming the reason, when it
cannot generate; the output is unformatted until ``pipeline.py build`` runs
the formatters over it.
"""

import ast
import json
from pathlib import Path
import re
import subprocess  # noqa: S404 - runs the code generator with fixed arguments. # nosec B404
import sys
import tempfile
from typing import Any, Dict, Iterator, List, Set, Tuple

ROOT = Path(__file__).resolve().parent.parent
PATCHED_SPEC = ROOT / "upstream" / "vault-management-api-fixed.json"
PACKAGE = ROOT / "bw_serve_client" / "_generated"
MODELS = PACKAGE / "models.py"
ROUTES = PACKAGE / "routes.py"
INIT = PACKAGE / "__init__.py"

METHODS = ("get", "put", "post", "delete", "patch")

# The method, the path, and the operation object.
Operation = Tuple[str, str, Dict[str, Any]]
SCHEMA_REF = "#/components/schemas/"
PARAMETER_REF = "#/components/parameters/"
ROUTE_EXPORTS = ["Parameter", "Route", "ROUTES"]

# The longest literal, quotes and escapes included. Long text is split into
# adjacent literals so no line runs past the 132-column code limit once yapf
# indents them.
CHUNK = 96

HEADER = '''"""{summary}

Generated from the patched OpenAPI spec by ``codegen/generate.py``.
DO NOT EDIT MANUALLY.
"""
'''

ROUTE_TYPES = '''

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class Parameter:
  """One parameter of a route.

  Attributes:
      name: The parameter's name in the spec.
      location: Where it goes: ``path``, ``query``, ``header`` or ``cookie``.
      required: Whether the route needs it.
  """

  name: str
  location: str
  required: bool


@dataclass(frozen=True)
class Route:
  """One operation in the spec.

  Attributes:
      method: The HTTP method, upper case.
      path: The path, with ``{name}`` parameters.
      parameters: The path, query and header parameters.
      summary: The spec's summary, or an empty string.
      description: The spec's description, or an empty string.
  """

  method: str
  path: str
  parameters: Tuple[Parameter, ...]
  summary: str
  description: str

'''


class GenerateError(Exception):
  """Generation could not finish."""


# -----------------------------------------------------------------------------
def operations(spec: Dict[str, Any]) -> Iterator[Operation]:
  """Yield every operation in the spec, in the spec's order.

  Arguments:
      spec: The patched spec.

  Yields:
      Operation: The method, the path and the operation.
  """
  for path, item in spec.get("paths", {}).items():
    for method, operation in item.items():
      if method in METHODS:
        yield method, path, operation


# -----------------------------------------------------------------------------
def parameters(spec: Dict[str, Any], path: str, operation: Dict[str, Any]) -> List[Dict[str, Any]]:
  """List an operation's parameters, with references resolved.

  Parameters declared on the path apply to every operation under it; one the
  operation declares with the same name and location replaces it.

  Arguments:
      spec: The patched spec.
      path: The operation's path.
      operation: The operation.

  Raises:
      GenerateError: When a reference does not resolve, or a parameter has no
          name or location.

  Returns:
      List[Dict[str, Any]]: The parameters, path-level first.
  """
  shared = spec.get("components", {}).get("parameters", {})
  merged: Dict[Tuple[str, str], Dict[str, Any]] = {}

  for parameter in [*spec["paths"][path].get("parameters", []), *operation.get("parameters", [])]:
    ref = parameter.get("$ref")
    if isinstance(ref, str):
      if not ref.startswith(PARAMETER_REF) or ref[len(PARAMETER_REF):] not in shared:
        raise GenerateError(f"{path}: parameter reference {ref} does not resolve")

      parameter = shared[ref[len(PARAMETER_REF):]]

    if not isinstance(parameter.get("name"), str) or not isinstance(parameter.get("in"), str):
      raise GenerateError(f"{path}: a parameter has no name or location")

    merged[(parameter["name"], parameter["in"])] = parameter

  return list(merged.values())


# -----------------------------------------------------------------------------
def _object_titles(node: Any, schemas: Dict[str, Any], seen: Set[str], untitled: List[str]) -> Set[str]:
  """Collect the titles of every object schema reachable from a node.

  datamodel-code-generator names each model after its schema's title
  (``use-title-as-name``), so the titles are the model names.

  Arguments:
      node: Any part of the spec.
      schemas: The spec's component schemas.
      seen: Component names already walked, so cycles end.
      untitled: Gets the property names of each object schema with no title.

  Returns:
      Set[str]: The titles found.
  """
  titles: Set[str] = set()

  if isinstance(node, list):
    for item in node:
      titles |= _object_titles(item, schemas, seen, untitled)

  elif isinstance(node, dict):
    ref = node.get("$ref")
    if isinstance(ref, str) and ref.startswith(SCHEMA_REF):
      name = ref[len(SCHEMA_REF):]
      if name not in seen:
        seen.add(name)
        titles |= _object_titles(schemas[name], schemas, seen, untitled)

    if isinstance(node.get("properties"), dict):
      if isinstance(node.get("title"), str):
        titles.add(node["title"])

      else:
        untitled.append(", ".join(node["properties"]))

    for value in node.values():
      titles |= _object_titles(value, schemas, seen, untitled)

  return titles


# -----------------------------------------------------------------------------
def response_models(spec: Dict[str, Any]) -> List[str]:
  """Name the models only responses use.

  Arguments:
      spec: The patched spec.

  Raises:
      GenerateError: When a model is used by both a request and a response,
          or a response object has no title to name its model by.

  Returns:
      List[str]: The model names, sorted.
  """
  schemas = spec.get("components", {}).get("schemas", {})
  requests: Set[str] = set()
  responses: Set[str] = set()
  untitled: List[str] = []

  for _, path, operation in operations(spec):
    requests |= _object_titles([operation.get("requestBody", {}), parameters(spec, path, operation)], schemas, set(), [])
    responses |= _object_titles(operation.get("responses", {}), schemas, set(), untitled)

  # Without a title the generator invents the model's name, so no override can
  # name it, and it would keep forbidding unknown fields.
  if untitled:
    raise GenerateError(f"response object(s) with no title, so their models cannot be named: {'; '.join(untitled)}")

  shared = sorted(requests & responses)
  if shared:
    raise GenerateError(f"used by both a request and a response, so #22 decides nothing for: {', '.join(shared)}")

  return sorted(responses)


# -----------------------------------------------------------------------------
def class_names(source: str) -> List[str]:
  """List the classes a module defines at its top level, in order.

  Arguments:
      source: The module's source.

  Returns:
      List[str]: The class names.
  """
  return [node.name for node in ast.parse(source).body if isinstance(node, ast.ClassDef)]


# -----------------------------------------------------------------------------
def all_line(names: List[str]) -> str:
  """Render an ``__all__`` assignment.

  Arguments:
      names: The exported names.

  Returns:
      str: The assignment and a newline.
  """
  return "__all__ = [" + ", ".join(json.dumps(name) for name in names) + "]\n"


# -----------------------------------------------------------------------------
def _chunks(text: str) -> List[str]:
  """Split text into pieces whose literals each fit in ``CHUNK`` columns.

  Splits between words where it can and inside a word only when the word
  alone is too long. Every character is kept, so the pieces join back to
  the text.

  Arguments:
      text: The string.

  Returns:
      List[str]: The pieces; one empty piece for empty text.
  """
  chunks: List[str] = []
  current = ""

  for token in re.findall(r"\S+\s*|\s+", text):
    if current and len(repr(current + token)) > CHUNK:
      chunks.append(current)
      current = ""

    for char in token:
      if current and len(repr(current + char)) > CHUNK:
        chunks.append(current)
        current = ""

      current += char

  return [*chunks, current] if current or not chunks else chunks


# -----------------------------------------------------------------------------
def literal(text: str, indent: str) -> str:
  """Render a string as one literal, or adjacent literals when it is long.

  Arguments:
      text: The string.
      indent: The indent for continuation lines.

  Returns:
      str: Python source for the string.
  """
  chunks = _chunks(text)
  if len(chunks) == 1:
    return repr(chunks[0])

  return "(\n" + "".join(f"{indent}  {chunk!r}\n" for chunk in chunks) + f"{indent})"


# -----------------------------------------------------------------------------
def render_routes(spec: Dict[str, Any]) -> str:
  """Render the route list module.

  Arguments:
      spec: The patched spec.

  Returns:
      str: The module's source.
  """
  entries = []

  for method, path, operation in operations(spec):
    rendered = "".join(
      f"Parameter(name={parameter['name']!r}, location={parameter['in']!r}, required={bool(parameter.get('required'))}), "
      for parameter in parameters(spec, path, operation)
    )
    entries.append(
      "  Route(\n"
      f"    method={method.upper()!r},\n"
      f"    path={path!r},\n"
      f"    parameters=({rendered}),\n"
      f"    summary={literal(operation.get('summary', ''), '    ')},\n"
      f"    description={literal(operation.get('description', ''), '    ')},\n"
      "  ),\n"
    )

  return (
    HEADER.format(summary="Every route in the Bitwarden Vault Management API spec.") + ROUTE_TYPES
    + "\nROUTES: Tuple[Route, ...] = (\n" + "".join(entries) + ")\n\n" + all_line(ROUTE_EXPORTS)
  )


# -----------------------------------------------------------------------------
def render_init(models: List[str]) -> str:
  """Render the package's ``__init__.py``.

  Arguments:
      models: The model names, in their module's order.

  Raises:
      GenerateError: When a model name collides with a route list name.

  Returns:
      str: The module's source.
  """
  clash = sorted(set(models) & set(ROUTE_EXPORTS))
  if clash:
    raise GenerateError(f"model name(s) clash with the route list: {', '.join(clash)}")

  return (
    HEADER.format(summary="Generated models and route list for the Bitwarden Vault Management API.") + "\n"
    + "".join(f"from .models import {name}\n" for name in models)
    + "".join(f"from .routes import {name}\n" for name in ROUTE_EXPORTS) + "\n" + all_line(models + ROUTE_EXPORTS)
  )


# -----------------------------------------------------------------------------
def generate_models(ignore: List[str]) -> List[str]:
  """Run datamodel-code-generator, then add ``__all__`` to its module.

  Arguments:
      ignore: The models that ignore unknown fields.

  Raises:
      GenerateError: When the generator fails, or a model to override is not
          in its output.

  Returns:
      List[str]: The model names, in the module's order.
  """
  # Quoted, because the generator writes the value into the source as is.
  overrides = {name: {"config": {"extra": "'ignore'"}} for name in ignore}

  # The generator reads template data only from a named file.
  with tempfile.TemporaryDirectory() as scratch:
    data = Path(scratch) / "template-data.json"
    data.write_text(json.dumps(overrides), encoding="utf-8")
    result = subprocess.run(  # noqa: S603 - fixed arguments. # nosec B603
      [sys.executable, "-m", "datamodel_code_generator", "--extra-template-data", str(data)],
      cwd=ROOT,
      capture_output=True,
      text=True,
      check=False,
    )

  if result.returncode != 0:
    raise GenerateError(f"datamodel-code-generator exited {result.returncode}: {result.stderr.strip() or result.stdout.strip()}")

  source = MODELS.read_text(encoding="utf-8")
  names = class_names(source)

  # The generator ignores template data for a name it does not produce, so a
  # renamed title would otherwise leave that model forbidding silently.
  missing = sorted(set(ignore) - set(names))
  if missing:
    raise GenerateError(f"no generated model for response schema title(s): {', '.join(missing)}")

  MODELS.write_text(f"{source.rstrip()}\n\n{all_line(names)}", encoding="utf-8")
  return names


# -----------------------------------------------------------------------------
def main() -> int:
  """Generate the package.

  Returns:
      int: 0 on success, 1 when generation could not finish.
  """
  try:
    spec = json.loads(PATCHED_SPEC.read_text(encoding="utf-8"))
    PACKAGE.mkdir(exist_ok=True)
    models = generate_models(response_models(spec))
    ROUTES.write_text(render_routes(spec), encoding="utf-8")
    INIT.write_text(render_init(models), encoding="utf-8")

  except (GenerateError, OSError, ValueError) as exc:
    print(f"generate: error: {exc}", file=sys.stderr)
    return 1

  return 0


if __name__ == "__main__":
  sys.exit(main())
