"""
Phase 2C: Adapter Contract Tests

Tests that verify implementations conform to adapter contracts.
"""

import pytest
from unittest.mock import Mock, patch
from typing import Dict, Any, List

from adapter_contracts import (
    GeneratedTest,
    LLMAdapterContract,
    LLMAdapterError,
    SemanticElement,
    SemanticModel,
    SemanticAdapterContract,
    SemanticAdapterError,
    ArtifactRecord,
    StorageAdapterContract,
    StorageAdapterError,
    QueueAdapterContract,
    QueueAdapterError,
    RunResultData,
    RunnerAdapterContract,
    RunnerAdapterError,
    ValidatorAdapterContract,
    ValidationError,
    AdapterRegistry,
)


# ============================================================================
# LLM ADAPTER CONTRACT TESTS
# ============================================================================

class TestLLMAdapterContract:
    """Test LLM adapter contract compliance."""
    
    def test_generated_test_fields(self):
        """GeneratedTest has required fields."""
        test = GeneratedTest(
            test_id="t_1",
            job_id="j_1",
            steps=[{"action": "goto", "url": "/"}],
            confidence=0.95,
        )
        
        assert test.test_id == "t_1"
        assert test.job_id == "j_1"
        assert isinstance(test.steps, list)
        assert test.confidence == 0.95
        assert test.format == "playwright-json"
    
    def test_generated_test_is_dataclass(self):
        """GeneratedTest is JSON-serializable."""
        test = GeneratedTest(
            test_id="t_1",
            job_id="j_1",
            steps=[],
            confidence=0.9,
        )
        
        # Should be convertible to dict
        test_dict = {
            "test_id": test.test_id,
            "job_id": test.job_id,
            "steps": test.steps,
            "confidence": test.confidence,
        }
        assert test_dict["test_id"] == "t_1"


# ============================================================================
# SEMANTIC ADAPTER CONTRACT TESTS
# ============================================================================

class TestSemanticAdapterContract:
    """Test semantic extraction adapter contract."""
    
    def test_semantic_element_fields(self):
        """SemanticElement has required fields."""
        elem = SemanticElement(
            id="btn_login",
            selector="#login-btn",
            role="login_button",
            label="Login Button",
            confidence=0.98,
        )
        
        assert elem.id == "btn_login"
        assert elem.selector == "#login-btn"
        assert elem.role == "login_button"
        assert 0.0 <= elem.confidence <= 1.0
    
    def test_semantic_model_fields(self):
        """SemanticModel has required fields."""
        elements = [
            SemanticElement(
                id="inp_user",
                selector="#username",
                role="username_input",
                label="Username",
                confidence=0.99,
            ),
        ]
        
        model = SemanticModel(
            job_id="j_1",
            elements=elements,
            flows=[],
            confidence=0.95,
        )
        
        assert model.job_id == "j_1"
        assert len(model.elements) == 1
        assert isinstance(model.flows, list)
        assert 0.0 <= model.confidence <= 1.0


# ============================================================================
# STORAGE ADAPTER CONTRACT TESTS
# ============================================================================

class TestStorageAdapterContract:
    """Test storage adapter contract."""
    
    def test_artifact_record_fields(self):
        """ArtifactRecord has required fields."""
        artifact = ArtifactRecord(
            name="dom.json",
            type="dom",
            path="job_1/dom.json",
        )
        
        assert artifact.name == "dom.json"
        assert artifact.type == "dom"
        assert artifact.path == "job_1/dom.json"
    
    def test_storage_error_is_exception(self):
        """StorageAdapterError is an Exception."""
        error = StorageAdapterError("Test error")
        assert isinstance(error, Exception)
        assert str(error) == "Test error"


# ============================================================================
# QUEUE ADAPTER CONTRACT TESTS
# ============================================================================

class TestQueueAdapterContract:
    """Test queue adapter contract."""
    
    def test_queue_error_is_exception(self):
        """QueueAdapterError is an Exception."""
        error = QueueAdapterError("Queue failed")
        assert isinstance(error, Exception)


# ============================================================================
# RUNNER ADAPTER CONTRACT TESTS
# ============================================================================

class TestRunnerAdapterContract:
    """Test runner adapter contract."""
    
    def test_test_run_result_fields(self):
        """TestRunResult has required fields."""
        result = RunResultData(
            run_id="run_1",
            job_id="j_1",
            test_id="t_1",
            status="passed",
            passed=5,
            failed=0,
            errors=[],
            duration_ms=1234.5,
        )
        
        assert result.run_id == "run_1"
        assert result.job_id == "j_1"
        assert result.test_id == "t_1"
        assert result.status in ["passed", "failed", "error"]
        assert result.passed >= 0
        assert result.failed >= 0
        assert isinstance(result.errors, list)
        assert result.duration_ms > 0
    
    def test_runner_error_is_exception(self):
        """RunnerAdapterError is an Exception."""
        error = RunnerAdapterError("Playwright failed")
        assert isinstance(error, Exception)


# ============================================================================
# VALIDATOR ADAPTER CONTRACT TESTS
# ============================================================================

class TestValidatorAdapterContract:
    """Test validator adapter contract."""
    
    def test_validation_error_is_exception(self):
        """ValidationError is an Exception."""
        error = ValidationError("Invalid steps")
        assert isinstance(error, Exception)


# ============================================================================
# ADAPTER REGISTRY TESTS
# ============================================================================

class TestAdapterRegistry:
    """Test adapter registry for pluggability."""
    
    def test_register_and_retrieve_adapter(self):
        """Registry can register and retrieve adapters."""
        registry = AdapterRegistry()
        mock_adapter = Mock()
        
        registry.register("llm", mock_adapter)
        assert registry.get("llm") is mock_adapter
    
    def test_get_unregistered_adapter_raises_error(self):
        """Getting unregistered adapter raises KeyError."""
        registry = AdapterRegistry()
        
        with pytest.raises(KeyError):
            registry.get("nonexistent")
    
    def test_list_adapters(self):
        """Registry can list all adapters."""
        registry = AdapterRegistry()
        adapter1 = Mock()
        adapter2 = Mock()
        
        registry.register("llm", adapter1)
        registry.register("storage", adapter2)
        
        adapters = registry.list_adapters()
        assert "llm" in adapters
        assert "storage" in adapters
        assert len(adapters) == 2
    
    def test_multiple_registries_are_independent(self):
        """Multiple registry instances are independent."""
        reg1 = AdapterRegistry()
        reg2 = AdapterRegistry()
        
        reg1.register("adapter1", Mock())
        
        # reg2 should not have adapter1
        with pytest.raises(KeyError):
            reg2.get("adapter1")


# ============================================================================
# ADAPTER PLUGGABILITY TESTS
# ============================================================================

class TestAdapterPluggability:
    """Test that adapters can be plugged in and out."""
    
    def test_mock_llm_adapter_meets_contract(self):
        """Mock LLM adapter can be registered and used."""
        # This is a smoke test - it verifies the pattern works
        registry = AdapterRegistry()
        mock_llm = Mock(spec=LLMAdapterContract)
        mock_llm.generate_tests.return_value = GeneratedTest(
            test_id="t_1",
            job_id="j_1",
            steps=[],
            confidence=0.9,
        )
        
        registry.register("llm", mock_llm)
        adapter = registry.get("llm")
        
        result = adapter.generate_tests("j_1", {})
        assert result.test_id == "t_1"
    
    def test_mock_storage_adapter_meets_contract(self):
        """Mock storage adapter can be registered."""
        registry = AdapterRegistry()
        mock_storage = Mock(spec=StorageAdapterContract)
        mock_storage.save_bytes.return_value = "job_1/test.bin"
        
        registry.register("storage", mock_storage)
        adapter = registry.get("storage")
        
        path = adapter.save_bytes("j_1", "test.bin", b"data")
        assert path == "job_1/test.bin"
    
    def test_multiple_implementations_can_coexist(self):
        """Different implementations can coexist in registry."""
        registry = AdapterRegistry()
        
        # Register multiple implementations
        registry.register("llm_mock", Mock(spec=LLMAdapterContract))
        registry.register("llm_prod", Mock(spec=LLMAdapterContract))
        
        assert registry.get("llm_mock") is not None
        assert registry.get("llm_prod") is not None


# ============================================================================
# ADAPTER ERROR HIERARCHY TESTS
# ============================================================================

class TestAdapterErrorHierarchy:
    """Test error hierarchy for adapters."""
    
    def test_all_adapter_errors_are_exceptions(self):
        """All adapter errors inherit from Exception."""
        errors = [
            LLMAdapterError("test"),
            SemanticAdapterError("test"),
            StorageAdapterError("test"),
            QueueAdapterError("test"),
            RunnerAdapterError("test"),
            ValidationError("test"),
        ]
        
        for error in errors:
            assert isinstance(error, Exception)
    
    def test_errors_can_be_caught(self):
        """Adapter errors can be caught and handled."""
        def failing_operation():
            raise StorageAdapterError("Disk full")
        
        with pytest.raises(StorageAdapterError):
            failing_operation()
