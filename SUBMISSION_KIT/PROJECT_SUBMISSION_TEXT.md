# AETHERIS — submission-ready project description

**Project title:** AETHERIS — Discover Earth's Hidden Changes  
**Challenge:** Be An Earth System Trend Detective!  
**Category:** Earth science, reproducible data analysis, interactive visualization  
**Tagline:** From Earth data to verifiable scientific evidence.

## Short description

AETHERIS is an interactive Earth intelligence research platform that helps people identify and understand changes in temperature and precipitation from historical NASA POWER datasets. Users can explore a point anywhere on Earth, estimate long-term trends with uncertainty, compare locations, investigate annual and seasonal patterns, and export reproducible scientific evidence.

## The problem

Climate data is increasingly available, but interpreting environmental change still involves complex workflows: finding the right observations, aggregating years correctly, comparing different units, understanding statistical uncertainty, and documenting where claims originated. A beautiful chart alone is not proof of a meaningful trend.

## Our solution

AETHERIS connects to real NASA POWER monthly point datasets and turns them into transparent investigations. It provides an Earth Explorer, statistical trend analysis, quality diagnostics, anomaly exploration, side-by-side regional comparisons, spatial and temporal investigations, and a guided Evidence Command Center.

Our **Research Campaign Studio** investigates temperature and precipitation together across 2–6 independently sourced locations. It reports annual observed departures, separately estimates trends in appropriate physical units, applies exploratory multiple-testing adjustments within each variable family, explicitly marks unavailable sources, and exports raw annual evidence, structured JSON, and an offline presentation.

The **Scientific Quality Passport** checks monthly coverage, completeness, agreement between ordinary least squares and robust trend estimates, sensitivity to individual years, and indicators of time-series dependence. A separate **Reproducibility Capsule** includes original annual data, hashes and a Python verification script.

## NASA data and methodology

- Provider: NASA POWER, official monthly point endpoint.
- Variables: `T2M` (2-meter air temperature) and `PRECTOTCORR` (corrected precipitation).
- Temperature: day-weighted mean of complete monthly observations, reported in °C.
- Precipitation: monthly mm/day rates multiplied by calendar days and summed to estimated annual millimetres.
- Trend estimation: annual OLS slope per decade, HAC/Newey–West exploratory inference, plus Theil–Sen robustness comparisons.
- Transparency: sources, exact coordinates, time period, data-quality diagnostics, methodological caveats and SHA-256 evidence fingerprints.

**Important:** NASA POWER meteorological data here is gridded/model-derived; it is not the same as in-situ weather-station measurements or a measured average for an entire administrative region. Observed associations and detected shifts do not establish causation or climate attribution. The optional external ML interface is not represented as a deployed trained model.

## Impact

The project makes the scientific process of investigating Earth-system change more accessible to students, educators, researchers and communities without requiring them to write statistical code. The exportable evidence helps users ask sharper questions and communicate findings with appropriate uncertainty instead of relying on unverified visual claims.

## What makes AETHERIS different

1. A multi-module scientific workflow instead of isolated dashboards.
2. Independent cross-region, two-variable research campaigns.
3. Statistical limitations, data completeness and robustness visible beside results.
4. Downloadable source-backed evidence and offline presentations.
5. Source failures and uncertainty are shown rather than replaced by fictional observations.
6. A lightweight local deployment without a dedicated GPU or paid map API.

## Technology

Python, FastAPI, NumPy, SciPy, Statsmodels, vanilla JavaScript, responsive HTML/CSS, bundled Natural Earth geographic outlines, NASA POWER public APIs, ReportLab, Pytest.

## Repository and demo links

Add your actual public repository URL and working deployment or video URL here **after uploading them**. Do not invent links.

## Attribution

AETHERIS is an independent project and is not affiliated with, endorsed by or officially reviewed by NASA. NASA POWER is used as a publicly accessible scientific data provider. Natural Earth outlines are used for background geography.
