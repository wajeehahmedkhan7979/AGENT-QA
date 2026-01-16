"""
Phase 2B: Structured JSON Logging for Job Observability

This module provides deterministic, zero-side-effect structured logging
for job execution timelines. Every phase transition is logged as JSON.
"""

import json
import os
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pathlib import Path


class Phase(str, Enum):
    """Job execution phases."""
    PREFLIGHT = "preflight"
    EXTRACTION = "extraction"
    SEMANTICS = "semantics"
    GENERATION = "generation"
    EXECUTION = "execution"
    REPORTING = "reporting"


class Status(str, Enum):
    """Log entry status."""
    STARTED = "started"
    COMPLETED = "completed"
    FAILED = "failed"


class TimelineEntry(dict):
    """A timeline log entry (JSON-serializable dict)."""
    
    def __init__(
        self,
        job_id: str,
        phase: Phase,
        status: Status,
        timestamp: str,
        details: Dict[str, Any],
    ):
        super().__init__(
            job_id=job_id,
            phase=phase.value,
            status=status.value,
            timestamp=timestamp,
            details=details or {},
        )


class StructuredLogger:
    """
    Deterministic, zero-side-effect structured JSON logger.
    
    Logs all phase transitions to a JSONL (JSON Lines) file.
    Timestamps are ISO 8601 UTC. Details are phase-specific context.
    """
    
    def __init__(self, job_id: str, log_dir: str = "."):
        """Initialize logger for a job."""
        self.job_id = job_id
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.log_dir / f"{job_id}_timeline.jsonl"
    
    def log(
        self,
        phase: Phase,
        status: Status,
        details: Optional[Dict[str, Any]] = None,
    ) -> TimelineEntry:
        """
        Log a phase transition.
        
        Args:
            phase: Job execution phase
            status: Status (started/completed/failed)
            details: Phase-specific context data
        
        Returns:
            TimelineEntry (dict) that was logged
        """
        details = details or {}
        timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        
        entry = TimelineEntry(
            job_id=self.job_id,
            phase=phase,
            status=status,
            timestamp=timestamp,
            details=details,
        )
        
        # Append entry to JSONL file (atomic operation)
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        
        return entry
    
    # Phase helper methods
    
    def log_preflight_started(self, details: Optional[Dict[str, Any]] = None) -> TimelineEntry:
        """Log preflight phase started."""
        return self.log(Phase.PREFLIGHT, Status.STARTED, details)
    
    def log_preflight_completed(self, details: Optional[Dict[str, Any]] = None) -> TimelineEntry:
        """Log preflight phase completed."""
        return self.log(Phase.PREFLIGHT, Status.COMPLETED, details)
    
    def log_extraction_started(self, details: Optional[Dict[str, Any]] = None) -> TimelineEntry:
        """Log extraction phase started."""
        return self.log(Phase.EXTRACTION, Status.STARTED, details)
    
    def log_extraction_completed(self, details: Optional[Dict[str, Any]] = None) -> TimelineEntry:
        """Log extraction phase completed."""
        return self.log(Phase.EXTRACTION, Status.COMPLETED, details)
    
    def log_semantics_started(self, details: Optional[Dict[str, Any]] = None) -> TimelineEntry:
        """Log semantics phase started."""
        return self.log(Phase.SEMANTICS, Status.STARTED, details)
    
    def log_semantics_completed(self, details: Optional[Dict[str, Any]] = None) -> TimelineEntry:
        """Log semantics phase completed."""
        return self.log(Phase.SEMANTICS, Status.COMPLETED, details)
    
    def log_generation_started(self, details: Optional[Dict[str, Any]] = None) -> TimelineEntry:
        """Log generation phase started."""
        return self.log(Phase.GENERATION, Status.STARTED, details)
    
    def log_generation_completed(self, details: Optional[Dict[str, Any]] = None) -> TimelineEntry:
        """Log generation phase completed."""
        return self.log(Phase.GENERATION, Status.COMPLETED, details)
    
    def log_execution_started(self, details: Optional[Dict[str, Any]] = None) -> TimelineEntry:
        """Log execution phase started."""
        return self.log(Phase.EXECUTION, Status.STARTED, details)
    
    def log_execution_completed(self, details: Optional[Dict[str, Any]] = None) -> TimelineEntry:
        """Log execution phase completed."""
        return self.log(Phase.EXECUTION, Status.COMPLETED, details)
    
    def log_reporting_started(self, details: Optional[Dict[str, Any]] = None) -> TimelineEntry:
        """Log reporting phase started."""
        return self.log(Phase.REPORTING, Status.STARTED, details)
    
    def log_reporting_completed(self, details: Optional[Dict[str, Any]] = None) -> TimelineEntry:
        """Log reporting phase completed."""
        return self.log(Phase.REPORTING, Status.COMPLETED, details)
    
    def log_error(
        self,
        phase: Phase,
        error_message: str,
        error_type: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> TimelineEntry:
        """Log an error in a phase."""
        error_details = details or {}
        error_details.update({
            "error_message": error_message,
            "error_type": error_type,
        })
        return self.log(phase, Status.FAILED, error_details)
    
    def read_timeline(self) -> List[TimelineEntry]:
        """Read all timeline entries from JSONL file."""
        entries = []
        if not self.log_file.exists():
            return entries
        
        with open(self.log_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        entry = json.loads(line)
                        entries.append(entry)
                    except json.JSONDecodeError:
                        continue
        
        return entries
    
    def get_timeline_summary(self) -> Dict[str, Any]:
        """Get aggregated timeline summary."""
        entries = self.read_timeline()
        summary = {
            "job_id": self.job_id,
            "entry_count": len(entries),
            "phases": {},
        }
        
        for entry in entries:
            phase_name = entry["phase"]
            status = entry["status"]
            timestamp = entry["timestamp"]
            
            if phase_name not in summary["phases"]:
                summary["phases"][phase_name] = {
                    "started": None,
                    "completed": None,
                    "failed": False,
                }
            
            phase_info = summary["phases"][phase_name]
            
            if status == "started" and phase_info["started"] is None:
                phase_info["started"] = timestamp
            elif status == "completed":
                phase_info["completed"] = timestamp
            elif status == "failed":
                phase_info["failed"] = True
                phase_info["completed"] = timestamp
        
        return summary


def get_logger(job_id: str, log_dir: str = ".") -> StructuredLogger:
    """Factory function to create or retrieve a logger for a job."""
    return StructuredLogger(job_id, log_dir)
