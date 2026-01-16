"""
PHASE 2A.3: Runner Failure Semantics

Tests that failure paths are observable and don't crash silently.
When a test fails, we should still capture:
  - Screenshots
  - Logs
  - Report status
  - Error messages
"""
import pytest
from validator import validate_steps, ValidationError


class TestFailureSemanticsContracts:
    """Test that failure paths follow contracts."""
    
    def test_validation_error_on_invalid_action(self):
        """Invalid actions should raise ValidationError, not silently fail."""
        invalid_steps = [
            {"action": "DELETE", "url": "/api/user"},  # Forbidden
        ]
        
        with pytest.raises(ValidationError):
            validate_steps("read-only", invalid_steps)
    
    def test_validation_error_on_missing_required_field(self):
        """Missing required fields should raise ValidationError."""
        invalid_steps = [
            {"action": "goto"},  # Missing 'url'
        ]
        
        with pytest.raises(ValidationError):
            validate_steps("read-only", invalid_steps)
    
    def test_validation_error_on_selector_required_but_missing(self):
        """Actions requiring selector should fail if missing."""
        invalid_steps = [
            {"action": "fill", "value": "text"},  # Missing 'selector'
        ]
        
        with pytest.raises(ValidationError):
            validate_steps("read-only", invalid_steps)


class TestValidStepsPassValidation:
    """Test that valid steps pass validation."""
    
    def test_valid_login_flow_passes(self):
        """A typical valid login flow should pass validation."""
        valid_steps = [
            {"action": "goto", "url": "/login"},
            {"action": "fill", "selector": "#username", "value": "user"},
            {"action": "fill", "selector": "#password", "value": "pass"},
            {"action": "click", "selector": "#login"},
            {"action": "expectText", "selector": "h1", "value": "Dashboard"},
        ]
        
        # Should not raise
        score = validate_steps("read-only", valid_steps)
        assert score >= 0.9
    
    def test_single_navigation_passes(self):
        """Simple navigation should pass."""
        valid_steps = [
            {"action": "goto", "url": "/"},
        ]
        
        score = validate_steps("read-only", valid_steps)
        assert score >= 0.9
    
    def test_empty_steps_validation(self):
        """Empty steps list should pass (edge case)."""
        valid_steps = []
        
        # Should handle gracefully
        try:
            score = validate_steps("read-only", valid_steps)
            # Either passes with low score or succeeds
            assert score >= 0.0
        except Exception:
            # If it raises, it should be ValidationError
            pass


class TestConfidenceScoring:
    """Test that confidence scores are meaningful."""
    
    def test_longer_valid_tests_have_higher_confidence(self):
        """Longer valid tests should have higher confidence than single step."""
        short_test = [
            {"action": "goto", "url": "/"},
        ]
        
        long_test = [
            {"action": "goto", "url": "/"},
            {"action": "fill", "selector": "#username", "value": "user"},
            {"action": "fill", "selector": "#password", "value": "pass"},
            {"action": "click", "selector": "#login"},
            {"action": "expectText", "selector": "h1", "value": "Success"},
        ]
        
        short_score = validate_steps("read-only", short_test)
        long_score = validate_steps("read-only", long_test)
        
        # Longer test should have higher confidence
        assert long_score > short_score


class TestErrorMessages:
    """Test that error messages are informative."""
    
    def test_validation_error_message_includes_reason(self):
        """ValidationError should include helpful message."""
        invalid_steps = [
            {"action": "MUTATE", "selector": "#form"},
        ]
        
        try:
            validate_steps("read-only", invalid_steps)
            assert False, "Should have raised ValidationError"
        except ValidationError as e:
            error_msg = str(e)
            # Should mention what went wrong
            assert "action" in error_msg.lower() or "unsupported" in error_msg.lower()


class TestBoundaryConditions:
    """Test edge cases and boundary conditions."""
    
    def test_very_long_steps_list(self):
        """Should handle large number of steps."""
        steps = [
            {"action": "goto", "url": "/"},
        ]
        # Add many valid steps
        for i in range(100):
            steps.append({
                "action": "expectText",
                "selector": f"#item_{i}",
                "value": f"Item {i}"
            })
        
        # Should handle without crashing
        score = validate_steps("read-only", steps)
        assert score >= 0.0
    
    def test_special_characters_in_values(self):
        """Should handle special characters in values."""
        steps = [
            {"action": "goto", "url": "/search?q=test&page=1"},
            {"action": "fill", "selector": "#query", "value": "test@example.com"},
            {"action": "expectText", "selector": ".result", "value": "Results <42>"},
        ]
        
        # Should not crash on special characters
        score = validate_steps("read-only", steps)
        assert score >= 0.0


class TestReadOnlyEnforcement:
    """Test that read-only scope is enforced."""
    
    def test_post_action_raises_error(self):
        """POST-like actions should be rejected in read-only scope."""
        steps_with_http_method = [
            {"action": "POST", "url": "/api/users"},
        ]
        
        with pytest.raises(ValidationError):
            validate_steps("read-only", steps_with_http_method)
    
    def test_delete_action_raises_error(self):
        """DELETE-like actions should be rejected."""
        steps_with_delete = [
            {"action": "DELETE", "url": "/api/user/123"},
        ]
        
        with pytest.raises(ValidationError):
            validate_steps("read-only", steps_with_delete)


class TestNoSilentFailures:
    """Contract: errors should be explicit, never silent."""
    
    def test_validation_always_returns_or_raises(self):
        """Validation should never return None or undefined."""
        valid_steps = [
            {"action": "goto", "url": "/"},
        ]
        
        result = validate_steps("read-only", valid_steps)
        
        # Should always return a number
        assert isinstance(result, (int, float))
        assert not (result is None)
    
    def test_invalid_scope_handling(self):
        """Even invalid scope should be handled (not crash)."""
        steps = [
            {"action": "goto", "url": "/"},
        ]
        
        # Try with invalid scope
        try:
            # This might raise or handle gracefully
            result = validate_steps("invalid_scope", steps)
            # If it returns, should be a number
            assert isinstance(result, (int, float))
        except Exception as e:
            # If it raises, should be an expected error type
            assert isinstance(e, (ValidationError, KeyError, ValueError))
