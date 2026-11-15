"""Multi-location exploratory scanning with multiple-comparison correction.

Independent fixed NASA POWER point locations, not spatial interpolation or
administrative-region maps. BH adjustment applies only to evaluated hypotheses.
"""
from __future__ import annotations

import asyncio
import math
from .nasa import DataError, fetch_power, validate_inputs
from .science import investigate


def benjamini_hochberg(p_values: list[float | None]) -> list[float | None]:
    """Monotone BH adjusted p-values, preserving missing/nonfinite entries."""
    valid = [(idx, float(p)) for idx,p in enumerate(p_values)
             if p is not None and math.isfinite(float(p)) and 0 <= float(p) <= 1]
    out: list[float | None] = [None] * len(p_values)
    m = len(valid)
    if not m:
        return out
    ordered = sorted(valid, key=lambda item:item[1], reverse=True)
    minimum = 1.0
    for reverse_index, (idx, p) in enumerate(ordered):
        rank = m - reverse_index
        minimum = min(minimum, p * m / rank)
        out[idx] = round(minimum, 8)
    return out


async def scan_locations(locations: list[dict], start: int, end: int, variable: str) -> dict:
    if len(locations) < 2 or len(locations) > 6:
        raise DataError('Select between 2 and 6 locations for a discovery scan.', 'INVALID_SCAN_SIZE', 422)
    for loc in locations:
        validate_inputs(loc['lat'], loc['lon'], start, end, variable)
    throttle = asyncio.Semaphore(2)

    async def scan_one(loc: dict) -> dict:
        async with throttle:
            try:
                observations, meta = await fetch_power(loc['lat'],loc['lon'],start,end,variable)
                result = investigate(observations,meta,variable,loc['lat'],loc['lon'],start,end)
                return {
                    'status':'ok', 'location':loc['name'], 'country':loc['country'],
                    'lat':loc['lat'], 'lon':loc['lon'],
                    'slope_per_decade':result['trend']['slope_per_decade'],
                    'slope_unit':result['trend']['slope_unit'],
                    'p_value_hac':result['trend']['p_value_hac'],
                    'sample_size':result['trend']['sample_size'],
                    'observation_sha256':result['evidence']['sha256_monthly'],
                    'source_request':result['evidence']['source_request'],
                    'warnings':result['quality']['warnings'],
                }
            except (DataError, ValueError, KeyError, TypeError) as err:
                return {'status':'error', 'location':loc['name'], 'country':loc['country'],
                        'lat':loc['lat'], 'lon':loc['lon'],
                        'error':str(err)[:180]}

    results = await asyncio.gather(*(scan_one(loc) for loc in locations))
    adjusted = benjamini_hochberg([item.get('p_value_hac') for item in results])
    for item, q in zip(results, adjusted):
        if item['status'] == 'ok':
            item['adjusted_p_bh'] = q
            item['fdr_flag_05'] = q is not None and q < 0.05
    results.sort(key=lambda item: (item['status'] != 'ok', -abs(item.get('slope_per_decade',0))))
    count = sum(r['status'] == 'ok' for r in results)
    return {
        'locations':results, 'successful':count, 'failed':len(results)-count,
        'variable':variable,'period':{'start':start,'end':end},
        'method':'NASA POWER point-wise annual OLS with HAC-robust inference; Benjamini-Hochberg FDR correction across successful, testable point hypotheses',
        'limitations':[
            'The scanned locations are a user-selected sample of points, not an exhaustive map or regional spatial interpolation.',
            'A BH-adjusted p-value is an exploratory result, not proof of causation or guaranteed false-discovery control under arbitrary spatial dependence.',
            'Inter-location spatial correlation and retrospective point selection can affect inference.',
            'Failed locations are reported, never silently imputed; a partial scan is not a complete ranking.',
        ]
    }
