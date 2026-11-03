# Codegen

Generates `bw_serve_client/_generated/` from the patched spec in
`upstream/vault-management-api-fixed.json`. The package is generated, never
edited by hand.

| File | What it is |
|------|------------|
| `generate.py` | Writes the three generated modules, below. |
| `snippets/` | The fixed text written into them, read at run time. |

| Snippet | What it is |
|---------|------------|
| `header.txt` | The module docstring every generated module opens with: as is for `models.py` (`custom-file-header-path`), with its first line swapped for the module's summary elsewhere. |
| `route-types.txt` | The imports and the `Parameter` and `Route` dataclasses at the top of `routes.py`. |
| `route.txt` | One `Route(...)` entry in `ROUTES`, with a `{name}` slot per field. |

| Generated module | What it holds |
|------------------|---------------|
| `models.py` | The pydantic 2 models, by [datamodel-code-generator][dcg], with its settings in `pyproject.toml` under `[tool.datamodel-codegen]`. |
| `routes.py` | `ROUTES`: one `Route` per operation in the spec, with its method, path, parameters, summary, description and tags. |
| `__init__.py` | Re-exports both. |

Each module defines `__all__`. The package root, `bw_serve_client`,
re-exports every model from `models.__all__`, so no list of model names is
kept by hand.

To regenerate, run this from the repository root:

```bash
poetry run python pipeline.py build
```

It applies the spec fixes, runs `generate.py`, and formats the result with
the pre-commit fix config's formatters. A second run changes nothing. CI
runs it on every pull request and fails if anything it writes differs from
what is committed. See `upstream/README.md` for the rest of the pipeline.

## Model strictness

Decided on #22 (2026-10-31): what a generated model does with a field it does
not know depends on which way the data flows.

| Model | Unknown fields | Why |
|-------|----------------|-----|
| Request (what a caller sends) | Rejected (`extra="forbid"`) | A misspelled field fails at the caller, not silently at the server. |
| Response (what `bw serve` returns) | Ignored (`extra="ignore"`) | A field Bitwarden adds upstream never breaks a caller that does not use it. |

`pyproject.toml` sets `forbid` for every model. `generate.py` finds the models
only responses use, by walking each operation's responses in the spec, and
passes the generator a per-model `ignore` for each. Two cases stop the build
rather than guess:

- A model that both a request and a response use, since #22 does not decide
  it.
- A response model the generator did not produce, since its override would
  silently do nothing.

`RootModel` classes take no `extra` setting.

## Hidden custom fields

A hidden custom field (`type` 1) holds a secret, but a spec `format` cannot
depend on a sibling field's value (#127). So two spec fixes type the `value`
of `FieldSchema` and `FieldResponseSchema` as `str | SecretStr`, and
`base-class-map` in `pyproject.toml` gives both models the hand-written base
`CustomField` (in `bw_serve_client/_custom_field.py`), whose validator wraps a
hidden field's value in `SecretStr`. The base must not import the generated
models, since they import it.

[dcg]: https://github.com/koxudaxi/datamodel-code-generator
