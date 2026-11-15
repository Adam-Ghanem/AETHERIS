"""Evidence Command Center — source-backed deterministic narrative, synthetic fixtures only."""
from unittest.mock import AsyncMock, patch
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from aetheris.briefing import build_briefing
from aetheris.systems import analyze_systems
from aetheris.server import app
from tests.test_systems import investigation

client = TestClient(app)


def result():
    return build_briefing(analyze_systems(investigation('T2M'), investigation('PRECTOTCORR')))


def test_briefing_is_deterministic_and_reproducible():
    a, b = result(), result()
    assert a['evidence']['briefing_sha256'] == b['evidence']['briefing_sha256']
    assert len(a['observations']) == 25
    assert len(a['evidence']['briefing_sha256']) == 64
    assert all(len(x['sha256_monthly']) == 64 for x in [a['evidence']['temperature'], a['evidence']['precipitation']])


def test_briefing_metrics_derived_from_real_numerical_inputs():
    d=result()
    t,p=d['findings']
    assert t['id']=='temperature' and p['id']=='precipitation'
    assert t['trend_per_decade']==pytest.approx(.7, abs=.0001)
    assert p['trend_per_decade'] < 0
    assert '°C per decade' in t['description']
    assert 'mm per decade' in p['description']
    assert len(d['observations'])==d['period']['shared_complete_years']


def test_briefing_never_claims_forecast_or_causality():
    d=result()
    all_text=' '.join(x['description'] for x in d['findings'])+' '.join(d['limitations'])
    assert 'not by a trained AI model' in all_text
    assert 'causal' in all_text.lower()
    assert d['contrast']['early']==[2001, 2012]
    assert d['contrast']['late']==[2014, 2025]
    assert d['contrast']['excluded_middle_year']==2013


def test_source_flags_and_data_rows_preserved():
    d=result()
    assert d['joint_flags']['count']==len(d['joint_flags']['years'])
    assert d['observations'][0]['year']==2001
    assert d['observations'][-1]['year']==2025
    assert d['product_type']=='gridded / model-derived point data'


def test_baseline_variance_zero_is_not_faked():
    from aetheris.science import investigate
    from aetheris.nasa import Observation
    from tests.test_systems import meta
    fixed=investigate([Observation(y,m,18.0) for y in range(2001,2026) for m in range(1,13)],meta('T2M'),'T2M',32.337,-6.349,2001,2025)
    data=build_briefing(analyze_systems(fixed,investigation('PRECTOTCORR')))
    assert all(y['temperature_z'] is None for y in data['observations'])
    assert data['joint_flags']['count']==0


def test_api_query_validation():
    assert client.get('/api/v1/briefing?lat=95&lon=0').status_code==422
    assert client.get('/api/v1/briefing?lat=32&lon=-6&start=2021&end=2025').status_code==422


def test_api_returns_source_derived_analysis():
    async def mock_run(*args,**kwargs):
        return analyze_systems(investigation('T2M'), investigation('PRECTOTCORR'))
    with patch('aetheris.briefing.run_systems',side_effect=mock_run):
        res=client.get('/api/v1/briefing?lat=32.337&lon=-6.349&start=2001&end=2025')
    assert res.status_code==200,res.text
    assert res.json()['findings'][0]['trend_per_decade']==pytest.approx(.7, abs=.0001)
    assert res.json()['evidence']['temperature']['product'].startswith('SYNTHETIC')


def test_api_upstream_errors_never_fabricate_results():
    from aetheris.nasa import DataError
    with patch('aetheris.briefing.run_systems',new=AsyncMock(side_effect=DataError('NASA unavailable','NASA_UNAVAILABLE'))):
        res=client.get('/api/v1/briefing?lat=32.337&lon=-6.349&start=2001&end=2025')
    assert res.status_code==502
    assert res.json()['error']['code']=='NASA_UNAVAILABLE'


def test_ui_workflow_wired():
    root=Path(__file__).resolve().parents[1]
    html=(root/'static/index.html').read_text()
    main=(root/'static/app.js').read_text()
    js=(root/'static/briefing.js').read_text()
    assert 'id="view-briefing"' in html
    assert 'data-view="briefing"' in html
    assert 'id="brief-form"' in html
    assert 'id="brief-year-matrix"' in html
    assert "go('briefing')" in main
    assert "window.AetherisBriefing.init" in main
    assert '/api/v1/briefing?' in js
    assert 'brief-export-json' in js
    assert 'brief-export-csv' in js
    assert 'temperature.product' in js
