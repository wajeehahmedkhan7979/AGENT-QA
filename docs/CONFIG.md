## Configuration and Environment Variables

The demo follows a 12-factor style: all environment-specific configuration is
provided via environment variables. Docker Compose sets sensible defaults.

### Backend (`apps/backend`)

- **`BACKEND_HOST`** (default: `0.0.0.0`)
  - Host for the FastAPI server.
- **`BACKEND_PORT`** (default: `8000`)
  - Port for the FastAPI server.
- **`DATABASE_URL`**
  - SQLAlchemy connection string.
  - Local default (non-Docker): `sqlite:///./qa_demo.db`
  - Docker Compose: `postgresql+psycopg2://qa_user:qa_pass@db:5432/qa_demo`
- **`REDIS_URL`** (default: `redis://localhost:6379/0`)
  - Connection URL for Redis, used by RQ.
- **`STORAGE_BACKEND`** (default: `localfs`)
  - Currently only `localfs` is implemented; this is where an `s3` adapter would plug in.
- **`STORAGE_ROOT`** (default: `./artifacts`)
  - Root directory for artifact storage (mounted as `/data/artifacts` in Docker).

### Extractor worker (`apps/extractor`)

- **`REDIS_URL`**
  - Points to Redis for the `jobs` queue.
- **`DATABASE_URL`**
  - Same as the backend; used to read and update job status.
- **`STORAGE_BACKEND`**, **`STORAGE_ROOT`**
  - Same contract as backend; must point to the same physical storage.

### Runner (`runner`)

- **`REDIS_URL`**
  - Points to Redis for the `runs` queue.
- **`STORAGE_BACKEND`**, **`STORAGE_ROOT`**
  - Same contract as backend/extractor; must be shared so the runner can read tests and write reports.
- **`TEST_BASE_URL`** (optional)
  - Base URL used by the runner when expanding relative `goto` URLs.
  - Defaults to `http://sample-app:3000` if not set.

### Web UI (`apps/web-ui`)

- **`VITE_BACKEND_URL`**
  - API base URL for the frontend.
  - In Docker Compose, set to `http://backend:8000`.
  - For local dev (`npm run dev`) outside Docker, you can set:
    - `VITE_BACKEND_URL=http://localhost:8000`

### Services and ports (Docker Compose)

- **Backend API** – `http://localhost:8000`
- **Sample app** – `http://localhost:3000/sample-app`
- **Web UI** – `http://localhost:3100`
- **MinIO** (optional, not wired yet) – console on `http://localhost:9001`

### Adapters and pluggability

Places where you will swap in production components:

- **LLM Adapter** (`apps/backend/llm_adapter.py`)
  - Default: `MockLLMAdapter` (deterministic, no network calls).
  - Optional: `OpenAIAdapter` is enabled when **`OPENAI_API_KEY`** is set.
  - **`OPENAI_MODEL`** (optional): defaults to `gpt-5-nano`.

- **Storage Adapter** (`apps/backend/storage.py`)
  - `LocalFSStorageAdapter` is used for demo.
  - To plug in S3/MinIO, create `S3StorageAdapter` with the same method signatures (`save_bytes`, `save_json`, `load_manifest`, `save_manifest`) and choose based on `STORAGE_BACKEND`.

- **Orchestration Adapter** (`apps/backend/queue_adapter.py`)
  - `OrchestrationQueue` wraps Redis+RQ for `jobs` and `runs` queues.
  - For Temporal or another workflow engine, replace calls to `enqueue_extraction` and `enqueue_test_run` with workflow/activities that respect the same high-level contract.

