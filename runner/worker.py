from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from playwright.sync_api import sync_playwright
from rq import get_current_job

from backend.config import settings
from backend.storage import storage_adapter


def _load_test(job_id: str, test_id: str) -> Dict[str, Any]:
    root = Path(settings.storage_root)
    path = root / job_id / "generated_test.json"
    raw = path.read_text(encoding="utf-8")
    data = json.loads(raw)
    if data.get("testId") != test_id:
        # For demo we assume a single test per job; in case of mismatch just return.
        return data
    return data


def _build_url(relative: str) -> str:
    base = getattr(settings, "test_base_url", None) or "http://sample-app:3000"
    if relative.startswith("http://") or relative.startswith("https://"):
        return relative
    if not relative.startswith("/"):
        relative = "/" + relative
    return base.rstrip("/") + relative


def run_test(job_id: str, test_id: str) -> None:
    """
    RQ task that executes a generated Playwright JSON test in an isolated
    container and stores a structured report.
    """
    test_def = _load_test(job_id, test_id)
    steps_def: List[Dict[str, Any]] = test_def.get("steps", [])

    started_at = datetime.now(timezone.utc)
    step_results: List[Dict[str, Any]] = []
    artifacts: List[str] = []
    status = "passed"

    root = storage_adapter.job_dir(job_id)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        try:
            for idx, step in enumerate(steps_def, start=1):
                action = step.get("action")
                try:
                    if action == "goto":
                        url = _build_url(step["url"])
                        page.goto(url, wait_until="networkidle")
                    elif action == "fill":
                        page.fill(step["selector"], step["value"])
                    elif action == "click":
                        page.click(step["selector"])
                    elif action == "expectText":
                        locator = page.locator(step["selector"])
                        locator.wait_for(state="visible", timeout=5000)
                        text_content = locator.inner_text()
                        if step["value"] not in text_content:
                            raise AssertionError(
                                f'Expected "{step["value"]}" in "{text_content}"'
                            )
                    else:
                        # Unsupported action should not happen if validator ran.
                        raise RuntimeError(f"Unsupported action at runtime: {action}")

                    # Optionally capture a screenshot per step for debugging
                    screenshot_name = f"run_{test_id}_step_{idx}.png"
                    screenshot_path = root / screenshot_name
                    page.screenshot(path=str(screenshot_path), full_page=True)
                    artifacts.append(f"{job_id}/{screenshot_name}")

                    step_results.append(
                        {
                            "step": idx,
                            "status": "passed",
                            "screenshot": f"{job_id}/{screenshot_name}",
                        }
                    )
                except Exception as exc:  # noqa: BLE001
                    status = "failed"
                    step_results.append(
                        {
                            "step": idx,
                            "status": "failed",
                            "error": str(exc),
                        }
                    )
                    break
        finally:
            context.close()
            browser.close()

    finished_at = datetime.now(timezone.utc)

    rq_job = get_current_job()
    run_id = rq_job.id if rq_job else f"run_{test_id}_{int(finished_at.timestamp())}"

    report = {
        "runId": run_id,
        "testId": test_id,
        "status": status,
        "steps": step_results,
        "artifacts": artifacts,
        "startedAt": started_at.isoformat(),
        "finishedAt": finished_at.isoformat(),
    }

    # Persist report as both a specific run file and a "latest" pointer
    report_name = f"test_report_{run_id}.json"
    storage_adapter.save_json(job_id, report_name, report)
    storage_adapter.save_json(job_id, "last_run.json", report)

