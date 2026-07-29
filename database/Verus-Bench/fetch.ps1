$COMMIT_ID = "78dea1fe92"
$REPO_URL = "https://github.com/microsoft/verus-proof-synthesis.git"

# Navigate to script directory
$SCRIPT_DIR = Split-Path -Parent $PSCommandPath
Push-Location $SCRIPT_DIR

# Enable long paths support on Windows
git config --global core.longpaths true

git clone "$REPO_URL" code
Push-Location code
git checkout "$COMMIT_ID"

if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to clone repository. Exiting."
    exit 1
}
