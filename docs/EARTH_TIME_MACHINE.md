# Earth Time Machine — AETHERIS 8.0

## Purpose

Explore **observed/model-derived annual anomalies**, at **nine discrete NASA POWER sampling points** in a 3 × 3 grid, as a function of year. The point grid is oriented north-up. It is **not** a continuous raster or a NASA satellite image.

## Sources and reproducibility

- Source: NASA POWER monthly point endpoint (`/api/temporal/monthly/point`), queried independently for each of nine points.
- Variables: `T2M` and `PRECTOTCORR` (when NASA reports valid results).
- Sample spacing: nominal 50 / 100 / 150 km using a latitude-adjusted longitude approximation; nearest underlying POWER grid cells may overlap.
- Each successful point contains the original source provider, response source/request URLs when available, retrieval timestamp, observation count and a SHA-256 fingerprint of the chronologically ordered monthly observations.
- The full JSON export contains **each point's complete annual data and every year snapshot**, not simply rendered card values.
- CSV export contains nine rows per year; null values remain empty, never zero-filled.

## Computation

1. Parse and validate NASA monthly values. Reject invalid units and missing-value sentinels.
2. Annualize only years containing all 12 monthly values. `T2M`: calendar-day-weighted annual mean (°C). `PRECTOTCORR`: sum over 12 monthly mean rates multiplied by days per calendar month (annual total, mm).
3. Reference interval: the **first ten calendar years of the requested period** (for example 2001–2010 if the request starts in 2001). At least eight reference years must be complete at each point. A point missing too many reference years becomes **unavailable**.
4. Reference value at point *i*: mean of available complete annual values within those ten reference years.
5. For point *i*, year *t*: **annual anomaly(i,t) = annual observation(i,t) − reference mean(i)**. No gap filling or spatial interpolation.
6. Frame summary: number of available points, median of valid point anomalies, number positive, center-point anomaly. These are *descriptive* statistics, not independently sampled area estimates.
7. Interface colors use one shared, symmetric absolute magnitude scale computed over every valid annual point anomaly for the entire investigation. Scrubbing the timeline does not silently rescale colors.

## Endpoint

`GET /api/v1/time-machine?lat=32.337&lon=-6.349&start=2001&end=2025&variable=T2M&spacing_km=100`

Inputs are validated with the existing NASA adapter rules and a minimum of 12 historical years.

Output: `points[]` with independently measured annual series and evidence; `snapshots[]` with annual nine-cell frames; `baseline`, `grid`, `limitations`, source details.

## Interpretive limitations

- NASA POWER is a gridded reanalysis/model-derived meteorological product. No direct station measurements are claimed.
- The reference uses **ten years**, not a 30-year WMO climate normal. All samples use the same reference calendar window but each point has a separate reference mean.
- Adjacent point queries may correspond to the same underlying POWER grid cell; nine points must not be interpreted as independent regional evidence.
- Point anomalies and color changes are **not statistical significance tests**, forecasts, drought classifications, satellite pixels, or evidence of causal drivers.
- Missing annual values and unavailable source points are explicitly shown as missing.

## Verification

`pytest -q tests/test_time_machine.py tests/test_v8_ui_integrity.py`

Tests use *explicitly synthetic, in-memory NASA response fixtures*. Successful fixture tests do not prove live NASA connectivity, browser rendering in all environments, or source availability. A complete live end-to-end test must be conducted on the developer machine.
