# Version Management

This project uses `bump2version` to keep version numbers synchronized between
`pyproject.toml` and `bw_serve_client/__init__.py`.

## Quick Reference

```bash
# Show current version
make version-show

# Bump patch version (0.1.1 → 0.1.2)
make version-patch

# Bump minor version (0.1.1 → 0.2.0)
make version-minor

# Bump major version (0.1.1 → 1.0.0)
make version-major
```

## Direct Usage

You can also use `bump2version` directly:

```bash
# Bump versions
poetry run bump2version patch    # 0.1.1 → 0.1.2
poetry run bump2version minor    # 0.1.1 → 0.2.0
poetry run bump2version major    # 0.1.1 → 1.0.0

# Dry run (see what would change)
poetry run bump2version --dry-run patch

# Allow dirty working directory
poetry run bump2version --allow-dirty patch
```

## What Gets Updated

When you bump the version, `bump2version` automatically updates:

1. **`pyproject.toml`** - Updates the `version = "X.Y.Z"` field
2. **`bw_serve_client/__init__.py`** - Updates the `__version__ = "X.Y.Z"` field
3. **`.bumpversion.cfg`** - Updates the `current_version` field
4. **Git** - Creates a commit and tag (e.g., `v0.1.2`)

## Version Numbering

- **Patch** (0.1.1 → 0.1.2): Bug fixes, small improvements
- **Minor** (0.1.1 → 0.2.0): New features, backward compatible changes
- **Major** (0.1.1 → 1.0.0): Breaking changes, major rewrites

## Requirements

- Clean git working directory (or use `--allow-dirty`)
- `bump2version` package (installed as dev dependency)

## Configuration

The version management is configured in `.bumpversion.cfg`:

```ini
[bumpversion]
current_version = 0.1.1
commit = True
tag = True
tag_name = v{new_version}
message = Bump version: {current_version} → {new_version}

[bumpversion:file:pyproject.toml]
search = version = "{current_version}"
replace = version = "{new_version}"

[bumpversion:file:bw_serve_client/__init__.py]
search = __version__ = "{current_version}"
replace = __version__ = "{new_version}"
```
