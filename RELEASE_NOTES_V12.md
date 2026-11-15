# AETHERIS 12.0 — Evidence Constellation & Reproducibility Capsule

## What's new

### Climate Constellation (Evidence Command Center)

- Interactive **annual temperature-vs-precipitation scatterplot** derived solely from the paired annual investigation records.
- Two axes use **internal-baseline standardized departures**, not physical units; the selected-year inspector shows the underlying °C and mm values and absolute departures.
- The amber lower-right quadrant marks an exploratory `temperature_z >= +1` and `precipitation_z <= -1` joint screening region. It is **not** a certified drought indicator or causal claim.
- Filter by complete years, flagged years, warmer years, or drier years; reset the lens; click or keyboard-select a year. Year selection synchronizes with the existing two-year comparison and evidence matrix.
- A year selector and horizontally scrollable chart make mobile inspection usable without distorting data. The entire module follows the **white + solar yellow** visual system.
- Zero-variance baseline cases show an explicit unavailable state rather than invented standard scores.

### Reproducibility Capsule

- New API endpoint: `GET /api/v1/reproducibility.zip` (lat, lon, start, end).
- Download button in **Evidence Command Center** exports an independent data package containing:
  - Complete briefing and source fingerprints (`briefing.json`).
  - Both original annual input series (`temperature_annual.csv`, `precipitation_annual.csv`).
  - Paired annual evidence (`paired_annual.csv`).
  - SHA-256 file manifest (`manifest.json`).
  - Portable `verify.py` using the Python standard library only.
  - `README.txt` with verification instructions and scientific caveats.
- The verifier recalculates independently the OLS decade slopes and checks hashes, report-to-manifest source-fingerprint linkage, and paired years.
- Checksums detect package modifications **relative to the included manifest**; they do not prove NASA authenticity or cryptographically sign the package. HAC inference and attribution are **not** independently verified by the capsule.
- The ZIP export re-fetches underlying NASA POWER observations according to the query rather than claiming data already on screen is automatically reverified. API failures remain failures; no silent synthetic fallback.
- Synthetic test results are clearly labeled **SYNTHETIC TEST FIXTURE**, including exports.

## Compatibility

All AETHERIS v11 modules, Mission Theater, offline slides, PDF reports, NASA POWER connector and optional AI bridge remain. No model downloads, database schema changes, or Docker dependency required. Backend version is now `12.0.0`.

## Verification in this environment

- **127/127 automated Python/API/static tests passed**.
- Independently tested ZIP verifier against a deterministic fixture. Tampering with a CSV produced a nonzero failure.
- Node.js syntax checks passed for app, briefing and theater JS.
- Browser component tested in Chromium at desktop 1440px and mobile 390px with **explicit synthetic fixtures**, including 25 circles, filtering, year-to-comparison synchronization, and no observed JavaScript exceptions or horizontal page overflow.
- App health endpoint responds with version 12.0.0 locally.
- **Not independently verified:** real NASA POWER live requests in this run, complete Windows installation, or unrestricted browser-to-localhost full E2E. The visual test used inline offline assets because the browser policy blocked localhost.

See `docs/EVIDENCE_CONSTELLATION.md`, `docs/REPRODUCIBILITY_CAPSULE.md` and `docs/QUALITY_V12.md`.
