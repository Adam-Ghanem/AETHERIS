# Quality evidence — AETHERIS 13.0

## Automated
- Python/API/static checks: **133 passed**, 0 failed (`python -m pytest -q`).
- JavaScript syntax: all `static/*.js` pass `node --check`.
- FastAPI TestClient: `/`, `/api/v1/health`, and both quality-passport static resources return HTTP 200.
- New tests use explicitly synthetic deterministic series. Missing 2010-05 yields 287/288 available months and excludes the incomplete year. The quality passport shares the parent evidence SHA-256.

## Browser component checks
- Chromium executable `/usr/bin/chromium`; isolated component tested at 1440×940 and 390×844 viewports.
- Synthetic 2001–2025 (25-year, 300-month) test data and a visible banner **SYNTHETIC TEST FIXTURE** used.
- 5 diagnostic rows, 300 coverage cells, 25 omittable years, slope changes when selecting a year, JSON download, no uncaught JS errors and no horizontal overflow.
- Previews are **not real NASA analysis**, and they are not proof that a full browser-to-server journey works.

## Not verified
- Real NASA POWER live request from this environment.
- Normal browser navigation to the local running server (browser policy blocked localhost and file navigation).
- Windows startup scripts and complete user journeys on the owner's PC.
- External Prithvi or other pretrained AI integration; remains optional and disconnected.

## User validation steps
1. Run `Start_AETHERIS.bat` on Windows.
2. Select **Earth explorer → Beni Mellal → Analyze NASA data** and verify the provider is NASA POWER, not a fixture.
3. Check the Quality Passport and select two different omission years.
4. Download Quality JSON and the normal Evidence JSON; confirm the monthly-source SHA-256 matches.
5. Run `Verify_Live_NASA.bat` to verify both supported NASA parameters.
