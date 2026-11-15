from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from aetheris.server import app
from aetheris.nasa import Observation

client=TestClient(app)


def test_health():
    assert client.get('/api/v1/health').json()['status']=='ok'


def test_catalog():
    data=client.get('/api/v1/catalog').json()
    assert any(x['name']=='Beni Mellal' for x in data['locations'])
    assert 'T2M' in data['variables']


def test_invalid_location():
    r=client.get('/api/v1/investigate?lat=100&lon=1&start=2001&end=2025')
    assert r.status_code==422


def test_fake_data_not_shown_when_nasa_unavailable():
    from aetheris.nasa import DataError
    with patch('aetheris.server.fetch_power',new=AsyncMock(side_effect=DataError('NASA unavailable','NASA_UNAVAILABLE'))):
        r=client.get('/api/v1/investigate?lat=32.337&lon=-6.349&start=2001&end=2025')
        assert r.status_code==502 and r.json()['error']['code']=='NASA_UNAVAILABLE'


def test_end_to_end_fixture_backed_api_contract():
    obs=[Observation(y,m,19+(y-2001)*.07) for y in range(2001,2026) for m in range(1,13)]
    meta={'source':'NASA POWER','source_url':'https://power.larc.nasa.gov','source_product':'fixture','missing_or_unavailable_months':0,'retrieved_at':'test','monthly_unit':'°C'}
    with patch('aetheris.server.fetch_power',new=AsyncMock(return_value=(obs,meta))):
        r=client.get('/api/v1/investigate?lat=32.337&lon=-6.349&start=2001&end=2025')
        assert r.status_code==200
        d=r.json()
        assert len(d['annual'])==25
        assert len(d['monthly'])==300
        assert d['trend']['slope_per_decade']==0.7
        assert d['evidence']['sha256_monthly']
