#!/bin/bash

COMMIT_ID=""
REPO_URL="https://github.com/rikosellic/verus-mathspec-bench.git"

git clone "$REPO_URL" code
if [ $? -ne 0 ]; then
    echo "Failed to clone repository. Exiting."
    exit 1
fi