"""Exploratory continuous piecewise-linear trend diagnostics for NASA time series.

Candidate years are searched on the *same* annual sample as the linear null model.
BIC accounts for one additional slope coefficient but **not** for the adaptive
search across break years. Consequently delta BIC is a descriptive model
selection score, NOT a formal change-point p-value or proof of a regime shift.
"""
from __future__ import annotations

import hashlib
import json
import math

import numpy as np

from .nasa import DataError

SCHEMA_VERSION = '1.0.0'


def _rounded(value: float, places: int = 5) -> float:
    return round(float(value), places)


def _regress(years: np.ndarray, values: np.ndarray, year: int | None = None):
    """Fit OLS against elapsed decades; optional continuous hinge at year."""
    elapsed = (years - years[0]) / 10.0
    columns = [np.ones(len(years)), elapsed]
    if year is not None:
        columns.append(np.maximum((years - year) / 10.0, 0.0))
    matrix = np.column_stack(columns)
    coefs, _, rank, _ = np.linalg.lstsq(matrix, values, rcond=None)
    if rank != matrix.shape[1]:
        raise DataError('Time series is not suitable for breakpoint regression.', 'INVALID_SERIES', 422)
    fit = matrix @ coefs
    residual = values - fit
    sse = float(np.dot(residual, residual))
    return coefs, fit, sse


def _bic(sse: float, n: int, k: int, floor: float) -> float:
    return n * math.log(max(sse, floor) / n) + k * math.log(n)


def _scan(years: np.ndarray, values: np.ndarray, min_segment_years: int):
    """Find best candidate among observed years with enough points on both sides."""
    n = len(years)
    linear_coeff, linear_fit, linear_sse = _regress(years, values)
    # Numerical floor prevents illusory breakpoints for perfectly linear samples.
    floor = max(1e-18, n * max(1.0, float(np.max(np.abs(values)))) ** 2 * 1e-20)
    linear_bic = _bic(linear_sse, n, 2, floor)
    candidates = []
    for knot in years:
        left = int(np.count_nonzero(years <= knot))
        right = n - left
        if left < min_segment_years or right < min_segment_years:
            continue
        coeff, fitted, sse = _regress(years, values, int(knot))
        bic = _bic(sse, n, 3, floor)
        candidates.append({
            'year': int(knot),
            'left_years': left,
            'right_years': right,
            'bic': bic,
            'delta_bic_vs_linear': linear_bic - bic,
            'slope_before_per_decade': float(coeff[1]),
            'slope_after_per_decade': float(coeff[1] + coeff[2]),
            'fitted': fitted,
            'sse': sse,
        })
    if not candidates:
        raise DataError('Insufficient complete years for both sides of a candidate breakpoint.', 'INSUFFICIENT_DATA', 422)
    best = min(candidates, key=lambda c: (c['bic'], c['year']))
    return linear_coeff, linear_fit, linear_sse, linear_bic, candidates, best


def analyze_change_points(investigation: dict, *, min_segment_years: int = 6) -> dict:
    """Compare a continuous slope-change model with one straight line.

    Input is an ordinary AETHERIS investigation produced from NASA POWER.
    Only complete years from the validated annual observations are used.
    """
    if not isinstance(min_segment_years, int) or not 5 <= min_segment_years <= 10:
        raise DataError('Minimum years per segment must be between 5 and 10.', 'INVALID_SEGMENT_LENGTH', 422)
    annual = investigation['annual']
    if len(annual) < max(14, min_segment_years * 2 + 2):
        raise DataError('Change-Point Lab requires at least 14 complete years and enough data in both segments.', 'INSUFFICIENT_DATA', 422)
    years = np.asarray([float(p['year']) for p in annual])
    values = np.asarray([float(p['value']) for p in annual])
    if (not np.isfinite(years).all() or not np.isfinite(values).all()
        or not np.all(np.diff(years) > 0)
        or not np.all(np.equal(np.mod(years, 1), 0))):
        raise DataError('Annual values must be finite with unique ascending integer years.', 'INVALID_SERIES', 422)
    coeff, fitted_linear, sse_linear, bic_linear, candidates, best = _scan(years, values, min_segment_years)
    delta = float(best['delta_bic_vs_linear'])
    near_constant = float(np.ptp(values)) < 1e-9
    if near_constant:
        preference = 'no_detectable_variation'
    elif delta >= 6:
        preference = 'piecewise_preferred_exploratory'
    elif delta >= 2:
        preference = 'weak_piecewise_preference'
    else:
        preference = 'linear_adequate'

    # A separate descriptive leave-one-year-out scan; NOT an uncertainty interval.
    picked = []
    for index in range(len(years)):
        reduced_years = np.delete(years, index)
        reduced_values = np.delete(values, index)
        try:
            *_, reduced_best = _scan(reduced_years, reduced_values, min_segment_years)
            picked.append(int(reduced_best['year']))
        except DataError:
            pass
    nearby = sum(abs(yr - int(best['year'])) <= 2 for yr in picked)
    stability_rate = nearby / len(picked) if picked else None
    modeled = best['fitted']
    missing_years = sorted(set(range(int(years[0]), int(years[-1]) + 1)) - set(years.astype(int)))
    evidence = investigation['evidence']
    fingerprint = hashlib.sha256(json.dumps({
        'annual': annual, 'source_sha256': evidence['sha256_monthly'],
        'min_segment_years': min_segment_years, 'method_version': SCHEMA_VERSION,
    }, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    return {
        'schema_version': SCHEMA_VERSION,
        'type': 'exploratory_continuous_trend_change',
        'location': investigation['location'],
        'variable': investigation['variable'],
        'period': investigation['period'],
        'settings': {'min_complete_years_per_side': min_segment_years,
                     'candidate_selection': 'observed year with >= min complete years before/at knot and after knot',
                     'model': 'continuous OLS hinge regression; BIC uses 2 vs 3 coefficients'},
        'annual_observations': annual,
        'linear': {
            'slope_per_decade': _rounded(coeff[1]),
            'bic': _rounded(bic_linear),
            'sse': _rounded(sse_linear, 9),
            'fitted': [{'year': int(y), 'value': _rounded(z)} for y,z in zip(years, fitted_linear)],
        },
        'best_candidate': {
            'year': int(best['year']),
            'bic': _rounded(best['bic']),
            'delta_bic_vs_linear': _rounded(delta),
            'slope_before_per_decade': _rounded(best['slope_before_per_decade']),
            'slope_after_per_decade': _rounded(best['slope_after_per_decade']),
            'left_years': best['left_years'], 'right_years': best['right_years'],
            'fitted': [{'year': int(y), 'value': _rounded(z)} for y,z in zip(years, modeled)],
        },
        'candidate_scores': [{
            'year': c['year'], 'delta_bic_vs_linear': _rounded(c['delta_bic_vs_linear']),
            'slope_before_per_decade': _rounded(c['slope_before_per_decade']),
            'slope_after_per_decade': _rounded(c['slope_after_per_decade']),
            'left_years': c['left_years'], 'right_years': c['right_years'],
        } for c in candidates],
        'robustness': {
            'reruns': len(picked),
            'within_two_years_of_best': nearby,
            'within_two_years_fraction': _rounded(stability_rate, 3) if stability_rate is not None else None,
            'year_selected_when_omitting_one': [{'omitted_year': int(y), 'selected_year': z}
                                                  for y,z in zip(years.astype(int), picked)] if len(picked) == len(years) else [],
            'interpretation': 'Leave-one-year-out candidate stability is descriptive; not a confidence interval or predictive validation.',
        },
        'assessment': {
            'label': preference,
            'meaning': {
                'no_detectable_variation': 'No meaningful observed variation; do not interpret a fitted breakpoint.',
                'piecewise_preferred_exploratory': 'Piecewise model has appreciably lower BIC; candidate remains exploratory.',
                'weak_piecewise_preference': 'Some descriptive preference for a breakpoint, without strong model separation.',
                'linear_adequate': 'No persuasive BIC improvement over a single linear slope.',
            }[preference],
            'formal_change_point_significance_assessed': False,
        },
        'quality': {'complete_years': len(annual), 'gaps_in_complete_years': missing_years,
                    'incomplete_years_excluded': investigation['quality']['incomplete_years_excluded']},
        'evidence': {'source_sha256_monthly': evidence['sha256_monthly'],
                     'change_point_analysis_sha256': fingerprint,
                     'provider': evidence['provider'], 'source_url': evidence['source_url'],
                     'source_product': evidence.get('product', ''),
                     'aggregation': evidence['annual_aggregation'],
                     'analysis_version': SCHEMA_VERSION},
        'limitations': [
            'Break year was chosen after examining the same data; BIC comparison is exploratory, not a pre-specified hypothesis test.',
            'BIC here penalizes one extra slope parameter but does not fully account for searching multiple candidate years.',
            'No calibrated change-point p-value or claim of formally statistically significant regime shift is provided.',
            'Serial dependence, missing years, gridded-model uncertainty and sampling affect comparisons.',
            'A continuous hinge cannot represent an abrupt level jump; it models a change in trend rate.',
            'No breakpoint implies a proven cause of climate change or an out-of-sample forecast.',
        ],
    }
