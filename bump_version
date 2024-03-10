#!/bin/bash

# Check if a version number is provided
if [ "$#" -ne 2 ]; then
    echo "Usage: $0 vX.Y.Z 'message'"
    exit 1
fi

# Extract the version number without the 'v' prefix
VERSION=${1#v}

# Update the __version__ variable in __init__.py
sed -i "s/^__version__ = .*/__version__ = '${VERSION}'/" bw_serve_client/__init__.py

# Commit the change
git add bw_serve_client/__init__.py
git commit -m "Update version to ${VERSION}"

# Tag the commit with the provided message
git tag -a "$1" -m "$2"

# Push the changes and tags to the remote repository
git push origin main --tags
