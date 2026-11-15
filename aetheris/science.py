"""Reproducible annual Earth-system trend estimation.

Statistical interpretation is careful: a trend estimate and a significance
assessment are distinct. Annual OLS inference uses HAC (Newey-West) robust
standard errors to partly account for short-range serial dependence; this
is exploratory, not attribution of climatic causes.
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
from scipy.stats import theilslopes, kendalltau

from .nasa import Observation, DataError, PARAMETERS
from .quality_passport import build_quality_passport


def annualize(observations: list[Observation], variable: str) -> tuple[list[dict], list[int]]:
    by_year = defaultdict(dict)
    for p in observations:
        if p.month in by_year[p.year]:
            raise DataError("Duplicate month encountered during annual aggregation.", "DUPLICATE_MONTH")
        by_year[p.year][p.month] = p.value
    annual, excluded = [], []
    for year in sorted(by_year):
        months = by_year[year]
        if len(months) != 12:
            excluded.append(year)
            continue
        days = [calendar.monthrange(year, m)[1] for m in range(1, 13)]
        if variable == "T2M":
            value = sum(months[m] * days[m - 1] for m in range(1, 13)) / sum(days)
        elif variable == "PRECTOTCORR":
            # POWER PRECTOTCORR monthly rate is mm/day: multiply by calendar days.
            value = sum(months[m] * days[m - 1] for m in range(1, 13))
        else:
            raise DataError("Unsupported annual aggregation.", "UNSUPPORTED_VARIABLE")
        annual.append({"year": year, "value": round(float(value), 5)})
    return annual, excluded


def trend_analysis(annual: list[dict], variable: str) -> dict:
    if len(annual) < 8:
        raise DataError("At least 8 complete calendar years are required for this investigation.", "INSUFFICIENT_DATA", 422)
    years = np.asarray([float(p["year"]) for p in annual], dtype=float)
    values = np.asarray([float(p["value"]) for p in annual], dtype=float)
    if len(set(years)) != len(years) or not np.isfinite(values).all():
        raise DataError("Invalid annual time series.", "INVALID_SERIES", 422)
    # Avoid floating-point false positives in exact/near-constant observations.
    # An OLS p-value on a series with zero variance has no useful interpretation.
    if float(np.ptp(values)) < 1e-10:
        unit = "°C/decade" if variable == "T2M" else "mm/decade"
        return {
            "method": "Annual OLS with HAC (Newey–West) robust standard errors",
            "sample_size": len(annual), "start_year": int(years.min()), "end_year": int(years.max()),
            "slope_per_year": 0.0, "slope_per_decade": 0.0,
            "slope_unit": unit, "annual_unit": PARAMETERS[variable]["annual_unit"],
            "observed_net_difference": 0.0, "modeled_total_change": 0.0,
            "p_value_hac": None, "ci95_hac_per_decade": [0.0, 0.0],
            "significance_label": "insufficient evidence",
            "significance_assumptions": "Constant series: a statistical test of a nonzero trend is not meaningful.",
            "r_squared": None, "residual_lag1": None, "theil_sen_per_decade": 0.0,
            "theil_sen_ci95_per_decade": [0.0, 0.0],
            "kendall_tau_exploratory": None, "kendall_p_exploratory": None,
            "fitted": [{"year": int(y), "value": float(values[0])} for y in years],
        }
    x = years - years.mean()
    fit = sm.OLS(values, sm.add_constant(x)).fit(cov_type="HAC", cov_kwds={"maxlags": min(3, max(1, len(years) // 10))})
    slope = float(fit.params[1]); intercept = float(fit.params[0])
    se = float(fit.bse[1]); p_value = float(fit.pvalues[1])
    ci = np.asarray(fit.conf_int(alpha=0.05))[1, :] * 10
    fitted = [float(v) for v in fit.predict(sm.add_constant(x))]
    residuals = values - fitted
    residual_lag1 = float(np.corrcoef(residuals[:-1], residuals[1:])[0, 1]) if len(years) >= 5 and np.std(residuals) > 1e-8 else None
    robust = theilslopes(values, years, alpha=0.95)
    tau, tau_p = kendalltau(years, values)
    if not (math.isfinite(se) and math.isfinite(p_value)):
        p_value = None
    significance = "insufficient evidence" if p_value is None else ("significant" if p_value < 0.05 else "not significant")
    return {
        "method": "Annual OLS with HAC (Newey–West) robust standard errors",
        "sample_size": len(annual), "start_year": int(years.min()), "end_year": int(years.max()),
        "slope_per_year": round(slope, 6), "slope_per_decade": round(slope * 10, 5),
        "slope_unit": "°C/decade" if variable == "T2M" else "mm/decade",
        "annual_unit": PARAMETERS[variable]["annual_unit"],
        "observed_net_difference": round(float(values[-1] - values[0]), 5),
        "modeled_total_change": round(slope * (years[-1] - years[0]), 5),
        "p_value_hac": round(p_value, 8) if p_value is not None else None,
        "ci95_hac_per_decade": [round(float(ci[0]), 5), round(float(ci[1]), 5)] if np.isfinite(ci).all() else None,
        "significance_label": significance,
        "significance_assumptions": "Exploratory HAC-robust OLS inference (two-sided, alpha=0.05); not attribution of cause. Very long memory, structural breaks and multiple comparisons can invalidate simple interpretations.",
        "r_squared": round(float(fit.rsquared), 5) if math.isfinite(float(fit.rsquared)) else None,
        "residual_lag1": round(residual_lag1, 3) if residual_lag1 is not None and math.isfinite(residual_lag1) else None,
        "theil_sen_per_decade": round(float(robust.slope) * 10, 5),
        "theil_sen_ci95_per_decade": [round(float(robust.low_slope) * 10, 5), round(float(robust.high_slope) * 10, 5)],
        "kendall_tau_exploratory": round(float(tau), 4) if math.isfinite(float(tau)) else None,
        "kendall_p_exploratory": round(float(tau_p), 6) if math.isfinite(float(tau_p)) else None,
        "fitted": [{"year": int(y), "value": round(v, 5)} for y, v in zip(years, fitted)],
    }


def seasonal_profile(observations: list[Observation], variable: str) -> dict:
    """Monthly climatology over the selected data, not an official 30-year normal.

    For precipitation the monthly POWER mm/day rate is converted to an estimated
    monthly total for each calendar month before averaging across years.
    """
    by_month = defaultdict(list)
    for obs in observations:
        days = calendar.monthrange(obs.year, obs.month)[1]
        value = obs.value if variable == 'T2M' else obs.value * days
        by_month[obs.month].append(value)
    profile = []
    for month in range(1, 13):
        vals = by_month.get(month, [])
        if vals:
            profile.append({'month':month,'label':calendar.month_abbr[month],
                            'mean':round(float(np.mean(vals)),5),
                            'min':round(float(min(vals)),5),'max':round(float(max(vals)),5),
                            'samples':len(vals)})
    return {'months':profile,'unit':'°C' if variable == 'T2M' else 'mm/month',
            'method':'Monthly mean across available years in the selected period',
            'limitation':'This within-sample seasonal profile is not an independent 30-year climate normal.'}


def unusual_years(annual: list[dict], baseline: float) -> list[dict]:
    """Largest annual departures from an explicitly documented local baseline.

    These are descriptive rankings, not trained AI predictions or statistically
    verified extreme events.
    """
    return [{'year':x['year'],'departure':round(x['value']-baseline,5), 'annual_value':x['value']}
            for x in sorted(annual,key=lambda x:abs(x['value']-baseline),reverse=True)[:4]]


def investigate(observations: list[Observation], meta: dict, variable: str, lat: float, lon: float, start: int, end: int) -> dict:
    annual, excluded = annualize(observations, variable)
    trend = trend_analysis(annual, variable)
    baseline = annual[:min(len(annual), 10)]
    baseline_mean = float(np.mean([p["value"] for p in baseline]))
    anomalies = [{"year": p["year"], "value": round(p["value"] - baseline_mean, 5)} for p in annual]
    source_data = [{"year": p.year, "month": p.month, "value": p.value} for p in observations]
    checksum = hashlib.sha256(json.dumps(source_data, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    messages = [
        "Association does not establish causation or attribution to a particular driver.",
        "NASA POWER is a gridded meteorological product, not a weather station reading.",
        "Statistical significance describes evidence under stated assumptions, not practical impact.",
    ]
    if excluded:
        messages.append(f"Excluded incomplete calendar years: {', '.join(map(str, excluded))}.")
    if len(annual) < 15:
        messages.append("Short annual series: treat significance estimates as preliminary.")
    if meta.get("missing_or_unavailable_months", 0):
        messages.append("Some requested months were missing or unavailable; annual aggregation excludes incomplete years.")
    return {
        "app": "AETHERIS", "analysis_version": "2.1.0",
        "location": {"latitude": lat, "longitude": lon},
        "variable": {"id": variable, **PARAMETERS[variable]},
        "period": {"requested_start": start, "requested_end": end,
                   "observed_start": annual[0]["year"], "observed_end": annual[-1]["year"]},
        "monthly": [p.as_dict() for p in observations],
        "annual": annual, "trend": trend,
        "quality_passport": build_quality_passport(annual, trend, meta, start, end, excluded, checksum, observations),
        "anomalies": anomalies,
        "seasonality": seasonal_profile(observations, variable),
        "unusual_years": unusual_years(annual,baseline_mean),
        "anomaly_baseline": {"start_year": baseline[0]["year"], "end_year": baseline[-1]["year"],
                             "mean": round(baseline_mean, 4), "note": "First up to ten complete years of the selected period; not a standard climate normal."},
        "quality": {"complete_years": len(annual), "incomplete_years_excluded": excluded,
                    "valid_months": len(observations), "warnings": messages},
        "evidence": {"sha256_monthly": checksum, "retrieved_at": meta.get("retrieved_at", ""),
                     "provider": meta.get("source", "NASA POWER"),
                     "product": meta.get("source_product", "NASA POWER monthly"),
                     "source_url": meta.get("source_url", ""),
                     "source_request": meta.get("source_request", ""),
                     "monthly_unit": meta.get("monthly_unit", ""),
                     "annual_aggregation": ("Day-weighted average of monthly air temperature" if variable == "T2M" else "Sum of monthly precipitation rate multiplied by calendar days"),
                     "cache": meta.get("cache", ""),
                     "science_method": trend["method"], "analysis_version": "2.1.0"},
        "limitations": messages,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
