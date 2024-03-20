# Notes about the templates

Since we're using `mustache` for the templating, and to save some typing,
unless otherwise specified a file is assumed to be a `mustache` template.

## Vendor Extensions


## Models

A simple tree of templates being included.

```plaintext
model
├── model_oneof
│   └── partial_header
├── model_anyof
│   └── partial_header
├── model_enum
└── model_generic
    └── partial_header
```

* `model_doc` is being called during documentation process.
* `model_test` is being called during test writing process.

### `model`

The main entry point for model template generation.

This template is used as the main entry point for generating model code. It
includes other templates based on the type of model being generated (enum,
oneOf, anyOf, or generic).

### `model_enum`

Defines an enumeration class.

This template is used when a schema defines an enumeration type. It generates
a Python class that represents the enum and includes methods for serialization
and deserialization.

### `model_oneof`

Defines a model class for a schema that uses the `oneOf` keyword.

This template is included when a schema specifies that it can be one of
several different types. It generates a Python class that can handle
validation and serialization of one of the specified types.

### `model_anyof`

Defines a model class for a schema that uses the `anyOf` keyword.

This template is included when a schema specifies that it can be any of
several different types. It generates a Python class that can handle
validation and serialization of any one of the specified types.

### `model_generic`

Defines a generic model class.

This template is the default for generating model classes. It's used when
a schema defines a regular object with properties and does not use `oneOf`,
`anyOf`, or `allOf`.

### `model_doc`

Generates documentation for a model.

This template is used for each model to create a Markdown file that documents
the properties, types, descriptions, and notes for the model. It's included
when documentation for models is generated.

### `model_test`

Generates unit test stubs for a model.

This template is used to create a test file for each model. It provides
a structure for writing unit tests, including setup and teardown methods, and
placeholders for test cases.
