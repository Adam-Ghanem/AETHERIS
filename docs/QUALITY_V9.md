# AETHERIS 9.0 — Engineering verification

## Evidence verified

- `python -m pytest -q`: **112 passed** (includes previous API/science suites and 9 Evidence Command Center tests).
- `node --check static/app.js` and `node --check static/briefing.js`: passed.
- Chromium with an **in-memory synthetic fixture**, actual HTML/CSS/JS: tested at **1440×900** and **390×844**.
- Interactive view: 2 findings, 25 year cells, SVG timeline, select year, compare years, expand evidence limitations, export CSV, export JSON.
- No browser page errors and no horizontal overflow for the tested fixture/viewport combinations.
- Static source code, Windows launcher, scientific methods and previous modules retained.

## NOT verified / still needed on the user's Windows laptop

- Live NASA POWER access at the selected time and network.
- Complete browser E2E via the running HTTP server (container browser policy blocked localhost); the in-memory harness is not a replacement for a live deployment test.
- Printing to an actual PDF printer, screen-reader audits, stress/load testing, Windows-specific dependency installation.
- Pretrained model or remote AI inference deployment (optional integration bridge only).

## Scientific limits

A generated briefing is not a validated climate-attribution result or a forecast. HAC evidence relies on modeling assumptions; separate signal p-values are not adjusted for multiplicity in this view. Individual-year and era comparisons are descriptive. The project documents what its numerical results can and cannot support.
