from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ClassifiedElement:
    role: str
    confidence: float


def classify_element(label: str, tag_name: str) -> ClassifiedElement:
    """
    Deterministic mock classifier for UI elements.

    This is deliberately simple and rule-based so that tests are
    repeatable and no external LLM calls are required.
    """
    text = (label or "").lower()
    tag = tag_name.lower()

    if "login" in text or ("sign in" in text):
        return ClassifiedElement(role="login_button", confidence=0.95)
    if "username" in text or "user name" in text:
        return ClassifiedElement(role="username_input", confidence=0.95)
    if "password" in text:
        return ClassifiedElement(role="password_input", confidence=0.95)
    if tag == "button":
        return ClassifiedElement(role="button", confidence=0.8)
    if tag in ("a", "link"):
        return ClassifiedElement(role="link", confidence=0.8)
    if tag == "input":
        return ClassifiedElement(role="input", confidence=0.7)

    return ClassifiedElement(role="generic", confidence=0.5)



@dataclass
class GeneratedTestStep:
    """Represents a single test step."""
    action: str
    selector: str = ""
    value: str = ""
    url: str = ""
    expectedText: str = ""
    
    def get(self, key: str, default=None):
        """Dict-like interface for backwards compatibility."""
        return getattr(self, key, default)


@dataclass
class GeneratedTestResult:
    """Represents a generated test."""
    test_id: str
    job_id: str
    steps: list
    confidence: float


class MockLLMAdapter:
    """Mock LLM adapter that generates deterministic test cases."""
    
    def __init__(self):
        self.test_counter = 0
    
    def generate_tests(self, job_id: str, semantic_model: dict) -> GeneratedTestResult:
        """
        Generate a test from a semantic model.
        
        Args:
            job_id: Job identifier
            semantic_model: Semantic model dict with elements, flows
            
        Returns:
            GeneratedTestResult with test steps
        """
        self.test_counter += 1
        test_id = f"t_{self.test_counter}"
        
        # Extract elements
        elements = semantic_model.get("elements", [])
        
        # Build test steps from elements
        steps = []
        
        # First step: navigate
        steps.append({"action": "goto", "url": "https://example.com", "selector": "", "value": ""})
        
        # Add interaction steps for each element
        for element in elements:
            role = element.get("role", "")
            selector = element.get("selector", "")
            label = element.get("label", "")
            
            if role == "username_input":
                steps.append({"action": "fill", "selector": selector, "value": "testuser"})
            elif role == "password_input":
                steps.append({"action": "fill", "selector": selector, "value": "testpass"})
            elif role == "login_button":
                steps.append({"action": "click", "selector": selector})
            elif role == "button":
                steps.append({"action": "click", "selector": selector})
        
        # Add assertion step
        if elements:
            steps.append({"action": "assert", "selector": "body", "expectedText": "success"})
        
        return GeneratedTestResult(
            test_id=test_id,
            job_id=job_id,
            steps=steps,
            confidence=0.92
        )
