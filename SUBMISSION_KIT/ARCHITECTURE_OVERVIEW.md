# AETHERIS — technical system architecture

```text
Browser (responsive white + yellow UI)
    │
    ├── Mission Control / Earth Explorer
    ├── Research Campaign Studio / Time Machine / Spatial Observatory
    ├── Scientific Quality Passport / Evidence Command Center
    ├── Mission Theater / Downloadable evidence & presentation
    │
    ▼
FastAPI REST endpoints — strict parameter validation
    │
    ├── NASA POWER HTTPS connector
    │       ├── T2M monthly point meteorology
    │       └── PRECTOTCORR monthly point precipitation
    │
    ├── Scientific processing (NumPy / SciPy / Statsmodels)
    │       ├── complete-year aggregation
    │       ├── OLS + HAC exploratory inference / Theil–Sen
    │       ├── year influence / temporal sensitivity / seasonal analysis
    │       └── BH corrections within defined hypothesis families
    │
    ├── Evidence & reporting
    │       ├── provenance, source metadata and hashes
    │       ├── PDF / CSV / JSON / HTML
    │       └── reproducibility ZIP verifier
    │
    └── Optional external ML bridge (not installed by default)
```

## Design principles

- One Python backend serves both the scientific API and bundled frontend.
- Independent, bounded concurrent point-source calls; no fake geographic interpolation.
- Pure scientific core where practical and deterministic tests without network.
- No database, cloud account, dedicated GPU or commercial map API required for base app.
- A trained external ML module can be integrated only when separately deployed, versioned, validated and tested.

## Security boundaries

- Input coordinates/years/variables are constrained; campaign point names selected from fixed catalog.
- NASA source destination is predefined in the backend, not an arbitrary user-supplied URL.
- Errors are shown explicitly. No secrets or private user accounts are bundled.
- Local server defaults to loopback only; do not expose it publicly without a security and deployment review.
