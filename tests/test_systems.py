"""Earth Systems Lab: genuine science calculations with clearly synthetic fixtures."""
from unittest.mock import AsyncMock, patch
import math

from fastapi.testclient import TestClient
import pytest

from aetheris.nasa import Observation, DataError
from aetheris.science import investigate
from aetheris.systems import analyze_systems, run_systems
from aetheris.server import app

CLIENT = TestClient(app)
YEARS = range(2001, 2026)


def series(variable, years=YEARS, *, temp_slope=.07, rain_slope=-.25):
    return [Observation(year, month,
        (18 + temp_slope * (year - 2001) + month * .03) if variable == 'T2M'
        else (2.5 + rain_slope * (year - 2001)/12 + month * .002))
        for year in years for month in range(1, 13)]


def meta(variable):
    return {'source': 'NASA POWER', 'source_product': 'SYNTHETIC FIXTURE — NOT NASA',
            'source_url': 'https://power.larc.nasa.gov/', 'source_request': 'fixture-only',
            'monthly_unit': '°C' if variable == 'T2M' else 'mm/day',
            'retrieved_at': 'test-only', 'missing_or_unavailable_months': 0}


def investigation(variable, years=YEARS, lat=32.337):
    return investigate(series(variable, years), meta(variable), variable, lat, -6.349, 2001, 2025)


def test_combines_independent_source_results():
    result = analyze_systems(investigation('T2M'), investigation('PRECTOTCORR'))
    assert result['period']['shared_complete_years'] == 25
    assert len(result['years']) == 25
    assert result['years'][0]['year'] == 2001
    assert result['years'][-1]['year'] == 2025
    assert result['metrics']['temperature']['trend_per_decade'] == pytest.approx(.7, abs=.0001)
    assert result['metrics']['precipitation']['trend_per_decade'] < 0
    assert len(result['evidence']['paired_sha256']) == 64
    assert result['evidence']['temperature']['sha256_monthly'] != result['evidence']['precipitation']['sha256_monthly']
    assert result['association']['n'] == 25
    assert 'not a validated drought' in ' '.join(result['limitations'])


def test_paired_years_never_imputed():
    a = investigation('T2M')
    b = investigation('PRECTOTCORR', [y for y in YEARS if y not in (2006, 2018)])
    result = analyze_systems(a, b)
    assert result['period']['shared_complete_years'] == 23
    assert result['period']['excluded_unpaired_years'] == [2006, 2018]
    assert all(x['year'] not in (2006, 2018) for x in result['years'])


def test_different_coordinates_rejected():
    with pytest.raises(DataError) as exc:
        analyze_systems(investigation('T2M', lat=32.337), investigation('PRECTOTCORR', lat=33.0))
    assert exc.value.code == 'LOCATION_MISMATCH'


def test_reversed_variables_rejected():
    with pytest.raises(DataError) as exc:
        analyze_systems(investigation('PRECTOTCORR'), investigation('T2M'))
    assert exc.value.code == 'INVALID_VARIABLE_PAIR'


def test_too_few_common_years():
    a = investigation('T2M', range(2001, 2010))
    b = investigation('PRECTOTCORR', range(2002, 2010))
    # A and B individually >=8, but their intersection is exactly 8.
    assert analyze_systems(a, b)['period']['shared_complete_years'] == 8
    b = investigation('PRECTOTCORR', range(2003, 2011))
    with pytest.raises(DataError) as exc:
        analyze_systems(a, b)
    assert exc.value.code == 'INSUFFICIENT_PAIRED_DATA'


def test_zero_sd_baseline_is_honestly_reported():
    # Constant annual temperature (same month pattern repeated every year).
    t = investigate([Observation(y, m, 18.) for y in YEARS for m in range(1,13)], meta('T2M'), 'T2M', 32.337, -6.349, 2001, 2025)
    p = investigation('PRECTOTCORR')
    result = analyze_systems(t, p)
    assert result['baseline']['temperature_sample_sd_c'] == 0
    assert all(r['temperature_z'] is None for r in result['years'])
    assert result['joint_deviations']['count'] == 0
    assert result['association']['raw_pearson_r'] is None


def test_pair_checksum_is_stable_for_same_sources():
    a = analyze_systems(investigation('T2M'), investigation('PRECTOTCORR'))
    b = analyze_systems(investigation('T2M'), investigation('PRECTOTCORR'))
    assert a['evidence']['paired_sha256'] == b['evidence']['paired_sha256']


def test_era_comparison_is_descriptive_only():
    d = analyze_systems(investigation('T2M'), investigation('PRECTOTCORR'))
    assert d['era_comparison']['excluded_middle_year'] == 2013
    assert d['era_comparison']['temperature_change_c'] > 0
    assert 'descriptive' in d['era_comparison']['method'].lower()
    assert d['association']['method'].endswith('no significance test.')


@pytest.mark.asyncio
async def test_two_independent_fetches_and_validated_result():
    async def fake_fetch(lat, lon, start, end, variable):
        return series(variable), meta(variable)
    with patch('aetheris.systems.fetch_power', side_effect=fake_fetch) as mock:
        result = await run_systems(32.337, -6.349, 2001, 2025)
    assert mock.await_count == 2
    assert set(call.args[4] for call in mock.await_args_list) == {'T2M', 'PRECTOTCORR'}
    assert result['period']['shared_complete_years'] == 25


def test_endpoint_validations():
    assert CLIENT.get('/api/v1/systems?lat=92&lon=0').status_code == 422
    assert CLIENT.get('/api/v1/systems?lat=32&lon=-6&start=2021&end=2025').status_code == 422
    assert CLIENT.get('/api/v1/systems?lat=32&lon=-6&start=2001&end=2120').status_code == 422


def test_endpoint_dual_products_and_provenance():
    async def fake_fetch(lat, lon, start, end, variable):
        return series(variable), meta(variable)
    with patch('aetheris.systems.fetch_power', side_effect=fake_fetch):
        r = CLIENT.get('/api/v1/systems?lat=32.337&lon=-6.349&start=2001&end=2025')
    assert r.status_code == 200, r.text
    data = r.json()
    assert data['period']['shared_complete_years'] == 25
    assert data['evidence']['temperature']['source_request'] == 'fixture-only'
    assert data['evidence']['precipitation']['source_request'] == 'fixture-only'
    assert all('joint_hot_dry_deviation' in year for year in data['years'])


def test_upstream_failure_not_fabricated():
    async def fake_fetch(lat, lon, start, end, variable):
        if variable == 'PRECTOTCORR':
            raise DataError('Rainfall service offline', 'NASA_UNAVAILABLE')
        return series(variable), meta(variable)
    with patch('aetheris.systems.fetch_power', side_effect=fake_fetch):
        r = CLIENT.get('/api/v1/systems?lat=32.337&lon=-6.349&start=2001&end=2025')
    assert r.status_code == 502
    assert r.json()['error']['code'] == 'NASA_UNAVAILABLE'


def test_v5_ui_integrity():
    from pathlib import Path
    root=Path(__file__).resolve().parents[1]
    html=(root/'static/index.html').read_text()
    js=(root/'static/app.js').read_text()
    assert 'id="view-systems"' in html
    assert 'id="systems-form"' in html
    assert "'/api/v1/systems" in js or '`/api/v1/systems' in js
    assert 'renderSystemsScatter' in js
