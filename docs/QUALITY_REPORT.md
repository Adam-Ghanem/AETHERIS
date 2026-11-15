# AETHERIS 3.0 — Engineering Verification Report

## Verified in this deliverable

- **37/37 tests passed**, including NASA fixture parser and validation, annualization, OLS/HAC, deterministic provenance, discovery scan and BH adjustment, partial NASA failures, PDF generation, external AI contract validation and rejection of unconfigured AI.
- JavaScript syntax: `node --check static/app.js` passed.
- PDF generation: a fixture-backed **two-page PDF** was generated, its PDF header and embedded text were verified, and pages were rendered to images for visual inspection. The fixture is **synthetic test data**, not NASA observations.
- Frontend source audit: no duplicate DOM IDs and no unmatched static selectors in the main frontend JavaScript.
- Local API health endpoint returned HTTP 200 from a running Uvicorn server.

## Not independently verified

- A live NASA POWER network response within this environment. The user must exercise a live query with an internet-connected machine.
- Direct Chromium requests to localhost were blocked by browser policy. The UI was nevertheless exercised in Chromium using an in-browser mocked NASA API with explicitly synthetic fixtures. The new Forensics page rendered all four KPI cards, twelve monthly cards and two SVG charts without JavaScript errors at desktop and mobile widths; 390px mobile had no horizontal overflow. This does **not** verify live NASA integration or local Windows launch.
- AI model inference: contract tests use a deliberately labeled fake remote response; **no trained model weights are bundled** and no actual ML inference is claimed.
- Production load testing, third-party penetration testing, Windows execution in the user's environment, and public-host deployment.

## Follow-up release checks

1. On Windows, run `Start_AETHERIS.bat`, then `Verify_Live_NASA.bat` for a real NASA API smoke test.
2. Inspect seasonality, descriptive departures, Evidence Ledger and Scientific PDF.
3. Run Discovery scanner with 2–6 points; check both normal success and partial upstream outage states.
4. Verify Climate Forensics with live NASA data and check the two charts, 12 month shifts, API export, and dashboard at desktop/mobile sizes.
5. Run `Run_AETHERIS_Tests.bat` and inspect complete output.
6. Do not claim real trained AI results until a model passes integration and scientific evaluation checks.

---

## Updated release status — AETHERIS 4.0

The preceding 3.0 figures document an earlier release. Current v4 evidence and limitations are recorded in **`docs/QUALITY_V4.md`**: **51/51 Python tests passed**, Node JavaScript syntax checks passed, and desktop/mobile browser fixture checks were performed. These are not live NASA network integration tests.
