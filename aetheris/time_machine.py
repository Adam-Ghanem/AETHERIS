"""Earth Time Machine: auditable, discrete nine-point annual anomaly snapshots.

No continuous raster, interpolation, causal inference or significance testing is
performed. One source request is made per sampled point; incomplete years are
shown as unavailable. Every anomaly uses that point's same fixed calendar-year
reference window, and observations are traceable to the downloaded source.
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import math
from datetime import datetime, timezone
from statistics import median

from .nasa import DataError, PARAMETERS, fetch_power, validate_inputs
from .science import annualize
from .spatial import sample_grid

BASELINE_YEARS = 10
MIN_BASELINE_YEARS = 8


def annual_snapshots(annual: list[dict], start: int, end: int, variable: str) -> dict:
    """Generate calendar-year anomalies from complete annual observations only.

    The same reference interval applies to each point. At least eight of its
    ten years must have complete months; missing years are NEVER interpolated.
    """
    if variable not in PARAMETERS:
        raise DataError('Unknown variable.', 'UNSUPPORTED_VARIABLE', 422)
    if end - start + 1 < 12:
        raise DataError('Time Machine requires at least 12 historical years.', 'TIME_MACHINE_SHORT_PERIOD', 422)
    values = {int(x['year']): float(x['value']) for x in annual}
    if len(values) != len(annual) or any(not math.isfinite(x) for x in values.values()):
        raise DataError('Annual observations contain invalid or duplicate values.', 'INVALID_SERIES', 422)
    reference_years = list(range(start, start + BASELINE_YEARS))
    available_ref = [values[y] for y in reference_years if y in values]
    if len(available_ref) < MIN_BASELINE_YEARS:
        raise DataError('Too few complete years in reference period.', 'BASELINE_INSUFFICIENT', 422)
    baseline = sum(available_ref) / len(available_ref)
    records = []
    for year in range(start, end + 1):
        if year in values:
            records.append({'year':year, 'annual_value':round(values[year], 5),
                            'anomaly':round(values[year] - baseline, 5), 'status':'ok'})
        else:
            records.append({'year':year,'annual_value':None,'anomaly':None,'status':'missing'})
    return {'baseline':round(baseline, 5),'baseline_start':start,
            'baseline_end':start + BASELINE_YEARS - 1,'baseline_complete_years':len(available_ref),
            'baseline_expected_years':BASELINE_YEARS,'annual':records,
            'available_years':sum(x['status']=='ok' for x in records),
            'missing_years':[x['year'] for x in records if x['status']=='missing']}


def make_snapshots(points: list[dict], start: int, end: int) -> list[dict]:
    """Each requested year contains nine explicit point states in grid order."""
    out = []
    for year in range(start,end+1):
        cells=[]
        for point in points:
            record = next((x for x in point.get('annual', []) if x['year']==year), None)
            available = point['status']=='ok' and record and record['status']=='ok'
            cells.append({'id':point['id'],'status':'ok' if available else 'missing',
                          'annual_value':record['annual_value'] if available else None,
                          'anomaly':record['anomaly'] if available else None})
        anomalies=[c['anomaly'] for c in cells if c['status']=='ok']
        out.append({'year':year,'points':cells,'available_points':len(anomalies),
                    'median_point_anomaly':round(float(median(anomalies)),5) if anomalies else None,
                    'min_point_anomaly':round(min(anomalies),5) if anomalies else None,
                    'max_point_anomaly':round(max(anomalies),5) if anomalies else None,
                    'positive_points':sum(x>0 for x in anomalies),
                    'center_anomaly':cells[4]['anomaly']})
    return out


async def time_machine_scan(lat: float,lon: float,start: int,end: int,variable: str,spacing_km: int) -> dict:
    validate_inputs(lat,lon,start,end,variable)
    if end-start+1<12:
        raise DataError('Select at least 12 complete historical years.', 'TIME_MACHINE_SHORT_PERIOD',422)
    grid=sample_grid(lat,lon,spacing_km)
    sem=asyncio.Semaphore(2)

    async def evaluate(p:dict) -> dict:
        async with sem:
            try:
                observations,meta=await fetch_power(p['lat'],p['lon'],start,end,variable)
                annual,excluded=annualize(observations,variable)
                series=annual_snapshots(annual,start,end,variable)
                raw=[{'year':x.year,'month':x.month,'value':x.value} for x in observations]
                checksum=hashlib.sha256(json.dumps(raw,sort_keys=True,separators=(',',':')).encode()).hexdigest()
                return {**p,'status':'ok',**series,
                        'evidence':{'provider':meta.get('source','NASA POWER'),
                                    'product':meta.get('source_product','NASA POWER monthly point'),
                                    'source_url':meta.get('source_url',''),
                                    'source_request':meta.get('source_request',''),
                                    'retrieved_at':meta.get('retrieved_at',''),
                                    'sha256_monthly':checksum,'valid_months':len(observations),
                                    'excluded_incomplete_years':excluded}}
            except (DataError,ValueError,KeyError,TypeError) as exc:
                return {**p,'status':'error','error':str(exc)[:200], 'annual':[],
                        'baseline':None,'missing_years':list(range(start,end+1))}

    points=await asyncio.gather(*(evaluate(p) for p in grid))
    successful=sum(p['status']=='ok' for p in points)
    if successful==0:
        raise DataError('No point had enough reference-period data for a Time Machine investigation.',
                        'TIME_MACHINE_SOURCE_UNAVAILABLE',502)
    snapshots=make_snapshots(points,start,end)
    return {'version':'time-machine-v1','source':'NASA POWER monthly point data',
            'variable':variable,'unit':PARAMETERS[variable]['annual_unit'],
            'grid':{'rows':3,'columns':3,'spacing_km':spacing_km,'center_lat':lat,'center_lon':lon},
            'period':{'start':start,'end':end},
            'baseline':{'start':start,'end':start+BASELINE_YEARS-1,
                        'minimum_complete_years':MIN_BASELINE_YEARS,
                        'method':'Per-point mean of complete annual values within the same ten-calendar-year reference interval. Not an official 30-year normal.'},
            'successful_points':successful,'failed_points':len(points)-successful,
            'points':points,'snapshots':snapshots,'generated_at':datetime.now(timezone.utc).isoformat(),
            'scientific_method':'Complete annual means (T2M) or annual corrected precipitation totals (PRECTOTCORR); annual minus local ten-year reference mean.',
            'limitations':[
                'Nine discrete NASA POWER gridded point samples are NOT a spatially continuous heatmap, satellite image or regional area average.',
                'Point anomalies use the same reference calendar years but each point has its own baseline. Different model grid cells may represent nearby locations.',
                'A ten-year local reference is descriptive and is NOT an official 30-year climatological normal.',
                'Point samples may share underlying reanalysis grid cells and are not spatially independent.',
                'Incomplete calendar years have no annual result and are never interpolated or represented as zero.',
                'Annual deviations are descriptive, not formal significance tests, impact attribution or forecasts.',
                'Rainfall annual values use monthly rates multiplied by calendar-day counts; units are mm per year.',
            ]}
