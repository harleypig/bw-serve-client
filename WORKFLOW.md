# Repository Workflow and Quality Gates

This document outlines the specific workflow, quality gates, and processes for
the bw-serve-client Python library. All agents and developers should follow
these procedures when working on this repository.

## Python Library Development Guidelines

- Use clear and descriptive names for classes, methods, and variables
- Keep classes focused on a single responsibility (SRP)
- Use type hints throughout the codebase (use Pydantic)
- Document all public APIs with docstrings
- Follow PEP 8 and project-specific formatting standards

### Naming Conventions

- **Module Files**: Use lowercase with underscores (e.g., `vault_client.py`)
- **Class Names**: Use PascalCase (e.g., `VaultClient`, `ErrorLogger`)
- **Method Names**: Use snake_case (e.g., `get_vault_item`, `handle_error`)
- **Constants**: Use UPPER_SNAKE_CASE (e.g., `DEFAULT_TIMEOUT`)
- **Private Methods**: Prefix with underscore (e.g., `_validate_token`)

### Project Structure and Best Practices

- Follow Poetry project structure and dependency management
- Use `pyproject.toml` for all project configuration
- Organize code into logical modules by functionality
- Include comprehensive README.md and documentation
- Use `__init__.py` files appropriately for package structure
- Implement proper error handling and logging throughout

### Code Quality Tools

- **pytest**: For unit testing and test discovery
- **pytest-mock**: For mocking external dependencies
- **pytest-cov**: For code coverage reporting
- **pyright**: For static type checking and type safety
- **pydantic**: For runtime data validation and type hints
- **flake8**: For code style and complexity checking
- **yapf**: For code formatting
- **tox**: For testing across multiple Python versions
- **Pre-commit hooks**: Automated formatting and linting on commit

### Type Safety and Data Validation

- **pyright + pydantic integration**: Use pydantic models for API data structures
- **Type hints**: All public methods must have complete type annotations
- **Runtime validation**: Use pydantic for request/response data validation
- **Static analysis**: pyright catches type errors before runtime
- **Model definitions**: Create pydantic models for all API data structures

### Pre-commit Configuration

Two pre-commit configs available:

- `.pre-commit-config.yaml` - Check-only (default, makes no changes)
- `.pre-commit-config-fix.yaml` - Auto-fix (applies fixes automatically)

Usage: Run `pre-commit install` to set up hooks, or use `pre-commit run
--all-files` to check all files

## API Client Development Guidelines

### Error/Logging Module Requirements

The Error/Logging module MUST be designed to be agnostic of specific error
object and logging implementations. It MUST:

- Accept optional error handling and logging objects during instantiation of
    any API class
- If no custom error handler is provided, implement minimal error handling
    that can construct and return error objects based on a defined error level
    setting
- If no custom logger is provided, use Python's logging library
- Allow users of the library to define the granularity of error reporting and
    logging by setting appropriate error level and log level thresholds
- Handle different types of errors appropriately (validation, system, user,
    external service, etc.)
- Provide flexible configuration for error handling patterns

### API Class Requirements

An API class MUST handle:

- Gracefully return errors when something isn't right
- Log various levels of information
- General API errors, such as 500 errors
- Authentication (proper inclusion of bearer token or whatever)
- Formatting of data into JSON (or proper format the API expects)
- Formatting of JSON (or whatever format the API returns) into data
- Validate parameters before making requests
- Handle different HTTP status codes appropriately
- Provide clear error messages for different failure scenarios

### Class Implementation Guidelines

When creating Python classes from API routes, consider the following elements
from the route definitions:

- **HTTP Method**: Determines the request method for class methods
- **Path**: Helps define method names and routing within the class. Path
    parameters become method arguments
- **Parameters**: Become the parameters of class methods, including handling
    of different parameter types
- **Request Body**: For methods that send data, defines how to construct the
    request body from method arguments
- **Responses**: Handling of different response types, affecting class method
    return types
- **Tags**: Can group related routes into the same class
- **Security**: Implementation of authentication methods for secured routes
- **Schemas**: Definitions of data structures for request and response bodies,
    used to create corresponding Python classes or types

Each class or class method MUST:

- Use summary, description, and/or tags as available from the API definition
    or create as needed for documentation
- Gracefully return errors when something isn't right
- Log various levels of information
- Have a method that mirrors the name of the route being used
  - Where a name uses multiple HTTP methods, the method should call the
      appropriate HTTP method based on the parameters passed
- Validate the parameters
- Ensure data is in correct format for sending to API
- Provide unit tests in the tests directory
  - Use pytest-mock to test functions that access external tools
- Provide examples of usage in the examples directory

### Planned Class Structure

For detailed information about the planned class structure, API routes, and
implementation guidelines, see [docs/api-architecture.md](docs/api-architecture.md).

## Post Branch Creation

After creating a new feature/fix/bug branch:

1. **Verify branch naming convention**
   - Feature branches: `feature/descriptive-name`
   - Bug fix branches: `bugfix/descriptive-name`
   - Refactor branches: `refactor/descriptive-name`

2. **Set up development environment**
   - Ensure pre-commit hooks are installed: `pre-commit install`
   - Verify Poetry environment is activated: `poetry shell`
   - Install dependencies: `poetry install`
   - Check that all required tools are available

3. **Review task scope**
   - Ensure the branch addresses a single, well-defined task
   - Verify the task is properly documented in TODO.md
   - Confirm the scope aligns with the branch name

## Development Process

### Code Changes

1. **Follow naming conventions**
   - Use snake_case for module and function names
   - Use PascalCase for class names
   - Use descriptive names for all identifiers
   - Follow PEP 8 guidelines

2. **Maintain code quality**
   - Run `pytest` on all modified files
   - Run `pyright` for type checking and static analysis
   - Use `pydantic` for data validation and type safety
   - Use `flake8` for code style validation
   - Use `yapf` for code formatting
   - Follow word wrapping to column 78 for all documentation

3. **Documentation updates**
   - Update docstrings for any new methods or classes
   - Add or update usage examples for complex functionality
   - Ensure all public APIs have comprehensive documentation
   - Update main repository README if structure changes
   - Generate API documentation using Sphinx

4. **Testing considerations**
   - Write unit tests for all new functionality
   - Use pytest-mock for testing external dependencies
   - Test error handling and edge cases
   - Maintain high code coverage
   - Test with different Python versions using tox

### API Client-Specific Guidelines

#### Error Handling Implementation

- Implement flexible error handling that can be configured per instance
- Support different error levels and logging granularity
- Handle authentication errors, network errors, and API-specific errors
- Provide clear error messages and proper exception hierarchy

#### Authentication Handling

- Support bearer token authentication
- Handle token refresh and expiration
- Implement secure credential storage
- Support different authentication methods as needed

#### Data Formatting

- Implement proper JSON serialization/deserialization
- Handle different data types and formats
- Validate input data before sending to API
- Transform API responses into appropriate Python objects

## Pre-Switch to Master / Pre-Merge Checklist

Before switching back to master or merging any branch:

### Code Quality Gates

- [ ] **Pre-commit Validation**
  - [ ] Run `pre-commit run -a` to check all files
  - [ ] Fix any linting errors or warnings
  - [ ] Ensure proper indentation and syntax
  - [ ] Verify no trailing spaces or tabs
  - [ ] Fix any type checking issues
  - [ ] Ensure proper error handling
  - [ ] See AGENTS.md for pre-commit usage details and development tips

### Documentation Standards

- [ ] **API Documentation**
  - [ ] All public methods have complete docstrings
  - [ ] All parameters documented with types and descriptions
  - [ ] Usage examples provided for complex methods
  - [ ] Documentation follows word wrapping to column 78
  - [ ] Sphinx documentation builds without errors

- [ ] **Repository Documentation**
  - [ ] Main README.md updated if structure changes
  - [ ] Installation and usage instructions current
  - [ ] Any new dependencies documented
  - [ ] Examples directory updated with new functionality

- [ ] **Code Comments**
  - [ ] Complex logic explained with comments
  - [ ] Method names are descriptive and clear
  - [ ] Variable names follow conventions
  - [ ] Type hints provided for all public methods

### Testing and Validation

- [ ] **Unit Testing**
  - [ ] All new code has comprehensive unit tests
  - [ ] Tests use pytest-mock for external dependencies
  - [ ] Error scenarios are tested
  - [ ] Edge cases are covered
  - [ ] Code coverage meets project standards

- [ ] **Integration Testing**
  - [ ] API client methods work with mock responses
  - [ ] Error handling works correctly
  - [ ] Authentication flows are tested
  - [ ] Data formatting works as expected

- [ ] **Type Checking and Data Validation**
  - [ ] All code passes pyright type checking
  - [ ] Type hints are accurate and complete
  - [ ] No type-related warnings
  - [ ] Pydantic models defined for all API data structures
  - [ ] Runtime validation working correctly
  - [ ] pyright and pydantic integration verified

### Security and Compliance

- [ ] **Security Review**
  - [ ] No hardcoded credentials or sensitive data
  - [ ] Proper handling of authentication tokens
  - [ ] Secure data transmission practices
  - [ ] No unnecessary privilege escalation
  - [ ] Review any new external dependencies

- [ ] **Compliance Check**
  - [ ] Follow established naming conventions
  - [ ] Maintain consistent code style
  - [ ] Ensure proper error handling
  - [ ] Verify logging and monitoring considerations
  - [ ] Follow Python packaging best practices

### Git and Version Control

- [ ] **Commit Quality**
  - [ ] Clear and descriptive commit messages
  - [ ] Commits are atomic and focused
  - [ ] No unnecessary merge commits
  - [ ] Proper branch naming maintained

- [ ] **File Management**
  - [ ] No temporary or debug files committed
  - [ ] Proper .gitignore entries for new file types
  - [ ] No sensitive information in version control
  - [ ] Poetry lock file is up to date

## Regular Repository Maintenance

### Weekly Checks

- [ ] **Code Quality Review**
  - [ ] Run full repository linting: `flake8`, `pyright`, and `pytest`
  - [ ] Review any new warnings or errors
  - [ ] Update linting rules if needed
  - [ ] Check code coverage reports
  - [ ] Audit pyright/pydantic integration and type safety
  - [ ] Review pydantic model definitions for completeness

- [ ] **Documentation Audit**
  - [ ] Check for outdated documentation
  - [ ] Verify all public APIs have current docstrings
  - [ ] Update examples if functionality changes
  - [ ] Ensure Sphinx documentation builds

### Monthly Checks

- [ ] **Dependency Updates**
  - [ ] Review and update Poetry dependencies
  - [ ] Check for security updates in dependencies
  - [ ] Update development tools if needed
  - [ ] Test with latest Python versions

- [ ] **Security Review**
  - [ ] Run security scanning tools
  - [ ] Review authentication and credential handling
  - [ ] Check for any security best practice updates
  - [ ] Audit external API integrations

- [ ] **Performance Review**
  - [ ] Profile API client performance
  - [ ] Identify optimization opportunities
  - [ ] Review memory usage patterns
  - [ ] Test with large datasets

### Quarterly Checks

- [ ] **Architecture Review**
  - [ ] Evaluate class structure and organization
  - [ ] Consider consolidation opportunities
  - [ ] Review naming conventions and standards
  - [ ] Assess error handling patterns

- [ ] **Tool Updates**
  - [ ] Update pytest, pyright, and other tools
  - [ ] Review and update pre-commit hooks
  - [ ] Evaluate new testing frameworks
  - [ ] Update Sphinx and documentation tools

## Emergency Procedures

### Hotfix Process

For critical issues requiring immediate fixes:

1. Create hotfix branch from master: `git checkout -b hotfix/critical-issue`
2. Make minimal necessary changes
3. Follow abbreviated pre-merge checklist (focus on critical items)
4. Merge directly to master after review
5. Tag release if appropriate

### Rollback Procedures

If issues are discovered after merge:

1. Identify the problematic commit
2. Create rollback branch: `git checkout -b rollback/issue-description`
3. Revert problematic changes
4. Follow full pre-merge checklist
5. Merge rollback to master

## Development Environment Setup

For detailed development environment setup instructions, including prerequisites,
initial setup, running tests, and code quality checks, see
[docs/development.md](docs/development.md).

## Notes

- All agents should reference this workflow before starting work
- This workflow should be updated as the repository evolves
- Any deviations from this workflow should be documented and justified
- Regular reviews of this workflow ensure it remains current and effective
- Focus on implementing the core API client functionality first, then add advanced features
- Prioritize error handling and logging implementation early in development
