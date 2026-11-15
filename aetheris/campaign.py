"""Cross-region, two-variable NASA POWER research campaign.

All geographic rows are independently obtained paired point observations. No
spatial interpolation, cross-variable causality, or trained AI is implied.
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import math

from .discovery import benjamini_hochberg
from .nasa import DataError, validate_inputs
from .systems import run_systems


LIMITATIONS = [
    'Each selected location represents one NASA POWER gridded/model-derived point, not an entire city or administrative region.',
    'Temperature and precipitation are different units and their slopes must not be compared numerically against one another.',
    'BH-adjusted p-values are exploratory, computed separately across successful temperature and precipitation hypotheses; spatial dependence and selection may affect their interpretation.',
    'The year-by-year compound marker uses point-specific internal baseline deviations, not a validated drought index, hazard warning, or causal attribution.',
    'Location ranking only describes the user-selected sampled points; it does not establish geographic extremes.',
    'Failed source requests remain explicit. Results from a partial campaign do not represent all requested points.',
    'Correlation is descriptive; no causal mechanism, future forecast, or official NASA endorsement is claimed.',
]


def assemble_campaign(locations: list[dict], outcomes: list[dict], start: int, end: int) -> dict:
    if len(locations) != len(outcomes) or not (2 <= len(locations) <= 6):
        raise ValueError('Campaign needs matching results for 2–6 points')
    rows = []
    for loc, outcome in zip(locations, outcomes):
        prefix = {'name': loc['name'], 'country': loc['country'], 'lat': loc['lat'], 'lon': loc['lon']}
        if outcome.get('status') == 'error':
            rows.append({**prefix, 'status': 'error', 'error': str(outcome.get('error', 'Unavailable'))[:160]})
            continue
        d = outcome['data']
        t, p = d['metrics']['temperature'], d['metrics']['precipitation']
        rows.append({
            **prefix, 'status': 'ok',
            'temperature': {'slope_per_decade': t['trend_per_decade'], 'unit': t['trend_unit'], 'p_hac': t['exploratory_p_hac']},
            'precipitation': {'slope_per_decade': p['trend_per_decade'], 'unit': p['trend_unit'], 'p_hac': p['exploratory_p_hac']},
            'shared_year_count': d['period']['shared_complete_years'],
            'excluded_years': d['period']['excluded_unpaired_years'],
            'annual': [{
                'year': x['year'], 'temperature_c': x['temperature_c'],
                'precipitation_mm': x['precipitation_mm'],
                'temperature_departure_c': x['temperature_departure_c'],
                'precipitation_departure_mm': x['precipitation_departure_mm'],
                'compound_flag': x['joint_hot_dry_deviation'],
            } for x in d['years']],
            'compound_years': d['joint_deviations']['years'],
            'source': {
                'provider': 'NASA POWER',
                'temperature_sha256': d['evidence']['temperature']['sha256_monthly'],
                'precipitation_sha256': d['evidence']['precipitation']['sha256_monthly'],
                'paired_sha256': d['evidence']['paired_sha256'],
                'temperature_url': d['evidence']['temperature'].get('source_request', ''),
                'precipitation_url': d['evidence']['precipitation'].get('source_request', ''),
            },
        })
    for signal in ('temperature', 'precipitation'):
        qvals = benjamini_hochberg([r[signal]['p_hac'] if r['status'] == 'ok' else None for r in rows])
        for row, q in zip(rows, qvals):
            if row['status'] == 'ok':
                row[signal]['q_bh'] = q
                row[signal]['exploratory_fdr_flag'] = q is not None and q < .05
    successful = [r for r in rows if r['status'] == 'ok']
    max_t = max(successful, key=lambda r: r['temperature']['slope_per_decade']) if successful else None
    min_r = min(successful, key=lambda r: r['precipitation']['slope_per_decade']) if successful else None
    stable = {
        'period': [start, end], 'samples': [
            {'name': r['name'], 'status': r['status'], 'source': r.get('source', {}).get('paired_sha256'),
             'error': r.get('error')}
            for r in rows
        ], 'method_version': 'campaign-v1',
    }
    fingerprint = hashlib.sha256(json.dumps(stable, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    return {
        'module': 'AETHERIS Research Campaign Studio', 'version': '14.0.0',
        'period': {'start': start, 'end': end}, 'requested_count': len(rows),
        'successful_count': len(successful), 'failed_count': len(rows) - len(successful),
        'locations': rows,
        'highlights': {
            'largest_temperature_slope_in_sample': None if max_t is None else {
                'name': max_t['name'], 'slope_per_decade': max_t['temperature']['slope_per_decade'], 'unit': '°C/decade'},
            'smallest_precipitation_slope_in_sample': None if min_r is None else {
                'name': min_r['name'], 'slope_per_decade': min_r['precipitation']['slope_per_decade'], 'unit': 'mm/decade'},
        },
        'manifest': {'campaign_sha256': fingerprint, 'provenance': 'Independently sourced NASA POWER gridded point time series',
                     'method': 'Paired annual analysis; OLS/HAC per point; BH correction independently within each of two variable families',
                     'reference': 'https://power.larc.nasa.gov/docs/services/api/temporal/monthly/'},
        'limitations': LIMITATIONS,
    }


async def run_campaign(locations: list[dict], start: int, end: int) -> dict:
    if len(locations) < 2 or len(locations) > 6:
        raise DataError('Select 2–6 points.', 'INVALID_CAMPAIGN_SIZE', 422)
    if len(set(x['name'] for x in locations)) != len(locations):
        raise DataError('Choose different locations.', 'DUPLICATE_CAMPAIGN_POINTS', 422)
    for loc in locations:
        validate_inputs(loc['lat'], loc['lon'], start, end, 'T2M')
    semaphore = asyncio.Semaphore(2)
    async def collect(loc: dict) -> dict:
        async with semaphore:
            try:
                return {'status': 'ok', 'data': await run_systems(loc['lat'], loc['lon'], start, end)}
            except (DataError, ValueError, TypeError, KeyError) as exc:
                return {'status': 'error', 'error': str(exc)}
    return assemble_campaign(locations, await asyncio.gather(*(collect(loc) for loc in locations)), start, end)
