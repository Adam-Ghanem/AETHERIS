# Scientific Quality Passport — methodology

Input: one successful NASA POWER monthly-point investigation. This module **does not** fetch extra data or run pretrained AI. It processes the same monthly values and annual trend already returned by the backend.

1. **Monthly completeness** counts distinct valid (year, month) observations. Expected count = 12 × requested inclusive year span. Input records are already validated by the NASA parser.
2. **Complete-year coverage** counts annual records with twelve valid months, which are the only annual values included in OLS/HAC trend analysis. Fully unavailable years appear as missing in the calendar matrix.
3. **Method agreement** compares only direction of OLS slope versus Theil–Sen slope. Agreement is not statistical validation.
4. **Leave-one-year-out sensitivity** recomputes elementary OLS slope with real calendar-year spacing after removing each one of the complete years. Direction stability and min/max slope are descriptive; no p-value is derived from this exercise.
5. **Residual lag-1** displays the existing regression residual serial-correlation estimate. The absolute 0.30 flag is merely an illustrative threshold to invite investigation. Lack of a flag does not show absence of dependence.

All trend slopes are expressed in the variable's annual unit per decade. The missing-month matrix displays availability only; it is not a climate heatmap. The source checksum is inherited from the parent investigation and detects changes to the locally processed observation serialization, not proof of NASA authenticity. All source data is NASA POWER gridded model/reanalysis, not local station measurements.

## Module location

- `aetheris/quality_passport.py` — pure diagnostic calculation
- `aetheris/science.py` — inclusion in `investigate(...)` response
- `static/quality-passport.js` — UI and JSON/text exports
- `static/quality-passport.css` — white/yellow responsive styling
- `tests/test_quality_passport.py` — automated checks

The UI is deliberately part of the Earth Explorer result rather than another disconnected sidebar page.
