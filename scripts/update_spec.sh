#!/bin/bash
# Update workflow for Bitwarden API client
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "🚀 Starting Bitwarden API client update workflow..."
echo "   Script dir: $SCRIPT_DIR"
echo "   Project root: $PROJECT_ROOT"

# Step 1: Fix the OpenAPI spec
echo ""
echo "🔧 Step 1: Fixing OpenAPI specification..."
cd "$PROJECT_ROOT"
python scripts/fix_openapi_spec.py

if [ $? -ne 0 ]; then
    echo "❌ Failed to fix OpenAPI spec"
    exit 1
fi

# Step 2: Generate models
echo ""
echo "🏗️  Step 2: Generating Pydantic models..."
datamodel-codegen

if [ $? -ne 0 ]; then
    echo "❌ Failed to generate models"
    exit 1
fi

# Step 3: Run pre-commit checks
echo ""
echo "🧹 Step 3: Running pre-commit checks..."
pre-commit run --all-files

if [ $? -ne 0 ]; then
    echo "⚠️  Pre-commit found issues (this is normal, they may be auto-fixed)"
    echo "   Running pre-commit again to verify fixes..."
    pre-commit run --all-files
fi

# Step 4: Run tests
echo ""
echo "🧪 Step 4: Running tests..."
pytest

if [ $? -ne 0 ]; then
    echo "❌ Tests failed"
    exit 1
fi

echo ""
echo "✅ Update workflow completed successfully!"
echo ""
echo "📋 Next steps:"
echo "   1. Review the generated code changes"
echo "   2. Update version number if needed"
echo "   3. Commit the changes"
echo "   4. Create a release if appropriate"
