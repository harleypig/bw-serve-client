# Thinking about how to do this library

Looking at the output of the analysis script, I think we need to have the
following classes.

## Core Architecture Components

### 1. `ApiClient` (Base Communication Layer)

**Purpose**: Handles all HTTP communication with the Bitwarden Vault Management API

**Responsibilities**:

- HTTP request/response handling
- Authentication (session-based via `bw serve`)
- Data serialization/deserialization (JSON, multipart/form-data)
- Error handling and HTTP status code management
- Base URL and endpoint management
- Request/response logging

**Key Methods**:

- `_make_request(method, endpoint, data=None, params=None, files=None)`
- `_serialize_data(data, content_type)`
- `_deserialize_response(response)`
- `_handle_error(response)`

**Dependencies**: `requests`, `pydantic` for validation

### 2. `BaseModel` (Data Models Foundation)

**Purpose**: Pydantic-based data models for all API request/response objects

**Key Models**:

- `VaultItem` (base item with common fields)
- `LoginItem`, `CardItem`, `IdentityItem`, `SecureNoteItem` (item types)
- `Folder`, `Collection`, `Organization`
- `Attachment`, `Field`
- `Send` (for Send functionality)
- Request/Response wrappers for each endpoint

**Features**:

- Type validation and coercion
- JSON serialization/deserialization
- Field validation (required, optional, format validation)
- Nested object handling

### 3. `RouteHandler` (Endpoint Management)

**Purpose**: Maps API endpoints to class methods with parameter handling

**Responsibilities**:

- Path parameter extraction and validation
- Query parameter handling
- Request body construction
- Response parsing and object creation
- Method signature generation based on API spec

**Pattern**:

```python
def get_item(self, item_id: str) -> VaultItem:
    return self._client.get(f"/object/item/{item_id}")
```

### 4. `ErrorHandler` (Error Management)

**Purpose**: Centralized error handling and logging

**Features**:

- HTTP status code mapping to custom exceptions
- API-specific error message parsing
- Logging configuration (debug, info, warning, error)
- Retry logic for transient failures
- User-friendly error messages

**Exception Hierarchy**:

- `BitwardenAPIError` (base)
- `AuthenticationError`, `ValidationError`, `NotFoundError`, `ServerError`

## Domain-Specific Classes

Based on the API analysis, organize into these main classes:

### 1. `VaultItems`

- CRUD operations for vault items
- Item type-specific methods (login, card, identity, secure note)
- Item restoration and deletion

### 2. `Attachments`

- File upload/download
- Attachment metadata management
- Multipart form data handling

### 3. `ItemFields`

- Username, password, TOTP retrieval
- URI and notes management
- Security exposure checking

### 4. `Folders`

- Folder CRUD operations
- Folder hierarchy management

### 5. `Collections`

- Collection management
- Organization membership
- Item-to-collection assignment

### 6. `VaultControl`

- Lock/unlock operations
- Sync functionality
- Status checking

### 7. `Utilities`

- Password generation
- Template retrieval
- Fingerprint management

### 8. `Send`

- Send creation and management
- Password removal from sends

## Implementation Strategy

### Phase 1: Core Infrastructure

1. `ApiClient` with basic HTTP handling
2. `BaseModel` with core Pydantic models
3. `ErrorHandler` with basic error management
4. Basic authentication flow
5. Create tests with pytest

### Phase 2: Core Functionality

1. `VaultItems` class (most commonly used)
2. `VaultControl` for basic vault operations
3. `Folders` for organization
4. Create tests with pytest

### Phase 3: Advanced Features

1. `Attachments` with file handling
2. `Collections` and organization management
3. `Send` functionality
4. Create tests with pytest

### Phase 4: Polish and Optimization

1. Comprehensive error handling
2. Advanced logging and debugging
3. Performance optimizations
4. Full test coverage

## Key Design Decisions

### Type Safety

- Use Pydantic for all data models
- Full type hints throughout
- type checking compliance
- Runtime validation

### Error Handling

- Graceful degradation
- Clear error messages
- Configurable logging levels
- Retry mechanisms for transient failures

### API Design

- Method names match API endpoint patterns
- Intuitive parameter handling
- Consistent return types
- Clear documentation

### Testing Strategy

- Unit tests for all classes
- Mock external API calls
- Integration tests with real API
- Example usage in examples/ directory

## Questions to Resolve

1. **Authentication**: How to handle the `bw serve` session? Store session state?
2. **File Handling**: Best approach for multipart uploads and downloads?
3. **Caching**: Should we implement response caching for frequently accessed data?
4. **Async Support**: Do we need async/await support for the client?
5. **Configuration**: How to handle different environments (dev, staging, prod)?
6. **Rate Limiting**: How to handle API rate limits and backoff?
