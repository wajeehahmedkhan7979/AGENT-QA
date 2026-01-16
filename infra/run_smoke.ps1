# PowerShell smoke runner (Windows-friendly). This will start core containers and run a basic POST /jobs smoke.
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
Push-Location $ScriptDir

Write-Host "Starting core containers..."
docker-compose up -d --build backend sample-app db redis

Write-Host "Waiting for backend to be healthy..."
$attempts = 0
while ($attempts -lt 30) {
  try {
    $r = Invoke-WebRequest -UseBasicParsing -Uri 'http://localhost:8000/health' -ErrorAction Stop -TimeoutSec 2
    if ($r.StatusCode -eq 200) { break }
  } catch { }
  Start-Sleep -Seconds 2
  $attempts++
}
if ($attempts -ge 30) {
  Write-Error 'Backend did not become healthy in time'
  docker-compose down -v
  Pop-Location
  exit 1
}

Write-Host "Backend healthy; creating a demo job..."
$body = '{
  "targetUrl":"http://sample-app:3000/sample-app/login",
  "scope":"read-only",
  "testProfile":"functional",
  "ownerId":"ci_user"
}'

Invoke-RestMethod -Method Post -Uri 'http://localhost:8000/jobs' -ContentType 'application/json' -Body $body

Write-Host "Smoke POST completed; tearing down containers..."
docker-compose down -v

Pop-Location
