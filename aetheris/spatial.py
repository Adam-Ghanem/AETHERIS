"""AETHERIS Spatial Observatory: nine explicit NASA POWER point investigations.

The 3x3 arrangement is a sparse sampling design, NOT a satellite raster,
continuous heatmap or an estimate of an administrative area's average.
"""
from __future__ import annotations

import asyncio
import math
from datetime import datetime, timezone

from .discovery import benjamini_hochberg
from .nasa import DataError, fetch_power, validate_inputs
from .science import investigate

MAX_SPATIAL_POINTS = 9


def sample_grid(lat: float, lon: float, spacing_km: int) -> list[dict]:
    """Generate nine point coordinates using a documented local geodesic approximation."""
    if not math.isfinite(lat) or not math.isfinite(lon) or abs(lat) > 75 or not -180 <= lon <= 180:
        raise DataError('Spatial sampling supports latitude -75° through 75° and valid longitude.', 'INVALID_SPATIAL_CENTER', 422)
    if spacing_km not in (50, 100, 150):
        raise DataError('Choose spatial grid spacing of 50, 100 or 150 km.', 'INVALID_GRID_SPACING', 422)
    delta_lat = spacing_km / 111.195
    result = []
    for row, north in enumerate((1, 0, -1)):
        next_lat = lat + north * delta_lat
        if not -90 < next_lat < 90:
            raise DataError('Spatial grid extends beyond valid latitude.', 'INVALID_GRID', 422)
        # Longitude scales with cos(latitude) for a small regional grid.
        delta_lon = spacing_km / (111.195 * math.cos(math.radians(next_lat)))
        for col, east in enumerate((-1, 0, 1)):
            next_lon = ((lon + east * delta_lon + 180) % 360) - 180
            result.append({
                'id': f'p{row * 3 + col}', 'row': row, 'column': col,
                'lat': round(next_lat, 5), 'lon': round(next_lon, 5),
                'is_center': row == 1 and col == 1,
            })
    return result


async def spatial_scan(lat: float, lon: float, start: int, end: int,
                       variable: str, spacing_km: int) -> dict:
    validate_inputs(lat, lon, start, end, variable)
    grid = sample_grid(lat, lon, spacing_km)
    limiter = asyncio.Semaphore(2)

    async def evaluate(point: dict) -> dict:
        async with limiter:
            try:
                observations, meta = await fetch_power(point['lat'], point['lon'], start, end, variable)
                outcome = investigate(observations, meta, variable, point['lat'], point['lon'], start, end)
                trend = outcome['trend']
                return {
                    **point, 'status': 'ok',
                    'slope_per_decade': trend['slope_per_decade'],
                    'slope_unit': trend['slope_unit'],
                    'p_value_hac': trend['p_value_hac'],
                    'significance': trend['significance_label'],
                    'annual_years': trend['sample_size'],
                    'sha256_monthly': outcome['evidence']['sha256_monthly'],
                    'data_source': outcome['evidence']['provider'],
                    'warnings': outcome['quality']['warnings'],
                }
            except (DataError, ValueError, KeyError, TypeError) as exc:
                return {**point, 'status': 'error', 'error': str(exc)[:200]}

    # Results stay in physical grid order, never sorted as a leaderboard.
    points = await asyncio.gather(*(evaluate(point) for point in grid))
    success = [p for p in points if p['status'] == 'ok']
    if not success:
        raise DataError('NASA data could not be retrieved for any sampled point. Please retry.', 'SPATIAL_SOURCE_UNAVAILABLE', 502)
    q_values = benjamini_hochberg([p.get('p_value_hac') for p in points])
    for point, q in zip(points, q_values):
        if point['status'] == 'ok':
            point['adjusted_p_bh'] = q
            point['exploratory_fdr_05'] = q is not None and q < .05
    slopes = [p['slope_per_decade'] for p in success]
    center = next((p for p in success if p['is_center']), None)
    return {
        'version': 'spatial-v1',
        'grid': {'rows': 3, 'columns': 3, 'spacing_km': spacing_km,
                 'center_lat': lat, 'center_lon': lon,
                 'projection': 'Approximate local lat/lon offsets based on 111.195 km per degree latitude and latitude-adjusted longitude'},
        'period': {'start': start, 'end': end}, 'variable': variable,
        'source': 'NASA POWER monthly point data',
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'points': points, 'successful': len(success), 'failed': len(points)-len(success),
        'summary': {
            'min_slope': min(slopes), 'max_slope': max(slopes),
            'slope_spread': round(max(slopes)-min(slopes), 5),
            'median_slope': round(float(sorted(slopes)[len(slopes)//2]), 5) if len(slopes)%2 else round((sorted(slopes)[len(slopes)//2-1]+sorted(slopes)[len(slopes)//2])/2, 5),
            'center_slope': center['slope_per_decade'] if center else None,
            'slope_unit': success[0]['slope_unit'],
            'exploratory_fdr_flags': sum(p.get('exploratory_fdr_05') is True for p in points),
        },
        'method': 'Independent point time-series annual OLS trend estimates with HAC standard errors; exploratory BH p-value adjustment across tested points.',
        'limitations': [
            'Nine discrete gridded/reanalysis samples are not a continuous spatial climate map or an administrative-region average.',
            'Nearby points may correspond to the same underlying gridded NASA POWER cell and are not independent observations.',
            'Displayed colors classify the nine measured trend estimates only; no spatial interpolation is performed.',
            'The BH procedure is exploratory; spatial dependence, selected region, missing data, and testing assumptions affect interpretation.',
            'The design does not attribute observed climate change to particular causes. Failed locations are explicitly marked.',
        ],
    }
