"""AETHERIS 5.0 Earth Systems Coupling Lab.

Two authentic NASA POWER source series are compared as paired annual signals.
Co-occurrence and correlations are DESCRIPTIVE and do not establish drought,
statistical significance, climate attribution, or causality.
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import math
from datetime import datetime, timezone

import numpy as np
from scipy.stats import pearsonr

from .nasa import DataError, fetch_power, validate_inputs
from .science import investigate


def _safe_float(value: float | None, digits: int = 5) -> float | None:
    return round(float(value), digits) if value is not None and math.isfinite(float(value)) else None


def _correlation(x: np.ndarray, y: np.ndarray) -> float | None:
    if len(x) < 8 or np.ptp(x) < 1e-10 or np.ptp(y) < 1e-10:
        return None
    return _safe_float(pearsonr(x, y).statistic, 4)


def _detrend(years: np.ndarray, values: np.ndarray) -> np.ndarray:
    # Residuals from simple linear trend. Association still descriptive,
    # because residuals can exhibit serial dependence and confounding.
    slope, intercept = np.polyfit(years - years.mean(), values, 1)
    return values - (slope * (years - years.mean()) + intercept)


def analyze_systems(temperature: dict, precipitation: dict) -> dict:
    """Cross-source annual temperature/precipitation investigation.

    Accept independently calculated investigations. Never fill missing years,
    and never interpret point data as a measured region-average climate index.
    """
    if temperature['variable']['id'] != 'T2M' or precipitation['variable']['id'] != 'PRECTOTCORR':
        raise DataError('Earth Systems requires T2M and PRECTOTCORR investigations.', 'INVALID_VARIABLE_PAIR', 422)
    for axis in ('latitude', 'longitude'):
        if abs(temperature['location'][axis] - precipitation['location'][axis]) > 1e-8:
            raise DataError('Both systems must represent the same coordinates.', 'LOCATION_MISMATCH', 422)
    tmap = {int(p['year']): float(p['value']) for p in temperature['annual']}
    pmap = {int(p['year']): float(p['value']) for p in precipitation['annual']}
    years = sorted(set(tmap).intersection(pmap))
    if len(years) < 8:
        raise DataError('At least eight shared complete calendar years are required.', 'INSUFFICIENT_PAIRED_DATA', 422)
    t = np.array([tmap[y] for y in years], dtype=float)
    p = np.array([pmap[y] for y in years], dtype=float)
    if not (np.isfinite(t).all() and np.isfinite(p).all()):
        raise DataError('Nonfinite yearly paired observations.', 'INVALID_PAIRED_DATA', 422)
    baseline_years = years[: min(10, len(years))]
    bt = t[:len(baseline_years)]
    bp = p[:len(baseline_years)]
    tmean, pmean = float(bt.mean()), float(bp.mean())
    # Sample SD, not a population climate normal. A constant baseline
    # cannot produce standardized deviations and is reported as such.
    tsd = float(bt.std(ddof=1)) if len(bt) > 1 else 0.
    psd = float(bp.std(ddof=1)) if len(bp) > 1 else 0.
    tz = (t - tmean) / tsd if tsd > 1e-9 else None
    pz = (p - pmean) / psd if psd > 1e-9 else None
    rows, flags = [], []
    for i, year in enumerate(years):
        temp_z = _safe_float(tz[i], 3) if tz is not None else None
        precip_z = _safe_float(pz[i], 3) if pz is not None else None
        joint = temp_z is not None and precip_z is not None and temp_z >= 1 and precip_z <= -1
        if joint:
            flags.append(year)
        rows.append({
            'year': year, 'temperature_c': _safe_float(t[i]), 'precipitation_mm': _safe_float(p[i]),
            'temperature_departure_c': _safe_float(t[i] - tmean),
            'precipitation_departure_mm': _safe_float(p[i] - pmean),
            'temperature_z': temp_z, 'precipitation_z': precip_z,
            'joint_hot_dry_deviation': bool(joint),
        })
    # Split paired years into balanced chronological eras. On odd sample
    # counts, omit the central year from only the era contrast.
    n = len(years)
    half = n // 2
    early = rows[:half]
    late = rows[-half:]
    era = {
        'early_years': [early[0]['year'], early[-1]['year']],
        'late_years': [late[0]['year'], late[-1]['year']],
        'excluded_middle_year': years[half] if n % 2 else None,
        'temperature_change_c': _safe_float(np.mean([r['temperature_c'] for r in late]) - np.mean([r['temperature_c'] for r in early])),
        'precipitation_change_mm': _safe_float(np.mean([r['precipitation_mm'] for r in late]) - np.mean([r['precipitation_mm'] for r in early])),
        'method': 'Difference of means between balanced early and late groups of shared complete years (descriptive)',
    }
    year_arr = np.asarray(years, dtype=float)
    actual_r = _correlation(t, p)
    residual_r = _correlation(_detrend(year_arr, t), _detrend(year_arr, p))
    a = temperature['evidence']['sha256_monthly']
    b = precipitation['evidence']['sha256_monthly']
    evidence_pair = hashlib.sha256(f'{a}:{b}:earth-systems-v1'.encode()).hexdigest()
    excluded = sorted(set(tmap).symmetric_difference(pmap))
    limitations = [
        'Both series are NASA POWER gridded/model-derived point products, not in-situ station measurements or an administrative-region mean.',
        'Pairing requires the same complete calendar years; no unavailable years are interpolated.',
        'The first up to ten common years define an INTERNAL descriptive baseline, not an independent standardized 30-year climate normal.',
        'The joint hot/dry marker uses arbitrary exploratory one-sample-SD thresholds, not a validated drought or extreme-event index.',
        'Raw and detrended correlations are descriptive, not adjusted for serial dependence, confounders, or multiplicity; they are not causal evidence.',
        'The early/late contrast describes observed differences, not statistical significance, forecasting, or climate attribution.',
        'Temperature is annual mean °C; precipitation is estimated annual total mm calculated from monthly mm/day rates.',
    ]
    if tsd <= 1e-9 or psd <= 1e-9:
        limitations.append('At least one baseline has zero variance; standardized flags for that baseline are unavailable.')
    if excluded:
        limitations.append('Years without BOTH complete products are excluded from paired analysis: ' + ', '.join(map(str, excluded)) + '.')
    return {
        'module': 'AETHERIS Earth Systems Coupling Lab', 'version': '5.0.0',
        'location': temperature['location'],
        'period': {'requested_start': temperature['period']['requested_start'],
                   'requested_end': temperature['period']['requested_end'],
                   'shared_complete_years': n, 'paired_years': [years[0], years[-1]],
                   'excluded_unpaired_years': excluded},
        'metrics': {
            'temperature': {'trend_per_decade': temperature['trend']['slope_per_decade'], 'trend_unit': '°C/decade',
                            'exploratory_p_hac': temperature['trend']['p_value_hac']},
            'precipitation': {'trend_per_decade': precipitation['trend']['slope_per_decade'], 'trend_unit': 'mm/decade',
                              'exploratory_p_hac': precipitation['trend']['p_value_hac']},
        },
        'baseline': {'first_year': baseline_years[0], 'last_year': baseline_years[-1],
                     'sample_size': len(baseline_years), 'temperature_mean_c': _safe_float(tmean),
                     'precipitation_mean_mm': _safe_float(pmean),
                     'temperature_sample_sd_c': _safe_float(tsd), 'precipitation_sample_sd_mm': _safe_float(psd)},
        'annual_inputs': {'temperature': temperature['annual'], 'precipitation': precipitation['annual']},
        'years': rows,
        'joint_deviations': {'years': flags, 'count': len(flags),
            'definition': 'Within-point annual temperature >= baseline mean + 1 sample SD AND precipitation <= baseline mean - 1 sample SD; exploratory screening only.'},
        'association': {'raw_pearson_r': actual_r, 'detrended_pearson_r': residual_r,
                        'n': n, 'method': 'Pearson correlation of aligned annual values and separately linear-detrended annual residuals; descriptive, no significance test.'},
        'era_comparison': era,
        'seasonality': {'temperature': temperature['seasonality'], 'precipitation': precipitation['seasonality']},
        'evidence': {'provider': 'NASA POWER', 'temperature': temperature['evidence'],
                     'precipitation': precipitation['evidence'], 'paired_sha256': evidence_pair,
                     'analysis_version': '5.0.0', 'generated_at': datetime.now(timezone.utc).isoformat()},
        'limitations': limitations,
    }


async def run_systems(lat: float, lon: float, start: int, end: int) -> dict:
    validate_inputs(lat, lon, start, end, 'T2M')
    # Each source is independently requested and fully validated.
    (t_obs, t_meta), (p_obs, p_meta) = await asyncio.gather(
        fetch_power(lat, lon, start, end, 'T2M'),
        fetch_power(lat, lon, start, end, 'PRECTOTCORR'),
    )
    return analyze_systems(
        investigate(t_obs, t_meta, 'T2M', lat, lon, start, end),
        investigate(p_obs, p_meta, 'PRECTOTCORR', lat, lon, start, end),
    )
