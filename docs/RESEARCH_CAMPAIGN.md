# Research Campaign Studio — scientific methodology

Research Campaign Studio is a cross-location paired investigation, not a satellite raster or continuous interpolated heatmap.

### Input and processing

1. User selects 2–6 names from a fixed catalog of georeferenced sample points and selects start/end years.
2. A bounded concurrency queue calls the existing `run_systems` pipeline for each point, independently retrieving both NASA POWER monthly products (`T2M`, `PRECTOTCORR`).
3. Only complete annual records are used for analysis; paired annual observations require both products.
4. Temperature annual values are calendar-day-weighted mean °C. Corrected precipitation is converted from monthly mm/day to estimated annual total mm.
5. Each point receives independent annual OLS/HAC inference (slope and exploratory p-value), source metadata, missing-year records, a SHA-256 source-pair fingerprint, and descriptive within-point baseline departures.
6. Benjamini–Hochberg adjustment is applied **separately** to the valid temperature p-values and valid precipitation p-values among successfully evaluated selected points.
7. A location failure remains visible as an error row, never as a zero result. Partial analysis is labeled as partial.

### Outputs

- Temperature and precipitation slope bars with correct physical units and exploratory BH q-values.
- Historical year explorer with pointwise observed annual values, departures and descriptive compound flags.
- JSON evidence, CSV annual values and an offline HTML presentation computed from the actual returned data.
- Campaign SHA-256 fingerprint derived from source pair fingerprints plus study definitions. It is an integrity marker, not a NASA-issued signature or proof that statistical inferences are true.

### Limitations

The selected locations are a convenience sample, not a representative spatial survey. FDR control can be affected by spatial dependence or retrospective point selection. Each `T2M`/`PRECTOTCORR` product represents a NASA POWER gridded/model-derived point, not a direct weather station or an entire city. Within-series departures relative to an internal baseline are descriptive and not necessarily 30-year climate normals. Joint hot/dry departures are **not** validated drought criteria, prediction, or causal attribution.
