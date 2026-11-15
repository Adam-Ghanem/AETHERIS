# Evidence Command Center — AETHERIS 9.0

## Motivation

Previous modules each answered a narrow technical question. This view brings a pair of NASA POWER signals into **one evidence-led, reproducible narrative** that a reviewer can explore without switching across many independent pages. It is not a generative AI explanation, an invented climate score, or a new observation product.

## One complete workflow

1. Open **Evidence command center** from the left navigation (or from a completed Earth Explorer investigation).
2. Select a known geographic point or enter latitude/longitude, and choose a period containing at least eight years.
3. Select **Generate evidence briefing**. The backend makes independently validated NASA POWER requests for **T2M** and **PRECTOTCORR** (retrieval caching applies).
4. Explore side-by-side estimated annual trends, the period-paired standardized timeline, and the yearly evidence atlas.
5. Select a year in the atlas to inspect it against another chosen year; the differences remain strictly descriptive.
6. Inspect early/late balanced groups, exploratory joint hot/dry flags, and a fully attributed evidence ledger.
7. Export the complete JSON evidence, a paired annual CSV, or print/save the case briefing as PDF using the browser.

## Evidence model

The API endpoint `GET /api/v1/briefing?lat=32.337&lon=-6.349&start=2001&end=2025` reuses the existing annualizing and investigation pipeline via `run_systems`. No separate temperature formulas are introduced. Each result includes:

- Annual paired observations with both original values and baseline departures
- Trend estimates per decade and exploratory HAC test information for both signals
- Early/late group contrasts, labeled as descriptive
- Raw/detrended correlations, labeled as non-causal
- Exploratory co-occurrence flags, not a drought classification
- The separate monthly-source SHA-256 fingerprints and a deterministic briefing fingerprint
- Product details, geographic sampling coordinates, time range, and limitations

The first up to ten **shared complete** years form an internal descriptive baseline. This is **not** an official climate normal. No missing values are interpolated, and NASA POWER gridded/model-derived point data are not described as direct station measurements or administrative-area averages.

The frontend detects explicitly labeled synthetic/fixture data during tests and exposes a clear **SYNTHETIC TEST FIXTURE — NOT NASA OBSERVATIONS** banner. On a real successful request it identifies NASA POWER as the provider.

## API, UI and tests

- Backend: `aetheris/briefing.py`, `aetheris/server.py`
- Frontend: `static/briefing.js`, `static/briefing.css`, `static/index.html`
- Tests: `tests/test_briefing.py` plus all previous test suites
- DOM/interaction validation: run with a fixture-only in-memory Chromium harness; this does not validate live NASA connectivity or Windows runtime.

The pretrained NASA–IBM Prithvi model is **not** included. Optional AI inference remains a separate component and is not confused with deterministic climate analysis.
