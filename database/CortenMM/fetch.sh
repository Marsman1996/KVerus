#!/bin/bash

COMMIT_ID=""
REPO_URL="https://github.com/asterinas/vostd.git"
BRANCH="main-archive-20251225"

# Navigate to script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

git clone "$REPO_URL" code -b "$BRANCH"
if [ $? -ne 0 ]; then
    echo "Failed to clone repository. Exiting."
    exit 1
fi

pushd code
cargo xtask bootstrap
if [ $? -ne 0 ]; then
    echo "Failed to initialize Verus. Exiting."
    exit 1
fi