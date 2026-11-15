"""Regression checks for the Solar Research UI and versioned backend."""
from pathlib import Path
from fastapi.testclient import TestClient
from aetheris.server import app

ROOT = Path(__file__).resolve().parents[1]


def test_solar_theme_is_integrated():
    html = (ROOT / 'static/index.html').read_text()
    assert 'href="/static/theme-solar.css"' in html
    assert html.index('href="/static/briefing.css"') < html.index('href="/static/theme-solar.css"')
    theme = (ROOT / 'static/theme-solar.css').read_text()
    assert '--solar:#ffce32' in theme and '--bg:#fafaf6' in theme
    assert 'prefers-reduced-motion' in theme


def test_quick_research_has_real_submit_flow():
    html = (ROOT / 'static/index.html').read_text()
    js = (ROOT / 'static/app.js').read_text()
    assert 'id="solar-quick-start"' in html
    assert "$('brief-form').requestSubmit()" in js
    assert "go('briefing')" in js


def test_research_url_is_resumable_with_parameter_validation():
    html = (ROOT / 'static/index.html').read_text()
    js = (ROOT / 'static/briefing.js').read_text()
    assert 'id="brief-share"' in html
    assert "query.get('research')" in js
    assert 'lastQuery=q' in js
    assert 'form();' in js
    assert 'restoreShared' in js
    assert 'clipboard.writeText' in js


def test_server_version_and_original_endpoints():
    client = TestClient(app)
    result = client.get('/api/v1/health')
    assert result.status_code == 200 and result.json()['version']=='14.0.0'
    assert client.get('/').status_code == 200
    assert client.get('/static/theme-solar.css').status_code == 200
    for uri in ('/api/v1/catalog','/api/v1/intelligence/status'):
        assert client.get(uri).status_code == 200
