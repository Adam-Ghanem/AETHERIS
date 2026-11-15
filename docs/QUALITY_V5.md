# AETHERIS 5.0 — Release verification

## Scope

This release is an in-place upgrade from AETHERIS 4.0, adding the independently validated **Earth Systems Coupling Lab**. It does not rewrite the original app or invent datasets. All existing modules remain accessible.

## Verified tests

- `python -m pytest tests -q`: **64 passed** (core V4 tests and 13 new coupled-systems tests).
- `node --check static/app.js`: **passed**.
- `python -m compileall -q aetheris`: **passed**.
- Chromium **desktop** (1440px) and **mobile** (390px) fixture-backed interaction tests: opened module, loaded data, rendered 4 metrics, 25 year buttons, 25 scatter points, selection detail, CSV/JSON exports, no JS exceptions and no horizontal overflow.
- Browser screenshots inspected; browser tests are **synthetic fixture-backed**. No fabricated data are shipped as live evidence.

## Scientific validation cases

- Two independent source fetch calls and preserved provenance.
- Verified annual trend slopes and coincident record pairing.
- Exclusion and disclosure of unpaired years.
- Rejection of mismatched coordinates and reversed parameter roles.
- Rejection of insufficient paired years and invalid endpoint inputs.
- Handling of zero-SD baseline without invented z-scores.
- Repeatability of evidence checksum.
- Explicit upstream failure when either source is unavailable.

## Known limitations

- Live NASA availability remains dependent on an internet-connected user environment; no live NASA retrieval was verified in this build session.
- Browsers are tested using controlled fixture responses, not production telemetry. Perform final live investigation on target Windows laptop.
- Data are point products and **not** equivalent to region-wide satellite rasters.
- Correlations and joint flags are descriptive. They are **not** causal, clinical, operational warnings, or validated climate-extreme event diagnostics.
- No heavy IBM/NASA Prithvi model weights included, and no pre-trained inference backend claimed connected.
- The app is a locally hosted research tool. Public production hosting would require infrastructure-specific controls.
