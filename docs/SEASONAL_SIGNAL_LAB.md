# Seasonal Signal Laboratory — Scientific Methods

## Purpose

To investigate how a historical monthly series changes by **calendar month**, rather than masking differences in annual means. NASA POWER monthly point products are the only live inputs.

## Input and aggregation

The `/api/v1/seasonal-signals` endpoint accepts `lat`, `lon`, `start`, `end` and `variable`. Only validated `T2M` and `PRECTOTCORR` are supported. The existing NASA POWER adapter retrieves actual monthly data and verifies NASA-provided units and coverage. `T2M` retains Celsius monthly mean values. `PRECTOTCORR` is the NASA monthly mean precipitation rate in mm/day multiplied by the actual calendar-month days to estimate mm/month (including leap years).

Only calendar years containing all twelve verified monthly values enter the trend analysis. Missing or partial calendar years are excluded, and full-year gaps appear as unavailable rows in the heatmap. There is **no interpolation or model-generated filling**.

## Trend calculations

Each month has a series of annual values: for example January of 2001, January of 2002, etc. Ordinary least squares is used to estimate a month-specific linear slope, scaled per decade. The regression uses centered calendar years, with HAC/Newey–West exploratory standard errors and lag length consistent with the existing scientific core. A Theil–Sen slope provides a robust descriptive comparison.

There are up to **12 estimable exploratory statistical comparisons** (one per calendar month). Constant or otherwise untestable series have no p-value and are excluded from the adjustment. The valid p-values are adjusted with Benjamini–Hochberg's step-up procedure, producing q-values; the interface flags q < 0.05 as exploratory only. The analysis does not claim independent significance for other AETHERIS modules; tests across locations and additional hypotheses would require a broader correction. The FDR procedure assumes the individual p-values are meaningful. Autocorrelation, non-stationarity, model error and other assumptions may invalidate formal interpretations. A constant series has no meaningful p-value and no significance flag.

## Calendar-month anomaly heatmap

For each month, the baseline is the mean of values from the **first up to ten complete calendar years of the requested period**. This is a transparent internal comparison, **not** an independent 30-year climate normal. A cell is `observed monthly value - month-specific baseline`. For precipitation, both values are in estimated mm/month. Missing cells are disabled and identified rather than filled.

The heatmap scale uses the largest absolute source-derived departure in the returned series; this is a visual relative intensity scale and **not** a standardized anomaly classification.

## Scientific evidence and reproducibility

Each result records a source-data SHA-256 fingerprint, input location/range, NASA POWER request, month-level sample sizes and estimates, method version, baseline definition, known limitations and an additional derived manifest digest. The fingerprint proves the data payload representation has not changed; it does not establish scientific correctness.

The API JSON is the source for charts, diagnostics, and exports. The UI creates no climate measurements client-side.

## Limitations

- NASA POWER is gridded/model-derived point data, not direct station measurements or an administrative-region average.
- The method does not attribute a change to greenhouse gases or any other cause.
- The lab does not forecast temperatures or rainfall or diagnose specific extreme events.
- The BH adjustment covers only twelve calendar-month tests, not the entire app's exploratory hypotheses.
- Live NASA availability depends on a working internet connection. Network failures must show explicit errors.

## Validate locally

Run `Run_AETHERIS_Tests.bat` to execute the deterministic science and API tests, then `Verify_Live_NASA.bat` to check NASA connectivity. From a running application, open **Seasonal signal lab** and run a historical investigation. The browser screen requires manual validation on Windows if automated browser testing is unavailable.
