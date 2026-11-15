# Climate Forensics — scientific methodology and implementation

The **Climate Forensics** view helps investigators examine how robust a trend narrative is to period selection, seasonality and the influence of individual years. It is not a trained AI model and does not replace the existing annual OLS/HAC inference.

## Input and evidence

The view uses the same validated monthly NASA POWER point observation series as Earth Explorer (`T2M` in °C and `PRECTOTCORR` in mm/day). Incomplete calendar years are removed by the existing documented `annualize` function. A SHA-256 digest of the exact valid observations is carried forward from the original investigation so a reviewer can match results to source data.

## 1. Balanced-era contrast

For `N` complete annual values, let `h = floor(N/2)`. Compute the mean of the first `h` and last `h` complete annual values and report **late − early**. For odd `N`, the middle observation is left out of this specific comparison. Every early/late year range and the excluded middle year (if any) is reported explicitly. Differences in temperature are in °C; differences in annual precipitation total are in mm. The result is descriptive and not a hypothesis test.

## 2. Monthly seasonal shift

Take only source monthly observations belonging to the `h` early complete years and `h` late complete years. Compare the average value for each calendar month, late minus early. For precipitation, convert each monthly rate (mm/day) to an estimated monthly total by multiplying by the actual number of calendar days *before* calculating the mean across corresponding months. This accounts for February in leap years. These are **within-sample** period differences, not a standard independent 30-year baseline.

## 3. Rolling signal

For each requested rolling window `w` (3–15 years), include the trailing arithmetic mean only if the `w` annual records cover exactly `w` consecutive calendar years. Any window that spans a missing or incomplete calendar year is omitted. Smoothing can conceal large year-to-year variability; it does not establish a projection.

## 4. Leave-one-year-out slope sensitivity

Repeatedly remove one annual observation and re-estimate the OLS slope, using the actual year coordinates. Convert slopes to per-decade values and report the minimum, maximum, sign stability and the most influential omitted year relative to the full-sample slope. The resulting range is a robustness/sensitivity diagnostic **not a confidence interval, cross-validation score, or independent p-value**.

## Endpoint

`GET /api/v1/forensics?lat=32.337&lon=-6.349&start=2001&end=2025&variable=T2M&window=7`

The backend fetches verified NASA data, computes the existing full investigation and then generates the forensic diagnostics from the exact same observations. It reports the data source, original observation SHA-256 fingerprint and scientific limitations. No simulated data is silently substituted when NASA is unreachable.

## Interpretation caveats

- A temporal trend does not establish the causes of climate change.
- The significance tests and exploratory HAC assumptions of the original investigation remain distinct from these descriptive robustness checks.
- A single gridded NASA point does not represent a citywide or regional average.
- Correlated time series, structural breaks, model uncertainty and missing years require substantive attention.
- The user-selected window/period can affect apparent contrasts.
