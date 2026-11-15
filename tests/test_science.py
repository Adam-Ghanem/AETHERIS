import calendar
import math

import pytest

from aetheris.nasa import DataError, Observation, parse_power, validate_inputs
from aetheris.science import annualize, trend_analysis, investigate


def create_monthly(make_value, start=2001, n=20):
    return [Observation(y, m, make_value(y, m)) for y in range(start, start+n) for m in range(1,13)]


def test_weighted_annual_temperature():
    obs = [Observation(2020,m,float(m)) for m in range(1,13)]
    a,ex = annualize(obs,'T2M')
    expected=sum(calendar.monthrange(2020,m)[1]*m for m in range(1,13))/366
    assert len(a)==1 and ex==[]
    assert a[0]['value']==pytest.approx(expected,abs=1e-5)


def test_precipitation_converts_rate_to_annual_mm():
    obs = [Observation(2020,m,1) for m in range(1,13)]
    a,_=annualize(obs,'PRECTOTCORR')
    assert a[0]['value']==366


def test_excludes_incomplete_year():
    obs=create_monthly(lambda y,m:20.,n=10)
    obs=[p for p in obs if not (p.year==2007 and p.month==5)]
    a,excluded=annualize(obs,'T2M')
    assert 2007 in excluded and len(a)==9


def test_linear_upward_trend():
    annual=[{'year':y,'value':15+(y-2000)*.15} for y in range(2001,2026)]
    t=trend_analysis(annual,'T2M')
    assert t['slope_per_decade']==pytest.approx(1.5,abs=1e-5)
    assert t['sample_size']==25


def test_linear_downward_trend():
    annual=[{'year':y,'value':60-(y-2000)*.2} for y in range(2001,2026)]
    t=trend_analysis(annual,'PRECTOTCORR')
    assert t['slope_per_decade']==pytest.approx(-2.,abs=1e-5)


def test_short_series_rejected():
    with pytest.raises(DataError):trend_analysis([{'year':2001+i,'value':20+i} for i in range(7)],'T2M')


def test_parser_monthly_ignores_annual_code_and_sentinels():
    payload={'properties':{'parameter':{'T2M':{'200101':18.1,'200102':-999,'200113':19.2}}},'parameters':{'T2M':{'units':'C'}}}
    obs,meta=parse_power(payload,'T2M',2001,2001)
    assert len(obs)==1 and obs[0].value==18.1 and meta['missing_or_unavailable_months']==11


def test_parser_rejects_unexpected_unit():
    payload={'properties':{'parameter':{'T2M':{'200101':18}}},'parameters':{'T2M':{'units':'kelvin'}}}
    with pytest.raises(DataError):parse_power(payload,'T2M',2001,2001)


def test_validate_request():
    for lat,lon,sy,ey,param in [(91,0,2001,2025,'T2M'),(30,181,2001,2025,'T2M'),(30,20,2001,2025,'fake'),(30,20,2001,2003,'T2M')]:
        with pytest.raises(DataError):validate_inputs(lat,lon,sy,ey,param)


def test_evidence_deterministic_with_same_monthly_data():
    obs=create_monthly(lambda y,m:20+(y-2000)*.025,n=12)
    metadata={'source':'NASA POWER','source_product':'test fixture','valid_months':len(obs),'missing_or_unavailable_months':0,'retrieved_at':'test'}
    d1=investigate(obs,metadata,'T2M',32.337,-6.349,2001,2012)
    d2=investigate(obs,metadata,'T2M',32.337,-6.349,2001,2012)
    assert d1['evidence']['sha256_monthly']==d2['evidence']['sha256_monthly']
    assert d1['trend']['slope_per_decade']==pytest.approx(.25,abs=1e-5)
    assert d1['anomaly_baseline']['start_year']==2001


def test_constant_series_does_not_claim_false_significance():
    annual=[{'year':y,'value':5.0} for y in range(2000,2025)]
    t=trend_analysis(annual,'T2M')
    assert t['slope_per_decade']==0
    assert t['significance_label']=='insufficient evidence'
    assert t['p_value_hac'] is None
