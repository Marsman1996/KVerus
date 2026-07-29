$COMMIT_ID = ""
$REPO_URL = "https://github.com/asterinas/vostd.git"
$BRANCH = "main-archive-20251225"

# Navigate to script directory
$SCRIPT_DIR = Split-Path -Parent $PSCommandPath
Push-Location $SCRIPT_DIR

git clone "$REPO_URL" code -b "$BRANCH"
Push-Location code

if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to clone repository. Exiting."
    exit 1
}

cargo xtask bootstrap
