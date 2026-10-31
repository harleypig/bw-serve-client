# Upstream

What this repository knows about Bitwarden's Vault Management API, and the
tool that works on it. None of it is part of the installed library.

| File | What it is |
|------|------------|
| `vault-management-api-original.json` | Bitwarden's spec, as committed. It is taken from the [Vault Management API help page][vm-api], which is the only place Bitwarden publishes it. |
| `spec-fixes.json` | Local fixes the model generator needs, applied to the original spec. |
| `vault-management-api-fixed.json` | The patched spec: the original with the fixes applied. Model generation reads this file. |
| `api-spec-tool.py` | The spec tool, described below. |

## The spec tool

Run it from the repository root:

```bash
poetry run python upstream/api-spec-tool.py <subcommand> [options]
```

| Subcommand | Does |
|------------|------|
| `analyze SPEC` | Summarise the spec's structure: paths, operations, tags. |
| `extract SPEC` | List the routes, as text (the default), Markdown or JSON. `-o FILE` writes to a file. |
| `update` | Compare the original and patched specs and add any new differences to `spec-fixes.json`. `--dry-run` shows them without writing. |
| `fix --fixed-file FILE` | Apply `spec-fixes.json` to the original spec and write the result to `FILE`. The path is required, so a plain run never overwrites the committed patched spec. |

Every subcommand takes `-q` for errors only and `-d` for debug output.
`poetry run python upstream/api-spec-tool.py <subcommand> --help` lists the
rest.

`analyze` and `extract` need only the standard library. `update` needs
`deepdiff`, which `poetry install` provides.

[vm-api]: https://bitwarden.com/help/vault-management-api/
