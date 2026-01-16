from llm_adapter import MockLLMAdapter


def test_mock_llm_generates_login_flow() -> None:
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

    assert result.test_id == "t_1"
    assert result.job_id == "job_123"
    assert any(step.get("action") == "goto" for step in result.steps)
    assert result.confidence > 0.9

