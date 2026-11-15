# AETHERIS 11.0 — Mission Theater Edition

## What's new

**Mission Theater** is a cohesive, full-screen, scientific presentation experience. It transforms the existing NASA POWER dual-signal Evidence Command Center results into seven connected chapters:

1. The investigation: geographic point, shared complete years, precise provenance.
2. The four research questions: what, where, how much, and the strength of the evidence.
3. Measured temperature and rainfall trends with actual units and exploratory HAC evidence.
4. Two independent, unit-correct annual-observation charts, generated exclusively from returned records.
5. Early–late period comparisons and clearly qualified joint anomaly screening.
6. Source hashes, original evidence fingerprint, methodological limitations.
7. Research summary, not a forecast or attribution statement.

- **White + solar-yellow premium design**, original typographic layouts, presentation navigation, accessible keyboard shortcuts and a responsive mobile experience.
- **Export an offline HTML presentation** containing the current evidence-based slides, with no CDN, network dependency or account requirement. It can be opened later and printed/saved to PDF through a browser.
- **Export the full underlying evidence JSON** directly from the theater.
- **No fictional observations:** theater remains unavailable until a valid Evidence Command Center investigation has returned.
- **Source honesty:** synthetic test fixtures are clearly labeled as synthetic rather than NASA observations.
- No pretrained AI weights bundled; the existing AI Bridge remains optional and independent.

## Compatibility

This is a non-destructive upgrade to **AETHERIS 10.0**. All research modules and FastAPI endpoints remain available. `/api/v1/health` now reports version 11.0.0. No databases or migration steps are required.

## Verification summary

- 120 Python/API/static automated tests passed (including four new Mission Theater checks).
- JavaScript syntax checked with Node.
- Mission Theater component tested in Chromium at 1440×900 and 390×844 with clearly labeled **synthetic test fixtures**, including navigation, slide numbers, keyboard interactions, HTML export, offline replay, and no observed JS exceptions or horizontal document overflow.
- Original local server health endpoint responds successfully.
- Full integrated-browser and live NASA POWER end-to-end tests were **not** completed in this environment and require real Windows/network verification. These are not represented as passed.

See `docs/QUALITY_V11.md` and `docs/MISSION_THEATER.md`.
