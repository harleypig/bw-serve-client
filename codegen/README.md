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

[dcg]: https://github.com/koxudaxi/datamodel-code-generator
