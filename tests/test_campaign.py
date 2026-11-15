"""Research Campaign Studio: deterministic synthetic tests; no NASA measurements are fabricated."""
from __future__ import annotations

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from aetheris.campaign import assemble_campaign, run_campaign
from aetheris.discovery import benjamini_hochberg
from aetheris.nasa import Observation, DataError
from aetheris.science import investigate
from aetheris.systems import analyze_systems
from aetheris.server import app, LOCATIONS


CLIENT = TestClient(app)
POINTS = LOCATIONS[:4]


def result(lat,lon,temperature_slope=.06,rainfall_slope=-.015):
    def observations(variable):
        return [Observation(year,month,(17+temperature_slope*(year-2001)+month*.035)
                            if variable=='T2M' else (2.8+rainfall_slope*(year-2001)+month*.006))
                for year in range(2001,2026) for month in range(1,13)]
    def details(variable):
        return {'source':'NASA POWER','source_product':'SYNTHETIC TEST ONLY','source_url':'https://power.larc.nasa.gov',
                'source_request':'synthetic-fixture-no-live-request','monthly_unit':'°C' if variable=='T2M' else 'mm/day',
                'retrieved_at':'fixture','missing_or_unavailable_months':0}
    return analyze_systems(investigate(observations('T2M'),details('T2M'),'T2M',lat,lon,2001,2025),
                           investigate(observations('PRECTOTCORR'),details('PRECTOTCORR'),'PRECTOTCORR',lat,lon,2001,2025))


def sample(n=3):
    return assemble_campaign(POINTS[:n], [{'status':'ok','data':result(p['lat'],p['lon'],.06+i*.01)}
                                                   for i,p in enumerate(POINTS[:n])], 2001,2025)


def test_verified_paired_outputs_and_provenance():
    d=sample()
    assert d['successful_count']==3 and d['failed_count']==0
    assert len(d['locations'])==3
    for p in d['locations']:
        assert len(p['annual'])==25
        assert p['temperature']['unit']=='°C/decade'
        assert p['precipitation']['unit']=='mm/decade'
        assert len(p['source']['temperature_sha256'])==64
        assert len(p['source']['precipitation_sha256'])==64
        assert p['source']['temperature_url']=='synthetic-fixture-no-live-request'
    assert len(d['manifest']['campaign_sha256'])==64
    assert all('causal' in ' '.join(d['limitations']).lower() for _ in range(1))


def test_per_variable_hypothesis_families_and_order_preserved():
    d=sample(4)
    assert [x['name'] for x in d['locations']]==[x['name'] for x in POINTS]
    assert [r['temperature']['q_bh'] for r in d['locations']]==benjamini_hochberg([r['temperature']['p_hac'] for r in d['locations']])
    assert [r['precipitation']['q_bh'] for r in d['locations']]==benjamini_hochberg([r['precipitation']['p_hac'] for r in d['locations']])


def test_partial_results_are_explicit_and_no_fake_data():
    rows=[{'status':'ok','data':result(POINTS[0]['lat'],POINTS[0]['lon'])},
          {'status':'error','error':'NASA offline'}]
    d=assemble_campaign(POINTS[:2],rows,2001,2025)
    assert d['successful_count']==1 and d['failed_count']==1
    assert d['locations'][1]['status']=='error'
    assert 'annual' not in d['locations'][1]
    assert d['locations'][1]['error']=='NASA offline'
    assert d['locations'][0]['temperature']['q_bh'] is not None


def test_all_failed_still_clearly_reported():
    d=assemble_campaign(POINTS[:2],[{'status':'error','error':'upstream timeout'}]*2,2001,2025)
    assert d['successful_count']==0 and d['failed_count']==2
    assert d['highlights']['largest_temperature_slope_in_sample'] is None
    assert d['highlights']['smallest_precipitation_slope_in_sample'] is None


def test_hash_reproducible_for_same_source_snapshots():
    assert sample()['manifest']['campaign_sha256']==sample()['manifest']['campaign_sha256']
    assert sample(2)['manifest']['campaign_sha256']!=sample(3)['manifest']['campaign_sha256']


@pytest.mark.asyncio
async def test_concurrent_campaign_and_error_isolation():
    async def fake(lat,lon,start,end):
        if lat==POINTS[1]['lat']:raise DataError('NASA temporary unavailable','NASA_UNAVAILABLE',502)
        return result(lat,lon)
    with patch('aetheris.campaign.run_systems',side_effect=fake) as mocked:
        d=await run_campaign(POINTS[:3],2001,2025)
    assert mocked.await_count==3
    assert d['successful_count']==2 and d['failed_count']==1
    assert d['locations'][1]['status']=='error'


@pytest.mark.asyncio
async def test_reject_duplicate_names_and_invalid_range():
    with pytest.raises(DataError):await run_campaign([POINTS[0],POINTS[0]],2001,2025)
    with pytest.raises(DataError):await run_campaign(POINTS[:3],2022,2025)


def test_campaign_api_validation_and_response():
    assert CLIENT.get('/api/v1/campaign?locations=Foo,Bar').status_code==422
    assert CLIENT.get('/api/v1/campaign?locations=Beni%20Mellal,Beni%20Mellal').status_code==422
    assert CLIENT.get('/api/v1/campaign?locations=Beni%20Mellal,Marrakech&start=2022&end=2025').status_code==422
    async def fake(locations,start,end):
        return assemble_campaign(locations,[{'status':'ok','data':result(p['lat'],p['lon'])} for p in locations],start,end)
    with patch('aetheris.server.run_campaign',side_effect=fake) as mocked:
        r=CLIENT.get('/api/v1/campaign?locations=Beni%20Mellal,Marrakech&start=2001&end=2025')
    assert r.status_code==200,r.text
    assert mocked.await_count==1
    assert r.json()['successful_count']==2
    assert r.json()['version']=='14.0.0'


def test_ui_integration_and_accessibility_hooks():
    root=Path(__file__).resolve().parents[1]
    html=(root/'static/index.html').read_text()
    js=(root/'static/campaign.js').read_text()
    for control in ('view-campaign','campaign-form','campaign-locations','campaign-year','campaign-year-options',
                    'campaign-export-json','campaign-export-csv','campaign-export-slides','campaign-source-list'):
        assert f'id="{control}"' in html
    assert 'data-view="campaign"' in html
    assert '/api/v1/campaign' in js
    assert 'window.AetherisCampaign' in js
    assert 'source_sha256' not in js or 'paired_source_sha256' in js
