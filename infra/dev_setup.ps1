# Dev setup for Windows PowerShell
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$RepoRoot = Resolve-Path "$ScriptDir\.."
$VenvPath = Join-Path $RepoRoot ".venv"

if (-not (Test-Path $VenvPath)) {
    Write-Host "Creating venv at $VenvPath"
    python -m venv $VenvPath
} else {
    Write-Host "Venv already exists at $VenvPath"
}

$pip = Join-Path $VenvPath "Scripts\pip.exe"
$python = Join-Path $VenvPath "Scripts\python.exe"
$req = Join-Path $RepoRoot "apps\backend\requirements.txt"

if (-not (Test-Path $req)) {
    Write-Error "Requirements file not found: $req"
    exit 1
}

Write-Host "Installing backend requirements..."
& $pip install -r $req

Write-Host "Running backend unit tests..."
& $python -m pytest -q apps/backend/tests

Write-Host "Dev setup complete. Activate the venv with:"
Write-Host "  PowerShell: $VenvPath\\Scripts\\Activate.ps1"
Write-Host "  Cmd.exe:   $VenvPath\\Scripts\\activate.bat"
