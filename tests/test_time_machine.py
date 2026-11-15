"""Time Machine scientific correctness, source integrity and endpoint validation."""
from unittest.mock import AsyncMock, patch
import math

import pytest
from fastapi.testclient import TestClient
from aetheris.nasa import Observation,DataError
from aetheris.time_machine import annual_snapshots,make_snapshots,time_machine_scan
from aetheris.server import app

client=TestClient(app)


def fixture_obs(delta=0, missing=None, rain=False):
    missing=missing or set()
    return [Observation(y,m, (2.0+.1*(y-2001)) if rain else (17+.2*(y-2001)+(m-6)*.03+delta))
            for y in range(2001,2026) for m in range(1,13) if (y,m) not in missing]


def meta():
    return {'source':'NASA POWER','source_product':'fixture data — not actual NASA',
            'source_url':'https://power.larc.nasa.gov/','retrieved_at':'test-fixture',
            'missing_or_unavailable_months':0}


def test_clean_year_anomalies_reference_and_units():
    years=[{'year':y,'value':15+.4*(y-2001)} for y in range(2001,2026)]
    result=annual_snapshots(years,2001,2025,'T2M')
    assert result['baseline']==pytest.approx(16.8)
    assert result['annual'][0]['anomaly']==pytest.approx(-1.8)
    assert result['annual'][-1]['anomaly']==pytest.approx(7.8)
    assert result['baseline_complete_years']==10


def test_missing_year_preserved_never_filled():
    annual=[{'year':y,'value':10.0} for y in range(2001,2026) if y not in (2004,2009,2019)]
    d=annual_snapshots(annual,2001,2025,'T2M')
    assert d['baseline_complete_years']==8
    assert d['missing_years']==[2004,2009,2019]
    assert d['annual'][18]['annual_value'] is None
    assert d['annual'][18]['anomaly'] is None


def test_invalid_baseline_and_period():
    with pytest.raises(DataError) as e:
        annual_snapshots([{'year':y,'value':1} for y in range(2001,2026) if y % 2],2001,2025,'T2M')
    assert e.value.code=='BASELINE_INSUFFICIENT'
    with pytest.raises(DataError):annual_snapshots([],2001,2009,'T2M')
    with pytest.raises(DataError):annual_snapshots([{'year':2001,'value':float('nan')}],2001,2025,'T2M')


def test_per_year_zero_is_valid_not_missing():
    points=[]
    for i in range(9):
        points.append({'id':f'p{i}','status':'ok','annual':[{'year':2001,'annual_value':20,'anomaly':0,'status':'ok'}]})
    frame=make_snapshots(points,2001,2001)[0]
    assert frame['available_points']==9
    assert frame['median_point_anomaly']==0
    assert frame['positive_points']==0


@pytest.mark.asyncio
async def test_all_nine_points_and_source_checksums():
    with patch('aetheris.time_machine.fetch_power',new=AsyncMock(return_value=(fixture_obs(),meta()))) as mock:
        d=await time_machine_scan(32.337,-6.349,2001,2025,'T2M',100)
    assert mock.await_count==9
    assert len(d['snapshots'])==25
    assert len(d['snapshots'][0]['points'])==9
    assert d['successful_points']==9
    assert d['snapshots'][-1]['center_anomaly'] == pytest.approx(3.9,abs=.03)
    assert d['points'][4]['evidence']['sha256_monthly']
    assert d['baseline']['start']==2001 and d['baseline']['end']==2010
    assert d['unit']=='°C'


@pytest.mark.asyncio
async def test_partial_failures_and_missing_months():
    calls=0
    async def fetch(*args):
        nonlocal calls
        calls+=1
        if calls==1:raise DataError('source unavailable')
        if calls==2:return fixture_obs(missing={(2020,5)}),meta()
        return fixture_obs(),meta()
    with patch('aetheris.time_machine.fetch_power',side_effect=fetch):
        d=await time_machine_scan(32.337,-6.349,2001,2025,'T2M',50)
    assert d['successful_points']==8
    assert d['points'][0]['status']=='error'
    frame=next(f for f in d['snapshots'] if f['year']==2020)
    assert frame['available_points']==7
    assert frame['points'][0]['anomaly'] is None
    assert frame['points'][1]['anomaly'] is None
    assert frame['points'][2]['anomaly'] is not None


@pytest.mark.asyncio
async def test_total_unavailability_raises_error():
    with patch('aetheris.time_machine.fetch_power',side_effect=DataError('unavailable')):
        with pytest.raises(DataError) as e:
            await time_machine_scan(32,-6,2001,2025,'T2M',100)
    assert e.value.code=='TIME_MACHINE_SOURCE_UNAVAILABLE'


@pytest.mark.asyncio
async def test_rainfall_units_and_day_weighting():
    with patch('aetheris.time_machine.fetch_power',new=AsyncMock(return_value=(fixture_obs(rain=True),meta()))):
        d=await time_machine_scan(32,-6,2001,2025,'PRECTOTCORR',100)
    assert d['unit']=='mm'
    assert d['points'][4]['annual'][0]['annual_value']==pytest.approx(730)
    assert d['points'][4]['annual'][3]['annual_value']==pytest.approx((2+.3)*366)


def test_endpoint_rejects_invalid_queries():
    for path in [
        '/api/v1/time-machine?lat=80&lon=0',
        '/api/v1/time-machine?lat=32&lon=-6&start=2018&end=2025',
        '/api/v1/time-machine?lat=32&lon=-6&start=2001&end=2025&variable=FAKE',
        '/api/v1/time-machine?lat=32&lon=-6&start=2001&end=2025&spacing_km=20',
    ]:
        assert client.get(path).status_code==422


def test_endpoint_fixture_returns_annual_snapshots():
    with patch('aetheris.time_machine.fetch_power',new=AsyncMock(return_value=(fixture_obs(),meta()))):
        res=client.get('/api/v1/time-machine?lat=32.337&lon=-6.349&start=2001&end=2025&variable=T2M')
    assert res.status_code==200
    body=res.json()
    assert body['version']=='time-machine-v1'
    assert len(body['snapshots'])==25
    assert body['points'][4]['baseline_complete_years']==10
