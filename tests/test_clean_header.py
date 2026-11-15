"""Regression coverage for simplified AETHERIS page chrome."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def test_unwanted_header_strip_is_removed():
    html = (ROOT / "static/index.html").read_text(encoding="utf-8")
    for label in ("GLOBAL RESEARCH INTERFACE", "SYSTEM READY", "WORKSPACE"):
        assert label not in html.split('<main class="main">', 1)[1].split('<div id="toast"', 1)[0]
    assert '<header class="topbar">' not in html

def test_navigation_still_works_without_breadcrumb():
    js = (ROOT / "static/app.js").read_text(encoding="utf-8")
    assert 'function go(view)' in js
    assert "location.hash = view" in js
    assert 'view-crumb' not in js
