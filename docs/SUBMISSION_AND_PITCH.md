# AETHERIS — scientific pitch and presentation guide

**Project:** AETHERIS — Discover Earth's Hidden Changes  
**Challenge:** Be An Earth System Trend Detective!  
**Category:** Earth data, climate data analytics, scientific reproducibility

Review your actual running build before claiming any feature below; do not present optional models as connected unless they genuinely are.

## One-sentence pitch

> AETHERIS transforms NASA's public Earth data into transparent, reproducible scientific investigations that detect and compare environmental trends while clearly communicating uncertainty.

## What problem does it solve?

Public climate and Earth science observations are extensive but difficult to interpret. A graph can suggest change without clearly explaining the magnitude, data quality, assumptions, or whether a calculated trend is statistically supported. AETHERIS helps make this evidence visible and understandable.

## Why it is different

Rather than displaying attractive but unverifiable heatmaps, AETHERIS provides a **Scientific Evidence Ledger**: the NASA data product, exact point and period, units, processing method, annual series, robust trend estimates, uncertainty, caveats, retrieval timestamp and checksum. The Discovery Scanner expands this to multiple user-chosen locations with statistical adjustment for multiple testing and explicit partial-failure handling.

## Demo plan (about three minutes; adjust to the actual presenter format)

1. **Problem (20 seconds):** The Earth changes unevenly, and scientists need to distinguish apparent changes from credible patterns.
2. **Investigate (50 seconds):** Open Earth Explorer, choose Beni Mellal and a time period, run a live NASA POWER analysis and show traceable provenance.
3. **Understand (40 seconds):** Inspect yearly observations, fitted trend, anomaly chart, statistical confidence and the seasonal fingerprint. Explain limitations.
4. **Discover (45 seconds):** Run a prepared Discovery Scanner selection of several points; review ranked measured changes, BH-adjusted p-values, and important warnings.
5. **Reproduce (25 seconds):** Export the full Evidence JSON and professionally formatted PDF report. Open Research Notebook to review a saved snapshot.

Plan an alternative path if NASA's public API is temporarily unavailable: show a **clearly labeled verified previous export**, not fictional live observations.

## Technical overview

- NASA POWER monthly point API, temperature and corrected precipitation.
- Python FastAPI backend, bounded retries, cache, strict validation.
- OLS trends, HAC/Newey–West exploratory inference, Theil–Sen robustness and SHA-256 evidence records.
- Native JS front-end and vector Natural Earth basemap; lightweight enough for laptops without discrete GPU.
- PDF and JSON/CSV export, local notebook and optional external AI bridge.

## Honest scientific limitations

- Gridded points are not district averages; no claim of full spatial gridded trends.
- Statistical significance does not establish a cause.
- Selected-period monthly profiles are not 30-year reference climatologies.
- A separately trained AI model must not be claimed as integrated until actually connected, validated and demonstrated.

## To fill in before presentation

**Actual team:** [names and roles]  
**Actual source repository:** [GitHub link]  
**Actual live demo:** [deployment URL or local demo]  
**Actual tests/evidence:** [results]  
**Verified NASA dataset names/period:** [fill from a successful live run]
