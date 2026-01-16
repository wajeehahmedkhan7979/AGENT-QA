## Architecture Overview

This document summarizes the architecture of the **Autonomous QA Automation WebApp demo**,
with a focus on pluggable adapters and end-to-end flow.

### High-level components

- **Backend (`apps/backend`)**
  - FastAPI application exposing:
    - `/jobs` – job lifecycle (creation, artifacts, semantic info, reports, generation).
    - `/tests` – trigger execution of generated tests.
  - Persists jobs and consent logs in Postgres (via SQLAlchemy).
  - Performs robots.txt preflight checks.
  - Coordinates workers via Redis + RQ (`OrchestrationQueue`).

- **Extractor (`apps/extractor`)**
  - Python worker consuming the `jobs` queue.
  - Uses Playwright (Chromium) to:
    - Load the target URL (sample-app).
    - Capture DOM snapshot, HAR, screenshot, accessibility tree.
  - Stores artifacts through the storage adapter and writes a manifest.

- **Semantic & LLM layer (backend)**
  - `semantic.py`:
    - Parses `dom.json` with BeautifulSoup.
    - Identifies clickable elements and inputs, labels them, builds CSS-like selectors.
    - Applies heuristic rules + `mock_llm` classification to assign higher-level roles.
    - Infers a simple login flow when username/password/login elements are present.
    - Extracts API endpoints from HAR into `api_catalog.json`.
  - `mock_llm.py` and `llm_adapter.py`:
    - Provide a deterministic mock LLM classifier and a `MockLLMAdapter` that generates one Playwright JSON test.

- **Runner (`runner`)**
  - Python worker consuming the `runs` queue.
  - Loads `generated_test.json` for a job.
  - Executes steps via Playwright in headless Chromium.
  - Captures per-step screenshots and produces a structured JSON test report (`test_report_<runId>.json` and `last_run.json`).

- **Web UI (`apps/web-ui`)**
  - React + TypeScript app calling the backend API.
  - Provides a simple dashboard for:
    - Submitting jobs.
    - Viewing job statuses.
    - Triggering test generation and execution.
    - Listing artifacts and viewing the latest test run report.

- **Sample app (`sample-app`)**
  - Minimal Express app exposing:
    - `/sample-app` – landing page with a link to `/sample-app/login`.
    - `/sample-app/login` – static login form and deterministic JS “login” that appends a `Welcome` heading.
  - Used as the consistent, safe target for extraction and test execution.

### Data flow

1. **Job creation**
   - Client calls `POST /jobs` with `targetUrl`, `scope`, `testProfile`, `ownerId`.
   - Backend:
     - Creates `Job` row and `ConsentLog`.
     - Runs robots.txt preflight:
       - If disallowed, marks job `rejected`.
       - If allowed, marks job `queued` and enqueues extraction via `OrchestrationQueue.enqueue_extraction(job_id)`.

2. **Extraction**
   - Extractor worker (`extractor.worker.process_job`) dequeues `job_id`.
   - Uses Playwright to:
     - Navigate to the target URL.
     - Record HAR.
     - Capture DOM + screenshot + accessibility snapshot.
   - Writes artifacts and `manifest.json` via `LocalFSStorageAdapter`.
   - Updates job status back in the DB.

3. **Semantic modeling & API discovery**
   - On-demand via `GET /jobs/{jobId}/semantic`:
     - `ensure_semantic_outputs` reads artifacts; if `semantic_model.json` or `api_catalog.json` are missing, it builds them.
     - Returns both structures in a single response.

4. **Test generation**
   - `POST /jobs/{jobId}/generate`:
     - Ensures semantic outputs exist.
     - Calls `get_llm_adapter().generate_tests(job_id, semantic_model)` to produce `GeneratedTest`.
     - Validates steps with `validate_steps(scope, steps)` to enforce:
       - Only whitelisted actions (`goto`, `fill`, `click`, `expectText`).
       - Basic per-action schema.
       - Read-only behavior (no HTTP method steps in demo).
     - Combines LLM confidence and validator score, sets test `status` to `ready` or `needs_review`.
     - Stores `generated_test.json` and a Gherkin `.feature` file as artifacts.

5. **Execution**
   - `POST /tests/{testId}/run` with `{ "jobId": "<job_123>" }`:
     - Enqueues `runner.worker.run_test(job_id, test_id)` on `runs` queue.
   - Runner worker:
     - Loads the JSON test definition.
     - Constructs full URLs using `TEST_BASE_URL` and relative `goto` URL.
     - Executes steps, capturing screenshots and step results.
     - Persists a structured run report and a `last_run.json` pointer for easy retrieval.

6. **Results**
   - `GET /jobs/{jobId}/artifacts` lists saved artifacts from the manifest.
   - `GET /jobs/{jobId}/report` returns the latest run report (`last_run.json`).
   - Web UI surfaces this information for non-technical users.

### Pluggable adapters

- **LLM**
  - Interface: `LLMAdapter` with `generate_tests(job_id, semantic_model)`.
  - Demo implementation: `MockLLMAdapter` (no network calls, deterministic).
  - Swap point: `get_llm_adapter()` – inspect env vars to return `OpenAIAdapter`, `AnthropicAdapter`, etc.

- **Storage**
  - Interface: `LocalFSStorageAdapter` defines:
    - `save_bytes(job_id, filename, data)`
    - `save_json(job_id, filename, obj)`
    - `load_manifest(job_id)`
    - `save_manifest(job_id, records)`
  - Swap point: `storage_adapter` instance, created based on `STORAGE_BACKEND`.

- **Orchestration**
  - Interface: `OrchestrationQueue` with:
    - `enqueue_extraction(job_id)`
    - `enqueue_test_run(job_id, test_id)`
  - Backed by Redis + RQ for demo.
  - Swap point: replace these methods with Temporal workflow invocations or another orchestrator.

- **Execution**
  - Runner directly uses Playwright in the worker container.
  - Future: wrap this in an execution adapter to support remote runners, K8s job dispatch, or a test-farm service.

