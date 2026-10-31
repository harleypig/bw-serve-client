# Codegen

Inputs to generating the library's data models.

The models in `bw_serve_client/models.py` are generated, as pydantic 2
models, by [datamodel-code-generator][dcg] from the patched spec in
`upstream/vault-management-api-fixed.json`. Its settings are in
`pyproject.toml` under `[tool.datamodel-codegen]`.

| File | What it is |
|------|------------|
| `generated-header.txt` | The module docstring placed at the top of the generated file. |

To regenerate the models, run this from the repository root, then run the
pre-commit fix config to format the result:

```bash
poetry run datamodel-codegen
pre-commit run --all-files --config .pre-commit-config-fix.yaml
```

`poetry run python pipeline.py build` does the same in one step, after
applying the spec fixes; see `upstream/README.md`.

## Model strictness

Decided on #22 (2026-10-31): what a generated model does with a field it does
not know depends on which way the data flows.

| Model | Unknown fields | Why |
|-------|----------------|-----|
| Request (what a caller sends) | Rejected (`extra="forbid"`) | A misspelled field fails at the caller, not silently at the server. |
| Response (what `bw serve` returns) | Ignored (`extra="ignore"`) | A field Bitwarden adds upstream never breaks a caller that does not use it. |

Today every model forbids unknown fields, the setting in `pyproject.toml`.
Generating the two kinds differently is part of #23.

[dcg]: https://github.com/koxudaxi/datamodel-code-generator
