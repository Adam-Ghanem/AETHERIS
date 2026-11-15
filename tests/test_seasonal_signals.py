"""Deterministic tests: no synthetic data is ever presented as live NASA data."""
import calendar
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from aetheris.nasa import Observation, DataError
from aetheris.science import investigate
from aetheris.seasonal_signals import benjamini_hochberg, analyze_seasonal_signals, run_seasonal_signals
from aetheris.server import app

YEARS = range(2000, 2025)


def observations(variable='T2M', years=YEARS):
    return [Observation(y, m, (
        11 + m * .8 + ((y - 2000) * .08 if m in (6, 7, 8) else 0.0) + ((y % 4) - 1.5) * .014
        if variable == 'T2M' else (1.0 + m * .08 + (y - 2000) * .002)
    )) for y in years for m in range(1, 13)]


def meta(variable='T2M'):
    return {'source': 'NASA POWER', 'source_product': 'SYNTHETIC FIXTURE ONLY',
            'source_url': 'https://power.larc.nasa.gov/', 'source_request': 'fixture-only',
            'monthly_unit': '°C' if variable == 'T2M' else 'mm/day',
            'retrieved_at': 'test', 'missing_or_unavailable_months': 0}


def analyze(variable='T2M', obs=None):
    obs = observations(variable) if obs is None else obs
    result = investigate(obs, meta(variable), variable, 32.337, -6.349, 2000, 2024)
    return analyze_seasonal_signals(result, obs)


def test_bh_known_adjustment_and_missing():
    assert benjamini_hochberg([0.01, 0.04, 0.03, None]) == [0.03, 0.04, 0.04, None]
    assert benjamini_hochberg([None, None]) == [None, None]
    with pytest.raises(DataError):
        benjamini_hochberg([1.1])


def test_monthly_signals_and_fdr():
    d = analyze()
    assert d['period']['complete_years'] == 25
    assert len(d['months']) == 12
    assert len(d['matrix']) == 25
    june = d['months'][5]
    january = d['months'][0]
    assert june['slope_per_decade'] == pytest.approx(.8, abs=.015)
    assert january['slope_per_decade'] == pytest.approx(0, abs=.015)
    assert june['theil_sen_per_decade'] == pytest.approx(.8, abs=.015)
    assert june['q_value_bh'] is not None
    assert d['summary']['strongest_absolute_slope_month'] in (6, 7, 8)
    assert d['baseline']['end_year'] == 2009
    assert 'climate normal' in d['baseline']['type']
    assert len(d['evidence']['seasonal_analysis_sha256']) == 64


def test_preclipitation_monthly_units_and_leap_year():
    obs = [Observation(y, m, 2.0) for y in YEARS for m in range(1,13)]
    d = analyze('PRECTOTCORR', obs)
    assert d['months'][1]['unit'] == 'mm/month'
    assert d['matrix'][0]['months'][1]['value'] == pytest.approx(58.0)  # leap 2000
    assert d['matrix'][1]['months'][1]['value'] == pytest.approx(56.0)
    assert d['months'][0]['first_value'] == pytest.approx(62.0)
    assert d['summary']['fdr_flagged_months'] == 0


def test_missing_month_excludes_whole_year_and_does_not_invent_matrix_values():
    obs = [x for x in observations() if not (x.year == 2007 and x.month == 4)]
    d = analyze(obs=obs)
    assert d['period']['complete_years'] == 24
    assert d['period']['excluded_years'] == [2007]
    row = next(x for x in d['matrix'] if x['year'] == 2007)
    assert row['complete'] is False
    assert all(x['value'] is None and x['departure'] is None for x in row['months'])


def test_constant_series_no_invented_significance():
    obs = [Observation(y, m, 14.0) for y in YEARS for m in range(1,13)]
    d = analyze(obs=obs)
    assert all(m['status'] == 'constant_series' for m in d['months'])
    assert all(m['q_value_bh'] is None for m in d['months'])
    assert d['summary']['fdr_flagged_months'] == 0


def test_digest_reproducible():
    assert analyze()['evidence']['seasonal_analysis_sha256'] == analyze()['evidence']['seasonal_analysis_sha256']


@pytest.mark.asyncio
async def test_service_fetches_real_source_adapter_once():
    async def fake_fetch(lat,lon,start,end,variable):
        return observations(variable),meta(variable)
    with patch('aetheris.seasonal_signals.fetch_power', side_effect=fake_fetch) as mocked:
        result = await run_seasonal_signals(32.337,-6.349,2000,2024,'T2M')
    assert mocked.await_count == 1
    assert result['months'][5]['month'] == 6


def test_api_route_contract_and_source_metadata():
    async def fake_fetch(lat,lon,start,end,variable):
        return observations(variable),meta(variable)
    with patch('aetheris.seasonal_signals.fetch_power', side_effect=fake_fetch):
        r = TestClient(app).get('/api/v1/seasonal-signals?lat=32.337&lon=-6.349&start=2000&end=2024&variable=T2M')
    assert r.status_code == 200, r.text
    d=r.json()
    assert d['evidence']['source_url'] == 'fixture-only'
    assert len(d['months']) == 12
    assert len(d['matrix']) == 25


def test_api_validation():
    client=TestClient(app)
    assert client.get('/api/v1/seasonal-signals?lat=100&lon=0').status_code == 422
    assert client.get('/api/v1/seasonal-signals?lat=32&lon=-6&start=2020&end=2023').status_code == 422
    assert client.get('/api/v1/seasonal-signals?lat=32&lon=-6&variable=invalid').status_code == 422


def test_api_upstream_failure_not_masked():
    async def failing(*args):
        raise DataError('NASA source unavailable', 'NASA_UNAVAILABLE', 502)
    with patch('aetheris.seasonal_signals.fetch_power', side_effect=failing):
        r = TestClient(app).get('/api/v1/seasonal-signals?lat=32&lon=-6')
    assert r.status_code == 502
    assert r.json()['error']['code'] == 'NASA_UNAVAILABLE'
