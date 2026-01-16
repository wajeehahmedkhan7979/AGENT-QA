# PowerShell smoke runner (Windows-friendly). This will start core containers and run a basic POST /jobs smoke.
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
Push-Location $ScriptDir

Write-Host "Starting core containers..."
# Use docker compose (modern syntax) instead of docker-compose
docker compose up -d --build backend sample-app db redis

Write-Host "Waiting for backend to be healthy..."
$attempts = 0
while ($attempts -lt 30) {
  try {
    $r = Invoke-WebRequest -UseBasicParsing -Uri 'http://localhost:8000/health' -ErrorAction Stop
    Write-Host "[OK] Backend is healthy!"
    break
  } catch {
    $attempts++
    Write-Host "  Attempt $attempts/30 - backend not yet healthy..."
    Start-Sleep -Seconds 2
  }
}

if ($attempts -ge 30) {
  Write-Host "[ERROR] Backend did not become healthy in time"
  exit 1
}

Write-Host "Running smoke test: creating a job..."
$body = @{
  targetUrl = "http://sample-app:3000/sample-app/login"
  scope = "read-only"
  testProfile = "functional"
  ownerId = "ci_user"
} | ConvertTo-Json

try {
  $response = Invoke-WebRequest -UseBasicParsing -Uri 'http://localhost:8000/jobs' `
    -Method Post `
    -Headers @{'Content-Type'='application/json'} `
    -Body $body `
    -ErrorAction Stop
  Write-Host "[OK] Job creation succeeded"
  Write-Host "Response: $($response.Content)"
} catch {
  Write-Host "[ERROR] Job creation failed: $($_.Exception.Message)"
  exit 1
}

Write-Host "Cleaning up containers..."
docker compose down -v
Write-Host "[OK] Smoke test completed successfully!"
