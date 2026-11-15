# AETHERIS 4.0 — Engineering Verification

The v4 package builds on the existing 3.0 climate forensics application. It does not include a trained NASA Prithvi model.

## Executed checks

- 48 Python automated unit/API tests: **passed** (`python -m pytest -q`). This includes 11 new spatial tests covering geometry, dateline wrap, input validation, reproducibility against fixture monthly observations, partial upstream failures, all-upstream failures, and the HTTP API contract.
- `node --check static/app.js` and `node --check static/globe.js`: passed.
- Headless Chromium desktop: Spatial Observatory field renders nine fixture-backed cells, details respond to point selection, CSV download triggered. Desktop Mission Control screenshot inspected.
- Headless Chromium mobile at 390px: navigation drawer, nine fixture-backed cells, point-detail selection, no JavaScript page errors, no horizontal page overflow.
- Backend health route live on local Python server: HTTP 200, v4.0.0.

## Not verified

- NASA POWER live network response from this container. Use `Verify_Live_NASA.bat` in an Internet-connected Windows environment.
- Full Windows launcher on the owner's PC (the current build/QA environment is Linux).
- Real external AI inference. The AI bridge is deliberately unconfigured until a separate validated model is attached.
- An end-to-end browser analysis using real live NASA data; DOM checks are deterministic fixture-backed checks and must not be labeled real data.

## Change controls

- The application is designed to bind locally to 127.0.0.1. Public deployment needs rate limits, secrets management, monitoring, and deployment review.
- NASA data retrieval failures are shown as errors rather than fictional results.
- No map tile keys or paid SaaS services are necessary for offline geography.
