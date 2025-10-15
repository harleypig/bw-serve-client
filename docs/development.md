# Development Environment Setup

This document provides instructions for setting up the development environment
for the bw-serve-client Python library.

## Prerequisites

- Python 3.9 or higher
- Poetry for dependency management
- Git for version control
- Pre-commit for code quality hooks

## Initial Setup

```bash
# Clone repository
git clone <repository-url>
cd bw-serve-client

# Install Poetry if not already installed
curl -sSL https://install.python-poetry.org | python3 -

# Install dependencies
poetry install

# Install pre-commit hooks
poetry run pre-commit install

# Activate virtual environment
poetry shell
```

## Running Tests

```bash
# Run all tests
poetry run pytest

# Run tests with coverage
poetry run pytest --cov=bw_serve_client
```

For comprehensive testing guidelines, requirements, and best practices, see
[WORKFLOW.md](../WORKFLOW.md).

## Code Quality Checks

For detailed code quality checks and development guidelines, see:
- [AGENTS.md](../AGENTS.md) - Pre-commit configuration and tool usage
- [WORKFLOW.md](../WORKFLOW.md) - Development process and quality gates

## Development Guidelines

The goal is minimization; DRY principles (refer Pragmatic Programming), proper
and decent error handling and logging.

This is a poetry project. Make sure pyproject.toml is updated to match the
current state of the project.

For comprehensive development standards, testing requirements, and documentation
guidelines, see [WORKFLOW.md](../WORKFLOW.md).

## Additional Resources

For detailed information about API architecture, planned classes, and
implementation guidelines, see [docs/api-architecture.md](api-architecture.md).
