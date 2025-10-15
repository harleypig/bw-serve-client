# API Architecture and Planned Classes

This document outlines the planned class structure and API routes for the
bw-serve-client Python library based on the Bitwarden Vault Management API.

## Planned Class Structure

Based on the API routes, the following classes should be implemented:

### VaultItems
- `/list/object/items` (GET)
- `/object/item` (POST)
- `/object/item/{id}` (GET, PUT, DELETE)
- `/restore/item/{id}` (POST)

### Attachments
- `/attachment` (POST)
- `/object/attachment/{id}` (GET, DELETE)

### ItemFields
- `/object/username/{id}` (GET)
- `/object/password/{id}` (GET)
- `/object/uri/{id}` (GET)
- `/object/totp/{id}` (GET)
- `/object/notes/{id}` (GET)
- `/object/exposed/{id}` (GET)

### Folders
- `/object/folder` (POST)
- `/object/folder/{id}` (GET, PUT, DELETE)
- `/list/object/folders` (GET)

### VaultControl
- `/lock` (POST)
- `/unlock` (POST)
- `/sync` (POST)
- `/status` (GET)

### Utilities
- `/generate` (GET)
- `/object/template/{type}` (GET)
- `/object/fingerprint/me` (GET)

## Class Implementation Guidelines

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

## Error/Logging Module Requirements

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

## API Class Requirements

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