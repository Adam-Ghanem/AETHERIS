"""Transparent diagnostic checks for point-scale annual NASA POWER investigations.

This is a *quality passport*, not a confidence score or formal validation of
climate attribution. All flags are interpretable diagnostics, not guarantees.
"""
from __future__ import annotations

import math
from typing import Any

from .nasa import Observation

import numpy as np


def _direction(slope: float, *, tol: float = 1e-10) -> str:
    return "increasing" if slope > tol else "decreasing" if slope < -tol else "flat"


def _ols_slope_decade(years: np.ndarray, values: np.ndarray) -> float:
    x = years - float(np.mean(years))
    denominator = float(np.sum(x * x))
    if denominator <= 0:
        return 0.0
    return 10.0 * float(np.sum(x * (values - float(np.mean(values)))) / denominator)


def build_quality_passport(annual: list[dict], trend: dict, meta: dict,
                           start: int, end: int, excluded_years: list[int],
                           source_checksum: str, observations: list[Observation]) -> dict[str, Any]:
    """Report completeness, agreement and single-year influence independently.

    Uses actual calendar years, including non-consecutive observations. `meta`
    must originate from the NASA response parser; no new network calls occur.
    """
    if len(annual) < 8:
        raise ValueError("Quality passport needs at least eight complete annual values.")
    years = np.asarray([int(row["year"]) for row in annual], dtype=float)
    values = np.asarray([float(row["value"]) for row in annual], dtype=float)
    if not (np.isfinite(values).all() and np.isfinite(years).all()) or len(np.unique(years)) != len(years):
        raise ValueError("Quality passport requires a finite unique-year series.")
    expected_months = 12 * (end - start + 1)
    # Use the actual scientific observations as source-of-truth, not an easily
    # stale provider metadata count. The parser validates uniqueness upstream.
    valid_months = len({(p.year, p.month) for p in observations if start <= p.year <= end and 1 <= p.month <= 12})
    valid_months = max(0, min(valid_months, expected_months))
    complete = len(annual)
    requested_years = end - start + 1
    missing_whole = sorted(set(range(start, end + 1)) - {int(y) for y in years})
    present = {(p.year, p.month) for p in observations}
    coverage_matrix = [{"year": y, "months": [(y, m) in present for m in range(1, 13)]}
                       for y in range(start, end + 1)]
    omitted_slopes = []
    for i, year in enumerate(years):
        remain = np.arange(len(years)) != i
        slope = _ols_slope_decade(years[remain], values[remain])
        omitted_slopes.append({"omitted_year": int(year), "slope_per_decade": round(slope, 6)})
    original = float(trend["slope_per_decade"])
    most_influential = max(omitted_slopes, key=lambda row: abs(row["slope_per_decade"] - original))
    omitted_directions = sorted({_direction(p["slope_per_decade"]) for p in omitted_slopes})
    direction_stable = len(omitted_directions) == 1 and omitted_directions[0] == _direction(original)
    robust = float(trend["theil_sen_per_decade"])
    align = _direction(original) == _direction(robust)
    lag1 = trend.get("residual_lag1")
    serial_note = ("Residual lag-1 not estimable for this series." if lag1 is None else
                   "Residual lag-1 correlation is substantial; interpret trend p-values carefully." if abs(float(lag1)) >= .3 else
                   "Residual lag-1 correlation is below an illustrative |0.30| review threshold; dependence is not ruled out.")
    checks = [
        {"id": "coverage", "label": "Monthly source coverage",
         "state": "complete" if valid_months == expected_months else "review",
         "value": f"{valid_months}/{expected_months} months",
         "detail": "Observed/valid monthly records relative to the requested calendar period."},
        {"id": "years", "label": "Complete annual records",
         "state": "complete" if complete == requested_years else "review",
         "value": f"{complete}/{requested_years} years",
         "detail": "Only years with twelve usable months enter the trend estimation."},
        {"id": "method", "label": "OLS vs Theil–Sen direction",
         "state": "consistent" if align else "review",
         "value": "Same direction" if align else "Different directions",
         "detail": "Method agreement is a diagnostic, not independent proof of a true trend."},
        {"id": "influence", "label": "Leave-one-year-out direction",
         "state": "consistent" if direction_stable else "review",
         "value": "Stable" if direction_stable else "Sensitive",
         "detail": "OLS is refitted after omitting each complete year in turn."},
        {"id": "dependence", "label": "Residual serial dependence",
         "state": "review" if lag1 is not None and abs(float(lag1)) >= .3 else "informational",
         "value": "Not estimated" if lag1 is None else f"lag-1 = {float(lag1):+.3f}",
         "detail": serial_note},
    ]
    return {
        "schema_version": "1.0.0", "title": "Scientific Quality Passport",
        "provider": meta.get("source", "NASA POWER"),
        "source_sha256_monthly": source_checksum,
        "period": {"start": start, "end": end},
        "coverage": {"valid_months": valid_months, "expected_months": expected_months,
                     "monthly_percent": round(100 * valid_months / expected_months, 2),
                     "complete_years": complete, "requested_years": requested_years,
                     "complete_annual_percent": round(100 * complete / requested_years, 2),
                     "excluded_or_unavailable_years": missing_whole,
                     "monthly_matrix": coverage_matrix},
        "method_agreement": {"ols_per_decade": round(original, 6),
                             "theil_sen_per_decade": round(robust, 6),
                             "same_direction": align},
        "influence": {"direction_stable": direction_stable,
                      "minimum_slope_per_decade": min(p["slope_per_decade"] for p in omitted_slopes),
                      "maximum_slope_per_decade": max(p["slope_per_decade"] for p in omitted_slopes),
                      "most_influential_omitted_year": most_influential,
                      "leave_one_out": omitted_slopes},
        "residual_lag1": lag1,
        "checks": checks,
        "review_required": any(c["state"] == "review" for c in checks),
        "limitations": [
            "Diagnostic flags are descriptive, not a grade, a validation certificate, or a probability that climate change occurred.",
            "Theil–Sen/OLS agreement and single-year stability do not correct for all climate variability, model bias or observation error.",
            "The lag-1 review threshold is an illustrative heuristic, not a formal independence test.",
            "NASA POWER values are gridded meteorological products, not direct point-station measurements.",
            "Any HAC p-value elsewhere in AETHERIS is exploratory and subject to model assumptions; these checks do not replace attribution studies.",
        ],
    }
