#!/bin/bash

COMMIT_ID="828bf01"
REPO_URL="https://github.com/microsoft/verus-proof-synthesis.git"

# Navigate to script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

git clone "$REPO_URL" code
pushd code
git checkout "$COMMIT_ID"

if [ $? -ne 0 ]; then
    echo "Failed to clone repository. Exiting."
    exit 1
fi