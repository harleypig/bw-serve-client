# Notes about the templates

Since we're using `mustache` for the templating, and to save some typing,
unless otherwise specified a file is assumed to be a `mustache` template.

## Models

```plaintext
model.mustache
│
├── model_doc.mustache
│
├── model_generic.mustache
│   ├── partial_header.mustache
│
├── model_oneof.mustache
│   ├── partial_header.mustache
│
├── model_anyof.mustache
│   ├── partial_header.mustache
│
└── model_enum.mustache
    ├── partial_header.mustache
```

### model_doc

Generates documentation for a model.

This template is used for each model to create a Markdown file that documents
the properties, types, descriptions, and notes for the model. It's included
when documentation for models is generated.

### model_oneof

- **Purpose**: Defines a model class for a schema that uses the `oneOf` keyword.
- **Included When**: This template is included when a schema specifies that it can be one of several different types. It generates a Python class that can handle validation and serialization of one of the specified types.

### model_enum

- **Purpose**: Defines an enumeration class.
- **Included When**: This template is used when a schema defines an enumeration type. It generates a Python class that represents the enum and includes methods for serialization and deserialization.

### model_generic

- **Purpose**: Defines a generic model class.
- **Included When**: This template is the default for generating model classes. It's used when a schema defines a regular object with properties and does not use `oneOf`, `anyOf`, or `allOf`.

### model_test

- **Purpose**: Generates unit test stubs for a model.
- **Included When**: This template is used to create a test file for each model. It provides a structure for writing unit tests, including setup and teardown methods, and placeholders for test cases.

### model_anyof

- **Purpose**: Defines a model class for a schema that uses the `anyOf` keyword.
- **Included When**: This template is included when a schema specifies that it can be any of several different types. It generates a Python class that can handle validation and serialization of any one of the specified types.

### model

- **Purpose**: The main entry point for model template generation.
- **Included When**: This template is used as the main entry point for generating model code. It includes other templates based on the type of model being generated (enum, oneOf, anyOf, or generic).

Each of these templates is part of a code generation process that typically occurs when the OpenAPI Generator CLI tool is used to generate client libraries from an OpenAPI specification. The templates are included based on the structure and requirements of the API schema defined in the OpenAPI document.
