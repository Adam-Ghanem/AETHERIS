# Climate Constellation — Scientific UI

The chart uses the `observations` collection returned by `/api/v1/briefing`. Each point is a calendar year with both complete annual NASA POWER-derived data streams. No spatial interpolation is performed.

- X coordinate: `temperature_z`, annual temperature relative to the **internal first-up-to-10-common-years baseline**, expressed in sample standard-deviation units.
- Y coordinate: `precipitation_z`, analogous annual precipitation departure from the corresponding internal baseline.
- The warm/dry screening region uses the same rule as the underlying Earth Systems Lab (`temperature_z >= 1`, `precipitation_z <= -1`). These are exploratory standardized-deviation flags, not an established drought index.
- Clicking a plotted year also updates the briefing's existing annual comparison selector and its matrix selection, retaining synchronized user context.
- A baseline with zero sample variance produces `null` standardized departures and therefore no numeric points. The module renders an explicit unavailable state.
- The tooltip/title and selected-year inspector show the actual annual °C and mm values, not synthetic estimates.

Previews supplied in the package were rendered using **clearly synthetic fixtures**, not live NASA observations. Scientific conclusions must be checked against live retrieved NASA source data.
