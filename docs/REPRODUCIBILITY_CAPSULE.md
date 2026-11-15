# AETHERIS Reproducibility Capsule

Endpoint: `GET /api/v1/reproducibility.zip?lat=32.337&lon=-6.349&start=2001&end=2025`

The server conducts a complete NASA POWER dual-variable investigation using the same source connectors as the Evidence Command Center. It exports an auditable ZIP so the recipient can examine the annual source-derived values outside the application.

## Package files

- `briefing.json`: full deterministic report, source fingerprints, conclusions and limitations.
- `temperature_annual.csv` and `precipitation_annual.csv`: independent annual series used by the two reported trend estimates. This is important because a missing year may be excluded from paired analysis but still be valid in a single-variable series.
- `paired_annual.csv`: overlapping complete years that underpin the multivariate visualization.
- `manifest.json`: file SHA-256 hashes, internal evidence fingerprints, scope and limitations.
- `verify.py`: standalone offline checker using no external dependencies.
- `README.txt`: consumer instructions and validity caveats.

## Verification

Unzip and run `python verify.py` from the extracted directory. The verifier:

1. Rechecks file hashes against `manifest.json`.
2. Confirms that the report fingerprints match the manifest fingerprints.
3. Independently recomputes annual OLS slopes using the separate annual input files, checking against reported per-decade slopes. Numerical tolerance accounts for rounded stored annual values.
4. Checks the paired year list and observation count.

**Boundary:** this does not independently authenticate NASA's server, prove a climate mechanism, validate HAC significance estimates, or provide a digital signature. A malicious actor can change files and rewrite an unsigned manifest. Do not describe it as cryptographic proof of authenticity.

The browser uses an actual new API request for each ZIP; if the NASA connector is unavailable, show an error. There is no hidden fallback to synthetic data. The test suite uses explicitly labeled synthetic data.
