"""AETHERIS Seasonal Signal Laboratory.

Exploratory calendar-month trend analysis of genuine NASA POWER meteorological
observations. Twelve tests are corrected by Benjamini-Hochberg FDR, with
explicit limitations about autocorrelation, model-derived input, and causality.

This is classical statistical analysis, NOT a trained AI model.
"""
from __future__ import annotations

import calendar
import hashlib
import json
import math
from collections import defaultdict
from datetime import datetime, timezone

import numpy as np
import statsmodels.api as sm
from scipy.stats import theilslopes

from .nasa import DataError, Observation, fetch_power, validate_inputs
from .science import investigate


def benjamini_hochberg(p_values: list[float | None]) -> list[float | None]:
    """Return adjusted p-values in original position; retain missing entries.

    The monotone step-up correction is applied to the number of actual tests.
    """
    result: list[float | None] = [None] * len(p_values)
    valid = []
    for i, p in enumerate(p_values):
        if p is not None:
            if not math.isfinite(float(p)) or not 0 <= p <= 1:
                raise DataError('Invalid input p-value.', 'INVALID_STATISTICS', 422)
            valid.append((i, float(p)))
    valid.sort(key=lambda v: v[1])
    m = len(valid)
    previous = 1.0
    for rank in range(m, 0, -1):
        i, p = valid[rank - 1]
        previous = min(previous, p * m / rank)
        result[i] = round(max(0.0, previous), 8)
    return result


def _month_trend(years: np.ndarray, values: np.ndarray) -> dict:
    if len(years) < 8:
        return {'slope_per_decade': None, 'theil_sen_per_decade': None,
                'p_value_hac': None, 'n': len(years), 'status': 'insufficient_data'}
    if np.ptp(values) < 1e-10:
        return {'slope_per_decade': 0.0, 'theil_sen_per_decade': 0.0,
                'p_value_hac': None, 'n': len(years), 'status': 'constant_series'}
    x = years - np.mean(years)
    fit = sm.OLS(values, sm.add_constant(x)).fit(
        cov_type='HAC', cov_kwds={'maxlags': min(3, max(1, len(years) // 10))}
    )
    slope = float(fit.params[1]) * 10
    p_value = float(fit.pvalues[1])
    robust = float(theilslopes(values, years).slope) * 10
    return {'slope_per_decade': round(slope, 5), 'theil_sen_per_decade': round(robust, 5),
            'p_value_hac': round(p_value, 8) if math.isfinite(p_value) else None,
            'n': len(years), 'status': 'estimated'}


def analyze_seasonal_signals(investigation: dict, observations: list[Observation]) -> dict:
    """Analyze each calendar month using only complete annual records.

    The same complete-year requirement as the core climate analysis avoids
    mixing baselines and sample inclusion. Excluded partial years are visible
    as missing matrix rows, not interpolated or silently completed.
    """
    variable = investigation['variable']['id']
    if variable not in ('T2M', 'PRECTOTCORR'):
        raise DataError('Unsupported seasonal variable.', 'UNSUPPORTED_VARIABLE', 422)
    annual = investigation['annual']
    complete_years = sorted({int(p['year']) for p in annual})
    if len(complete_years) < 8:
        raise DataError('At least eight complete years are required.', 'INSUFFICIENT_DATA', 422)
    requested = investigation['period']
    expected_years = list(range(int(requested['requested_start']), int(requested['requested_end']) + 1))
    complete = set(complete_years)
    month_data: dict[int, dict[int, float]] = defaultdict(dict)
    for obs in observations:
        if obs.year not in complete:
            continue
        if obs.month in month_data[obs.year]:
            raise DataError('Duplicate year/month observation.', 'DUPLICATE_MONTH', 422)
        value = float(obs.value)
        if variable == 'PRECTOTCORR':
            value *= calendar.monthrange(obs.year, obs.month)[1]
        if not math.isfinite(value):
            raise DataError('Nonfinite NASA observation.', 'INVALID_SERIES', 422)
        month_data[obs.year][obs.month] = value
    if any(len(month_data[year]) != 12 for year in complete_years):
        raise DataError('Missing monthly values within a complete annual record.', 'INVALID_SERIES', 422)

    baseline_years = complete_years[:min(10, len(complete_years))]
    months = []
    raw_p = []
    monthly_baselines: dict[int, float] = {}
    for month in range(1, 13):
        vals = np.asarray([month_data[year][month] for year in complete_years], dtype=float)
        yrs = np.asarray(complete_years, dtype=float)
        baseline = float(np.mean([month_data[year][month] for year in baseline_years]))
        monthly_baselines[month] = baseline
        stats = _month_trend(yrs, vals)
        raw_p.append(stats['p_value_hac'])
        months.append({
            'month': month, 'name': calendar.month_abbr[month],
            'sample_size': len(vals), 'baseline_mean': round(baseline, 5),
            'observed_mean': round(float(vals.mean()), 5),
            'first_value': round(float(vals[0]), 5),
            'last_value': round(float(vals[-1]), 5),
            'unit': '°C' if variable == 'T2M' else 'mm/month',
            'trend_unit': '°C/decade' if variable == 'T2M' else 'mm/month/decade',
            **stats,
        })
    q_values = benjamini_hochberg(raw_p)
    for month, q in zip(months, q_values):
        month['q_value_bh'] = q
        month['fdr_flag_exploratory'] = bool(q is not None and q < 0.05)

    matrix = []
    for year in expected_years:
        cells = []
        for month in range(1, 13):
            if year in complete:
                value = month_data[year][month]
                cells.append({'month': month, 'value': round(value, 5),
                              'departure': round(value - monthly_baselines[month], 5)})
            else:
                cells.append({'month': month, 'value': None, 'departure': None})
        matrix.append({'year': year, 'complete': year in complete, 'months': cells})

    estimable = [p for p in months if p['slope_per_decade'] is not None]
    strongest = sorted(estimable, key=lambda p: abs(p['slope_per_decade']), reverse=True)
    numeric_matrix = [abs(cell['departure']) for row in matrix for cell in row['months'] if cell['departure'] is not None]
    finite_scale = max(numeric_matrix) if numeric_matrix else 0.0
    evidence = investigation['evidence']
    checksum = hashlib.sha256(json.dumps({
        'source_sha256': evidence['sha256_monthly'], 'complete_years': complete_years,
        'method_version': 'seasonal-signals-1.0', 'variable': variable,
    }, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    return {
        'module': 'Seasonal Signal Laboratory', 'version': '6.0.0',
        'location': investigation['location'], 'variable': investigation['variable'],
        'period': {'requested_start': requested['requested_start'], 'requested_end': requested['requested_end'],
                   'complete_years': len(complete_years), 'excluded_years': [y for y in expected_years if y not in complete]},
        'baseline': {'start_year': baseline_years[0], 'end_year': baseline_years[-1],
                     'number_of_years': len(baseline_years), 'type': 'Internal first-available-years baseline, NOT an official climate normal'},
        'months': months, 'matrix': matrix,
        'summary': {'fdr_flagged_months': sum(bool(p['fdr_flag_exploratory']) for p in months),
                    'strongest_absolute_slope_month': strongest[0]['month'] if strongest else None,
                    'maximum_absolute_departure': round(finite_scale, 5),
                    'multiplicity': 'Benjamini-Hochberg FDR correction across up to 12 estimable calendar-month exploratory HAC trend tests',
                    'interpretation': 'Flagging is exploratory and assumption-dependent; it is not attribution or a physical event diagnosis.'},
        'evidence': {'provider': 'NASA POWER', 'source_sha256_monthly': evidence['sha256_monthly'],
                     'source_url': evidence.get('source_request') or evidence.get('source_url'),
                     'seasonal_analysis_sha256': checksum, 'retrieved_at': evidence.get('retrieved_at'),
                     'generated_at': datetime.now(timezone.utc).isoformat(),
                     'aggregation': 'T2M = monthly mean °C; PRECTOTCORR = monthly mm/day multiplied by calendar days',
                     'method': 'Monthly OLS slope/HAC, Theil-Sen slope, BH correction across 12 tests'},
        'limitations': [
            'NASA POWER is gridded/model-derived point meteorology, not weather-station observations or a regional mean.',
            'Only complete 12-month calendar years enter each trend and baseline; excluded years are visible as missing heatmap rows.',
            'The baseline is an internal first-available-years reference, not an independent 30-year climate normal.',
            'Monthly OLS/HAC p-values and BH-adjusted q-values are exploratory and rely on serial-dependence and regression assumptions.',
            'FDR correction addresses these 12 tests only, not the wider set of comparisons throughout AETHERIS.',
            'Departures and monthly trends do not prove causes or forecast future climate.',
            'Precipitation monthly totals are estimated from NASA POWER monthly mean mm/day and calendar-month day counts.',
        ],
    }


async def run_seasonal_signals(lat: float, lon: float, start: int, end: int, variable: str) -> dict:
    validate_inputs(lat, lon, start, end, variable)
    observations, meta = await fetch_power(lat, lon, start, end, variable)
    investigation = investigate(observations, meta, variable, lat, lon, start, end)
    return analyze_seasonal_signals(investigation, observations)
