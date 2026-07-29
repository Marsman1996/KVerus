# Remove and recreate build/bin directories
Remove-Item -Recurse -Force build -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Path build\bin | Out-Null

# Build Rust processor
#Push-Location processor/rust
# $env:CARGO_TARGET_DIR = "$PSScriptRoot\..\..\build"
# cargo build --release
# if ($LASTEXITCODE -ne 0) {
#    Write-Host "Rust processor build failed"
#    Exit 1
#}
#Pop-Location
#Copy-Item -Path build\release\PromeX-Rust -Destination build\bin
#Remove-Item -Recurse -Force build\release

# Build Verus processor
Push-Location processor\promex-verus
$env:CARGO_TARGET_DIR = "$PSScriptRoot\..\build"
cargo build --release
if ($LASTEXITCODE -ne 0) {
    Write-Host "Test failed"
    Exit 1
}
Pop-Location
Copy-Item -Path build\release\PromeX-Verus.exe -Destination build\bin
Remove-Item -Recurse -Force build\release