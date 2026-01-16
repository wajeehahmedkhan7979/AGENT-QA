from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes import jobs, tests
from db import init_db

app = FastAPI(title="Autonomous QA Automation WebApp Demo")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


app.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
app.include_router(tests.router, prefix="/tests", tags=["tests"])


