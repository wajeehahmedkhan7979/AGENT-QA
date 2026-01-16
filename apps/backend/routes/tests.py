from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from db import Job, SessionLocal
from queue_adapter import queue_adapter
from storage import storage_adapter

router = APIRouter()


class RunRequest(BaseModel):
    jobId: str


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post(
    "/{test_id}/run",
)
async def run_test(
    test_id: str,
    body: RunRequest,
    db: Session = Depends(get_db),
) -> dict:
    """
    Trigger execution of a generated test in the runner.
    For demo purposes we require the caller to provide the jobId.
    """
    job: Job | None = db.query(Job).filter(Job.id == body.jobId).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )

    run_id = queue_adapter.enqueue_test_run(body.jobId, test_id)
    return {
        "runId": run_id,
        "testId": test_id,
        "jobId": body.jobId,
        "status": "queued",
    }

