"""Spatial Observatory QA: geometry, API, source integrity, and partial failures."""
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
import pytest

from aetheris.spatial import sample_grid, spatial_scan
from aetheris.nasa import DataError, Observation
from aetheris.server import app

client = TestClient(app)


def observations():
    return [Observation(y,m,19+(y-2001)*0.07+(m-1)*.025) for y in range(2001, 2026) for m in range(1,13)]


def metadata():
    return {'source':'NASA POWER','source_url':'https://power.larc.nasa.gov',
            'source_product':'test fixture / NOT NASA', 'retrieved_at':'fixture-test',
            'monthly_unit':'°C','missing_or_unavailable_months':0}


def test_grid_geometry_and_order():
    grid=sample_grid(32.337, -6.349, 100)
    assert len(grid)==9
    assert [p['id'] for p in grid]==[f'p{i}' for i in range(9)]
    assert grid[4]['lat']==32.337 and grid[4]['lon']==-6.349
    assert grid[0]['lat']>grid[4]['lat']>grid[8]['lat']
    assert grid[0]['lon']<grid[1]['lon']<grid[2]['lon']
    assert len(set((p['lat'],p['lon']) for p in grid))==9


@pytest.mark.parametrize('lat,lon,spacing', [(80,1,100),(0,190,100),(0,0,20),(float('nan'),0,100)])
def test_invalid_grid(lat,lon,spacing):
    with pytest.raises(DataError):sample_grid(lat,lon,spacing)


def test_dateline_wrap():
    grid=sample_grid(0,179.6,150)
    assert all(-180 <=p['lon']<=180 for p in grid)


@pytest.mark.asyncio
async def test_spatial_reproducible_point_stats():
    with patch('aetheris.spatial.fetch_power',new=AsyncMock(return_value=(observations(),metadata()))) as mock:
        result=await spatial_scan(32.337,-6.349,2001,2025,'T2M',100)
    assert mock.await_count==9
    assert result['successful']==9
    assert result['summary']['center_slope']==pytest.approx(0.7,abs=0.00002)
    assert result['summary']['slope_spread']==0
    assert all(p['sha256_monthly'] for p in result['points'])
    assert result['points'][4]['is_center']


@pytest.mark.asyncio
async def test_partial_failure_never_imputed():
    calls=0
    async def fetch(*args):
        nonlocal calls
        calls+=1
        if calls==2:raise DataError('Unavailable')
        return observations(),metadata()
    with patch('aetheris.spatial.fetch_power',side_effect=fetch):
        result=await spatial_scan(32.337,-6.349,2001,2025,'T2M',50)
    assert result['failed']==1
    assert result['points'][1]['status']=='error'
    assert result['points'][1].get('slope_per_decade') is None


@pytest.mark.asyncio
async def test_total_failure_cannot_appear_as_valid_map():
    with patch('aetheris.spatial.fetch_power',side_effect=DataError('NASA unavailable')):
        with pytest.raises(DataError) as exc:
            await spatial_scan(32.337,-6.349,2001,2025,'T2M',100)
        assert exc.value.code=='SPATIAL_SOURCE_UNAVAILABLE'


def test_spatial_endpoint_validation():
    assert client.get('/api/v1/spatial?lat=80&lon=0&start=2001&end=2025').status_code==422
    assert client.get('/api/v1/spatial?lat=32&lon=-6&start=2001&end=2025&spacing_km=500').status_code==422
    assert client.get('/api/v1/spatial?lat=32&lon=-6&start=2001&end=2025&variable=FAKE').status_code==422


def test_spatial_endpoint_fixture():
    with patch('aetheris.spatial.fetch_power',new=AsyncMock(return_value=(observations(),metadata()))):
        response=client.get('/api/v1/spatial?lat=32.337&lon=-6.349&start=2001&end=2025&spacing_km=100')
    assert response.status_code==200
    body=response.json()
    assert body['successful']==9 and len(body['points'])==9
    assert body['summary']['slope_unit']=='°C/decade'
