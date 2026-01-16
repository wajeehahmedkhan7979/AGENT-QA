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

