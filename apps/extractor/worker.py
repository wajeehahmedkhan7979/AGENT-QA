from __future__ import annotations

from datetime import datetime
from typing import List

from playwright.sync_api import sync_playwright

from backend.config import settings
from backend.db import Job, JobStatus, SessionLocal
from backend.storage import ArtifactRecord, storage_adapter


def _capture_artifacts(job_id: str, target_url: str) -> List[ArtifactRecord]:
    records: List[ArtifactRecord] = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        har_path = storage_adapter.job_dir(job_id) / "trace.har"
        context = browser.new_context(record_har_path=str(har_path), record_har_content="embed")
        page = context.new_page()

        page.goto(target_url, wait_until="networkidle")

        # DOM snapshot
        outer_html = page.evaluate("() => document.documentElement.outerHTML")
        dom_record_path = storage_adapter.save_json(
            job_id,
            "dom.json",
            {"outer_html": outer_html},
        )
        records.append(
            ArtifactRecord(
                name="dom.json",
                type="dom",
                path=dom_record_path,
            )
        )

        # Screenshot
        screenshot_file = storage_adapter.job_dir(job_id) / "screenshot.png"
        page.screenshot(path=str(screenshot_file), full_page=True)
        records.append(
            ArtifactRecord(
                name="screenshot.png",
                type="screenshot",
                path=f"{job_id}/screenshot.png",
            )
        )

        # Accessibility tree (if available)
        try:
            accessibility_tree = page.accessibility.snapshot()
        except Exception:
            accessibility_tree = None

        if accessibility_tree is not None:
            acc_path = storage_adapter.save_json(
                job_id,
                "accessibility.json",
                accessibility_tree,
            )
            records.append(
                ArtifactRecord(
                    name="accessibility.json",
                    type="accessibility",
                    path=acc_path,
                )
            )

        # HAR is already being recorded via record_har_path
        records.append(
            ArtifactRecord(
                name="trace.har",
                type="har",
                path=f"{job_id}/trace.har",
            )
        )

        context.close()
        browser.close()

    # Save manifest
    storage_adapter.save_manifest(job_id, records)
    return records


def process_job(job_id: str) -> None:
    """
    RQ task entry point.
    Picks up a job, runs Playwright extraction, saves artifacts, and updates job status.
    """
    db = SessionLocal()
    try:
        job: Job | None = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            return

        # Mark as extracting (reuse PENDING for demo as \"in progress\")
        job.status = JobStatus.PENDING
        db.commit()

        _capture_artifacts(job.id, job.target_url)

        # Update basic metadata and mark as queued for next phase
        job.status = JobStatus.QUEUED
        job.updated_at = datetime.utcnow()
        db.commit()
    finally:
        db.close()

