"""Regression guard: AETHERIS UI never shows decorative northeast/southeast arrows."""
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def test_no_decorative_diagonal_arrows_in_frontend():
    files=[p for p in (ROOT/'static').rglob('*') if p.suffix in {'.html','.js','.css'}]
    assert files
    leftover=[str(p.relative_to(ROOT)) for p in files if '↗' in p.read_text(encoding='utf-8') or '↘' in p.read_text(encoding='utf-8')]
    assert not leftover, 'Decorative arrows found in: '+', '.join(leftover)

def test_primary_buttons_and_navigation_are_preserved():
    html=(ROOT/'static/index.html').read_text(encoding='utf-8')
    assert 'id="analyze-btn"' in html
    assert 'id="campaign-action"' in html
    assert 'id="brief-submit"' in html
    assert 'id="primary-nav"' in html
