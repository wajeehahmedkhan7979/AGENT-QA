import json

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from db import ConsentLog, Job, JobScope, JobStatus, SessionLocal
from preflight import check_robots
from queue_adapter import queue_adapter
from schemas import (
    ArtifactItem,
    ConsentRecord,
    JobCreateRequest,
    JobResponse,
    PreflightResult,
)
from semantic import ensure_semantic_outputs
from storage import storage_adapter
from llm_adapter import get_llm_adapter
from validator import validate_steps

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post(
    "/",
    response_model=JobResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_job(
    payload: JobCreateRequest,
    db: Session = Depends(get_db),
) -> JobResponse:
    # Create job record
    job = Job(
        target_url=str(payload.targetUrl),
        scope=payload.scope,
        test_profile=payload.testProfile,
        owner_id=payload.ownerId,
        status=JobStatus.PENDING,
    )
    db.add(job)
    db.flush()

    # Record consent entry
    consent = ConsentLog(
        job_id=job.id,
        owner_id=payload.ownerId,
        note="Demo consent recorded",
    )
    db.add(consent)

    # Preflight robots.txt check
    robots_result = check_robots(job.target_url)
    job.preflight_allowed = robots_result.allowed
    job.preflight_robots = robots_result.robots_txt

    if not robots_result.allowed:
        job.status = JobStatus.REJECTED
    else:
        job.status = JobStatus.QUEUED
        # Enqueue extraction job via orchestration adapter
        queue_adapter.enqueue_extraction(job.id)

    db.commit()
    db.refresh(job)

    preflight = PreflightResult(
        allowed=robots_result.allowed,
        robots=robots_result.robots_txt,
    )
    consent_record = ConsentRecord(
        ownerId=consent.owner_id,
        consentTimestamp=consent.consent_timestamp,
        note=consent.note,
    )

    return JobResponse(
        jobId=job.id,
        status=job.status,
        preflight=preflight,
        createdAt=job.created_at,
        consent=[consent_record],
    )


@router.get(
    "/{job_id}",
    response_model=JobResponse,
)
async def get_job(
    job_id: str,
    db: Session = Depends(get_db),
) -> JobResponse:
    job: Job | None = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )

    consents = [
        ConsentRecord(
            ownerId=c.owner_id,
            consentTimestamp=c.consent_timestamp,
            note=c.note,
        )
        for c in job.consent_logs
    ]
    preflight = None
    if job.preflight_allowed is not None:
        preflight = PreflightResult(
            allowed=job.preflight_allowed,
            robots=job.preflight_robots,
        )

    return JobResponse(
        jobId=job.id,
        status=job.status,
        preflight=preflight,
        createdAt=job.created_at,
        consent=consents,
    )


@router.get(
    "/{job_id}/artifacts",
    response_model=list[ArtifactItem],
)
async def list_artifacts(
    job_id: str,
) -> list[ArtifactItem]:
    records = storage_adapter.load_manifest(job_id)
    return [
        ArtifactItem(name=r.name, type=r.type, path=r.path)
        for r in records
    ]


@router.get(
    "/{job_id}/semantic",
)
async def get_semantic(
    job_id: str,
) -> dict:
    """
    Return the semantic model and API catalog for a job.
    If they do not yet exist, they will be built from existing artifacts.
    """
    return ensure_semantic_outputs(job_id)


@router.post(
    "/{job_id}/generate",
)
async def generate_tests_for_job(
    job_id: str,
    db: Session = Depends(get_db),
) -> dict:
    """
    Generate a Playwright test definition from the semantic model using the mock LLM,
    validate it, and store it as an artifact.
    """
    job: Job | None = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )

    semantic_bundle = ensure_semantic_outputs(job_id)
    semantic_model = semantic_bundle["semanticModel"]

    adapter = get_llm_adapter()
    generated = adapter.generate_tests(job_id, semantic_model)

    # Validate steps
    score = validate_steps(job.scope.value, generated.steps)
    effective_confidence = min(generated.confidence, score)
    status_label = "high" if effective_confidence >= 0.8 else "low"

    test_artifact = {
        "testId": generated.test_id,
        "jobId": generated.job_id,
        "steps": generated.steps,
        "confidence": effective_confidence,
        "format": generated.format,
        "status": "needs_review" if status_label == "low" else "ready",
    }

    # Store artifacts
    storage_adapter.save_json(job_id, "generated_test.json", test_artifact)
    if generated.gherkin:
        storage_adapter.save_bytes(
            job_id,
            "generated_test.feature",
            generated.gherkin.encode("utf-8"),
        )

    return test_artifact


@router.get(
    "/{job_id}/report",
)
async def get_job_report(
    job_id: str,
) -> dict:
    """
    Return the latest test run report for a job, if available.
    """
    # For the demo we treat `last_run.json` as the canonical latest report.
    job_dir = storage_adapter.job_dir(job_id)
    report_path = job_dir / "last_run.json"
    if not report_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No report found for this job",
        )
    raw = report_path.read_text(encoding="utf-8")
    return json.loads(raw)

