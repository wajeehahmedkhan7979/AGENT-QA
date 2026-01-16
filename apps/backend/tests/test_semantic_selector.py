from bs4 import BeautifulSoup

from semantic import _build_selector  # type: ignore[attr-defined]


def test_build_selector_prefers_id_over_class() -> None:
    html = '<button id="login" class="btn primary">Login</button>'
    soup = BeautifulSoup(html, "html.parser")
    el = soup.find("button")
    assert el is not None

    selector = _build_selector(el)
    assert selector == "#login"

