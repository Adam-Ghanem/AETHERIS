"""Independent, deterministic QA for the Climate Forensics Lab."""
import calendar
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from aetheris.forensics import analyze_forensics
from aetheris.nasa import DataError, Observation
from aetheris.science import investigate
from aetheris.server import app

client = TestClient(app)


def fixture(years=range(2000, 2026), variable='T2M', *, missing=None):
    missing = missing or set()
    values = []
    for year in years:
        for month in range(1, 13):
            if (year, month) in missing:
                continue
            v = 8 + .2 * (year-2000) + month * .1 if variable == 'T2M' else 1 + .02 * (year-2000)
            values.append(Observation(year, month, v))
    meta = {'source': 'NASA POWER', 'source_url':'https://power.larc.nasa.gov/',
            'source_product': 'SYNTHETIC FIXTURE — NOT LIVE NASA',
            'monthly_unit': '°C' if variable=='T2M' else 'mm/day', 'valid_months':len(values),
            'missing_or_unavailable_months': 0, 'retrieved_at':'synthetic', 'source_request':'synthetic'}
    return values, meta


def forensic(obs, meta, variable='T2M', window=7):
    result=investigate(obs, meta, variable, 32.337,-6.349, min(x.year for x in obs),max(x.year for x in obs))
    return analyze_forensics(result, obs, window=window)


def test_linear_warming_stable_jackknife_and_shift():
    obs, meta=fixture()
    d=forensic(obs,meta)
    assert d['period_contrast']['difference']==pytest.approx(2.6,abs=.002)
    assert d['jackknife']['direction_stable_under_single_year_removal'] is True
    assert d['jackknife']['original_slope_per_decade']==pytest.approx(2.0, abs=.001)
    assert d['jackknife']['minimum_slope_per_decade']==pytest.approx(2.0, abs=.001)
    assert len(d['rolling']['points'])==20
    assert all(p['difference']==pytest.approx(2.6,abs=.002) for p in d['seasonal_shift']['months'])
    assert d['evidence']['sha256_monthly']


def test_odd_length_middle_year_omission():
    obs,meta=fixture(range(2001,2026))
    d=forensic(obs,meta)
    assert d['period_contrast']['omitted_middle_year']==2013
    assert d['period_contrast']['first_period']['n_years']==12
    assert d['period_contrast']['last_period']['n_years']==12


def test_precipitation_units_and_monthly_totals():
    obs,meta=fixture(range(2000,2020),'PRECTOTCORR')
    d=forensic(obs,meta,'PRECTOTCORR')
    assert d['period_contrast']['unit']=='mm'
    assert d['seasonal_shift']['unit']=='mm/month'
    assert d['seasonal_shift']['months'][0]['difference']==pytest.approx(.2*31,abs=.001)
    assert d['seasonal_shift']['months'][1]['difference']>0


def test_missing_calendar_year_breaks_rolling_windows():
    obs,meta=fixture(range(2001,2017),missing={(2009,6)})
    d=forensic(obs,meta,window=5)
    years={p['year'] for p in d['rolling']['points']}
    assert 2009 not in years
    assert not any(p['start_year']<=2009<=p['year'] for p in d['rolling']['points'])


def test_window_limits_and_undersized_series():
    obs,meta=fixture(range(2001,2010))
    inv=investigate(obs,meta,'T2M',32,-6,2001,2009)
    for window in (2,16,10):
        with pytest.raises(DataError) as exc:
            analyze_forensics(inv, obs, window=window)
        assert exc.value.code=='INVALID_WINDOW'


def test_api_v3_forensics_and_validation():
    obs,meta=fixture(range(2001,2026))
    with patch('aetheris.server.fetch_power',new=AsyncMock(return_value=(obs,meta))):
        r=client.get('/api/v1/forensics?lat=32.337&lon=-6.349&start=2001&end=2025&variable=T2M&window=7')
    assert r.status_code==200, r.text
    d=r.json()
    assert d['rolling']['window_years']==7
    assert len(d['seasonal_shift']['months'])==12
    assert d['period_contrast']['last_period']['end']==2025
    assert d['evidence']['sha256_monthly']
    assert client.get('/api/v1/forensics?lat=100&lon=-6').status_code==422
    assert client.get('/api/v1/forensics?lat=32&lon=-6&window=18').status_code==422
    assert client.get('/api/v1/forensics?lat=32&lon=-6&variable=FAKE').status_code==422


def test_forensics_preserves_source_and_refuses_trend_causation():
    obs, meta=fixture(range(2001,2019))
    d=forensic(obs,meta)
    assert 'not an independent significance test' in d['period_contrast']['interpretation']
    assert all('cause' not in str(p).lower() for p in d['jackknife']['points'])
    assert any('No result' in x for x in d['limitations'])
