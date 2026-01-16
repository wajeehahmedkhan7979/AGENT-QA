from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
from urllib.error import URLError
from urllib.parse import urlparse, urlunparse
from urllib.request import urlopen


@dataclass
class RobotsPreflight:
    allowed: bool
    robots_txt: Optional[str]


def _build_robots_url(target_url: str) -> str:
    parsed = urlparse(target_url)
    robots_path = "/robots.txt"
    return urlunparse((parsed.scheme, parsed.netloc, robots_path, "", "", ""))


def check_robots(target_url: str) -> RobotsPreflight:
    """
    Minimal robots.txt check for demo purposes.
    Strategy:
      - If robots.txt cannot be fetched -> treat as allowed.
      - If fetched, search for a \"User-agent: *\" section and a \"Disallow: /\" rule.
    """
    robots_url = _build_robots_url(target_url)
    try:
        with urlopen(robots_url, timeout=5) as resp:  # type: ignore[arg-type]
            content_bytes = resp.read()
    except URLError:
        return RobotsPreflight(allowed=True, robots_txt=None)

    try:
        robots_text = content_bytes.decode("utf-8", errors="ignore")
    except Exception:  # pragma: no cover - extremely defensive
        return RobotsPreflight(allowed=True, robots_txt=None)

    lines = [line.strip() for line in robots_text.splitlines()]
    in_global_user_agent = False
    disallow_root = False

    for line in lines:
        if not line or line.startswith("#"):
            continue
        lower = line.lower()
        if lower.startswith("user-agent:"):
            agent = lower.split(":", 1)[1].strip()
            in_global_user_agent = agent == "*" or agent == '"*"'
        elif in_global_user_agent and lower.startswith("disallow:"):
            path = lower.split(":", 1)[1].strip()
            if path == "/" or path == "/*":
                disallow_root = True

    allowed = not disallow_root
    return RobotsPreflight(allowed=allowed, robots_txt=robots_text)

