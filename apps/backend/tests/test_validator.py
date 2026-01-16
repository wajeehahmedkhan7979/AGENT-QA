from validator import validate_steps


def test_validate_steps_happy_path() -> None:
    steps = [
        {"action": "goto", "url": "/sample-app/login"},
        {"action": "fill", "selector": "#username", "value": "demo"},
        {"action": "fill", "selector": "#password", "value": "demo"},
        {"action": "click", "selector": "#login"},
        {"action": "expectText", "selector": "h2", "value": "Welcome"},
    ]

    score = validate_steps("read-only", steps)
    assert 0.9 <= score <= 1.0

