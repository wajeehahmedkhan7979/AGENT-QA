#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Clean up any lingering containers/networks from previous runs
echo "Cleaning up previous containers..."
docker compose down -v --remove-orphans 2>/dev/null || true

# Use docker compose (modern syntax) instead of docker-compose
echo "Starting containers..."
docker compose up -d --build backend sample-app db redis

echo "Waiting for backend to be healthy..."
attempts=0
until curl -sf http://localhost:8000/health > /dev/null; do
  attempts=$((attempts + 1))
  if [ "$attempts" -gt 30 ]; then
    echo "Backend did not become healthy in time"
    docker compose logs backend
    exit 1
  fi
  sleep 2
done

echo "Backend is healthy, running a simple job creation smoke test..."
curl -sf -X POST "http://localhost:8000/jobs" \
  -H "Content-Type: application/json" \
  -d '{
    "targetUrl": "http://sample-app:3000/sample-app/login",
    "scope": "read-only",
    "testProfile": "functional",
    "ownerId": "ci_user"
  }' > /dev/null

echo "Smoke test succeeded."

docker compose down -v
