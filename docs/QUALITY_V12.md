# Quality report — AETHERIS v12

## Tested

- Python/API/static: **127 passed**, no failed assertions in final run.
- A synthetic data export was independently verified with `python verify.py` using Python standard library only.
- Modified annual input values triggered an expected manifest integrity failure.
- Frontend JavaScript syntax passed with `node --check`.
- Chromium inline-asset tests (desktop 1440×950, mobile 390×844) exercised 25 plotted years, year selection synced with comparison, filter and reset, and responsive layout. No JavaScript exceptions or overall document overflow observed.
- FastAPI health endpoint in the local server responded with `12.0.0`.

## Not tested / limitations

- Browser network policy prevented normal browser requests to localhost. The visual component test used inline, offline assets and a clearly **synthetic fixture** rather than an end-to-end network request.
- NASA POWER live connectivity and full Windows startup require validation on the owner's Windows computer using `Verify_Live_NASA.bat` and the standard application launcher.
- The AI/Prithvi model remains **unconnected** unless a separate compatible inference service is provided; no ML inference results are simulated.
- SHA-256 manifests are not cryptographic signatures or independent proof of dataset authenticity. The verifier checks OLS trends, not HAC p-values.

## Windows validation checklist

1. Launch `Start_AETHERIS.bat` and open `http://127.0.0.1:8765`.
2. Open Evidence Command Center and run Beni Mellal 2001–2025 using internet connectivity.
3. Check NASA provider fields (not Synthetic Test Fixture), inspect the Climate Constellation and click multiple years.
4. Download Reproducibility ZIP, extract, and run `python verify.py`.
5. Check existing modules including Mission Theater and PDFs. Report any API failures verbatim rather than using generated values.
