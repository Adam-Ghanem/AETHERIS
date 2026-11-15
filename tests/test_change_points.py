"""Change-point science and API tests using explicitly synthetic annual patterns."""
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from aetheris.change_points import analyze_change_points
from aetheris.nasa import DataError, Observation
from aetheris.science import investigate
from aetheris.server import app

CLIENT = TestClient(app)


def synthetic(mode='break', *, start=1990, end=2025, missing=None, variable='T2M'):
    missing = missing or set()
    rows = []
    for year in range(start, end+1):
        if year in missing:
            continue
        for month in range(1, 13):
            if mode == 'break':
                value = 11 + .08*(year - start) + .42*max(0, year-2008) + .12*((year % 4)-1.5)
            elif mode == 'linear':
                value = 11 + .2*(year-start)
            elif mode == 'constant':
                value = 10.
            elif mode == 'downbreak':
                value = 23 - .09*(year-start) - .5*max(0, year-2008) + .08*((year % 4)-1.5)
            else:
                value = 12 + .2*(year-start)
            if variable == 'PRECTOTCORR':
                value = value / 30
            rows.append(Observation(year, month, value))
    meta = {'source':'SYNTHETIC NASA POWER TEST FIXTURE', 'source_url':'https://power.larc.nasa.gov/test',
            'source_product':'SYNTHETIC — NOT LIVE NASA', 'retrieved_at':'test',
            'monthly_unit':'°C' if variable=='T2M' else 'mm/day'}
    return rows, meta


def build(mode='break', **kwargs):
    obs, meta = synthetic(mode, **kwargs)
    investigation = investigate(obs,meta,kwargs.get('variable', 'T2M'),32.337,-6.349,
                                kwargs.get('start', 1990),kwargs.get('end',2025))
    return analyze_change_points(investigation)


def test_known_synthetic_slope_change_localized_near_2008():
    data = build('break')
    assert abs(data['best_candidate']['year']-2008) <= 2
    assert data['best_candidate']['slope_after_per_decade'] > data['best_candidate']['slope_before_per_decade'] + 3
    assert data['assessment']['label'] == 'piecewise_preferred_exploratory'
    assert data['assessment']['formal_change_point_significance_assessed'] is False


def test_known_synthetic_linear_series_does_not_invent_break():
    data=build('linear')
    assert data['assessment']['label'] == 'linear_adequate'
    assert data['best_candidate']['delta_bic_vs_linear'] < 2


def test_constant_series_does_not_claim_shift():
    data=build('constant')
    assert data['assessment']['label'] == 'no_detectable_variation'


def test_negative_synthetic_slope_change():
    data=build('downbreak')
    assert abs(data['best_candidate']['year']-2008) <= 2
    assert data['best_candidate']['slope_after_per_decade'] < data['best_candidate']['slope_before_per_decade']


def test_missing_years_preserved_not_interpolated():
    d=build('break',missing={1998,2013})
    assert d['quality']['gaps_in_complete_years'] == [1998,2013]
    assert len(d['annual_observations']) == 34
    assert len(d['best_candidate']['fitted']) == 34


def test_precipitation_unit_from_parent_investigation():
    d=build('break',variable='PRECTOTCORR')
    assert d['variable']['annual_unit'] == 'mm'
    assert d['best_candidate']['year'] >= 1995


def test_stability_and_hash_are_deterministic():
    a=build('break'); b=build('break')
    assert a['evidence']['change_point_analysis_sha256']==b['evidence']['change_point_analysis_sha256']
    assert a['robustness']['reruns']==len(a['annual_observations'])
    assert 0<=a['robustness']['within_two_years_fraction']<=1


def test_invalid_segment_and_short_series():
    d=build('break')
    obs,meta=synthetic('break',start=2015,end=2025)
    base=investigate(obs,meta,'T2M',32,-6,2015,2025)
    with pytest.raises(DataError,match='at least 14'):
        analyze_change_points(base)
    obs,meta=synthetic()
    base=investigate(obs,meta,'T2M',32,-6,1990,2025)
    with pytest.raises(DataError,match='between 5 and 10'):
        analyze_change_points(base,min_segment_years=11)


def test_api_returns_evidence_using_mocked_nasa():
    obs,meta=synthetic('break')
    with patch('aetheris.server.fetch_power',new_callable=AsyncMock,return_value=(obs,meta)):
        response=CLIENT.get('/api/v1/change-points?lat=32.337&lon=-6.349&start=1990&end=2025&variable=T2M')
    assert response.status_code==200, response.text
    payload=response.json()
    assert payload['best_candidate']['year'] in range(2006,2011)
    assert payload['evidence']['source_sha256_monthly']
    assert len(payload['candidate_scores'])>3


def test_api_rejects_bad_parameter_without_upstream_call():
    bad=CLIENT.get('/api/v1/change-points?lat=32&lon=-6&start=1990&end=2025&min_segment_years=15')
    assert bad.status_code==422
    bad=CLIENT.get('/api/v1/change-points?lat=400&lon=-6&start=1990&end=2025')
    assert bad.status_code==422
