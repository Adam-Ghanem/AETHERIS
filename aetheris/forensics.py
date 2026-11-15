"""Climate Forensics: transparent stability diagnostics for NASA POWER investigations.

These descriptive diagnostics complement (but do not replace) HAC inference.
They deliberately avoid claims of causal attribution or independent trend significance.
"""
from __future__ import annotations

import calendar
import math
from collections import defaultdict

import numpy as np

from .nasa import DataError, Observation


def _slope_decade(rows: list[dict]) -> float:
    years = np.array([row['year'] for row in rows], dtype=float)
    values = np.array([row['value'] for row in rows], dtype=float)
    if len(rows) < 3 or np.ptp(years) == 0:
        raise DataError('Not enough distinct years for a trend estimate.', 'INSUFFICIENT_DATA', 422)
    centered = years - years.mean()
    return float(np.dot(centered, values - values.mean()) / np.dot(centered, centered) * 10)


def _by_month(observations: list[Observation], variable: str, years: set[int]) -> dict[int, list[float]]:
    monthly: dict[int, list[float]] = defaultdict(list)
    for obs in observations:
        if obs.year not in years:
            continue
        if variable == 'T2M':
            val = obs.value
        elif variable == 'PRECTOTCORR':
            val = obs.value * calendar.monthrange(obs.year, obs.month)[1]
        else:
            raise DataError('Unsupported forensic variable.', 'UNSUPPORTED_VARIABLE', 422)
        monthly[obs.month].append(val)
    return monthly


def analyze_forensics(investigation: dict, observations: list[Observation], *, window: int = 7) -> dict:
    """Perform period contrast, consecutive-window smooth and jackknife stability.

    Only complete years from investigation['annual'] participate in inference.
    Missing calendar years break rolling windows instead of being bridged.
    """
    annual = investigation['annual']
    variable = investigation['variable']['id']
    years = [int(row['year']) for row in annual]
    if len(years) < 8 or years != sorted(set(years)):
        raise DataError('At least 8 unique sorted complete years are required.', 'INSUFFICIENT_DATA', 422)
    if not (3 <= window <= 15):
        raise DataError('Rolling window must be between 3 and 15 years.', 'INVALID_WINDOW', 422)
    if len(annual) < window:
        raise DataError('Rolling window exceeds the available annual record.', 'INVALID_WINDOW', 422)
    unit = investigation['trend']['annual_unit']
    # Equal-size first/last non-overlapping samples. Middle year intentionally omitted for odd counts.
    half = len(annual) // 2
    early, late = annual[:half], annual[-half:]
    early_mean = float(np.mean([p['value'] for p in early]))
    late_mean = float(np.mean([p['value'] for p in late]))
    difference = late_mean - early_mean
    first_months = _by_month(observations, variable, {p['year'] for p in early})
    last_months = _by_month(observations, variable, {p['year'] for p in late})
    season_shift = []
    for month in range(1, 13):
        e, l = first_months[month], last_months[month]
        if not e or not l:
            raise DataError('Annual data lack corresponding monthly observations.', 'INVALID_SERIES', 422)
        e_mean, l_mean = float(np.mean(e)), float(np.mean(l))
        season_shift.append({
            'month': month, 'label': calendar.month_abbr[month],
            'first_mean': round(e_mean, 5), 'last_mean': round(l_mean, 5),
            'difference': round(l_mean - e_mean, 5),
            'sample_count_each_period': min(len(e), len(l)),
        })
    # A rolling mean is only computed for a consecutive calendar-year window.
    moving = []
    for i in range(len(annual) - window + 1):
        group = annual[i:i + window]
        if group[-1]['year'] - group[0]['year'] != window - 1:
            continue
        moving.append({
            'year': group[-1]['year'],
            'start_year': group[0]['year'],
            'value': round(float(np.mean([p['value'] for p in group])), 5),
        })
    # Leave-one-year-out diagnostic measures dependence on a single annual observation.
    jackknife = []
    for i, row in enumerate(annual):
        remaining = annual[:i] + annual[i + 1:]
        jackknife.append({'omitted_year': row['year'], 'slope_per_decade': round(_slope_decade(remaining), 5)})
    slopes = [x['slope_per_decade'] for x in jackknife]
    full_slope = _slope_decade(annual)
    same_sign = all(s > 0 for s in slopes) if full_slope > 0 else (all(s < 0 for s in slopes) if full_slope < 0 else False)
    sensitive = max(jackknife, key=lambda p: abs(p['slope_per_decade'] - full_slope))
    observations_source = investigation['evidence']['sha256_monthly']
    return {
        'schema_version': '1.0',
        'type': 'descriptive_robustness_diagnostics',
        'variable': investigation['variable'],
        'location': investigation['location'],
        'period': investigation['period'],
        'annual_observations': annual,
        'period_contrast': {
            'first_period': {'start': early[0]['year'], 'end': early[-1]['year'], 'n_years': half, 'mean': round(early_mean, 5)},
            'last_period': {'start': late[0]['year'], 'end': late[-1]['year'], 'n_years': half, 'mean': round(late_mean, 5)},
            'difference': round(difference, 5), 'unit': unit,
            'omitted_middle_year': annual[half]['year'] if len(annual) % 2 else None,
            'interpretation': 'Descriptive difference between equal-length non-overlapping samples; not an independent significance test.',
        },
        'rolling': {'window_years': window, 'points': moving, 'unit': unit,
                    'note': 'Trailing calendar-year mean; windows with missing years are omitted; smoothing is descriptive.'},
        'seasonal_shift': {'months': season_shift, 'unit': '°C' if variable == 'T2M' else 'mm/month',
                           'note': 'Contrast of early/late monthly means using only complete years. These are within-sample comparisons.'},
        'jackknife': {
            'original_slope_per_decade': round(full_slope, 5),
            'minimum_slope_per_decade': round(min(slopes), 5),
            'maximum_slope_per_decade': round(max(slopes), 5),
            'direction_stable_under_single_year_removal': same_sign,
            'most_influential_omitted_year': sensitive,
            'points': jackknife,
            'unit': investigation['trend']['slope_unit'],
            'note': 'Leave-one-year-out sensitivity of OLS slope; not cross-validation, uncertainty bounds or causal evidence.',
        },
        'evidence': {'sha256_monthly': observations_source, 'provider': investigation['evidence']['provider'],
                     'source_url': investigation['evidence']['source_url'],
                     'analysis_version': investigation['analysis_version'],
                     'forensics_version': '1.0.0'},
        'limitations': [
            'NASA POWER is model-derived point-sampled meteorology, not a station or administrative-region measurement.',
            'Early/late contrast and single-year influence are descriptive; neither establishes statistical significance.',
            'Rolling means suppress year-to-year variation and must not be interpreted as forecasts.',
            'Climate variability, serial dependence, missing years, and dataset uncertainty remain relevant.',
            'No result here attributes environmental changes to a specific cause.',
        ],
    }
