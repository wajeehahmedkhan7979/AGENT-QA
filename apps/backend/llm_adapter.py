from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Dict, List, Protocol

from openai import OpenAI


@dataclass
class GeneratedTest:
    test_id: str
    job_id: str
    steps: List[Dict[str, Any]]
    confidence: float
    format: str = "playwright-json"
    gherkin: str | None = None


class LLMAdapter(Protocol):
    def generate_tests(self, job_id: str, semantic_model: dict) -> GeneratedTest:
        ...


class MockLLMAdapter:
    """
    Deterministic mock implementation for demo.
    Uses simple rules over the semantic model to emit a single happy-path test.
    """

    def generate_tests(self, job_id: str, semantic_model: dict) -> GeneratedTest:
        elements = semantic_model.get("elements", [])
        flows = semantic_model.get("flows", [])

        username = next((e for e in elements if e.get("role") == "username_input"), None)
        password = next((e for e in elements if e.get("role") == "password_input"), None)
        login_btn = next((e for e in elements if e.get("role") == "login_button"), None)

        steps: List[Dict[str, Any]] = [
            {"action": "goto", "url": "/sample-app/login"},
        ]

        if username and password and login_btn:
            steps.extend(
                [
                    {
                        "action": "fill",
                        "selector": username["selector"],
                        "value": "demo",
                    },
                    {
                        "action": "fill",
                        "selector": password["selector"],
                        "value": "demo",
                    },
                    {
                        "action": "click",
                        "selector": login_btn["selector"],
                    },
                    {
                        "action": "expectText",
                        "selector": "h2",
                        "value": "Welcome",
                    },
                ]
            )
            confidence = 0.95
        else:
            # Fallback: only visit the page
            confidence = 0.6

        gherkin_lines = [
            "Feature: Sample app login",
            "  Scenario: Happy path login",
            "    Given I open the login page",
        ]
        if username and password:
            gherkin_lines.append(
                "    When I fill in username and password with demo credentials"
            )
        if login_btn:
            gherkin_lines.append("    And I click the login button")
        gherkin_lines.append('    Then I should see "Welcome" on the page')

        gherkin = "\n".join(gherkin_lines)

        return GeneratedTest(
            test_id="t_1",
            job_id=job_id,
            steps=steps,
            confidence=confidence,
            format="playwright-json",
            gherkin=gherkin,
        )


class OpenAIAdapter:
    """
    Real LLM adapter using OpenAI. Only enabled when OPENAI_API_KEY is present.

    For demo safety, we still generate a read-only, happy-path test definition.
    """

    def __init__(self, api_key: str, model: str) -> None:
        self._client = OpenAI(api_key=api_key)
        self._model = model

    def generate_tests(self, job_id: str, semantic_model: dict) -> GeneratedTest:
        # Minimal prompt: produce Playwright-json steps only.
        # NOTE: We do not set store=True and we do not include secrets.
        prompt = {
            "job_id": job_id,
            "task": "Generate ONE happy-path Playwright-json test for this semantic model. Read-only only.",
            "semantic_model": semantic_model,
            "required_format": {
                "testId": "t_1",
                "steps": [
                    {"action": "goto", "url": "/..."},
                    {"action": "fill", "selector": "...", "value": "..."},
                    {"action": "click", "selector": "..."},
                    {"action": "expectText", "selector": "...", "value": "..."},
                ],
            },
        }

        resp = self._client.responses.create(
            model=self._model,
            input=[
                {
                    "role": "system",
                    "content": "Return ONLY valid JSON. No markdown. No extra keys.",
                },
                {
                    "role": "user",
                    "content": str(prompt),
                },
            ],
        )
        text = resp.output_text.strip()

        # Extremely defensive parse: if OpenAI returns anything unexpected,
        # fall back to the deterministic mock adapter.
        import json

        try:
            data = json.loads(text)
            steps = data.get("steps", [])
            return GeneratedTest(
                test_id=data.get("testId", "t_1"),
                job_id=job_id,
                steps=steps,
                confidence=0.85,
                format="playwright-json",
                gherkin=None,
            )
        except Exception:
            return MockLLMAdapter().generate_tests(job_id, semantic_model)


def get_llm_adapter() -> LLMAdapter:
    """
    Adapter selection:
      - If OPENAI_API_KEY is set, use OpenAIAdapter.
      - Otherwise, use the deterministic MockLLMAdapter.
    """
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if api_key:
        model = os.getenv("OPENAI_MODEL", "gpt-5-nano").strip() or "gpt-5-nano"
        return OpenAIAdapter(api_key=api_key, model=model)
    return MockLLMAdapter()

