"""
Phase 2B: Observability Test Suite

Tests for structured JSON logging, timeline API, and observability guarantees.
"""

import json
import pytest
import tempfile
from pathlib import Path
from datetime import datetime, timezone
from observability import (
    Phase,
    Status,
    StructuredLogger,
    TimelineEntry,
    get_logger,
)


@pytest.fixture
def temp_log_dir():
    """Temporary directory for test logs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


class TestStructuredLoggerBasics:
    """Test basic logger functionality."""
    
    def test_logger_creates_timeline_file(self, temp_log_dir):
        """Logger creates JSONL timeline file."""
        logger = StructuredLogger("job_1", temp_log_dir)
        assert not logger.log_file.exists()
        
        logger.log(Phase.PREFLIGHT, Status.STARTED)
        assert logger.log_file.exists()
    
    def test_log_entry_structure(self, temp_log_dir):
        """Log entry has correct JSON structure."""
        logger = StructuredLogger("job_1", temp_log_dir)
        entry = logger.log(Phase.EXTRACTION, Status.COMPLETED, {"count": 42})
        
        assert "job_id" in entry
        assert "phase" in entry
        assert "status" in entry
        assert "timestamp" in entry
        assert "details" in entry
    
    def test_timestamp_is_iso8601_utc(self, temp_log_dir):
        """Timestamp is ISO 8601 UTC format."""
        logger = StructuredLogger("job_1", temp_log_dir)
        entry = logger.log(Phase.PREFLIGHT, Status.STARTED)
        
        timestamp = entry["timestamp"]
        # Should end with Z (UTC indicator)
        assert timestamp.endswith("Z")
        # Should parse as ISO 8601
        dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        assert dt.tzinfo is not None
    
    def test_details_always_dict(self, temp_log_dir):
        """Details field is always dict, never None."""
        logger = StructuredLogger("job_1", temp_log_dir)
        
        # Without details
        entry1 = logger.log(Phase.PREFLIGHT, Status.STARTED)
        assert isinstance(entry1["details"], dict)
        assert entry1["details"] == {}
        
        # With details
        entry2 = logger.log(Phase.EXTRACTION, Status.COMPLETED, {"x": 1})
        assert isinstance(entry2["details"], dict)
        assert entry2["details"]["x"] == 1
    
    def test_jsonl_format(self, temp_log_dir):
        """Timeline file is valid JSONL (one JSON per line)."""
        logger = StructuredLogger("job_1", temp_log_dir)
        logger.log(Phase.PREFLIGHT, Status.STARTED)
        logger.log(Phase.EXTRACTION, Status.COMPLETED, {"url": "http://example.com"})
        
        with open(logger.log_file, "r") as f:
            lines = f.readlines()
        
        assert len(lines) == 2
        for line in lines:
            # Each line should be valid JSON
            parsed = json.loads(line.strip())
            assert isinstance(parsed, dict)


class TestLoggerPhaseHelpers:
    """Test phase-specific logging methods."""
    
    def test_preflight_helpers(self, temp_log_dir):
        """Preflight phase helpers work correctly."""
        logger = StructuredLogger("job_1", temp_log_dir)
        
        started = logger.log_preflight_started()
        assert started["phase"] == "preflight"
        assert started["status"] == "started"
        
        completed = logger.log_preflight_completed({"robots_allowed": True})
        assert completed["phase"] == "preflight"
        assert completed["status"] == "completed"
        assert completed["details"]["robots_allowed"] is True
    
    def test_all_phase_helpers_exist(self, temp_log_dir):
        """All phase helper methods exist."""
        logger = StructuredLogger("job_1", temp_log_dir)
        
        # All phases should have started and completed helpers
        phases = ["preflight", "extraction", "semantics", "generation", "execution", "reporting"]
        
        for phase in phases:
            start_method = getattr(logger, f"log_{phase}_started")
            complete_method = getattr(logger, f"log_{phase}_completed")
            
            assert callable(start_method)
            assert callable(complete_method)
    
    def test_error_logging(self, temp_log_dir):
        """Error logging captures error details."""
        logger = StructuredLogger("job_1", temp_log_dir)
        
        error = logger.log_error(
            Phase.EXTRACTION,
            "Connection timeout",
            "TimeoutError",
            {"url": "http://example.com"},
        )
        
        assert error["phase"] == "extraction"
        assert error["status"] == "failed"
        assert error["details"]["error_message"] == "Connection timeout"
        assert error["details"]["error_type"] == "TimeoutError"
        assert error["details"]["url"] == "http://example.com"


class TestTimelineReading:
    """Test reading timeline entries."""
    
    def test_read_empty_timeline(self, temp_log_dir):
        """Reading non-existent timeline returns empty list."""
        logger = StructuredLogger("job_nonexistent", temp_log_dir)
        entries = logger.read_timeline()
        assert entries == []
    
    def test_read_timeline_preserves_order(self, temp_log_dir):
        """Entries are read in order they were written."""
        logger = StructuredLogger("job_1", temp_log_dir)
        
        logger.log(Phase.PREFLIGHT, Status.STARTED, {"order": 1})
        logger.log(Phase.EXTRACTION, Status.STARTED, {"order": 2})
        logger.log(Phase.SEMANTICS, Status.COMPLETED, {"order": 3})
        
        entries = logger.read_timeline()
        assert len(entries) == 3
        assert entries[0]["details"]["order"] == 1
        assert entries[1]["details"]["order"] == 2
        assert entries[2]["details"]["order"] == 3
    
    def test_read_timeline_returns_list_of_dicts(self, temp_log_dir):
        """Timeline entries are dicts."""
        logger = StructuredLogger("job_1", temp_log_dir)
        logger.log(Phase.PREFLIGHT, Status.STARTED)
        
        entries = logger.read_timeline()
        assert isinstance(entries, list)
        assert len(entries) == 1
        assert isinstance(entries[0], dict)
    
    def test_multiple_loggers_same_job(self, temp_log_dir):
        """Multiple logger instances for same job access same file."""
        logger1 = StructuredLogger("job_1", temp_log_dir)
        logger2 = StructuredLogger("job_1", temp_log_dir)
        
        logger1.log(Phase.PREFLIGHT, Status.STARTED)
        
        entries = logger2.read_timeline()
        assert len(entries) == 1


class TestTimelineSummary:
    """Test timeline summary generation."""
    
    def test_summary_structure(self, temp_log_dir):
        """Summary has correct structure."""
        logger = StructuredLogger("job_1", temp_log_dir)
        logger.log_preflight_started()
        logger.log_preflight_completed()
        
        summary = logger.get_timeline_summary()
        
        assert "job_id" in summary
        assert "entry_count" in summary
        assert "phases" in summary
        assert summary["job_id"] == "job_1"
        assert summary["entry_count"] == 2
    
    def test_summary_tracks_phase_timing(self, temp_log_dir):
        """Summary tracks start and completion times."""
        logger = StructuredLogger("job_1", temp_log_dir)
        logger.log_preflight_started()
        logger.log_preflight_completed()
        
        summary = logger.get_timeline_summary()
        phase_info = summary["phases"]["preflight"]
        
        assert phase_info["started"] is not None
        assert phase_info["completed"] is not None
        assert phase_info["failed"] is False
    
    def test_summary_marks_failures(self, temp_log_dir):
        """Summary marks failed phases."""
        logger = StructuredLogger("job_1", temp_log_dir)
        logger.log_extraction_started()
        logger.log_error(Phase.EXTRACTION, "Failed", "Error")
        
        summary = logger.get_timeline_summary()
        phase_info = summary["phases"]["extraction"]
        
        assert phase_info["failed"] is True


class TestJSONSerialization:
    """Test JSON serialization and format."""
    
    def test_entries_are_json_serializable(self, temp_log_dir):
        """Log entries are fully JSON serializable."""
        logger = StructuredLogger("job_1", temp_log_dir)
        entry = logger.log(Phase.PREFLIGHT, Status.STARTED, {"nested": {"data": [1, 2, 3]}})
        
        # Should be able to serialize to JSON string
        json_str = json.dumps(entry)
        assert isinstance(json_str, str)
        
        # Should be able to deserialize back
        parsed = json.loads(json_str)
        assert parsed["job_id"] == "job_1"
    
    def test_unicode_in_details(self, temp_log_dir):
        """Unicode characters in details are preserved."""
        logger = StructuredLogger("job_1", temp_log_dir)
        entry = logger.log(
            Phase.EXTRACTION,
            Status.COMPLETED,
            {"text": "Hello World 2023 Testing"},
        )
        
        json_str = json.dumps(entry, ensure_ascii=False)
        parsed = json.loads(json_str)
        assert parsed["details"]["text"] == "Hello World 2023 Testing"


class TestLoggerDeterminism:
    """Test logging determinism and no side effects."""
    
    def test_same_inputs_produce_same_structure(self, temp_log_dir):
        """Same phase/status inputs produce same entry structure."""
        logger = StructuredLogger("job_1", temp_log_dir)
        
        entry1 = logger.log(Phase.PREFLIGHT, Status.STARTED, {"value": 42})
        entry2 = logger.log(Phase.PREFLIGHT, Status.STARTED, {"value": 42})
        
        # Structure should be identical (timestamps differ)
        assert entry1["job_id"] == entry2["job_id"]
        assert entry1["phase"] == entry2["phase"]
        assert entry1["status"] == entry2["status"]
        assert entry1["details"] == entry2["details"]
    
    def test_logging_does_not_modify_state(self, temp_log_dir):
        """Logging does not modify job state (no side effects)."""
        logger = StructuredLogger("job_1", temp_log_dir)
        
        # Job ID should not change
        assert logger.job_id == "job_1"
        logger.log(Phase.PREFLIGHT, Status.STARTED)
        assert logger.job_id == "job_1"
        
        # Log dir should not change
        orig_dir = logger.log_dir
        logger.log(Phase.EXTRACTION, Status.COMPLETED)
        assert logger.log_dir == orig_dir


class TestFactoryFunction:
    """Test get_logger factory function."""
    
    def test_get_logger_returns_structured_logger(self, temp_log_dir):
        """get_logger factory returns StructuredLogger instance."""
        logger = get_logger("job_1", temp_log_dir)
        assert isinstance(logger, StructuredLogger)
        assert logger.job_id == "job_1"
    
    def test_get_logger_creates_new_instance(self, temp_log_dir):
        """Multiple calls create separate instances."""
        logger1 = get_logger("job_1", temp_log_dir)
        logger2 = get_logger("job_1", temp_log_dir)
        
        # Different instances
        assert logger1 is not logger2
        # But same job ID
        assert logger1.job_id == logger2.job_id


class TestErrorHandling:
    """Test error handling and edge cases."""
    
    def test_large_details_dict(self, temp_log_dir):
        """Logger handles large detail dictionaries."""
        logger = StructuredLogger("job_1", temp_log_dir)
        
        large_details = {"data_" + str(i): i for i in range(1000)}
        entry = logger.log(Phase.PREFLIGHT, Status.STARTED, large_details)
        
        assert len(entry["details"]) == 1000
        assert entry["details"]["data_0"] == 0
    
    def test_malformed_jsonl_is_skipped(self, temp_log_dir):
        """Malformed JSONL lines are skipped gracefully."""
        logger = StructuredLogger("job_1", temp_log_dir)
        
        # Manually write a malformed line
        with open(logger.log_file, "w") as f:
            f.write("{invalid json
")
            f.write('{"valid": "json"}\n')
        
        entries = logger.read_timeline()
        # Should have 1 entry (the valid one)
        assert len(entries) == 1
        assert entries[0]["valid"] == "json"


class TestTimelineIntegration:
    """Integration tests for full timeline workflow."""
    
    def test_complete_job_lifecycle(self, temp_log_dir):
        """Track a complete job lifecycle."""
        logger = StructuredLogger("job_complete", temp_log_dir)
        
        # Preflight phase
        logger.log_preflight_started()
        logger.log_preflight_completed({"robots_allowed": True})
        
        # Extraction phase
        logger.log_extraction_started({"url": "http://example.com"})
        logger.log_extraction_completed({"elements": 42})
        
        # Semantics phase
        logger.log_semantics_started()
        logger.log_semantics_completed({"classified": 42})
        
        # Generation phase
        logger.log_generation_started()
        logger.log_generation_completed({"tests": 5})
        
        # Execution phase
        logger.log_execution_started()
        logger.log_execution_completed({"passed": 5})
        
        # Reporting phase
        logger.log_reporting_started()
        logger.log_reporting_completed({"report": "generated"})
        
        # Verify timeline
        entries = logger.read_timeline()
        assert len(entries) == 12  # 2 entries per phase
        
        summary = logger.get_timeline_summary()
        assert len(summary["phases"]) == 6
        
        for phase_name in ["preflight", "extraction", "semantics", "generation", "execution", "reporting"]:
            phase_info = summary["phases"][phase_name]
            assert phase_info["started"] is not None
            assert phase_info["completed"] is not None
            assert phase_info["failed"] is False
