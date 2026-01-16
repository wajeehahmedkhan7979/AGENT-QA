"""
Phase 2B: Timeline API Endpoints

Provides queryable access to job execution timelines.
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Query
from pathlib import Path
from observability import StructuredLogger, Phase

router = APIRouter()

# Default timeline log directory (can be configured)
TIMELINE_DIR = "."


def get_logger_for_job(job_id: str) -> StructuredLogger:
    """Get logger for a job."""
    return StructuredLogger(job_id, TIMELINE_DIR)


def job_exists(job_id: str) -> bool:
    """Check if job timeline exists."""
    logger = get_logger_for_job(job_id)
    return logger.log_file.exists()


@router.get("/jobs/{job_id}/timeline")
def get_timeline(job_id: str) -> Dict[str, Any]:
    """
    GET /jobs/{job_id}/timeline
    
    Get complete timeline for a job with all log entries.
    
    Returns:
        - job_id: Job identifier
        - entry_count: Number of timeline entries
        - entries: All log entries as list
    """
    if not job_exists(job_id):
        raise HTTPException(status_code=404, detail="Job not found")
    
    logger = get_logger_for_job(job_id)
    entries = logger.read_timeline()
    
    return {
        "job_id": job_id,
        "entry_count": len(entries),
        "entries": entries,
    }


@router.get("/jobs/{job_id}/timeline/summary")
def get_timeline_summary(job_id: str) -> Dict[str, Any]:
    """
    GET /jobs/{job_id}/timeline/summary
    
    Get aggregated timeline summary with phase timings.
    
    Returns:
        - job_id: Job identifier
        - entry_count: Total number of entries
        - phases: Mapping of phase to timing data
    """
    if not job_exists(job_id):
        raise HTTPException(status_code=404, detail="Job not found")
    
    logger = get_logger_for_job(job_id)
    return logger.get_timeline_summary()


@router.get("/jobs/{job_id}/timeline/phases")
def get_timeline_phases(job_id: str) -> Dict[str, Any]:
    """
    GET /jobs/{job_id}/timeline/phases
    
    Get current status of all execution phases.
    
    Returns:
        - job_id: Job identifier
        - current_phase: Phase currently in progress
        - phases: Mapping of phase names to status
    """
    if not job_exists(job_id):
        raise HTTPException(status_code=404, detail="Job not found")
    
    logger = get_logger_for_job(job_id)
    entries = logger.read_timeline()
    
    # Build phase status map
    phase_status = {
        "preflight": "pending",
        "extraction": "pending",
        "semantics": "pending",
        "generation": "pending",
        "execution": "pending",
        "reporting": "pending",
    }
    
    current_phase = None
    
    for entry in entries:
        phase = entry["phase"]
        status = entry["status"]
        
        if status == "started":
            phase_status[phase] = "in_progress"
            current_phase = phase
        elif status == "completed":
            phase_status[phase] = "completed"
        elif status == "failed":
            phase_status[phase] = "failed"
    
    return {
        "job_id": job_id,
        "current_phase": current_phase,
        "phases": phase_status,
    }


@router.get("/jobs/{job_id}/timeline/latest")
def get_latest_events(
    job_id: str,
    limit: int = Query(10, ge=1, le=100),
) -> Dict[str, Any]:
    """
    GET /jobs/{job_id}/timeline/latest?limit=10
    
    Get most recent N log entries.
    
    Query Parameters:
        - limit: Number of events (1-100, default 10)
    
    Returns:
        - job_id: Job identifier
        - requested_limit: Requested limit
        - returned_count: Actual events returned
        - events: Latest N events in reverse chronological order
    """
    if not job_exists(job_id):
        raise HTTPException(status_code=404, detail="Job not found")
    
    logger = get_logger_for_job(job_id)
    entries = logger.read_timeline()
    
    # Get latest N entries (reversed for most recent first)
    latest = entries[-limit:] if limit < len(entries) else entries
    latest.reverse()
    
    return {
        "job_id": job_id,
        "requested_limit": limit,
        "returned_count": len(latest),
        "events": latest,
    }


@router.get("/jobs/{job_id}/timeline/phase/{phase}")
def get_phase_events(job_id: str, phase: str) -> Dict[str, Any]:
    """
    GET /jobs/{job_id}/timeline/phase/{phase}
    
    Get all events from a specific phase.
    
    URL Parameters:
        - phase: One of [preflight, extraction, semantics, generation, execution, reporting]
    
    Returns:
        - job_id: Job identifier
        - phase: Requested phase
        - entry_count: Number of entries for phase
        - entries: All entries for phase
    """
    if not job_exists(job_id):
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Validate phase
    valid_phases = [p.value for p in Phase]
    if phase not in valid_phases:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid phase. Must be one of: {', '.join(valid_phases)}",
        )
    
    logger = get_logger_for_job(job_id)
    entries = logger.read_timeline()
    
    # Filter entries by phase
    phase_entries = [e for e in entries if e["phase"] == phase]
    
    return {
        "job_id": job_id,
        "phase": phase,
        "entry_count": len(phase_entries),
        "entries": phase_entries,
    }
