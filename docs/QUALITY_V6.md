# AETHERIS 6.0 — Quality and Verification

## Automated code checks

- `python -m pytest -q tests`: **77 passed** (64 previously existing + 10 new seasonal-science/API tests + 3 static UI integrity tests).
- `python -m compileall -q aetheris`: passes.
- `node --check static/app.js`: passes.
- Full API route exercised with test-injected clearly synthetic source observations. Input validation, proper error responses and source provenance tested.
- Benjamini–Hochberg adjustment, known monthwise trends, temperature/precipitation units, leap-year precipitation, incomplete years, constant series, checksum repeatability and upstream error propagation tested.

## Browser validation constraint

Chromium Playwright navigation was blocked by the environment's administrative policy even for a `data:` URL; consequently, a full browser E2E run and visual review of the new v6 interface **could not be completed here**. This limitation does not invalidate the passing Python scientific/API suite, but interactive UI behavior remains **unverified** until a real browser run on the target machine.

## Live-data constraint

No fresh live NASA data request was successfully verified from this build environment. The server and routes run locally and rely on the existing NASA connector; a local connectivity check should be performed using `Verify_Live_NASA.bat`. Fixture data are never presented as live NASA values.

## Scope

This is a local Windows-oriented research application, not a production-hardened internet service. The pretrained NASA/IBM Prithvi weights are not included, and no ML training is claimed.
