# Scientific methodology and integrity

## Mission alignment

The official 2026 Earth System Trend Detective challenge asks for a tool that selects NASA Earth science variables, visualizes time series, quantifies change and evaluates significance. AETHERIS directly implements those capabilities for historical temperature and precipitation sampled at a point.

## Data handling

**Air temperature:** For a year with all 12 monthly T2M values, compute `sum(monthly_°C × calendar_days_in_month) / days_in_year`. Annual unit: °C.

**Corrected precipitation:** POWER `PRECTOTCORR` monthly rate has units `mm/day` under the selected request. Compute `sum(monthly_rate_mm_per_day × days_in_month)`. Annual unit: mm. This is an integrated approximate annual precipitation amount from the monthly rate product.

The implementation rejects missing/nonfinite values and excludes incomplete years. It filters monthly keys `YYYY01`…`YYYY12` and ignores POWER's extra `YYYY13` annual aggregation key. It preserves source units and data metadata.

## Trend estimation

1. Fit annual `y` as a linear function of centered calendar year `x` using ordinary least squares.
2. Report the slope multiplied by 10 to express modeled change per decade.
3. Compute Newey–West HAC standard errors with a short lag window to partially account for serial correlation and heteroskedasticity.
4. Test the two-sided null of zero linear slope at the 0.05 level, recording the HAC p-value and approximate 95% interval.
5. Report a Theil–Sen robust slope and interval for cross-checking.
6. Display the model fit and compare it to annual observed values.

HAC inference is exploratory, especially in short records; it is not automatically valid under long-memory processes, model misspecification, structural breaks, selection bias or repeated comparison of many locations.

**Important:** A low p-value is not proof of a specific climate-change driver or practical importance. Inference describes the observed time-series behavior under assumptions. It is not an attribution study.

## Baseline anomalies

Subtract the mean of the **first up to ten complete annual observations** in the user's selected range. This is a transparent local comparison baseline, *not* a climatological 30-year normal. The selected years and mean are included in every JSON export.

## Reproducibility

The API responds with all monthly and annual data, regression values, HAC interval, Theil–Sen, notes, source request and a SHA-256 hash of the ordered monthly observations. The hash checks record consistency, not scientific truth.

## Exclusions and boundaries

- No causal attribution.
- No AI-generated unverified climate stories.
- No true regional gridded heatmap from single-point NASA POWER queries.
- No Prithvi model inference in the current deliverable.
- No historical claims until live NASA data has been received and checked.

## Additional discovery and seasonal analyses

**Seasonal fingerprint:** Monthly values are aggregated across years within the selected study period to show month-by-month patterns. Temperature values remain in °C. Monthly precipitation rate values are converted to monthly totals using the respective calendar month's day count, then averaged by calendar month. This is descriptive and not an independent reference climatology.

**Notable years:** Annual observations are ordered by absolute difference from the explicitly reported first-up-to-ten-years baseline mean. This is a **descriptive ranking**, not an AI classifier, event attribution, or a severity rating.

**Discovery Scanner:** Calculates a scientifically independent trend at each selected NASA POWER grid point, with a maximum of six points per scan. It computes Benjamini–Hochberg adjusted p-values over the set of successfully computed and testable hypotheses. These exploratory adjusted values are not guarantees under unknown spatial dependence, post-hoc selection, or undisclosed multiple scans. Partial network failures remain visible, not imputed.

**PDF:** Generated from the same validated investigation service as the JSON and charts, with source metadata, data checksum, methodological limits, trend and fitted series. The report does not convey NASA endorsement.

**Trained AI bridge:** No model is bundled. A separately evaluated model can consume the validated annual NASA data and return bounded, provenance-rich anomaly signals. Its scores are separate from the statistical significance calculations.
