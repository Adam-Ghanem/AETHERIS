"""Mission Theater contracts — no invented briefing values and static app wiring."""
from pathlib import Path
import re
from fastapi.testclient import TestClient
from aetheris.server import app
from tests.test_briefing import result

ROOT=Path(__file__).resolve().parents[1]
client=TestClient(app)

def test_mission_theater_is_bundled_and_accessible():
    html=client.get('/').text
    assert client.get('/static/mission-theater.js').status_code==200
    assert client.get('/static/mission-theater.css').status_code==200
    assert 'id="mission-overlay"' in html
    assert 'role="dialog"' in html
    assert 'aria-modal="true"' in html
    assert 'id="mission-download"' in html
    assert 'id="mission-present"' in html
    assert 'id="mission-launch-home"' in html
    assert 'id="mission-launch-spotlight"' in html


def test_source_briefing_has_reproducible_evidence():
    d=result()
    assert d['findings'][0]['trend_per_decade'] is not None
    assert len(d['evidence']['briefing_sha256'])==64
    assert d['observations'][0]['year'] < d['observations'][-1]['year']
    # No automatic inference of causality or manufactured forecasting claim.
    assert any('caus' in x.lower() for x in d['limitations'])


def test_mission_theater_data_gating_and_offline_mode():
    js=(ROOT/'static'/'mission-theater.js').read_text()
    assert 'function valid(d)' in js
    assert 'observations.length >= 8' in js
    assert 'aetheris:briefing-ready' in js
    assert 'function offlineHtml()' in js
    assert 'SYNTHETIC' not in js or 'synthetic' in js.lower()
    assert 'window.AetherisMissionTheater' in js
    assert 'NASA POWER' in js


def test_no_new_untrusted_dynamic_source_urls():
    js=(ROOT/'static'/'mission-theater.js').read_text()
    assert 'fetch(' not in js
    assert 'eval(' not in js
    assert 'innerHTML=state.data' not in js
    assert '.replace(/[&<>"\']/g' in js
