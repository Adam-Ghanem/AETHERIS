"""Release structure contract for the key v4 UI and bundled geography."""
import json
from pathlib import Path
from fastapi.testclient import TestClient
from aetheris.server import app
ROOT=Path(__file__).resolve().parent.parent


def test_v4_health_and_spatial_route_visible():
    client=TestClient(app)
    assert client.get('/api/v1/health').json()['version']=='14.0.0'
    assert '/api/v1/spatial' in app.openapi()['paths']


def test_spatial_controls_ship_together():
    html=(ROOT/'static/index.html').read_text(encoding='utf-8')
    js=(ROOT/'static/app.js').read_text(encoding='utf-8')
    for anchor in ('id="view-spatial"','id="spatial-form"','id="spatial-matrix"','id="spatial-run"','id="spatial-point-detail"','id="spatial-location"','id="spatial-lat"','id="spatial-lon"','id="mobile-menu-toggle"'):
        assert anchor in html
    for handler in ('runSpatial','renderSpatial','selectedSpatialPoint','exportSpatialJson','exportSpatialCsv'):
        assert handler in js
    assert 'data-view="spatial"' in html


def test_offline_globe_geography_is_bundled():
    dots=json.loads((ROOT/'static/assets/land-dots.json').read_text())
    assert 1500 < len(dots) < 10000
    assert all(-180 <= lon <=180 and -90<=lat<=90 for lon,lat in dots)
    assert 'AetherisLegacyGlobe' in (ROOT/'static/globe.js').read_text()
    assert 'AetherisGlobe' in (ROOT/'static/ghostcat-earth.js').read_text()
