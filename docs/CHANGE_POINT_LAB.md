# Change-Point Laboratory — scientific methodology (v7)

## Purpose

AETHERIS 7.0 adds a careful **exploratory continuous trend-shift comparison**. It does **not** claim a NASA-confirmed climate regime change. It contrasts a single linear fit and a continuous two-slope fit evaluated across eligible observed years, using **NASA POWER gridded point** time series and the same annual aggregation as AETHERIS's established Scientific Engine.

## Reproducible calculation

For a complete-year annual value `y_t` and elapsed time in decades `x_t`:

- Linear null: `y_t = beta0 + beta1 * x_t + residual_t`.
- Candidate hinge: `y_t = beta0 + beta1*x_t + beta2*max(0, x_t - x_break) + residual_t`.
- The candidate represents a *continuous* slope change, not an abrupt value jump.
- Estimated slope before the candidate is `beta1` per decade; after it is `beta1 + beta2` per decade.
- Candidate break years are taken **only from existing complete annual observations**. Each side must contain at least the chosen minimum number of complete years (default 6).
- For fixed candidate fits, the information score is `BIC = n*ln(RSS/n) + k*ln(n)`, with `k=2` for linear and `k=3` for the hinge fit. A tiny deterministic residual floor prevents false score differences for exact linear/constant series.
- `ΔBIC = BIC_linear - BIC_piecewise`. Positive values favor the more flexible fit, descriptively. Reported categories (`>=6`, `2–6`, `<2`) are **heuristics**, not statistically calibrated change-point thresholds.
- The model scans across all eligible candidate years and reports the best BIC candidate. A leave-one-year-out *descriptive* sensitivity analysis repeats the scan and reports the fraction of selected years within ±2 calendar years of the original candidate.

## Interpretation rules

- Selecting the break from the same data invalidates a naive single-break p-value; AETHERIS deliberately reports **no formal change-point significance**.
- BIC penalizes the third slope coefficient, but this simple comparison **does not fully penalize the search over break years**. Thus apparent model preference is not calibrated evidence for a regime shift.
- Serial dependence, observational uncertainty, other nonlinearity, missing calendar years and external forcing can influence the candidate.
- The apparent slope difference is historical curve fitting, **not** a forecast, an explanation of causal drivers, or an attribution of climatic change.
- Future validation could include a null-calibrated block bootstrap or independent testing, but it must retain explicit assumptions about dependence, multiple testing and gridded data quality.

## Data integrity and provenance

The API response contains all annual observations, fitted linear and piecewise values, candidate rankings, source NASA data fingerprint, method/version fingerprint, excluded incomplete years, missing complete-year gaps, limitations and the original provider URL. CSV export includes the observed annual series and two fitted series; JSON export retains the full evidence.

## Endpoint

`GET /api/v1/change-points?lat=32.337&lon=-6.349&start=1990&end=2025&variable=T2M&min_segment_years=6`

Parameters are bounded and validated. The client never supplies a remote data-source URL. Upstream NASA requests are handled by the existing secure NASA connector. The endpoint returns an explicit error if there are insufficient complete years.

## Development validation

Synthetic test fixtures include a known continuous slope shift, exact linear series, constant series, reversed trend, missing complete years, precipitation annual units and deterministic evidence hashes. API responses are tested with mocked NASA inputs; they are **not** evidence of a live NASA request. Desktop/mobile interface checks also use explicitly fixture-backed data, not live NASA measurements.
