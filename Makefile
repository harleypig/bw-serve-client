# Version management
.PHONY: version-patch version-minor version-major version-show

# Show current version
version-show:
	@poetry run python -c "from bw_serve_client import __version__; print(f'Current version: {__version__}')"

# Bump patch version (0.1.0 → 0.1.1)
version-patch:
	@poetry run bump2version patch

# Bump minor version (0.1.0 → 0.2.0)
version-minor:
	@poetry run bump2version minor

# Bump major version (0.1.0 → 1.0.0)
version-major:
	@poetry run bump2version major

# Development helpers
.PHONY: test lint format install

# Run tests
test:
	@poetry run pytest --cov=bw_serve_client --cov-report=term-missing

# Run linting
lint:
	@poetry run pre-commit run --all-files

# Format code
format:
	@poetry run pre-commit run --all-files --config .pre-commit-config-fix.yaml

# Install dependencies
install:
	@poetry install
