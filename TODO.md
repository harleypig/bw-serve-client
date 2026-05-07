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
    - [x] isort integration (flake8-isort)
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

- [ ] **Decide formatter: yapf+isort vs black+isort**
  - Currently using yapf (column_limit = 132, google style); see
      `.claude/CONVENTIONS.md`
  - Run a parallel experiment on a representative module with both
      formatters and compare diff churn, readability, and pre-commit speed
  - Confirm or change the repo's choice in `.claude/CONVENTIONS.md`
  - Global `rules/black.md`, `rules/yapf.md`, `rules/isort.md` already
      describe both toolchains

## API Spec Tool Improvements

- [ ] **Document key replacement limitation**
  - **Known Issue**: When a key in a dictionary is replaced in the fixed spec,
      the entire value is treated as new during `api-spec-tool update`
  - **Impact**: Even if the content of the value hasn't changed, it will be
      detected as a difference
  - **Example**: Path
      `"/device-approval/{organizationId}/approve/{request-id}}"` becomes
      `"/device-approval/{organizationId}/approve/{request-id}"` - the entire
      key **and** value will be deleted and recreated, showing up in
      spec-fixes.json as two separate operations: `delete_value` (old key) and
      `add_if_missing` (new key with duplicated value)
  - **Root Cause**: DeepDiff with `ignore_order=True` doesn't recognize key
      renames, treats them as complete removal + addition
  - **Current Workaround**: No practical solution exists - this is
      a fundamental limitation of the current approach
  - **Documentation Needed**: Add to developer docs (README.md or
      docs/api-spec-tool.md) explaining this limitation and its impact on
      spec-fixes.json size

- [ ] **Document DeepDiff ignore_order=True design decision**
  - **Purpose**: Explain why `ignore_order=True` is used in DeepDiff comparison
  - **Benefit**: Prevents false positives for array reordering (e.g., tags, parameters)
  - **Trade-off**: Creates key replacement limitation but avoids hundreds of unnecessary array reorder operations
  - **Context**: Most OpenAPI array order changes are cosmetic and don't affect semantic meaning
  - **Documentation Needed**: Add to developer docs explaining the design rationale and its implications

- [ ] **CRITICAL: Fix fragile array handling in api-spec-tool.py**
  - **Current Problem**: `_is_array_path` logic is too simplistic and will break with complex array structures
  - **Issue**: Only checks if last path component is numeric, but fails for nested array properties like `parameters[3].schema.format`
  - **Impact**: Current fix works for immediate issue but creates technical debt for future array structures
  - **Constraint**: Must work with DeepDiff `ignore_order=True` (needed to prevent false positives for array reordering)
  - **Suggested Solution**:
    1. **Content-based array element tracking**: Use hashing of entire array element values to maintain identity across changes
    2. **Parent array identification**: Detect array parent paths by finding numeric indices anywhere in path, not just at end
    3. **Robust element mapping**: Implement proper array element mapping that handles both structural changes (additions/removals) and property modifications within elements
    4. **DeepDiff integration**: Consider leveraging DeepDiff's built-in array tracking features or implement custom comparison logic
  - **Why This Matters**: Future array structures with nested properties will
      likely break current logic, so need robust solution that can handle
      array elements with complex nested properties, array reordering, and
      mixed changes

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
  - Contract: `.claude/WORKFLOW.md` *Error / Logging Module Contract*
  - Architecture: `docs/api-architecture.md`
  - Support injected error handlers and loggers; minimal built-in
      defaults when neither is provided
  - Configurable error-level and log-level thresholds

- [ ] **Implement base API client class**
  - Contract: `.claude/WORKFLOW.md` *API Class Contract*
  - Foundation class with common functionality (auth, request build,
      response parse)
  - Handle authentication (bearer token, etc.)
  - JSON serialization/deserialization via pydantic models
  - Request/response validation at the public boundary
  - Wire in the injected error handler and logger

- [ ] **Implement planned API classes** (see `docs/api-architecture.md`)
  - [ ] VaultItems class
  - [ ] Attachments class
  - [ ] ItemFields class
  - [ ] Folders class
  - [ ] VaultControl class
  - [ ] Utilities class

## Testing Infrastructure

- [ ] **Set up comprehensive testing**
  - Strategy and required coverage points: `.claude/TESTS.md`
  - Implement unit tests for all classes and methods (one
      `tests/test_<module>.py` per source module)
  - Add integration tests with mock API responses via `pytest-mock`
  - Achieve high code coverage (target: >90%)

- [ ] **Create test data and fixtures**
  - Add `tests/conftest.py` for shared fixtures and `tests/fixtures/`
      for recorded API payloads (per `.claude/TESTS.md`)
  - Mock API responses for all endpoints
  - Test data for various scenarios (success, error, edge cases)

- [ ] **Add multi-Python version testing support**
  - Set up Tox or GitHub Actions matrix for testing Python 3.9, 3.10, 3.11, 3.12
  - Ensure compatibility across supported Python versions
  - Add version-specific test configurations if needed

- [ ] **Regular type checking/pydantic auditing**
  - Set up automated type checking in CI (see "Set up GitHub Actions"
      below) — `pyright` runs locally and in pre-commit; CI gets `mypy`
      as the second-pass checker
  - Create process for regular type safety audits
  - Review and update pydantic models as API evolves
  - Ensure type checking and pydantic integration remains optimal
  - [x] Add type checking to pre-commit hooks (pyright is wired in
      `.pre-commit-config.yaml`)

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
  - Create `examples/` directory (does not yet exist) per
      `.claude/TESTS.md` *Examples Directory*
  - Each public API surface MUST have a runnable example, kept in sync
      with the API in the same PR that changes it
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
  - Tooling and conventions live in `.claude/CONVENTIONS.md` (yapf
      column_limit = 132, comment wrap at 72) and global
      `rules/python.md` / `rules/code-style.md`
  - Run `pre-commit run --all-files` to apply the configured
      formatter / linter / type-checker stack
  - Resolve any outstanding flake8, pyright, or formatter warnings as
      part of normal development

## Package Configuration

- [ ] **Update pyproject.toml**
  - Ensure all dependencies are properly specified
  - Add proper package metadata
  - Configure build system correctly
  - Add proper license information

- [ ] **Package structure**
  - Layout and naming conventions live in `.claude/CONVENTIONS.md` and
      global `rules/python.md`
  - Organize code into logical modules per the architecture in
      `docs/api-architecture.md`
  - Ensure `__init__.py` defines the public surface (ties to the
      `__all__` exports todo above)

## CI/CD Pipeline

- [ ] **Set up GitHub Actions for tests and type-checking**
  - Currently only `docs.yml` runs in CI; no pytest or type-check
      workflow exists
  - Create workflow that runs `pytest` on every push and PR
  - Decide whether to add `mypy` as a second-pass type checker
      (complements local `pyright`); see `.claude/CONVENTIONS.md` and
      global `rules/python.md` for the dev/CI split rationale
  - Add matrix for supported Python versions (tie to the multi-version
      todo above)
  - Add coverage reporting (`pytest --cov=bw_serve_client`)

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

- All tasks should follow the guidelines in `.claude/` (`CLAUDE.md`,
  `WORKFLOW.md`, `CONVENTIONS.md`, `TESTS.md`)
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
- [x] Code quality tools configured (yapf, flake8, pyright, pydocstyle,
  bandit, isort)
- [x] Agent configuration migrated from root `AGENTS.md` / `WORKFLOW.md`
  to `.claude/` (`CLAUDE.md`, `WORKFLOW.md`, `CONVENTIONS.md`,
  `TESTS.md`)
- [x] Route extraction script completed with clean output formatting
- [x] Development workflow enhanced with comprehensive linting and formatting
- [ ] Core implementation started
- [ ] Testing infrastructure ready
- [ ] Documentation complete
