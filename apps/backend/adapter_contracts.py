"""
Phase 2C: Adapter Contracts

Explicit Protocol definitions for all adapters.
These contracts define the boundaries and expected behavior.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Protocol


# ============================================================================
# LLM ADAPTER CONTRACT
# ============================================================================

@dataclass
class GeneratedTest:
    """Output of LLM test generation."""
    test_id: str
    job_id: str
    steps: List[Dict[str, Any]]
    confidence: float
    format: str = "playwright-json"
    gherkin: Optional[str] = None


class LLMAdapterContract(Protocol):
    """
    LLM Adapter Contract: Converts semantic models to test steps.
    
    Contract:
    - Input: job_id (str) + semantic_model (dict with elements/flows)
    - Output: GeneratedTest with deterministic test steps
    - No side effects: Never modifies job state or logs
    - Determinism: Same semantic model produces same test structure
    - Error handling: Raises LLMAdapterError on validation failure
    """
    
    def generate_tests(self, job_id: str, semantic_model: dict) -> GeneratedTest:
        """
        Generate test steps from semantic model.
        
        Args:
            job_id: Unique job identifier
            semantic_model: Dict with 'elements' list and 'flows' list
        
        Returns:
            GeneratedTest with steps, confidence score
        
        Raises:
            LLMAdapterError: If semantic model is invalid
        """
        ...


class LLMAdapterError(Exception):
    """LLM adapter errors."""
    pass


# ============================================================================
# SEMANTIC EXTRACTION ADAPTER CONTRACT
# ============================================================================

@dataclass
class SemanticElement:
    """Extracted semantic element from DOM."""
    id: str
    selector: str
    role: str  # e.g., "login_button", "username_input", "form"
    label: str  # Human-readable description
    confidence: float  # 0.0 to 1.0


@dataclass
class SemanticModel:
    """Output of semantic extraction."""
    job_id: str
    elements: List[SemanticElement]
    flows: List[Dict[str, Any]]
    confidence: float  # Overall model confidence


class SemanticAdapterContract(Protocol):
    """
    Semantic Extraction Adapter Contract: Analyzes HTML to extract meaning.
    
    Contract:
    - Input: job_id (str) + DOM HTML + optional HAR trace
    - Output: SemanticModel with elements and flows
    - No side effects: Never modifies job state
    - Determinism: Same DOM produces same semantic model
    - Error handling: Raises SemanticAdapterError on invalid input
    """
    
    def extract_semantic_model(
        self,
        job_id: str,
        dom_html: str,
        har_trace: Optional[Dict[str, Any]] = None,
    ) -> SemanticModel:
        """
        Extract semantic model from HTML DOM.
        
        Args:
            job_id: Unique job identifier
            dom_html: HTML string
            har_trace: Optional HAR trace for additional context
        
        Returns:
            SemanticModel with extracted elements and flows
        
        Raises:
            SemanticAdapterError: If DOM is invalid
        """
        ...


class SemanticAdapterError(Exception):
    """Semantic adapter errors."""
    pass


# ============================================================================
# STORAGE ADAPTER CONTRACT
# ============================================================================

@dataclass
class ArtifactRecord:
    """Reference to a stored artifact."""
    name: str
    type: str  # e.g., "dom", "trace", "test", "results"
    path: str  # Relative path from storage root


class StorageAdapterContract(Protocol):
    """
    Storage Adapter Contract: Persists job artifacts.
    
    Contract:
    - Storage: File-based or S3-backed, transparent to caller
    - Atomicity: save_* operations are atomic
    - Consistency: All reads return consistent data
    - Error handling: Raises StorageAdapterError on failure
    """
    
    def save_bytes(self, job_id: str, filename: str, data: bytes) -> str:
        """
        Save binary data for a job.
        
        Args:
            job_id: Unique job identifier
            filename: Filename within job directory
            data: Binary data to save
        
        Returns:
            Relative path to saved file
        
        Raises:
            StorageAdapterError: If save fails
        """
        ...
    
    def save_json(self, job_id: str, filename: str, obj: object) -> str:
        """
        Save JSON object for a job.
        
        Args:
            job_id: Unique job identifier
            filename: Filename within job directory
            obj: Object to JSON serialize
        
        Returns:
            Relative path to saved file
        
        Raises:
            StorageAdapterError: If save fails
        """
        ...
    
    def load_bytes(self, job_id: str, filename: str) -> bytes:
        """
        Load binary data for a job.
        
        Args:
            job_id: Unique job identifier
            filename: Filename within job directory
        
        Returns:
            Binary data
        
        Raises:
            StorageAdapterError: If load fails
        """
        ...
    
    def load_json(self, job_id: str, filename: str) -> object:
        """
        Load JSON object for a job.
        
        Args:
            job_id: Unique job identifier
            filename: Filename within job directory
        
        Returns:
            Deserialized JSON object
        
        Raises:
            StorageAdapterError: If load fails
        """
        ...
    
    def load_manifest(self, job_id: str) -> List[ArtifactRecord]:
        """
        List all artifacts for a job.
        
        Args:
            job_id: Unique job identifier
        
        Returns:
            List of ArtifactRecords
        
        Raises:
            StorageAdapterError: If manifest read fails
        """
        ...


class StorageAdapterError(Exception):
    """Storage adapter errors."""
    pass


# ============================================================================
# QUEUE ADAPTER CONTRACT
# ============================================================================

class QueueAdapterContract(Protocol):
    """
    Queue Adapter Contract: Orchestrates async job processing.
    
    Contract:
    - Enqueue: Submit jobs atomically
    - Idempotent: Same job_id can be enqueued multiple times
    - Ordering: FIFO within each queue
    - Error handling: Raises QueueAdapterError on failure
    """
    
    def enqueue_extraction(self, job_id: str) -> None:
        """
        Enqueue extraction job.
        
        Args:
            job_id: Unique job identifier
        
        Raises:
            QueueAdapterError: If enqueue fails
        """
        ...
    
    def enqueue_test_run(self, job_id: str, test_id: str) -> str:
        """
        Enqueue test run job.
        
        Args:
            job_id: Unique job identifier
            test_id: Unique test identifier
        
        Returns:
            Run ID (opaque string)
        
        Raises:
            QueueAdapterError: If enqueue fails
        """
        ...


class QueueAdapterError(Exception):
    """Queue adapter errors."""
    pass


# ============================================================================
# RUNNER ADAPTER CONTRACT
# ============================================================================

@dataclass
class RunResultData:
    """Result of test execution."""
    run_id: str
    job_id: str
    test_id: str
    status: str  # "passed", "failed", "error"
    passed: int
    failed: int
    errors: List[str]
    duration_ms: float


class RunnerAdapterContract(Protocol):
    """
    Runner Adapter Contract: Executes tests with Playwright.
    
    Contract:
    - Execution: Runs test steps deterministically
    - Isolation: Each run is isolated (no state leakage)
    - Reporting: Captures pass/fail with error messages
    - Error handling: Raises RunnerAdapterError on critical failure
    """
    
    def run_test(
        self,
        job_id: str,
        test_id: str,
        steps: List[Dict[str, Any]],
        timeout_seconds: float = 30.0,
    ) -> TestRunResult:
        """
        Execute test steps.
        
        Args:
            job_id: Unique job identifier
            test_id: Unique test identifier
            steps: List of test steps
            timeout_seconds: Execution timeout
        
        Returns:
            TestRunResult with status and metrics
        
        Raises:
            RunnerAdapterError: If execution fails critically
        """
        ...


class RunnerAdapterError(Exception):
    """Runner adapter errors."""
    pass


# ============================================================================
# VALIDATOR ADAPTER CONTRACT
# ============================================================================

class ValidatorAdapterContract(Protocol):
    """
    Validator Adapter Contract: Validates test steps and scope.
    
    Contract:
    - Validation: Check steps conform to schema
    - Scope enforcement: Ensure no side effects (read-only)
    - Confidence scoring: Return 0.0-1.0 score
    - Error handling: Raises ValidationError on invalid steps
    """
    
    def validate_steps(self, scope: str, steps: List[Dict[str, Any]]) -> float:
        """
        Validate test steps against scope and schema.
        
        Args:
            scope: Execution scope (e.g., "read_only")
            steps: List of test steps
        
        Returns:
            Confidence score (0.0-1.0)
        
        Raises:
            ValidationError: If steps are invalid
        """
        ...


class ValidationError(Exception):
    """Validation errors."""
    pass


# ============================================================================
# ADAPTER REGISTRY
# ============================================================================

class AdapterRegistry:
    """
    Central registry for all adapters.
    
    Purpose: Enable pluggable adapter implementations.
    """
    
    def __init__(self):
        self._adapters: Dict[str, Any] = {}
    
    def register(self, name: str, adapter: Any) -> None:
        """Register an adapter implementation."""
        self._adapters[name] = adapter
    
    def get(self, name: str) -> Any:
        """Retrieve registered adapter."""
        if name not in self._adapters:
            raise KeyError(f"Adapter not registered: {name}")
        return self._adapters[name]
    
    def list_adapters(self) -> Dict[str, str]:
        """List all registered adapters with their types."""
        return {name: type(adapter).__name__ for name, adapter in self._adapters.items()}
