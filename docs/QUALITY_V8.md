# AETHERIS 8.0 — Quality report

## Automated verification

- **103 Python unit/API/UI-structure tests pass** using `python -m pytest -q`.
- **10 new scientific/API tests** for Earth Time Machine: reference definition, missing annual years, source fingerprints, nine points, partial/total source failures, precipitation day weighting, API validation.
- **3 new static UI integration checks**: no duplicate HTML IDs, navigation/control presence, JS handler wiring, documented FastAPI endpoint.
- `node --check static/app.js` passes.
- `python -m compileall -q aetheris` passes.
- `GET /api/v1/health` returns `8.0.0` locally using the local HTTP service.

## Manual/browser and network limitations

- **Full local-server browser E2E was not verified**: the sandbox browser rejects localhost navigation with `ERR_BLOCKED_BY_ADMINISTRATOR`. Alternate DOM-based automation was also blocked. Neither run is counted as passed.
- No live NASA POWER Time Machine request was verified in this execution environment. NASA output should be tested on the developer's Windows machine. The nine-point endpoint uses bounded concurrency and may require a stable connection.
- Do not present test fixtures as NASA-sourced observations; all science/API tests use explicitly mocked data.
- The full GUI must be visually and interactively reviewed on the user's desktop/mobile browser. See `docs/EARTH_TIME_MACHINE.md` for acceptance steps.

## Recommended acceptance sequence (Windows)

1. Launch `Start_AETHERIS.bat` and open `http://127.0.0.1:8765`.
2. In the left menu select **Earth time machine**.
3. Select Beni Mellal, 2001–2025, T2M, 100 km and click **Build time machine**. Confirm no mock data is shown if NASA requests fail.
4. Scrub from 2001 to 2025; the nine numbers and year summaries must update without requesting NASA again.
5. Select P4 center and a neighboring point; check full-source evidence and annual chart.
6. Play and pause animation; try the arrow buttons and keyboard navigation on the range slider.
7. Download CSV/JSON, verify source fingerprints and empty cells for missing years.
8. Repeat on a narrow browser viewport and with precipitation.
9. Run `Run_AETHERIS_Tests.bat` for the offline suite and `Verify_Live_NASA.bat` for an existing live API smoke check.

## Known limitations

- No pretrained AI weights are included. AI inference bridge is independent.
- Annual point anomalies are descriptive, not formal climate attribution, statistical significance or area averages.
- Browser chart and download interactions still need real-device validation.
- True local deployment and end-to-end experience are independent acceptance gates.
