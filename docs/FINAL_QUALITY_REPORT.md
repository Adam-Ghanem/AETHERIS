# AETHERIS 14.0 — Final QA and release evidence

## Build source

Based on AETHERIS 13.0 Scientific Quality Passport release. Version 14.0 adds Research Campaign Studio with backend, UI, scientific outputs, tests, and submission materials.

## Tests completed in the release working environment

- Command: `python -m pytest -q`
- Result: **142 passed** (including 9 new `tests/test_campaign.py` tests).
- JavaScript syntax: `node --check static/app.js` and `node --check static/campaign.js` passed.
- HTML: project page 380 IDs; duplicate ID check passed.
- HTML pitch: seven offline slides present.
- Browser component review: Chromium 1440×900 and 390×844; Research Campaign Studio exercised with **explicitly synthetic fixture data**. Four location cards, eight signal slope bars, year selection, JSON/CSV/offline HTML downloads, zero JS exceptions and zero horizontal overflow in those component tests.
- API health: local FastAPI server returned `status=ok`, version `14.0.0`.
- Release archive: ZIP integrity tested after creation; SHA256 manifest generated and verified.

## Unverified or not included

- **Live NASA POWER request** from this environment: `scripts/verify_live_nasa.py` returned `NASA_UNAVAILABLE: ConnectError`. No claim of successful live retrieval in this release test environment.
- Full browser-to-live-backend E2E: browser automation in the environment blocked navigation to localhost and file URLs. The component was instead tested using safe inline fixtures; that is a narrower result.
- Windows `.bat` launch was inspected but not executed inside this Linux environment.
- No pretrained NASA/IBM Prithvi model bundled. An external ML module is **optional and disconnected by default**.
- The included screenshots are synthetic fixture previews with a clearly visible warning watermark. They are **not source-backed climate findings**.
- The project is a locally runnable scientific software package. It is not a public deployed web link or a confirmed official submission.

## What to verify on the destination Windows computer

1. Python 3.10+ available, unzip and run `Start_AETHERIS.bat`.
2. Confirm `http://127.0.0.1:8765/api/v1/health` and app home load.
3. Run `Verify_Live_NASA.bat` on an internet connection that can reach NASA POWER.
4. Open Earth Explorer, execute genuine historical analysis and inspect source metadata.
5. Open Research Campaign Studio with 2–4 point locations. Run live paired investigation. Confirm JSON, CSV and offline HTML exports and proper error behavior.
6. Test Scientific PDF, Quality Passport, Mission Theater and Reproducibility ZIP.
7. Confirm no stale or unauthorized files/tokens are being uploaded.

## Scientific non-claims

AETHERIS does not claim that a gridded NASA POWER point is a measured city-wide average; it does not establish climate causation from associations; it does not claim a trained AI model is connected; it does not fabricate values if upstream requests fail.
