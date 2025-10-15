# Utility Scripts

This directory contains utility scripts for the bw-serve-client project. These scripts are not part of the main library but are useful for development, documentation, and maintenance tasks.

## Available Scripts

### Route Extraction Script (`extract_routes.py`)

This script extracts API routes from the Bitwarden Vault Management API swagger/OpenAPI specification file and generates formatted output for documentation and comparison purposes.

## Features

- **Multiple output formats**: Markdown, plain text, and JSON
- **Comprehensive extraction**: Extracts all HTTP methods, paths, summaries, descriptions, and tags
- **Organized output**: Groups routes by their API tags for better readability
- **Command-line interface**: Easy to use with various options

## Usage

```bash
# Basic usage (markdown format to stdout)
python3 scripts/extract_routes.py docs/vault-management-api.json

# Save to file
python3 scripts/extract_routes.py -o routes.md docs/vault-management-api.json

# Text format
python3 scripts/extract_routes.py -f text -o routes.txt docs/vault-management-api.json

# JSON format for programmatic use
python3 scripts/extract_routes.py -f json -o routes.json docs/vault-management-api.json
```

## Command Line Options

- `--format, -f`: Output format (markdown, text, json) - default: markdown
- `--output, -o`: Output file - default: stdout
- `--help, -h`: Show help message

## Output Formats

### Markdown

- Groups routes by API tags
- Includes HTTP method badges
- Shows summaries and descriptions
- Ready for documentation

### Text

- Simple text format
- Organized by tags
- Includes summaries
- Good for quick reference

### JSON

- Machine-readable format
- Complete route information
- Includes parameters and response codes
- Suitable for programmatic processing

## Examples

```bash
# Generate markdown documentation
python3 scripts/extract_routes.py docs/vault-management-api.json > API_ROUTES.md

# Create a simple text reference
python3 scripts/extract_routes.py -f text -o routes.txt docs/vault-management-api.json

# Extract for programmatic use
python3 scripts/extract_routes.py -f json -o api_routes.json docs/vault-management-api.json
```

## Requirements

- Python 3.6+
- No external dependencies (uses only standard library)

## Integration

This script is designed to be run whenever the swagger file is updated to ensure documentation stays current with the API specification.
