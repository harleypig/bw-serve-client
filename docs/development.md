# General Instructions

The goal is minimization; DRY principles (refer Pragmatic Programming), proper
and decent error handling and logging.

This is a poetry project. Make sure pyproject.toml is updated to match the
current state of the project.

Documentation MUST be created. The README should contain basic information.
Installation, contributing, development and usage documents MUST be created.
mkdocs and rst format (experiment with Sphinx).

General code examples MUST be included in the examples directory.

Workflows MUST be identified, documented and tested in the tests directory.

## Error/Logging Module

The Error/Logging module should be designed to be agnostic of specific error
object and logging implementations. It MUST:

- accept optional error handling and logging objects during the instantiation
    of an API class.
- if no custom error handler is provided, implement minimal error handling
    that can construct and return error objects based on a defined error level
    setting.
- if no custom logger is provided, use python's logging library
- allow users of the library to define the granularity of error reporting and
    logging by setting appropriate error level and log level thresholds.

## API Class Instructions

An API class MUST handle:

- gracefully returns errors when something isn't right
- logs various levels of information
- general api errors, such as 500 errors
- authentication (proper inclusion of bearer token or whatever)
- formatting of data into json (or proper format the api expects)
- formatting of json (or whatever format the api returns) into data

## Class Instructions

### General Class Instructions

When creating Python classes from API routes, consider the following elements
from the route definitions:

- HTTP Method: Determines the request method for class methods.
- Path: Helps define method names and routing within the class. Path
  parameters become method arguments.
- Parameters: Become the parameters of class methods, including handling of
  different parameter types.
- Request Body: For methods that send data, defines how to construct the
  request body from method arguments.
- Responses: Handling of different response types, affecting class method
  return types.
- Tags: Can group related routes into the same class.
- Security: Implementation of authentication methods for secured routes.
- Schemas: Definitions of data structures for request and response bodies,
  used to create corresponding Python classes or types.

Each class or class method MUST:

- use summary, description, and/or tags as available from the api definition
  or create as needed for documentation
- gracefully return errors when something isn't right
- logs various levels of information
- have a method that mirrors the name of the route being used
   - where a name uses multiple HTTP methods, the method should call the
     appropriate HTTP method based on the parameters passed
- validate the parameters
- ensure data is in correct format for sending to api
- provide unit tests in the tests directory
  - use pytest-mock to test functions that access external tools
- provide examples of usage in the examples directory

### Specific Class Instructions

PROMPT: Using the provided API JSON file, generate a class tree list that
organizes endpoints into classes based on their functionality and associated
HTTP methods. Use the data in this file as a template.

Item
  /list/object/items (GET)
  /object/item (POST)
  /object/item/{id} (GET, PUT, DELETE)
  /object/notes/{id} (GET)
  /object/password/{id} (GET)
  /object/totp/{id} (GET)
  /object/uri/{id} (GET)
  /object/username/{id} (GET)
  /restore/item/{id} (POST)

Send
  /list/object/send (GET)
  /object/send (POST)
  /object/send/{id} (GET, PUT, DELETE)
  /send/{id}/remove-password (POST)

Attachment
  /attachment (POST)
  /object/attachment/{id} (GET, DELETE)

Folder
  /list/object/folders (GET)
  /object/folder (POST)
  /object/folder/{id} (GET, PUT, DELETE)

Collection
  /list/object/collections (GET)
  /list/object/org-collections (GET)
  /object/org-collection (POST)
  /object/org-collection/{id} (GET, PUT, DELETE)

Organization
  /confirm/org-member/{id} (POST)
  /list/object/organizations (GET)
  /list/object/org-members (GET)

Template
  /object/template/{type} (GET)

Status
  /status (GET)

Sync
  /sync (POST)

Unlock
  /unlock (POST)

Lock
  /lock (POST)

Move
  /move/{itemid}/{organizationId} (POST)

Generate
  /generate (GET)

Exposed
  /object/exposed/{id} (GET)

Fingerprint
  /object/fingerprint/me (GET)
