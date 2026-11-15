# AETHERIS 7.0 — QA and release validation

## Automated checks (local build)

- **90 / 90 Python tests passed** across science, NASA adapter fixtures, API, spatial, seasonal, Earth Systems, forensic, new change-point methods, and UI structure contracts.
- **10 newly added scientific/API change-point tests** and 3 new V7 UI integrity tests. All are fixture-backed and deterministic; they do not imply successful live NASA access.
- JavaScript syntax validation completed via `node --check static/app.js`.
- `/api/v1/change-points` was exercised through an isolated fixture server returning clearly marked synthetic NASA-style observations; candidate year identified correctly for the generated known-shift series.
- Chromium headless **DOM-level** tests performed with local HTML/CSS/JS and an explicitly substituted synthetic API payload because navigating to localhost is blocked by the browser policy in this environment. Desktop 1440×900 and mobile 390×844 checks verified navigation, submit, result rendering, candidate selection, 3-series SVG chart, no JavaScript exceptions and no horizontal overflow.
- Synthetic fixture used in screenshots: generated time series with a designed transition near 2007, NOT real climate evidence.

## Limitations

- No live NASA POWER endpoint was verified from this build environment. `Verify_Live_NASA.bat` is included for a user's Windows machine.
- The DOM-level browser test proves client rendering and interactions with fixture-backed API data, NOT full end-to-end network integration. A direct browser-to-localhost navigation was blocked by environment policy.
- Break-year scores and leave-one-year-out stability are **descriptive model-selection diagnostics**, not formally calibrated change-point significance.
- External AI models are not bundled or connected; the existing optional AI bridge remains separate.
- The product is a local scientific research tool and not an externally production-hardened public multi-tenant deployment.

## Exact reproducibility commands

```bash
python -m pytest -q tests
node --check static/app.js
```

Run `Run_AETHERIS_Tests.bat` on Windows; use the documented backend launch command and test `GET /api/v1/change-points` against actual NASA observations where network access allows it.
