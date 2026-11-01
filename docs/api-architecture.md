# API Architecture and Resource Classes

This document describes the resource classes bw-serve-client exports and the
`bw serve` routes each one calls, as defined by the Bitwarden Vault
Management API.

Every class is constructed from a shared `ApiClient`, with an optional
logger and error handler that default to the client's. Each public method
calls exactly one route, and declares it with `@route(METHOD, path)`. Every
class has a runnable example in [`examples/`][examples], named for the class
in snake case (`examples/vault_items.py` for `VaultItems`).

When the error handler returns a failure instead of raising it, the method
returns the handler's value in place of its result.

## Resource Classes

### Folders

| Method   | Route                        |
|----------|------------------------------|
| `add`    | `POST /object/folder`        |
| `modify` | `PUT /object/folder/{id}`    |
| `get`    | `GET /object/folder/{id}`    |
| `delete` | `DELETE /object/folder/{id}` |
| `list`   | `GET /list/object/folders`   |

Results are `Folder` models. Deleting a folder does not delete its items;
`bw serve` moves them to "No Folder".

### VaultItems

| Method    | Route                         |
|-----------|-------------------------------|
| `list`    | `GET /list/object/items`      |
| `add`     | `POST /object/item`           |
| `modify`  | `PUT /object/item/{id}`       |
| `get`     | `GET /object/item/{id}`       |
| `delete`  | `DELETE /object/item/{id}`    |
| `restore` | `POST /restore/item/{id}`     |
| `archive` | `POST /archive/{object}/{id}` |

- `get` takes an item id or, in its place, a keyword `search` term; give
  exactly one. An ambiguous search is a `ValidationError` listing the
  matching ids, and an id that is not a UUID is refused, never searched for.
- `modify` replaces the whole item, so pass the full object, usually one
  fetched with `get` and changed. It cannot remove an item from a collection
  or change its organization: those are `OrgCollections`'
  `modify_item_collections` and `move`.
- `delete` moves the item to the trash unless `permanent=True`; `restore`
  brings an item back from the trash or the archive.
- `archive` needs a premium account and does not apply to organization
  items.

### Attachments

| Method   | Route                            |
|----------|----------------------------------|
| `add`    | `POST /attachment`               |
| `get`    | `GET /object/attachment/{id}`    |
| `delete` | `DELETE /object/attachment/{id}` |

`add` uploads a path, bytes or a binary file object; bytes and file objects
need a `file_name`. `get` returns the file's exact bytes. An attachment id is
the one listed in the item's `attachments`, not a UUID, and `get` and
`delete` also take the id of the item it is on.

### ItemFields

| Method     | Route                       |
|------------|-----------------------------|
| `username` | `GET /object/username/{id}` |
| `password` | `GET /object/password/{id}` |
| `uri`      | `GET /object/uri/{id}`      |
| `totp`     | `GET /object/totp/{id}`     |
| `notes`    | `GET /object/notes/{id}`    |
| `exposed`  | `GET /object/exposed/{id}`  |

Each method reads one field of an item, named by its id; a search term is
refused before sending. `password` and `totp` return a `SecretStr`, and
`exposed` returns the breach count as an `int`.

### Sends

| Method            | Route                             |
|-------------------|-----------------------------------|
| `add`             | `POST /object/send`               |
| `modify`          | `PUT /object/send/{id}`           |
| `get`             | `GET /object/send/{id}`           |
| `delete`          | `DELETE /object/send/{id}`        |
| `list`            | `GET /list/object/send`           |
| `remove_password` | `POST /send/{id}/remove-password` |

Only text Sends are supported. A Send's `key`, `password` and `accessUrl`
come back as `SecretStr`. `modify` replaces the whole Send: `disabled` is
always sent and defaults to `False`, so modifying a disabled Send without
`disabled=True` enables it again.

### VaultControl

| Method   | Route          |
|----------|----------------|
| `lock`   | `POST /lock`   |
| `unlock` | `POST /unlock` |
| `sync`   | `POST /sync`   |
| `status` | `GET /status`  |

The master password and the session key travel as `SecretStr`. `bw serve`
keeps the session itself, so the key `unlock` returns is only for a caller
that also drives the `bw` CLI. `status` works on a locked vault.

### Utilities

| Method        | Route                         |
|---------------|-------------------------------|
| `template`    | `GET /object/template/{type}` |
| `fingerprint` | `GET /object/fingerprint/me`  |
| `generate`    | `GET /generate`               |

`template` and `fingerprint` raise a `UserError` while the vault is locked;
`generate` works either way. With no arguments `generate` returns a
14-character password of letters and digits. Naming any of the four
character sets turns off every set not named. `avoid_ambiguous` leaves out
`I`, `O`, `l`, `0` and `1`; it is sent as the spec's `ambiguous`
parameter.

### Organizations

| Method           | Route                            |
|------------------|----------------------------------|
| `get`            | `GET /object/organization/{id}`  |
| `list_members`   | `GET /list/object/org-members`   |
| `confirm_member` | `POST /confirm/org-member/{id}`  |
| `list`           | `GET /list/object/organizations` |

`get` reads the vault's local state as of its last sync.

### OrgCollections

| Method                    | Route                                  |
|---------------------------|----------------------------------------|
| `add`                     | `POST /object/org-collection`          |
| `modify`                  | `PUT /object/org-collection/{id}`      |
| `get`                     | `GET /object/org-collection/{id}`      |
| `delete`                  | `DELETE /object/org-collection/{id}`   |
| `get_collection`          | `GET /object/collection/{id}`          |
| `move`                    | `POST /move/{itemid}/{organizationId}` |
| `modify_item_collections` | `PUT /object/item-collections/{id}`    |
| `list_collections`        | `GET /list/object/collections`         |
| `list`                    | `GET /list/object/org-collections`     |

Two families read collections. `get` and `list` go to the server, need
administrative rights in the organization or the **Can Manage** permission,
and return groups and users. `get_collection` and `list_collections` read
the vault's local state as of its last sync, across every organization.
`move` takes a personal item into an organization;
`modify_item_collections` replaces an organization item's collections
outright, and is the only way to take an item out of one.

### DeviceApproval

| Method        | Route                                                         |
|---------------|---------------------------------------------------------------|
| `approve`     | `POST /device-approval/{organizationId}/approve/{request-id}` |
| `approve_all` | `POST /device-approval/{organizationId}/approve-all`          |
| `deny`        | `POST /device-approval/{organizationId}/deny/{request-id}`    |
| `deny_all`    | `POST /device-approval/{organizationId}/deny-all`             |
| `list`        | `GET /device-approval/{organizationId}`                       |

**Commercial CLI build only.** The open-source `bw serve` has none of these
routes and answers each with a 404, which arrives as a `ValidationError`
with `status_code` 404. The account also needs permission to manage the
organization's users' passwords.

## Routes Not Offered

Two spec routes have no method. [`tests/route_exclusions.json`][exclusions]
lists them with their reasons, and the route coverage test fails on any
other undeclared route.

- `GET /object/item-collections/{id}` is documented, but `bw serve` answers
  it with a 400. An item's `collection_ids` carries the same list.
- `GET /send/list` is an alias of `GET /list/object/send`, which
  `Sends.list` uses. `bw serve` answers the alias with every Send's `key`
  empty and an `accessUrl` ending in `/undefined`, so its Sends cannot be
  opened.

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
- **Tags**: Group related routes into the same class, mostly; a class may
  span tags where its routes belong together
- **Security**: Nothing to implement; `bw serve` has no endpoint auth
- **Schemas**: Definitions of data structures for request and response bodies,
  used to create corresponding Python classes or types

Each class or class method MUST:

- Use summary, description, and/or tags as available from the API definition
  or create as needed for documentation
- Hand every failure to the error handler, and return its value when it
  returns instead of raising
- Log various levels of information
- Declare its route with `@route(METHOD, path)`; each public method calls
  one route, named for the operation (`add`, `modify`, `get`, `delete`,
  `list`, and so on)
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

As built, validation and user errors default to `WARNING`, and
external-service and internal errors to `ERROR`. The default handler raises
at `WARNING` and above, so every error raises out of the box; passing
`error_level=logging.ERROR` returns validation and user errors instead.

## API Class Requirements

An API class MUST handle:

- Failures through the error handler, raising or returning as it decides
- Log various levels of information
- General API errors, such as 500 errors
- No authentication: `bw serve` has none on its endpoints, because the
  session lives in the `bw serve` process
- Formatting of data into JSON (or proper format the API expects)
- Formatting of JSON (or whatever format the API returns) into data
- Validate parameters before making requests
- Handle different HTTP status codes appropriately
- Provide clear error messages for different failure scenarios

## Type Safety and Data Validation

All API classes MUST implement:

- **Complete type hints**: All public methods must have type annotations
- **Pydantic models**: Use pydantic for all request/response data structures
- **Runtime validation**: Validate data before sending to API and after
  receiving
- **Static analysis**: Code must pass type checking
- **Model definitions**: Create pydantic models for all API data structures
- **Type safety**: pyright and pydantic integration for comprehensive type
  checking

[examples]: ../examples/
[exclusions]: ../tests/route_exclusions.json
