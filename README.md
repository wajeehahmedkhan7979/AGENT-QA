## Autonomous QA Automation WebApp (Demo)

This repository contains a **demo implementation** of an Autonomous QA Automation WebApp.
The goal is to validate the core architecture and flows, not to build a production-ready system.

### High-level demo flow

1. **Job creation** via API or UI for a target URL.
2. **Preflight & consent**: record consent, check `robots.txt`, and queue a job.
3. **Extraction** (worker): load the page with Playwright, capture DOM/HAR/screenshot/accessibility info.
4. **Semantic modeling**: derive a simple semantic model of the UI and API calls (mock LLM-assisted).
5. **Test generation**: mock LLM generates a deterministic Playwright test (happy-path only) and validates it.
6. **Execution**: a runner executes the Playwright test in an isolated container (read-only).
7. **Results UI**: view artifacts and test results in a simple React UI.

### Monorepo layout

- `apps/web-ui` – React + TypeScript frontend for job submission and results.
- `apps/backend` – FastAPI backend, API, orchestration facade, DB access.
- `apps/extractor` – Playwright-based extractor worker (Python) for DOM/HAR/screenshot.
- `runner` – Playwright runner service that executes generated tests in isolation.
- `infra` – Docker Compose, environment, and infra-related configuration.
- `docs` – Architecture notes, runbooks, configuration docs.
- `sample-app` – Minimal deterministic demo app to target with generated tests.

### Quickstart

1. Ensure you have **Docker Desktop** and **Docker Compose** installed and running.
2. From the repo root, start all services:

```bash
cd infra
docker-compose up --build
```

3. Once everything starts (wait ~30 seconds for all services to be healthy):
   - **Web UI**: `http://localhost:3100` (submit jobs and view results)
   - **Backend API**: `http://localhost:8000` (OpenAPI docs at `/docs`)
   - **Sample app**: `http://localhost:3000/sample-app` (demo target)

4. **Quick test**: Open `http://localhost:3100`, submit a job for `http://sample-app:3000/sample-app/login`, wait for extraction, generate a test, run it, and view the report.

### Documentation

- **[DEMO_RUNBOOK.md](docs/DEMO_RUNBOOK.md)** – Step-by-step instructions for running the demo
- **[TESTING.md](docs/TESTING.md)** – Comprehensive testing guide with API examples
- **[CONFIG.md](docs/CONFIG.md)** – Configuration and environment variables
- **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** – System architecture and adapter design

### Verification

Run the verification script to check your setup:

```bash
bash scripts/verify_setup.sh
```

