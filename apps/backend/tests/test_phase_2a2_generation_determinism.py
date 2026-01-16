"""
PHASE 2A.2: Test Generation Determinism

Tests that the mock LLM adapter produces stable, deterministic output.
Same semantic input must ALWAYS generate same test output.
"""
import pytest
from llm_adapter import MockLLMAdapter, GeneratedTest
from validator import validate_steps, ValidationError


class TestMockLLMDeterminism:
    """Test that mock LLM generates tests deterministically."""
    
    def test_same_input_same_output_multiple_calls(self):
        """Same semantic model should generate identical tests."""
        adapter = MockLLMAdapter()
        
        semantic_model = {
            "elements": [
                {"id": "el_1", "selector": "#username", "role": "username_input", "label": "Username", "confidence": 0.95},
                {"id": "el_2", "selector": "#password", "role": "password_input", "label": "Password", "confidence": 0.95},
                {"id": "el_3", "selector": "#login", "role": "login_button", "label": "Login", "confidence": 0.95},
            ],
            "flows": [],
        }
        
        results = []
        for i in range(3):
            result = adapter.generate_tests(f"job_{i}", semantic_model)
            results.append(result)
        
        # All steps should be identical (except test_id and job_id)
        step_sequences = [r.steps for r in results]
        
        # First check: all have same number of steps
        assert all(len(s) == len(step_sequences[0]) for s in step_sequences)
        
        # Second check: all steps match
        for i in range(len(step_sequences[0])):
            step_0 = step_sequences[0][i]
            for j in range(1, len(step_sequences)):
                step_j = step_sequences[j][i]
                assert step_0 == step_j, \
                    f"Step {i} differs between runs: {step_0} vs {step_j}"


class TestGeneratedTestStructure:
    """Test that generated test has correct structure."""
    
    def test_generated_test_has_required_fields(self):
        """GeneratedTest must have all required fields."""
        adapter = MockLLMAdapter()
        semantic_model = {
            "elements": [
                {"id": "el_1", "selector": "#btn", "role": "button", "label": "Click", "confidence": 0.9},
            ],
            "flows": [],
        }
        
        result = adapter.generate_tests("job_123", semantic_model)
        
        assert result.test_id is not None
        assert result.job_id == "job_123"
        assert isinstance(result.steps, list)
        assert result.confidence >= 0.0
        assert result.confidence <= 1.0
        assert result.format == "playwright-json"
    
    def test_generated_test_starts_with_goto(self):
        """Generated test should start with 'goto' action."""
        adapter = MockLLMAdapter()
        semantic_model = {
            "elements": [
                {"id": "el_1", "selector": "#btn", "role": "button", "label": "Click", "confidence": 0.9},
            ],
            "flows": [],
        }
        
        result = adapter.generate_tests("job_123", semantic_model)
        
        assert len(result.steps) > 0
        first_step = result.steps[0]
        assert first_step.get("action") == "goto"
        assert "url" in first_step


class TestGeneratedTestStepSchema:
    """Test that generated test steps conform to schema."""
    
    def test_all_steps_have_action(self):
        """Every step must have an 'action' field."""
        adapter = MockLLMAdapter()
        semantic_model = {
            "elements": [
                {"id": "el_1", "selector": "#username", "role": "username_input", "label": "Username", "confidence": 0.95},
                {"id": "el_2", "selector": "#password", "role": "password_input", "label": "Password", "confidence": 0.95},
                {"id": "el_3", "selector": "#login", "role": "login_button", "label": "Login", "confidence": 0.95},
            ],
            "flows": [],
        }
        
        result = adapter.generate_tests("job_123", semantic_model)
        
        for step in result.steps:
            assert "action" in step, f"Step missing 'action': {step}"
            assert step["action"] in {"goto", "fill", "click", "expectText"}
    
    def test_step_action_selector_validation(self):
        """Steps that need selectors must have them."""
        adapter = MockLLMAdapter()
        semantic_model = {
            "elements": [
                {"id": "el_1", "selector": "#username", "role": "username_input", "label": "Username", "confidence": 0.95},
                {"id": "el_2", "selector": "#password", "role": "password_input", "label": "Password", "confidence": 0.95},
                {"id": "el_3", "selector": "#login", "role": "login_button", "label": "Login", "confidence": 0.95},
            ],
            "flows": [],
        }
        
        result = adapter.generate_tests("job_123", semantic_model)
        
        for step in result.steps:
            action = step.get("action")
            
            # goto doesn't need selector
            if action == "goto":
                assert "url" in step
                continue
            
            # fill, click, expectText all need selector
            if action in {"fill", "click", "expectText"}:
                assert "selector" in step, f"Action {action} missing selector: {step}"


class TestReadOnlyConstraint:
    """Test that generated tests respect read-only scope."""
    
    def test_generated_tests_only_use_allowed_actions(self):
        """Generated tests should only use allowed actions."""
        adapter = MockLLMAdapter()
        
        semantic_model = {
            "elements": [
                {"id": "el_1", "selector": "#username", "role": "username_input", "label": "Username", "confidence": 0.95},
                {"id": "el_2", "selector": "#password", "role": "password_input", "label": "Password", "confidence": 0.95},
                {"id": "el_3", "selector": "#login", "role": "login_button", "label": "Login", "confidence": 0.95},
            ],
            "flows": [],
        }
        
        result = adapter.generate_tests("job_123", semantic_model)
        
        allowed = {"goto", "fill", "click", "expectText"}
        for step in result.steps:
            action = step.get("action")
            assert action in allowed, f"Forbidden action in read-only scope: {action}"
    
    def test_no_post_delete_in_test_steps(self):
        """Tests should never include POST, DELETE, or other HTTP mutations."""
        adapter = MockLLMAdapter()
        
        semantic_model = {
            "elements": [
                {"id": "el_1", "selector": "#username", "role": "username_input", "label": "Username", "confidence": 0.95},
                {"id": "el_2", "selector": "#password", "role": "password_input", "label": "Password", "confidence": 0.95},
                {"id": "el_3", "selector": "#login", "role": "login_button", "label": "Login", "confidence": 0.95},
            ],
            "flows": [],
        }
        
        result = adapter.generate_tests("job_123", semantic_model)
        
        forbidden_keywords = {"POST", "DELETE", "PUT", "PATCH"}
        for step in result.steps:
            step_str = str(step).upper()
            for keyword in forbidden_keywords:
                assert keyword not in step_str, \
                    f"Forbidden keyword '{keyword}' in step: {step}"


class TestValidatorIntegration:
    """Test that generated tests pass validation."""
    
    def test_generated_test_passes_validation(self):
        """Generated test should pass step validation."""
        adapter = MockLLMAdapter()
        
        semantic_model = {
            "elements": [
                {"id": "el_1", "selector": "#username", "role": "username_input", "label": "Username", "confidence": 0.95},
                {"id": "el_2", "selector": "#password", "role": "password_input", "label": "Password", "confidence": 0.95},
                {"id": "el_3", "selector": "#login", "role": "login_button", "label": "Login", "confidence": 0.95},
            ],
            "flows": [],
        }
        
        result = adapter.generate_tests("job_123", semantic_model)
        
        # Should not raise ValidationError
        score = validate_steps("read-only", result.steps)
        assert 0.0 <= score <= 1.0
        assert score >= 0.8  # Should have high confidence
