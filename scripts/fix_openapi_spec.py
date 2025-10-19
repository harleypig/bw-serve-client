#!/usr/bin/env python3
"""Fix OpenAPI specification for Bitwarden Vault Management API.

This script applies systematic fixes to the original Bitwarden OpenAPI spec
to make it suitable for code generation with datamodel-code-generator.

Usage:
    python scripts/fix_openapi_spec.py
"""

import json
import re
import sys
from pathlib import Path
from typing import Dict, Any, List


class OpenAPISpecFixer:
    """Applies systematic fixes to OpenAPI specifications."""
    
    def __init__(self, fixes_config_path: str):
        """Initialize with fixes configuration.
        
        Args:
            fixes_config_path: Path to JSON file containing fix configurations
        """
        with open(fixes_config_path) as f:
            self.fixes = json.load(f)
        self.changes_made = []
    
    def fix_syntax_errors(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Fix basic syntax errors in the spec.
        
        Args:
            spec: OpenAPI specification dictionary
            
        Returns:
            Fixed specification
        """
        syntax_fixes = self.fixes.get("syntax_fixes", {})
        path_corrections = syntax_fixes.get("path_corrections", {})
        
        # Fix path syntax errors
        if "paths" in spec:
            paths_to_fix = {}
            for old_path, new_path in path_corrections.items():
                if old_path in spec["paths"]:
                    paths_to_fix[old_path] = new_path
                    self.changes_made.append(f"Fixed path: {old_path} -> {new_path}")
            
            # Apply path fixes
            for old_path, new_path in paths_to_fix.items():
                spec["paths"][new_path] = spec["paths"].pop(old_path)
        
        return spec
    
    def add_response_schemas(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Add missing response schemas to endpoints.
        
        Args:
            spec: OpenAPI specification dictionary
            
        Returns:
            Specification with added response schemas
        """
        response_config = self.fixes.get("response_schemas", {})
        endpoints = response_config.get("endpoints", {})
        
        for endpoint_key, response_def in endpoints.items():
            # Parse endpoint key like "GET /object/item/{id}"
            method, path = endpoint_key.split(" ", 1)
            method = method.lower()
            
            if (path in spec.get("paths", {}) and 
                method in spec["paths"][path] and
                "responses" in spec["paths"][path][method]):
                
                # Add/update response definitions
                for status_code, schema_def in response_def.items():
                    if status_code in spec["paths"][path][method]["responses"]:
                        # Update existing response with schema
                        existing_response = spec["paths"][path][method]["responses"][status_code]
                        if "content" not in existing_response:
                            existing_response["content"] = {}
                        if "application/json" not in existing_response["content"]:
                            existing_response["content"]["application/json"] = {}
                        
                        # Add the schema
                        existing_response["content"]["application/json"]["schema"] = schema_def["content"]["application/json"]["schema"]
                        
                        # Update description if provided
                        if "description" in schema_def:
                            existing_response["description"] = schema_def["description"]
                        
                        self.changes_made.append(f"Added response schema: {method.upper()} {path} {status_code}")
        
        return spec
    
    def add_descriptions(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Add missing descriptions to schemas and properties.
        
        Args:
            spec: OpenAPI specification dictionary
            
        Returns:
            Specification with added descriptions
        """
        descriptions_config = self.fixes.get("descriptions", {})
        
        # Add schema descriptions
        schema_descriptions = descriptions_config.get("schemas", {})
        if "components" in spec and "schemas" in spec["components"]:
            for schema_name, description in schema_descriptions.items():
                if schema_name in spec["components"]["schemas"]:
                    if "description" not in spec["components"]["schemas"][schema_name]:
                        spec["components"]["schemas"][schema_name]["description"] = description
                        self.changes_made.append(f"Added schema description: {schema_name}")
        
        # Add property descriptions
        property_descriptions = descriptions_config.get("properties", {})
        if "components" in spec and "schemas" in spec["components"]:
            for schema_name, props in property_descriptions.items():
                if (schema_name in spec["components"]["schemas"] and
                    "properties" in spec["components"]["schemas"][schema_name]):
                    
                    schema_props = spec["components"]["schemas"][schema_name]["properties"]
                    for prop_name, prop_description in props.items():
                        if (prop_name in schema_props and
                            "description" not in schema_props[prop_name]):
                            schema_props[prop_name]["description"] = prop_description
                            self.changes_made.append(f"Added property description: {schema_name}.{prop_name}")
        
        return spec
    
    def fix_parameters(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Fix parameter definitions.
        
        Args:
            spec: OpenAPI specification dictionary
            
        Returns:
            Specification with fixed parameters
        """
        param_fixes = self.fixes.get("parameter_fixes", {})
        
        # Add global parameter definitions if missing
        global_params = param_fixes.get("global_parameters", {})
        if global_params:
            if "components" not in spec:
                spec["components"] = {}
            if "parameters" not in spec["components"]:
                spec["components"]["parameters"] = {}
            
            for param_name, param_def in global_params.items():
                if param_name not in spec["components"]["parameters"]:
                    spec["components"]["parameters"][param_name] = param_def
                    self.changes_made.append(f"Added global parameter: {param_name}")
        
        return spec
    
    def apply_all_fixes(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Apply all configured fixes to the specification.
        
        Args:
            spec: Original OpenAPI specification
            
        Returns:
            Fixed specification
        """
        print("🔧 Applying OpenAPI spec fixes...")
        
        spec = self.fix_syntax_errors(spec)
        spec = self.add_response_schemas(spec)
        spec = self.add_descriptions(spec)
        spec = self.fix_parameters(spec)
        
        return spec
    
    def print_summary(self):
        """Print summary of changes made."""
        if self.changes_made:
            print(f"\n✅ Applied {len(self.changes_made)} fixes:")
            for change in self.changes_made:
                print(f"   • {change}")
        else:
            print("\n⚠️  No fixes were applied")


def main():
    """Main function to fix the OpenAPI specification."""
    script_dir = Path(__file__).parent
    
    # File paths
    original_spec = script_dir / "vault-management-api.json"
    fixed_spec = script_dir / "vault-management-api-fixed.json"
    fixes_config = script_dir / "spec-fixes.json"
    
    # Check if files exist
    if not original_spec.exists():
        print(f"❌ Original spec not found: {original_spec}")
        sys.exit(1)
    
    if not fixes_config.exists():
        print(f"❌ Fixes config not found: {fixes_config}")
        sys.exit(1)
    
    try:
        # Load original specification
        print(f"📖 Loading original spec: {original_spec}")
        with open(original_spec) as f:
            spec = json.load(f)
        
        # Apply fixes
        fixer = OpenAPISpecFixer(str(fixes_config))
        fixed_spec_data = fixer.apply_all_fixes(spec)
        
        # Write fixed specification
        print(f"💾 Writing fixed spec: {fixed_spec}")
        with open(fixed_spec, 'w') as f:
            json.dump(fixed_spec_data, f, indent=2)
        
        # Print summary
        fixer.print_summary()
        print(f"\n🎉 Fixed specification written to: {fixed_spec}")
        
    except json.JSONDecodeError as e:
        print(f"❌ JSON parsing error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
