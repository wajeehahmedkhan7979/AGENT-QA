# Testing Guide

This document outlines how to test the Autonomous QA Automation WebApp demo.

## Prerequisites

- Docker Desktop installed and running
- Docker Compose v2+ installed
- Git (for cloning the repo)

## Quick Start Testing

### 1. Start the Full Stack

From the repo root:

```bash
cd infra
docker-compose up --build
```

This will start:
- Backend API (port 8000)
- Web UI (port 3100)
- Sample app (port 3000)
- Postgres database
- Redis
- MinIO (S3-compatible storage)
- Extractor worker
- Runner worker

Wait for all services to be healthy (check logs for "Application startup complete" from backend).

### 2. Health Check

```bash
curl http://localhost:8000/health
```

Expected: `{"status":"ok"}`

### 3. End-to-End Flow Test

#### Step 1: Create a Job

```bash
curl -X POST "http://localhost:8000/jobs" \
  -H "Content-Type: application/json" \
  -d '{
    "targetUrl": "http://sample-app:3000/sample-app/login",
    "scope": "read-only",
    "testProfile": "functional",
    "ownerId": "test_user"
  }'
```

Expected response:
- `jobId` (e.g., `job_abc123`)
- `status: "queued"`
- `preflight.allowed: true`
- `consent` array with one record

**Note the `jobId` from the response.**

#### Step 2: Wait for Extraction (10-30 seconds)

The extractor worker will:
1. Pick up the job from the queue
2. Load the page with Playwright
3. Capture DOM, HAR, screenshot, accessibility tree
4. Update job status

Check job status:

```bash
curl "http://localhost:8000/jobs/<jobId>"
```

Wait until you see artifacts available:

```bash
curl "http://localhost:8000/jobs/<jobId>/artifacts"
```

Expected: Array with at least:
- `dom.json`
- `screenshot.png`
- `trace.har`
- `accessibility.json`

#### Step 3: Generate Semantic Model

```bash
curl "http://localhost:8000/jobs/<jobId>/semantic"
```

Expected: JSON with:
- `semanticModel.elements` (array of UI elements with selectors, roles, labels)
- `semanticModel.flows` (inferred flows like login)
- `apiCatalog.endpoints` (XHR calls from HAR)

#### Step 4: Generate Test

```bash
curl -X POST "http://localhost:8000/jobs/<jobId>/generate"
```

Expected: JSON with:
- `testId` (e.g., `t_1`)
- `steps` (array of Playwright actions)
- `confidence` (0.0-1.0)
- `format: "playwright-json"`
- `status: "ready"` or `"needs_review"`

**Note the `testId` from the response.**

#### Step 5: Run the Test

```bash
curl -X POST "http://localhost:8000/tests/<testId>/run" \
  -H "Content-Type: application/json" \
  -d '{"jobId": "<jobId>"}'
```

Expected: JSON with:
- `runId`
- `testId`
- `jobId`
- `status: "queued"`

Wait 10-20 seconds for the runner to execute.

#### Step 6: View Test Report

```bash
curl "http://localhost:8000/jobs/<jobId>/report"
```

Expected: JSON with:
- `runId`
- `testId`
- `status: "passed"` or `"failed"`
- `steps` (array with step-by-step results)
- `artifacts` (screenshot paths)
- `startedAt`, `finishedAt` timestamps

### 4. UI Testing

Open `http://localhost:3100` in your browser.

1. **Submit a Job**:
   - Enter URL: `http://sample-app:3000/sample-app/login`
   - Select scope: `read-only`
   - Test profile: `functional`
   - Owner ID: `demo_user`
   - Click "Create Job"

2. **Wait and Refresh**:
   - Job appears in the list
   - Click "Refresh Status" to see extraction progress
   - Wait until artifacts are available

3. **Generate Test**:
   - Click "Generate Test"
   - Wait for test artifact to appear

4. **Run Test**:
   - Click "Run Test"
   - Wait 10-20 seconds
   - Click "Refresh Report" to see results

5. **View Artifacts**:
   - Artifacts list shows all captured files
   - Test result viewer shows step-by-step execution with screenshots

## Unit Tests (Inside Docker)

To run backend unit tests:

```bash
docker exec qa-backend python -m pytest /app/tests -v
```

Or from the repo root (if you have pytest installed locally):

```bash
cd apps/backend
pytest tests/ -v
```

## Integration Tests

The smoke test script (`infra/smoke.sh`) performs a minimal end-to-end check:

```bash
cd infra
./smoke.sh
```

Or manually:

```bash
# Start services
docker-compose up -d backend db redis sample-app

# Wait for health
sleep 5
curl http://localhost:8000/health

# Create a job
curl -X POST "http://localhost:8000/jobs" \
  -H "Content-Type: application/json" \
  -d '{
    "targetUrl": "http://sample-app:3000/sample-app/login",
    "scope": "read-only",
    "testProfile": "functional",
    "ownerId": "smoke_test"
  }'
```

## Test Scenarios

### Happy Path
- ✅ Create job → Extract → Generate → Run → Pass

### Edge Cases
- **Robots.txt disallowed**: Submit a URL that disallows crawlers (should set status to `rejected`)
- **Missing semantic elements**: Submit a page with no buttons/inputs (should still generate a minimal test)
- **Low confidence test**: Generate a test with confidence < 0.8 (should set status to `needs_review`)

### Failure Cases
- **Invalid URL**: Submit a non-existent URL (extraction should fail gracefully)
- **Timeout**: Very slow page (extraction should timeout and mark job as failed)

## CI Testing

GitHub Actions runs:
1. Unit tests (`pytest apps/backend`)
2. Docker Compose smoke test (`infra/smoke.sh`)

See `.github/workflows/ci.yml` for details.

## Debugging

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f extractor
docker-compose logs -f runner
```

### Check Database

```bash
docker exec -it qa-postgres psql -U qa_user -d qa_demo

# List jobs
SELECT id, target_url, status, created_at FROM jobs;

# List consent logs
SELECT * FROM consent_logs;
```

### Check Redis Queue

```bash
docker exec -it qa-redis redis-cli

# List queues
KEYS *

# Check job queue
LLEN rq:queue:jobs
```

### Inspect Artifacts

Artifacts are stored in the Docker volume `backend_artifacts`. To access:

```bash
# Find volume location
docker volume inspect infra_backend_artifacts

# Or exec into backend container
docker exec -it qa-backend ls -la /data/artifacts/
docker exec -it qa-backend cat /data/artifacts/<jobId>/manifest.json
```

## Performance Testing

For basic performance checks:

1. **Concurrent Jobs**: Submit 5 jobs simultaneously and verify all complete
2. **Large Page**: Test with a page that has many DOM elements
3. **Slow Network**: Use network throttling in Playwright (future enhancement)

## Security Testing

- ✅ All tests are read-only by default (no POST/PUT/DELETE)
- ✅ Robots.txt preflight check
- ✅ Consent logging for audit trail
- ✅ Isolated container execution

## Next Steps

After verifying the demo works:
1. Review generated test artifacts
2. Check semantic model accuracy
3. Validate test execution results
4. Review architecture docs for production migration paths
