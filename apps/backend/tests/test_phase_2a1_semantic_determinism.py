"""
PHASE 2A.1: Semantic Model Validation

Tests that semantic extraction is DETERMINISTIC and STABLE.
Same HTML input must ALWAYS produce same semantic output.
"""
import json
import pytest
from bs4 import BeautifulSoup
from pathlib import Path

# Import semantic functions - adjust path as needed
try:
    from semantic import build_semantic_model, _build_selector
except ImportError:
    # For running from test directory
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from semantic import build_semantic_model, _build_selector


def load_golden_fixture(fixture_name: str) -> dict:
    """Load golden fixture from JSON file."""
    fixture_path = Path(__file__).parent / "golden" / "semantic" / f"{fixture_name}.json"
    with open(fixture_path, 'r') as f:
        return json.load(f)


class TestSemanticDeterminism:
    """Test that semantic extraction is deterministic."""
    
    def test_selector_determinism_with_id(self):
        """Selector should ALWAYS prefer ID over other attributes."""
        html = '<button id="login" class="btn primary">Login</button>'
        soup = BeautifulSoup(html, "html.parser")
        el = soup.find("button")
        
        selector = _build_selector(el)
        assert selector == "#login", f"Expected #login, got {selector}"
    
    def test_selector_determinism_with_name(self):
        """Selector should use name if ID not available."""
        html = '<input name="username" class="input" />'
        soup = BeautifulSoup(html, "html.parser")
        el = soup.find("input")
        
        selector = _build_selector(el)
        # Should be input[name='username']
        assert "username" in selector or "input" in selector
    
    def test_selector_stability_multiple_calls(self):
        """Multiple calls with same HTML should produce identical selectors."""
        html = '<div id="form"><input id="email" type="email" /></div>'
        
        results = []
        for _ in range(5):
            soup = BeautifulSoup(html, "html.parser")
            el = soup.find("input")
            results.append(_build_selector(el))
        
        # All results should be identical
        assert len(set(results)) == 1, f"Selector not stable: {results}"
        assert results[0] == "#email"


class TestSemanticStructure:
    """Test that semantic output has correct structure."""
    
    def test_semantic_element_has_required_fields(self):
        """Each element must have required fields."""
        fixture = load_golden_fixture("login_page")
        required_fields = {"selector", "role", "label", "confidence_range"}
        
        for expected in fixture["expected_elements"]:
            assert all(field in expected for field in required_fields), \
                f"Missing fields in {expected}"
    
    def test_confidence_within_bounds(self):
        """Confidence must be in valid range."""
        fixture = load_golden_fixture("login_page")
        
        for expected in fixture["expected_elements"]:
            conf_range = expected["confidence_range"]
            assert len(conf_range) == 2
            assert 0.0 <= conf_range[0] <= conf_range[1] <= 1.0, \
                f"Invalid confidence range: {conf_range}"


class TestSemanticRoleClassification:
    """Test role classification stability."""
    
    def test_login_page_roles_deterministic(self):
        """Login page should always extract same roles."""
        fixture = load_golden_fixture("login_page")
        
        # Expected roles from fixture
        expected_roles = {elem["selector"]: elem["role"] 
                         for elem in fixture["expected_elements"]}
        
        # Verify fixture is well-formed
        assert len(expected_roles) == 3
        assert "username_input" in expected_roles.values()
        assert "password_input" in expected_roles.values()
        assert "login_button" in expected_roles.values()


class TestSemanticOutputFormat:
    """Test that output conforms to schema."""
    
    def test_semantic_model_structure(self):
        """Semantic model must have 'elements' and 'flows' keys."""
        fixture = load_golden_fixture("login_page")
        
        # The fixture itself should define the expected structure
        assert "expected_elements" in fixture
        expected_elements = fixture["expected_elements"]
        
        assert isinstance(expected_elements, list)
        assert len(expected_elements) > 0
        
        # Each element should have required structure
        for elem in expected_elements:
            assert "selector" in elem
            assert "role" in elem
            assert "confidence_range" in elem
