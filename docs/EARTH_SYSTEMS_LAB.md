# Earth Systems Lab — scientific methodology (AETHERIS 5.0)

The lab fetches **two independent, authentic NASA POWER monthly point series** at the **same WGS84 coordinates and requested calendar years**:

- `T2M`: 2-m air temperature, monthly mean °C. Annual mean is weighted by calendar days of each month, using only years with all 12 months.
- `PRECTOTCORR`: corrected precipitation, monthly mean rate in mm/day. Estimated annual total in mm is the sum of monthly rates × days in each calendar month, using only complete years.

The backend uses the existing validated NASA POWER provider and tested scientific aggregation. Two fetches execute concurrently. If either fetch fails, **the entire dual-source investigation fails explicitly**; it never substitutes artificial observations.

## Pairing and baseline

Annual records are joined by their *actual calendar year*. Unpaired years are discarded from the **joint** investigation and explicitly listed. At least **8 shared complete years** are required. Nothing is interpolated.

The first up to **10 shared years** define an **internal descriptive baseline**, not an official climatological normal or external reference period. For each year, AETHERIS calculates observed departures from this baseline (absolute °C and mm) and standardizes with baseline sample SD when nonzero. A constant baseline yields missing standardized departures, not misleading infinities.

## Joint hot/dry exploratory markers

A year is marked only when:

- Temperature is at least **one baseline sample SD above** the baseline mean; **and**
- Precipitation is at least **one baseline sample SD below** the baseline mean.

This is an **arbitrary exploratory screening heuristic**, *not* a drought diagnosis, a standardized compound-event index, a probability estimate, or evidence of cause.

## Association and contrasting eras

The software reports **Pearson r** for (1) aligned annual observations and (2) annual residuals after separately subtracting a fitted linear trend from both series. Correlation is suppressed if either series has effectively zero variance or there are too few observations. No p-value is reported for correlation; these are descriptive results that **do not account for serial dependence, confounding, or multiple testing**.

The early/late comparison uses equal-sized chronological groups from the shared years. If there is an odd number of observations, the middle year is **explicitly excluded from the era comparison only**. Each contrast is the late mean minus the early mean in °C or mm and cannot on its own establish a significant or causal change.

The separate T2M and PRECTOTCORR trend estimates are from the core AETHERIS scientific engine (OLS/HAC exploratory inference), and are not the same as the descriptive joint association.

## Reproducibility / audit

The response includes independently verified underlying NASA requests, their source monthly SHA-256 checksums and a deterministic paired checksum `SHA256(temp_hash + ':' + rain_hash + ':earth-systems-v1')`. Checksums track data identity, **not scientific correctness**. Export the full evidence JSON or aligned annual CSV. The current implementation deliberately does not bundle trained ML models; the teammate's external AI module remains optional.

**Limitations:** NASA POWER data are gridded/model-derived point products and not direct readings from a weather station or a whole city/region. Short records, missing data, seasonal biases, serial dependence, and site selection affect interpretation. This analysis cannot provide climate attribution, validated extreme-event counts, future weather forecasts, or causal conclusions.

**API:** `GET /api/v1/systems?lat=32.337&lon=-6.349&start=2001&end=2025`

**Source:** https://power.larc.nasa.gov/docs/services/api/temporal/monthly/
