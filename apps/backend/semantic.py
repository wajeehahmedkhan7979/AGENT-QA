from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List

from bs4 import BeautifulSoup

from config import settings
from mock_llm import ClassifiedElement, classify_element
from storage import storage_adapter, ArtifactRecord


@dataclass
class SemanticElement:
    id: str
    selector: str
    role: str
    label: str
    confidence: float


def _load_dom(job_id: str) -> str:
    path = Path(settings.storage_root) / job_id / "dom.json"
    raw = path.read_text(encoding="utf-8")
    data = json.loads(raw)
    return data.get("outer_html", "")


def _load_har(job_id: str) -> Dict[str, Any] | None:
    path = Path(settings.storage_root) / job_id / "trace.har"
    if not path.exists():
        return None
    raw = path.read_text(encoding="utf-8", errors="ignore")
    try:
        return json.loads(raw)
    except Exception:
        return None


def _build_selector(el) -> str:
    el_id = el.get("id")
    if el_id:
        return f"#{el_id}"
    name = el.get("name")
    if name:
        return f"{el.name}[name='{name}']"
    cls = el.get("class")
    if cls:
        return f"{el.name}.{'.'.join(cls)}"
    return el.name


def _label_for_input(soup: BeautifulSoup, el) -> str:
    # Label via <label for="...">
    el_id = el.get("id")
    if el_id:
        label_el = soup.find("label", attrs={"for": el_id})
        if label_el and label_el.get_text(strip=True):
            return label_el.get_text(strip=True)
    # aria-label
    aria = el.get("aria-label")
    if aria:
        return aria
    # Placeholder as a last resort
    placeholder = el.get("placeholder")
    if placeholder:
        return placeholder
    return ""


def build_semantic_model(job_id: str) -> Dict[str, Any]:
    outer_html = _load_dom(job_id)
    soup = BeautifulSoup(outer_html, "html.parser")

    elements: List[SemanticElement] = []
    counter = 1

    # Clickable elements
    clickable_tags = ["a", "button"]
    for tag in clickable_tags:
        for el in soup.find_all(tag):
            label = el.get_text(strip=True) or el.get("aria-label", "") or ""
            if not label:
                continue
            selector = _build_selector(el)
            classified: ClassifiedElement = classify_element(label, el.name)
            elements.append(
                SemanticElement(
                    id=f"el_{counter}",
                    selector=selector,
                    role=classified.role,
                    label=label,
                    confidence=classified.confidence,
                )
            )
            counter += 1

    # Inputs
    for el in soup.find_all("input"):
        label = _label_for_input(soup, el)
        selector = _build_selector(el)
        classified = classify_element(label or selector, el.name)
        elements.append(
            SemanticElement(
                id=f"el_{counter}",
                selector=selector,
                role=classified.role,
                label=label or selector,
                confidence=classified.confidence,
            )
        )
        counter += 1

    # Simple inferred flow (very naive): if we have username_input, password_input,
    # and login_button, define a login flow.
    roles = {e.role: e for e in elements}
    flows: List[Dict[str, Any]] = []
    if (
        "username_input" in roles
        and "password_input" in roles
        and "login_button" in roles
    ):
        flows.append(
            {
                "id": "flow_login",
                "description": "Basic login flow inferred from semantic elements.",
                "steps": [
                    {"action": "fill", "target": roles["username_input"].id},
                    {"action": "fill", "target": roles["password_input"].id},
                    {"action": "click", "target": roles["login_button"].id},
                ],
            }
        )

    model = {
        "elements": [asdict(e) for e in elements],
        "flows": flows,
    }

    storage_adapter.save_json(job_id, "semantic_model.json", model)
    return model


def build_api_catalog(job_id: str) -> Dict[str, Any]:
    har = _load_har(job_id)
    endpoints: List[Dict[str, Any]] = []
    if not har:
        catalog = {"endpoints": endpoints}
        storage_adapter.save_json(job_id, "api_catalog.json", catalog)
        return catalog

    entries = har.get("log", {}).get("entries", [])
    for entry in entries:
        request = entry.get("request", {})
        response = entry.get("response", {})

        method = request.get("method", "")
        url = request.get("url", "")
        status = response.get("status", 0)

        post_data = request.get("postData", {})
        req_body = post_data.get("text") if isinstance(post_data, dict) else None

        content = response.get("content", {})
        res_body = content.get("text") if isinstance(content, dict) else None

        endpoints.append(
            {
                "method": method,
                "url": url,
                "status": status,
                "sampleRequestBody": req_body,
                "sampleResponseBody": res_body,
            }
        )

    catalog = {"endpoints": endpoints}
    storage_adapter.save_json(job_id, "api_catalog.json", catalog)
    return catalog


def ensure_semantic_outputs(job_id: str) -> Dict[str, Any]:
    """
    Build semantic_model.json and api_catalog.json if they don't exist yet,
    then return both in a single structure for the API.
    """
    job_dir = storage_adapter.job_dir(job_id)
    semantic_path = job_dir / "semantic_model.json"
    api_catalog_path = job_dir / "api_catalog.json"

    if not semantic_path.exists():
        build_semantic_model(job_id)
    if not api_catalog_path.exists():
        build_api_catalog(job_id)

    semantic = json.loads(semantic_path.read_text(encoding="utf-8"))
    api_catalog = json.loads(api_catalog_path.read_text(encoding="utf-8"))

    return {
        "semanticModel": semantic,
        "apiCatalog": api_catalog,
    }

