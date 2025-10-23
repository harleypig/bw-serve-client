# TODO - bw-serve-client Library Development

This document outlines the tasks needed to complete the bw-serve-client Python
library for Bitwarden Vault Management API.

## High Priority - Code Generation & Quality Tools

- [ ] **Implement Pydantic slots optimization**
  - Research Pydantic v2 slots configuration: `Config(slots=True)` or `model_config = ConfigDict(slots=True)`
  - Determine if slots provide meaningful performance benefits for this API client
  - If beneficial, customize code generation templates to include slots configuration
  - Add `flake8-slots` for testing and validation
  - Test memory usage and performance impact

- [ ] **Implement proper `__all__` exports**
  - Configure code generation to automatically include `__all__` in generated modules or customize code generation templates
  - Add `flake8-dunder-all` to check for missing `__all__` declarations
  - Add `flake8-all-not-strings` to ensure all `__all__` entries are strings
  - Ensure all public API classes and functions are properly exported

- [ ] **Enhance flake8 plugin ecosystem**
  - Add `flake8-encodings` to check for encoding issues
  - Research automation for `flake8-clean-block` errors (may need custom tooling)
  - Investigate flake8 plugins for:
    - [ ] pyright integration (if available)
    - [ ] pydocstyle integration (flake8-docstrings)
    - [ ] bandit integration (flake8-bandit)
    - [ ] mypy integration (flake8-mypy)
    - [ ] isort integration (flake8-isort)
    - [ ] markdownlint integration (flake8-markdown)
    - [ ] yamllint integration (flake8-yaml)
  - Evaluate existing plugin configurations and optimize
  - Research additional useful flake8 plugins for Python development

- [ ] **Evaluate ruff as yapf replacement**
  - Research ruff's formatting capabilities vs yapf
  - Test ruff performance and feature parity
  - Evaluate integration with existing flake8 setup
  - Consider ruff's built-in linting capabilities
  - Plan migration strategy if beneficial

## API Spec Tool Improvements

- [ ] **Document key replacement limitation**
  - **Known Issue**: When a key in a dictionary is replaced in the fixed spec, the entire value is treated as new during `api-spec-tool update`
  - **Impact**: Even if the content of the value hasn't changed, it will be detected as a difference
  - **Example**: Path `"/device-approval/{organizationId}/approve/{request-id}}"` becomes `"/device-approval/{organizationId}/approve/{request-id}"` - entire POST operation definition is duplicated
  - **Root Cause**: DeepDiff with `ignore_order=True` doesn't recognize key renames, treats them as complete removal + addition
  - **Current Workaround**: No practical solution exists - this is a fundamental limitation of the current approach
  - **Documentation Needed**: Add to developer docs (README.md or docs/api-spec-tool.md) explaining this limitation and its impact on spec-fixes.json size

- [ ] **Enhance array difference detection**
  - Improve field-level modification detection within array elements
  - Add support for nested object changes in arrays
  - Optimize content-based hashing for better performance
  - Add configuration for array comparison strategies

## Document Swagger/OpenAPI Source

- [ ] **Document that this code is generated from Bitwarden's swagger file**
  - Add clear documentation in README.md about the source
  - Include link to the original swagger file: `docs/vault-management-api.json`
  - Document the generation process and tools used
  - Add note about keeping the swagger file up to date

## Core Library Implementation

- [ ] **Implement error/logging module**
  - Create flexible error handling system as specified in `docs/api-architecture.md`
  - Support custom error handlers and loggers
  - Implement minimal default error handling
  - Add proper error level and log level configuration

- [ ] **Implement base API client class**
  - Create foundation class with common functionality
  - Handle authentication (bearer token, etc.)
  - Implement JSON serialization/deserialization
  - Add request/response validation
  - Include proper error handling and logging

- [ ] **Implement planned API classes** (see `docs/api-architecture.md`)
  - [ ] VaultItems class
  - [ ] Attachments class
  - [ ] ItemFields class
  - [ ] Folders class
  - [ ] VaultControl class
  - [ ] Utilities class

## Testing Infrastructure

- [ ] **Set up comprehensive testing**
  - Create test structure following pytest conventions
  - Implement unit tests for all classes and methods
  - Add integration tests with mock API responses
  - Use pytest-mock for external dependency testing
  - Achieve high code coverage (target: >90%)

- [ ] **Create test data and fixtures**
  - Mock API responses for all endpoints
  - Test data for various scenarios (success, error, edge cases)
  - Fixtures for common test setup

- [ ] **Add multi-Python version testing support**
  - Set up Tox or GitHub Actions matrix for testing Python 3.9, 3.10, 3.11, 3.12
  - Ensure compatibility across supported Python versions
  - Add version-specific test configurations if needed

- [ ] **Regular mypy/pydantic auditing**
  - Set up automated mypy checking in CI/CD pipeline
  - Create process for regular type safety audits
  - Review and update pydantic models as API evolves
  - Ensure mypy and pydantic integration remains optimal
  - Add type checking to pre-commit hooks

- [ ] **Add pylint for comprehensive code analysis**
  - Integrate pylint into CI/CD pipeline for thorough code review
  - Configure pylint rules to complement flake8 and yapf
  - Set up pylint reports for code quality metrics
  - Use pylint for detailed refactoring suggestions and best practices
  - Configure pylint to work alongside existing flake8 pre-commit hooks
  - Is there a plugin for flake8?

## Documentation

- [ ] **Complete API documentation**
  - Generate Sphinx documentation from docstrings
  - Add comprehensive docstrings to all public methods
  - Include usage examples for each class
  - Document authentication and configuration

- [ ] **Create usage examples**
  - Add examples directory with practical usage scenarios
  - Include examples for each major class
  - Show error handling patterns
  - Demonstrate authentication setup

## Code Quality and Standards

- [ ] **Enhance pre-commit hooks**
  - Add yesqa pre-commit hook for removing unused noqa comments
  - Determine which PyCQA pre-commit hooks are valid for this project
  - Research additional useful hooks for Python development
  - Optimize hook performance and execution order

- [ ] **Code formatting and linting**
  - Run yapf for consistent code formatting
  - Fix all flake8 violations
  - Resolve mypy type checking issues
  - Follow PEP 8 and project naming conventions

## Package Configuration

- [ ] **Update pyproject.toml**
  - Ensure all dependencies are properly specified
  - Add proper package metadata
  - Configure build system correctly
  - Add proper license information

- [ ] **Package structure**
  - Organize code into logical modules
  - Ensure proper `__init__.py` files
  - Add type hints throughout codebase
  - Implement proper package exports

## CI/CD Pipeline

- [ ] **Set up GitHub Actions**
  - Create workflow for testing on multiple Python versions
  - Add code quality checks
  - Implement automated testing
  - Add coverage reporting

- [ ] **Release automation**
  - Set up automated version bumping
  - Create release workflows
  - Add changelog generation

## Advanced Features

- [ ] **Add advanced functionality**
  - Implement retry logic for failed requests
  - Add request/response caching
  - Implement rate limiting
  - Add connection pooling

- [ ] **Performance optimization**
  - Profile API client performance
  - Optimize memory usage
  - Add async support (if needed)
  - Implement efficient data structures

## Security and Compliance

- [ ] **Security review**
  - Audit authentication handling
  - Review credential storage
  - Check for security vulnerabilities
  - Implement secure defaults

- [ ] **Compliance checks**
  - Run security scanning tools
  - Review dependency vulnerabilities
  - Ensure proper license compliance

## Documentation Enhancement

- [ ] **Advanced documentation**
  - Create developer guides
  - Add troubleshooting documentation
  - Create migration guides
  - Add performance tuning guides

- [ ] **Website and examples**
  - Set up project website (if needed)
  - Create interactive examples
  - Add tutorial content
  - Use github pages

## Regular Updates

- [ ] **Keep dependencies updated**
  - Regular Poetry dependency updates
  - Security patch management
  - Python version compatibility

- [ ] **API compatibility**
  - Monitor Bitwarden API changes
  - Update swagger file when needed
  - Test compatibility with new API versions

## Community and Support

- [ ] **Community engagement**
  - Set up issue templates
  - Create contribution guidelines
  - Add code of conduct
  - Set up discussion forums

## Notes

- All tasks should follow the guidelines in `AGENTS.md` and `WORKFLOW.md`
- Prioritize error handling and logging implementation early
- Focus on core API client functionality before advanced features
- Maintain high code quality standards throughout development
- Keep documentation up to date with code changes

## Current Status

- [x] Documentation structure reorganized
- [x] Development environment setup documented
- [x] API architecture planned
- [x] Basic project structure in place
- [x] Pre-commit configuration implemented
- [x] Code quality tools configured (yapf, flake8, mypy, pydocstyle, bandit, isort)
- [x] Route extraction script completed with clean output formatting
- [x] Development workflow enhanced with comprehensive linting and formatting
- [ ] Core implementation started
- [ ] Testing infrastructure ready
- [ ] Documentation complete
