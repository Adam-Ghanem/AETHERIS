"""Contract, inference and PDF quality smoke tests for advanced AETHERIS features."""
import io
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from aetheris.discovery import benjamini_hochberg
from aetheris.nasa import Observation, DataError
from aetheris.science import seasonal_profile, unusual_years
from aetheris.server import app

client = TestClient(app)


def fixtures(start=2001, end=2025):
    obs = [Observation(y, m, 16 + .1 * (y-start) + (m % 4))
           for y in range(start, end+1) for m in range(1,13)]
    return obs, {'source':'NASA POWER', 'source_product':'TEST FIXTURE — NOT LIVE NASA',
                 'source_url':'https://power.larc.nasa.gov/', 'valid_months':len(obs),
                 'missing_or_unavailable_months':0,'retrieved_at':'fixture',
                 'monthly_unit':'°C', 'source_request':'https://power.larc.nasa.gov/test-fixture'}


def test_bh_adjustment_handles_missing_and_ties():
    values = benjamini_hochberg([.01,.03,.06,None,.001])
    assert values[0] == .02
    assert values[1] == .04
    assert values[2] == .06
    assert values[3] is None
    assert values[4] == .004


def test_bh_no_valid_p_values():
    assert benjamini_hochberg([None,None]) == [None,None]


def test_seasonal_temperature_profile():
    obs,_=fixtures(2001,2010)
    profile=seasonal_profile(obs,'T2M')
    assert len(profile['months'])==12
    assert all(p['samples']==10 for p in profile['months'])


def test_seasonal_precip_converts_mm_per_day_to_monthly_mm():
    obs=[Observation(y,m,1.) for y in range(2001,2009) for m in range(1,13)]
    profile=seasonal_profile(obs,'PRECTOTCORR')
    assert profile['months'][0]['mean'] == 31.
    assert 28 < profile['months'][1]['mean'] < 29
    assert profile['unit']=='mm/month'


def test_unusual_years_are_descriptive():
    years=[{'year':2020+i,'value':float(i)} for i in range(8)]
    notable=unusual_years(years,0)
    assert [x['year'] for x in notable]==[2027,2026,2025,2024]


def test_discovery_scan_uses_presets_and_bh():
    with patch('aetheris.discovery.fetch_power',new=AsyncMock(return_value=fixtures())):
        res=client.get('/api/v1/discover?locations=Beni%20Mellal,Marrakech,Casablanca&start=2001&end=2025')
    assert res.status_code==200, res.text
    data=res.json()
    assert data['successful']==3
    assert data['failed']==0
    assert all('adjusted_p_bh' in v for v in data['locations'])
    assert all('observation_sha256' in v for v in data['locations'])


def test_discovery_rejects_invalid_points():
    for locations in ['Beni Mellal','Beni Mellal,Beni Mellal','Unknown,Marrakech', ','.join(str(i) for i in range(7))]:
        res=client.get('/api/v1/discover',params={'locations':locations})
        assert res.status_code==422


def test_discovery_partial_upstream_failure():
    async def intermittent(lat,lon,*args):
        if lat==32.337:raise DataError('NASA service unavailable','NASA_UNAVAILABLE')
        return fixtures()
    with patch('aetheris.discovery.fetch_power',new=intermittent):
        res=client.get('/api/v1/discover?locations=Beni%20Mellal,Marrakech&start=2001&end=2025')
    assert res.status_code==200
    data=res.json()
    assert data['failed']==1 and data['successful']==1


def test_pdf_report_has_genuine_pdf_signature_and_source():
    with patch('aetheris.server.fetch_power',new=AsyncMock(return_value=fixtures())):
        res=client.get('/api/v1/report.pdf?lat=32.337&lon=-6.349&start=2001&end=2025&variable=T2M&place=Beni+Mellal')
    assert res.status_code==200,res.text
    assert res.headers['content-type']=='application/pdf'
    assert res.content[:5]==b'%PDF-'
    assert len(res.content)>3300
    from pypdf import PdfReader
    reader=PdfReader(io.BytesIO(res.content))
    assert len(reader.pages)==2
    assert 'SCIENTIFIC' in reader.pages[0].extract_text()
    assert 'SHA-256' in reader.pages[1].extract_text()


def test_intelligence_status_is_truthful():
    res=client.get('/api/v1/intelligence/status')
    assert res.json()['available'] is False


def test_ai_endpoint_declines_unconfigured():
    with patch.dict('os.environ', {'AETHERIS_AI_ENDPOINT':''}):
        res=client.get('/api/v1/intelligence/analyze?lat=32&lon=-6&start=2001&end=2025')
        assert res.status_code==503
        assert res.json()['error']['code']=='AI_NOT_CONFIGURED'


def test_ai_contract_requires_provenance():
    from pydantic import ValidationError
    from aetheris.intelligence import ModelOutput
    with pytest.raises(ValidationError):
        ModelOutput.model_validate({'model_name':'model','model_version':'1','model_type':'IF', 'signals':[]})


def test_ai_rejects_insecure_endpoint():
    from aetheris.intelligence import configured_endpoint
    with patch.dict('os.environ', {'AETHERIS_AI_ENDPOINT':'http://example.com/infer'}):
        assert configured_endpoint() is None
    with patch.dict('os.environ', {'AETHERIS_AI_ENDPOINT':'http://127.0.0.1:8002/predict'}):
        assert configured_endpoint() is not None


def test_ai_integration_contract_mocked():
    from aetheris.intelligence import run_external_inference
    from aetheris.science import investigate
    obs, meta=fixtures()
    inp=investigate(obs,meta,'T2M',32.337,-6.349,2001,2025)
    class RemoteResponse:
        def raise_for_status(self): return None
        def json(self):return {'model_name':'Verified Example Model','model_version':'0.1',
         'model_type':'Isolation Forest','methodology':'Seasonally adjusted annual anomaly detection evaluation',
         'data_provenance':'Local test fixture annual series and validation data',
         'limitations':['Synthetic contract smoke test only, not genuine trained performance.'],
         'signals':[{'year':2008,'anomaly_score':.76,'is_anomaly':True,'explanation':'Unusual relative to baseline.'}]}
    class RemoteClient:
        async def __aenter__(self):return self
        async def __aexit__(self,*args):return False
        async def post(self,*args,**kwargs):return RemoteResponse()
    with patch.dict('os.environ',{'AETHERIS_AI_ENDPOINT':'https://models.example.org/infer'}):
      with patch('aetheris.intelligence.httpx.AsyncClient',return_value=RemoteClient()):
        import asyncio
        out=asyncio.run(run_external_inference(inp))
    assert out['status']=='ok' and out['model']['signals'][0]['year']==2008
