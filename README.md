# AETHERIS 14.0 — Final Submission Edition: Discover Earth's Hidden Changes

**Scientific Earth intelligence software** built for the challenge **Be An Earth System Trend Detective!**

AETHERIS turns real NASA POWER historical meteorological time series into evidence-based investigations: **What changed? Where? By how much? How strong is the evidence?** The platform reports limitations rather than inventing answers.

> Independent software, not affiliated with, reviewed by or endorsed by NASA. AETHERIS is not a substitute for professional climate-attribution research.

## What is implemented

**NEW IN V14 — Research Campaign Studio:** Build a single investigation across 2–6 cities with both NASA POWER temperature and precipitation, independently estimated trends and BH-adjusted exploratory inference per variable family; use the annual timeline and export evidence JSON, annual CSV or offline research slides. See `docs/RESEARCH_CAMPAIGN.md` and `SUBMISSION_KIT/README_FIRST.txt`.


| Module | Included behavior |
|---|---|
| **Research Campaign Studio (V14)** | Independent paired NASA POWER investigations at 2–6 preset point locations; annual year explorer, separate variable-family BH correction, partial failure transparency and offline campaign presentation export |
| **Scientific Quality Passport (V13)** | From every Earth Explorer investigation: monthly-availability matrix, complete-year diagnostics, OLS/Theil–Sen directional comparison, leave-one-year-out sensitivity, residual lag-1 review flag, 25-year influence drilldown and JSON/summary exports, with explicit scientific limitations |
| **Climate Constellation (NEW V12)** | Paired-year interactive NASA temperature/rainfall departure scatter, selectable and filtered historical years, synchronized annual comparison, accessible mobile year selector, explanatory evidence inspector |
| **Reproducibility Capsule (NEW V12)** | Download a scientific ZIP containing original annual inputs, paired evidence, SHA-256 manifest, complete briefing and an independent stdlib-only Python OLS verifier; hashes are NOT source-authentication signatures |
| **Mission Theater (NEW V11)** | One-click research presentation from real source-backed evidence: seven cinematic scenes, desktop/mobile full-screen, keyboard navigation, two real-unit series, statistical caveats, exportable standalone offline HTML and raw evidence JSON |
| **Solar Research Edition (V10)** | Complete high-contrast white/yellow design system across all 13 research sections; mobile Earth globe layout, light scientific charts and accessible controls |
| **Quick Research (NEW V10)** | One-click Beni Mellal dual-signal investigation from Mission Control; a single source-backed flow with honest error states |
| **Reopen Research Links (NEW V10)** | Copy a URL containing validated coordinates and years to reopen a paired investigation on the **same accessible AETHERIS installation**; sources are re-fetched when opened, no scientific values embedded or fabricated |
| Mission Control | Professional, responsive scientific UI with fully working navigation |
| **Evidence Command Center (NEW V9)** | One-page, research-led dual-signal briefing, source-backed trends, yearly evidence atlas, interactive year-to-year comparison, exploratory flags, source fingerprints, paired CSV/JSON exports and print-to-PDF |
| Earth Explorer | Bundled vector world map, coordinates, location presets and date/variable selection |
| NASA Data | Real public NASA POWER monthly point API (`T2M`, `PRECTOTCORR`); explicit errors if unreachable |
| Scientific Engine | Verified annualization, OLS/HAC inference, Theil–Sen, anomalies, evidence checksum |
| Seasonal Fingerprint | 12-month climatology for selected period, temperature and precipitation-aware units |
| Notable Years | Descriptive ranking of annual departures from documented within-period reference |
| Regional Comparison | Two independently evaluated points on one chart |
| Discovery Scanner | 2–6 preset locations, bounded parallel requests, sorted observed trends, BH adjusted p-values, partial error reporting |
| **Earth Time Machine (V8)** | Nine NASA POWER source points, interactive year-by-year temperature or precipitation anomalies, fixed ten-year pointwise baselines, one-scale temporal matrix, Play/Pause, selected-point provenance, annual CSV and evidence JSON |
| **Change-point Lab (V7)** | Exploratory continuous slope-change detection: candidate year scan, single vs piecewise BIC comparison, leave-one-year-out robustness, interactive charts and evidence exports |
| **Seasonal Signal Laboratory (V6)** | 12 separate NASA-backed calendar-month trend analyses, OLS/HAC + Theil–Sen estimates, BH adjusted exploratory q-values, interactive year-by-month anomaly matrix, baseline evidence, source fingerprint and CSV/JSON exports |
| **Earth Systems Lab (V5)** | Dual real NASA POWER T2M/precipitation annual pairing, co-occurrence screening, raw/detrended correlations (descriptive), interactive scatter, single-year detail, independent source hashes, CSV/JSON exports |
| **Climate Forensics Lab** | Early/late period comparisons, rolling means, 12-month change analysis, leave-one-year-out slope sensitivity, full forensic evidence JSON |
| **Spatial Observatory (V4)** | 3×3 NASA POWER spatial sampling with nine independently sourced trend estimates, BH adjusted exploratory p-values, point-level provenance, interactive field matrix, and CSV/JSON exports |
| Orbital Atlas (V4) | Offline rotating orthographic globe of bundled Natural Earth geography, with manual rotation and reduced-motion support; not a NASA heatmap |
| Research Notebook | Save, reopen and remove evidence snapshots in local browser storage |
| Reports | Download source-backed, two-page scientific PDF; export annual CSV / complete evidence JSON |
| AI Bridge | Optional secure, configurable external ML inference adapter with validated JSON contract; **no pretrained weights bundled** |
| Testing | Deterministic science, API, discovery, PDF and AI-contract tests |

### Important scientific boundaries

- Evidence Command Center contains deterministic analytical explanations and two-signal comparisons; it does **not** include a trained AI model or establish causation. See `docs/EVIDENCE_COMMAND_CENTER.md`.

- Earth Time Machine displays **discrete annual anomalies at nine point samples**; the reference is a fixed first-ten-calendar-year local mean, with at least eight complete years per point. It is not an official 30-year normal or a continuous spatial heatmap. Missing values are never interpolated.

- Seasonal Signal Lab uses only complete annual records for monthly investigations, excludes and explicitly marks incomplete years, compares to an internal first-up-to-10-year monthwise baseline and applies BH FDR adjustment across exactly twelve exploratory tests. It does **not** establish causal attribution, a 30-year climate normal, or a forecast.
- Earth Systems Lab joint-hot/dry flags and raw/detrended correlation are **descriptive exploratory calculations**, not drought diagnostics or claims of causation.
- NASA POWER is **gridded/model-derived meteorological data**, not direct readings from a chosen city's weather station. A geographic point is not an administrative-region mean.
- `T2M` is mean °C; annual means are **calendar-day-weighted** across complete years.
- `PRECTOTCORR` is average precipitation rate in **mm/day**; estimated annual mm sum multiplies each rate by the days in its calendar month.
- Annual OLS slopes are scaled per decade; HAC/Newey–West p-values are **exploratory**, depend on model assumptions, and do not establish causes.
- BH FDR adjustment is calculated across the successful, testable locations in a particular scan, with caveats about spatial dependence and user selection.
- The seasonal fingerprint uses data within the selected study period; it is **not** an independent standardized 30-year normal.
- "Notable years" are descriptive annual deviations, **not ML anomaly classifications**.
- Climate Forensics period differences and leave-one-year-out diagnostics are **descriptive**; they do not prove significance or causation. Missing years interrupt the rolling mean instead of being silently bridged.
- The AI bridge requires your teammate to connect a real trained model. The UI accurately reports when none is connected.

## Windows quick start

**In v14:** Research Campaign Studio → choose 2–6 selected locations → Launch Research Campaign → inspect two separate variable charts and historical year explorer → download source-backed JSON/CSV/HTML. **Also available:** Earth Explorer → Analyze NASA data → Scientific Quality Passport → inspect month coverage and year influence → download audit JSON. The older v12 workflow remains: Evidence Command Center → generate briefing → explore **Climate Constellation** (select individual years) → click **Reproducibility ZIP** → extract and run `python verify.py` in the extracted folder. The ZIP re-fetches source data, and live NASA connectivity is required.


**Prerequisite:** Python **3.10+** with PATH enabled; internet for first-time dependencies and NASA API access.

1. Extract the ZIP to a normal Windows folder (for example, `Desktop\AETHERIS`).
2. Double-click **`Start_AETHERIS.bat`**.
3. Wait for initial dependency installation; browser opens at **http://127.0.0.1:8765**.
4. On **Mission Control**, click **Run Beni Mellal research** to start a paired investigation immediately. You can also open **Evidence command center → Beni Mellal → Generate evidence briefing**.
5. Open **Earth explorer → Beni Mellal → Analyze NASA data**.
6. Open **Discovery scanner**, select 2–6 places, then **Scan NASA points**.
7. Select **Climate forensics** for deeper robustness diagnostics, or open it directly from a finished investigation.
8. Open **Earth Systems Lab** to investigate temperature and rainfall together, select a year on the scatter plot, and export joint evidence.
9. Open **Change-point lab** to compare candidate slope transitions with a simple linear trend.
10. Open **Seasonal signal lab** to inspect twelve calendar-month trends, select months, explore the year × month anomaly matrix, and download the evidence.
11. Open **Earth time machine**, select a center, date range and variable, then press **Build time machine**. Scrub/play the historical record, inspect nine points, and export JSON/CSV.
12. From a successful single-point analysis, click **Scientific PDF**, **CSV**, or **Evidence JSON**. In the Evidence Command Center, choose **Copy research link** to reopen the same input settings. URLs pointing at `127.0.0.1` are local-only; others need network access to the same server.

No JavaScript package manager, Docker, dedicated GPU, or paid map API is required. Bundled Natural Earth country polygons render offline. NASA data retrieval itself requires internet.

### Manual startup

```powershell
cd C:\path\to\AETHERIS
py -3 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m uvicorn aetheris.server:app --host 127.0.0.1 --port 8765
```

### Tests

```powershell
.venv\Scripts\python.exe -m pytest -q tests
```

Or run `Run_AETHERIS_Tests.bat`. The unit/API tests work without NASA network access using explicitly marked synthetic fixtures. They are *not* live data verification.

### Live data verification (optional)

Run **`Verify_Live_NASA.bat`** after the initial installation to request genuine NASA POWER historical temperature and precipitation data and validate the new forensics pipeline. This requires internet access; fixture-based unit tests cannot substitute for it.

## Core API

| Endpoint | Description |
|---|---|
| `/api/v1/health` | Server health |
| `/api/v1/briefing?lat=32.337&lon=-6.349&start=2001&end=2025` | Source-backed two-signal evidence story, paired annual observations, exploratory HAC evidence, early/late contrast, distinct source hashes |
| `/api/v1/catalog` | Verified presets and supported variables |
| `/api/v1/investigate?...` | Scientific single-point investigation |
| `/api/v1/compare?...` | Two-point contrast with configurable historical year range |
| `/api/v1/time-machine?lat=32.337&lon=-6.349&start=2001&end=2025&variable=T2M&spacing_km=100` | Nine-point annual anomaly timeline, reference-period metadata, missing-year flags and full per-point NASA evidence |
| `/api/v1/change-points?lat=32.337&lon=-6.349&start=1990&end=2025&variable=T2M&min_segment_years=6` | Observed annual NASA series, exploratory continuous trend shifts, BIC candidate comparison, leave-one-year-out stability and source evidence |
| `/api/v1/seasonal-signals?lat=32.337&lon=-6.349&start=2001&end=2025&variable=T2M` | Monthly OLS/HAC and Theil–Sen trend estimates, BH correction, month-specific baseline and calendar-year × month anomaly matrix |
| `/api/v1/systems?lat=32.337&lon=-6.349&start=2001&end=2025` | Align two independent real NASA POWER source series and compute descriptive paired climate signals |
| `/api/v1/spatial?lat=32.337&lon=-6.349&start=2001&end=2025&variable=T2M&spacing_km=100` | Nine explicitly retrieved NASA POWER sampled points with spatial trend comparison and per-point evidence |
| `/api/v1/forensics?lat=32.337&lon=-6.349&start=2001&end=2025&variable=T2M&window=7` | Early/late contrast, seasonality shift, rolling means, leave-one-year-out slope diagnostics |
| `/api/v1/discover?locations=Beni%20Mellal,Marrakech&start=2001&end=2025&variable=T2M` | 2–6 fixed-location scan, BH-adjusted exploratory evidence |
| `/api/v1/report.pdf?lat=32.337&lon=-6.349&start=2001&end=2025&variable=T2M` | Source-backed PDF generated from a fresh/cached NASA query |
| `/api/v1/intelligence/status` | Honest external AI connection status |
| `/api/v1/intelligence/analyze?...` | Inference through trusted configured external model; 503 if not connected |
| `/docs` | OpenAPI documentation |

Requests accept only known NASA parameters and bounded coordinate/period values. Errors return HTTP status codes and explicit errors; NASA failures do not silently switch to fake observations.

## Trained AI integration

The core product does **not** need a GPU or a trained model to function. Your teammate can host a compatible inference model on another PC/cloud server. Configure these administrator-owned environment variables when ready:

```text
AETHERIS_AI_ENDPOINT=https://your-trusted-inference-service.example/infer
AETHERIS_AI_TOKEN=put-your-secret-token-in-local-env-not-in-git
```

Non-TLS remote HTTP URLs are not supported; loopback HTTP is supported for local development only. See **`docs/AI_INTEGRATION.md`** for the exact request/response contract, validated scoring, and Prithvi compatibility cautions. **Do not put API tokens in the frontend.**

## Security and deployment

- Local server binds to 127.0.0.1 by default; no login service is exposed.
- Scientific NASA URL is fixed server-side; clients cannot supply arbitrary network endpoints.
- AI endpoint is configured by the administrator, not user input; only HTTPS and loopback HTTP are supported.
- NASA request retries are bounded; discovery runs at most two requests concurrently per scan.
- Validation, controlled error responses, metadata provenance and tests are included.
- For public hosting, add infrastructure rate limits, authentication if needed, durable shared caches, monitoring, and deployment-specific secrets management; this local build alone is **not production-hardened hosting infrastructure**.

## Known limitations / validation

- No live NASA requests were executed in the build environment. API request structure and parsing are implemented and fixture-tested; validate live connectivity on your own network.
- Browser automation in this build environment was blocked by its browser policy; tests cover APIs and JavaScript syntax, but full interactive visual E2E still requires user-machine verification.
- The pretrained NASA–IBM Prithvi WxC model is **not bundled**. It requires specialized multidimensional MERRA-2 inputs, not the NASA POWER point CSV directly.
- No cloud hosting is provided; the deliverable is a runnable local app with source code.

## Source links

- [Challenge](https://www.spaceappschallenge.org/2026/challenges/earth-system-trend-detective/)
- [NASA POWER API](https://power.larc.nasa.gov/docs/services/api/temporal/monthly/)
- [Natural Earth public-domain geography](https://www.naturalearthdata.com/)

## Files

`aetheris/server.py` API; `aetheris/nasa.py` NASA connector; `aetheris/science.py` statistics; `aetheris/discovery.py` region scan; `aetheris/intelligence.py` optional model bridge; `aetheris/reports.py` PDF; `static/` self-hosted UI and map; `tests/` deterministic test suite; `docs/` method, AI, quality, project presentation.


## V3 upgrade notes

See [RELEASE_NOTES.md](RELEASE_NOTES.md), [docs/CLIMATE_FORENSICS.md](docs/CLIMATE_FORENSICS.md), and [docs/QUALITY_REPORT.md](docs/QUALITY_REPORT.md).

## AETHERIS 4.0 update

The new spatial module goes beyond one-dimensional and preset-only time-series comparisons. It samples **nine actual historical NASA POWER source points**, explicitly displays every location and potential failure, supports custom lat/lon and a navigation path back to single-point Explorer, and exports a source-backed evidence file. Its visualization does **not** interpolate a satellite layer. See `docs/SPATIAL_OBSERVATORY.md` and `docs/QUALITY_V4.md`. Mobile navigation was redesigned so all modules remain accessible at phone widths. The overview globe is a cartographic animation using bundled Natural Earth geometry, not a scientific measurement or live NASA imagery.


## AETHERIS 5.0 — Earth Systems Lab

Earth Systems Lab links **temperature and precipitation** at the same NASA POWER geographic point and across shared complete calendar years. The new dual-source charts, temperature–precipitation scatter, selectable-year explorer, balanced-era comparison and deterministic paired-data fingerprint form a reproducible analysis. The module displays transparent source information and limitations and never claims that a descriptive correlation proves causation.

Enter **Earth Systems Lab** in the navigation, select **Beni Mellal**, use **2001–2025** (or a different valid range), then click **Investigate both signals**. Internet is needed to retrieve real observations. When a source fails, the interface shows an explicit error rather than fake data. Review [`docs/EARTH_SYSTEMS_LAB.md`](docs/EARTH_SYSTEMS_LAB.md) for methodological assumptions and [`docs/QUALITY_V5.md`](docs/QUALITY_V5.md) for verification evidence.

## AETHERIS 6.0 — Seasonal Signal Laboratory

Open **Seasonal signal lab** from the sidebar. Select a city or coordinates, choose either T2M or PRECTOTCORR and an 8–45-year historical range. After NASA data retrieval succeeds, the interface shows 12 month cards, a month-specific chart, exploratory q-values and a year-by-month anomaly matrix. Clicking any month changes the historical plot; clicking any available heatmap cell displays its underlying source-derived value and baseline departure. Export the full JSON (including source fingerprint and limitations) or a tabular CSV of monthwise trend estimates. See `docs/SEASONAL_SIGNAL_LAB.md`.

The local Windows executable does not require training or loading an ML model. The optional collaborator-provided AI adapter remains separate.

## AETHERIS 8.0 — Earth Time Machine

Annual environmental histories at nine discrete NASA POWER points with reproducible source evidence. See `docs/EARTH_TIME_MACHINE.md` and `docs/QUALITY_V8.md`.

## AETHERIS 7.0 — Change-point Lab

The new [Change-point Lab](docs/CHANGE_POINT_LAB.md) asks whether the **rate** of an observed NASA POWER trend changes across the historical period. Users inspect a continuous hinge model, its best data-selected candidate year, annual observed/linear/piecewise fits, candidate BIC rankings, and leave-one-year-out sensitivity. Viewers can inspect candidate slopes and export reproducible JSON and annual CSV. The method is expressly exploratory: selecting the break after seeing the data is not an independent significance test. All pre-existing AETHERIS modules remain available.

## 3D Earth by GhostCatcg (MIT)

The Mission Overview globe uses a Three.js/WebGL adaptation of [GhostCatcg/3d-earth](https://github.com/GhostCatcg/3d-earth) with its original globe texture downloaded on setup (if online), animated orbit lines and satellites, and a lightweight offline fallback. See `docs/GHOSTCAT_3D_EARTH.md` and the bundled MIT license. This is illustrative geography, not NASA climate data.
