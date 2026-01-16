## Demo Runbook

This runbook explains how to run the **Autonomous QA Automation WebApp demo** locally,
from `docker-compose up` to viewing a full end-to-end run in the UI.

### Prerequisites

- Docker and Docker Compose installed and running.
- Ports `8000`, `3000`, and `3100` available on your machine.

### 1. Start the stack

From the repository root:

```bash
cd infra
docker-compose up --build
```

This brings up:

- `backend` – FastAPI API at `http://localhost:8000`
- `db` – Postgres
- `redis` – Redis + RQ queues
- `extractor` – Playwright-based extractor worker
- `runner` – Playwright-based runner worker
- `sample-app` – demo app at `http://localhost:3000/sample-app`
- `web-ui` – React UI at `http://localhost:3100`

Artifacts are stored under the shared volume mapped to `/data/artifacts` in containers.

### 2. Smoke check via API

With the stack running, verify the backend is healthy:

```bash
curl http://localhost:8000/health
```

Expected:

```json
{"status": "ok"}
```

Create a job targeting the sample app:

```bash
curl -X POST "http://localhost:8000/jobs" \
  -H "Content-Type: application/json" \
  -d '{
    "targetUrl": "http://sample-app:3000/sample-app/login",
    "scope": "read-only",
    "testProfile": "functional",
    "ownerId": "demo_user"
  }'
```

You should receive a JSON response with `jobId` and `status: "queued"`.

### 3. Full flow via Web UI

Open the UI in a browser:

- `http://localhost:3100`

Then:

1. **Create job**
   - Enter the target URL (default already points to the sample app login).
   - Click **Create job**.
2. **Monitor job**
   - The job appears in the **Jobs** table.
   - Click **Select** to focus this job.
   - Click **Refresh status** after a few seconds to see extraction complete.
3. **Inspect artifacts**
   - Click **Select** and then look at the **Artifacts** list.
   - You should see items such as `dom.json`, `screenshot.png`, `trace.har`.
4. **Generate test**
   - Click **Generate test** to create a Playwright JSON test via the mock LLM.
   - The generated test is stored as `generated_test.json` (and `.feature`) in artifacts.
5. **Run test**
   - Click **Run test** to enqueue execution in the runner.
   - After a few seconds, click **Refresh report**.
6. **View report**
   - The **Latest test report** panel shows:
     - Overall status (`passed` / `failed`)
     - Run ID and timestamps
     - Step-by-step results with screenshot paths

### 4. Running tests and CI locally

Backend unit tests (pytest):

```bash
pip install -r apps/backend/requirements.txt
pytest apps/backend -q
```

Docker-compose smoke test (same as CI):

```bash
cd infra
chmod +x smoke.sh
./smoke.sh
```

This script:

- Starts `backend`, `sample-app`, `db`, and `redis`.
- Waits for `/health` to be ready.
- Submits a simple `POST /jobs` request.
- Tears everything down.

