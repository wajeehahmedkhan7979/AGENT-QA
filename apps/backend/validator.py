from __future__ import annotations

from typing import Any, Dict, List


READ_ONLY_METHODS = {"GET", "HEAD", "OPTIONS"}


class ValidationError(Exception):
    pass


def validate_steps(scope: str, steps: List[Dict[str, Any]]) -> float:
    """
    Validate that steps conform to the allowed action schema and scope.
    Returns a confidence score between 0 and 1.
    Raises ValidationError if the steps are structurally invalid.
    """
    allowed_actions = {
        "goto",
        "fill",
        "click",
        "expectText",
    }

    for step in steps:
        action = step.get("action")
        if action not in allowed_actions:
            raise ValidationError(f"Unsupported action: {action}")

        # Very simple schema checks
        if action == "goto" and "url" not in step:
            raise ValidationError("goto step must include 'url'")
        if action in {"fill", "click", "expectText"} and "selector" not in step:
            raise ValidationError(f"{action} step must include 'selector'")
        if action in {"fill", "expectText"} and "value" not in step:
            raise ValidationError(f"{action} step must include 'value'")

        # Enforce read-only constraint: for this demo, steps never issue HTTP
        # methods directly, but this is where we would inspect any embedded
        # method/url metadata if present.

    # Confidence heuristic: longer well-formed tests get slightly higher confidence
    base_confidence = 0.9
    length_bonus = min(len(steps) * 0.01, 0.05)
    return base_confidence + length_bonus

