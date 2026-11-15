"""Ensure unwanted Change-point Lab visuals are removed without harming research UI."""
from html.parser import HTMLParser
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

def test_badge_and_decorative_plot_removed():
    html = (ROOT / "static/index.html").read_text(encoding="utf-8")
    start = html.index('<section id="view-breakpoints"')
    end = html.index('<form class="panel breakpoint-form"', start)
    hero = html[start:end]
    assert "REAL NASA · REPRODUCIBLE" not in hero
    assert 'class="breakpoint-decor"' not in hero
    assert 'YEAR / Δ' not in hero

def test_scientific_content_and_navigation_preserved():
    html = (ROOT / "static/index.html").read_text(encoding="utf-8")
    for token in ('id="view-breakpoints"', 'id="breakpoints-title"',
                  'id="breakpoint-form"', 'id="breakpoint-run"',
                  'id="breakpoint-results"', 'id="breakpoint-main-chart"'):
        assert token in html
    assert 'Find changes <em>within</em> the change.' in html
    css = (ROOT / "static/style.css").read_text(encoding="utf-8")
    assert '.breakpoint-feature{display:grid;grid-template-columns:minmax(0,1fr)' in css
    assert '.breakpoint-decor' not in css
