"""Independent checks for scientific quality diagnostics, not ML scoring."""
import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

from aetheris.nasa import Observation
from aetheris.science import investigate
from aetheris.server import app


def monthly(start=2001, years=24, *, missing=None, outlier=None):
    missing = missing or set()
    rows = []
    for y in range(start, start + years):
        for m in range(1, 13):
            if (y, m) in missing:
                continue
            value = 12.0 + (y - start) * .08
            if y == outlier:
                value += 12.0
            rows.append(Observation(y, m, value))
    return rows


def get(rows, start=2001, end=2024):
    meta = {"source":"Synthetic Test Fixture", "valid_months":len(rows),
            "source_url":"fixture://test", "missing_or_unavailable_months":(end-start+1)*12-len(rows)}
    return investigate(rows,meta,"T2M",32.337,-6.349,start,end)


def test_complete_monthly_coverage_and_agreement():
    data=get(monthly())
    passport=data['quality_passport']
    assert passport['coverage']['valid_months']==288
    assert passport['coverage']['monthly_percent']==100
    assert passport['coverage']['complete_years']==24
    assert passport['method_agreement']['same_direction'] is True
    assert passport['influence']['direction_stable'] is True
    assert passport['source_sha256_monthly']==data['evidence']['sha256_monthly']
    assert len(passport['influence']['leave_one_out'])==24
    assert passport['review_required'] is False


def test_missing_month_is_flagged_and_excluded():
    rows=monthly(missing={(2010,5)})
    data=get(rows)
    p=data['quality_passport']
    assert p['coverage']['valid_months']==287
    assert p['coverage']['complete_years']==23
    assert 2010 in p['coverage']['excluded_or_unavailable_years']
    assert p['checks'][0]['state']=='review'
    assert p['coverage']['monthly_matrix'][9]['months'][4] is False
    assert sum(not m for row in p['coverage']['monthly_matrix'] for m in row['months']) == 1
    assert p['checks'][1]['state']=='review'
    assert p['review_required'] is True


def test_one_year_outlier_can_affect_direction_and_influence():
    data=get(monthly(outlier=2019))
    p=data['quality_passport']
    assert p['influence']['most_influential_omitted_year']['omitted_year']==2019
    assert p['influence']['maximum_slope_per_decade']>=p['influence']['minimum_slope_per_decade']
    assert p['method_agreement']['ols_per_decade']==data['trend']['slope_per_decade']
    assert 'diagnostic' in p['limitations'][0].lower() or 'Diagnostic' in p['limitations'][0]


def test_constancy_not_automatically_significant():
    rows = [Observation(y,m,20.0) for y in range(2001,2025) for m in range(1,13)]
    data = get(rows)
    assert data['trend']['p_value_hac'] is None
    assert data['quality_passport']['influence']['direction_stable']
    assert data['quality_passport']['method_agreement']['same_direction']


def test_quality_passport_is_delivered_by_real_api_contract():
    rows=monthly()
    with patch('aetheris.server.fetch_power', new=AsyncMock(return_value=(rows,{'source':'Synthetic Test Fixture','valid_months':len(rows)}))):
        response=TestClient(app).get('/api/v1/investigate?lat=32.337&lon=-6.349&start=2001&end=2024&variable=T2M')
    assert response.status_code==200
    result=response.json()
    assert result['quality_passport']['source_sha256_monthly']==result['evidence']['sha256_monthly']
    assert result['quality_passport']['period']=={'start':2001,'end':2024}


def test_ui_assets_and_browser_hooks_are_present():
    from pathlib import Path
    root=Path(__file__).resolve().parents[1]
    html=(root/'static/index.html').read_text()
    js=(root/'static/app.js').read_text()
    assert 'id="quality-passport"' in html
    assert 'quality-passport.js' in html and 'quality-passport.css' in html
    assert 'AetherisQuality?.render(d)' in js
    assert 'id="qp-export"' in html and 'id="qp-copy"' in html
