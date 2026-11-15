"""AETHERIS Evidence Briefing: deterministic narrative derived from paired NASA products.

No LLM output, fabricated observations, inferred causes, or invented confidence scores.
"""
from __future__ import annotations

import hashlib
import json
import math
from .systems import run_systems


def _signed(v: float | None, places: int = 2) -> str:
    if v is None or not math.isfinite(float(v)):
        return 'not available'
    return f'{float(v):+.{places}f}'


def _direction(value: float | None, positive: str, negative: str) -> str:
    if value is None or not math.isfinite(float(value)):
        return 'not estimable'
    if value > 0:
        return positive
    if value < 0:
        return negative
    return 'no estimated linear change'


def _evidence_label(p: float | None) -> str:
    if p is None or not math.isfinite(float(p)):
        return 'HAC test unavailable'
    return ('exploratory HAC evidence at the 5% threshold' if p < .05
            else 'no exploratory HAC evidence at the 5% threshold')


def build_briefing(paired: dict) -> dict:
    """Generate an auditable briefing from an already validated Earth Systems analysis."""
    years = paired['years']
    if not years:
        raise ValueError('Paired time series is empty')
    t = paired['metrics']['temperature']
    p = paired['metrics']['precipitation']
    tc = t['trend_per_decade']
    pc = p['trend_per_decade']
    era = paired['era_comparison']
    temp_early_late = era['temperature_change_c']
    rain_early_late = era['precipitation_change_mm']
    cases = [
        {
            'id': 'temperature', 'eyebrow': '01 / THERMAL SIGNAL',
            'title': 'Air temperature', 'unit': '°C / decade',
            'direction': _direction(tc, 'warming estimate', 'cooling estimate'),
            'trend_per_decade': tc, 'p_hac': t['exploratory_p_hac'],
            'assessment': _evidence_label(t['exploratory_p_hac']),
            'description': (f'Annual mean temperature has an estimated OLS change of {_signed(tc, 3)} °C per decade. '
                            'This is an estimate for a NASA POWER gridded point, not a measured city-wide average.'),
        },
        {
            'id': 'precipitation', 'eyebrow': '02 / HYDROLOGICAL SIGNAL',
            'title': 'Estimated precipitation', 'unit': 'mm / decade',
            'direction': _direction(pc, 'increasing estimate', 'decreasing estimate'),
            'trend_per_decade': pc, 'p_hac': p['exploratory_p_hac'],
            'assessment': _evidence_label(p['exploratory_p_hac']),
            'description': (f'Estimated annual precipitation totals have an OLS change of {_signed(pc, 2)} mm per decade. '
                            'Monthly mm/day rates are day-weighted to annual millimetres.'),
        },
    ]
    # Compare paired first/last balanced halves, not arbitrary decade labels.
    contrast = {
        'early': era['early_years'], 'late': era['late_years'],
        'temperature_change_c': temp_early_late,
        'precipitation_change_mm': rain_early_late,
        'excluded_middle_year': era['excluded_middle_year'],
        'interpretation': 'Difference between balanced early and late groups, descriptive; not independent proof of causation or significance.',
    }
    flags = paired['joint_deviations']
    source = paired['evidence']
    fingerprint = hashlib.sha256(json.dumps({
        'parent': source['paired_sha256'], 'years': [row['year'] for row in years],
        'version': 'evidence-briefing-v1'
    }, sort_keys=True).encode()).hexdigest()
    return {
        'title': 'Evidence Briefing', 'version': '9.0.0',
        'location': paired['location'], 'period': paired['period'],
        'source': 'NASA POWER', 'product_type': 'gridded / model-derived point data',
        'findings': cases, 'contrast': contrast,
        'association': paired['association'],
        'joint_flags': {'count': flags['count'], 'years': flags['years'],
                        'definition': flags['definition']},
        'baseline': paired['baseline'], 'observations': years,
        'annual_inputs': paired.get('annual_inputs', {}),
        'evidence': {**source, 'briefing_sha256': fingerprint},
        'limitations': paired['limitations'] + [
            'The story is generated deterministically from numerical outputs, not by a trained AI model.',
            'Exploratory p-values for multiple signals are not corrected for multiple testing in this view.',
            'Differences between individual years are descriptive and do not establish a climate trend.',
        ],
    }


async def run_briefing(lat: float, lon: float, start: int, end: int) -> dict:
    return build_briefing(await run_systems(lat, lon, start, end))
