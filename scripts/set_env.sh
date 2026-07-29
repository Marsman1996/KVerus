#!/usr/bin/env bash

if [[ -n "$ZSH_VERSION" ]]; then
    # Zsh-specific
    SCRIPT_DIR="$(cd -- "$(dirname -- "${(%):-%N}")" && pwd)"
elif [[ -n "$BASH_VERSION" ]]; then
    # Bash-specific
    SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
else
    echo "Unsupported shell" >&2
    return 1
fi

echo "Setting up environment variables..."
export PATH="$SCRIPT_DIR/../database/CortenMM/code/tools/verus/source/target-verus/release:$PATH"
echo "Add $SCRIPT_DIR/../database/CortenMM/code/tools/verus/source/target-verus/release to PATH"