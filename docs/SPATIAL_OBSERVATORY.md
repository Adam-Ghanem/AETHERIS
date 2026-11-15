# AETHERIS Spatial Observatory — Engineering & Scientific Specification

## What it does

`GET /api/v1/spatial` samples a 3 × 3 array of **nine actual NASA POWER point time series**, runs the existing annual aggregation and HAC-robust OLS trend engine on each, adjusts available p-values using Benjamini–Hochberg within the selected family, and returns a traceable JSON result. This module is an exploratory *spatial comparison of sampled point trends*, not a continuous climate raster or spatial model.

The browser draws **nine discrete data cells** arranged north-to-south and west-to-east. Color is relative to the min/max trend among successfully returned samples, and does not imply interpolated values between the sample points. Each cell is selectable, displays geographic coordinates, annual-years count, HAC p-value and adjusted q-value, and links back to the full single-point Earth Explorer investigation. Point-level and full-evidence CSV/JSON are exportable.

## API

Example:

`GET /api/v1/spatial?lat=32.337&lon=-6.349&start=2001&end=2025&variable=T2M&spacing_km=100`

Parameters: center lat [-75, 75], lon [-180, 180], valid full-year period (8–45 historical years), variable (`T2M`, `PRECTOTCORR`), spacing in {50, 100, 150} km. Spatial placement uses a **documented local geographic approximation**: 111.195 km/degree latitude and a latitude-cosine correction for longitude. This is an approximate coordinate design, not an exact geographic buffer.

Each point independently retrieves the NASA POWER monthly series and reports its source-data SHA-256. Queries are capped at nine points and limited to two concurrent NASA requests per scan. Backend cache reuses unchanged NASA responses. Partial source failures stay explicitly visible, and the endpoint returns HTTP 502 if **all nine source requests fail**. No fake fallback results are used.

## Key caveats

- NASA POWER meteorological products are gridded/reanalysis series, not high-resolution satellite imagery, in situ station observations, or a municipal/administrative mean.
- Two nearby chosen coordinates may map to the *same underlying data cell*. The nine samples are not guaranteed to be independent.
- HAC significance and BH adjustments are *exploratory*. Spatial dependence and retrospective center selection can undermine nominal false-discovery interpretation.
- A high/low slope spread is descriptive, not a causal conclusion, a cluster analysis, or evidence of a region-wide effect.
- Failed sites remain marked as unavailable and are excluded from numerical summaries. Maps do not interpolate or fill them.
- Browser test screenshots use labeled synthetic fixtures. They are not proof that live NASA data has been fetched.

## Performance and accessibility

- Preset-based or custom coordinates. The user can start a Spatial Observatory scan directly from an Earth Explorer result.
- Structured API responses, keyboard-accessible data cells, mobile-friendly layout and mobile navigation drawer.
- Bundled Natural Earth geometry powers the decorative orthographic globe and vector world map with no mapping-service keys; the globe is **cartography only**, not a NASA measurement layer.
- Live scans depend on network availability and NASA API behavior. For public hosting, add shared rate limiting and distributed caching beyond the local defaults.
