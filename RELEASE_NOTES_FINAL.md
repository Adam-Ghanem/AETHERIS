# AETHERIS 14.0 — Final Submission Edition

## Major new feature: Research Campaign Studio

- One bounded, concurrent cross-location investigation of 2–6 selected points.
- Both NASA POWER `T2M` and `PRECTOTCORR` independently sourced and scientifically aggregated for every point.
- Exploratory HAC p-values and BH multiple-testing adjustment within **separate temperature and precipitation hypothesis families**.
- Partial NASA failures reported per point, without fabricated or interpolated results.
- User-selectable annual timeline, internal-baseline departures, descriptive compound flags, and complete point provenance.
- Download scientific evidence JSON, annual CSV and a self-contained offline HTML research presentation directly from the user interface.
- White/yellow responsive visual system inherited from 13.0 with new high-contrast campaign components.
- Prominent new Mission Control campaign entry and research sidebar navigation.

## Final submission kit

- Official-portal-ready description to adapt, demo narration, technical architecture, and checklist.
- Conceptual self-contained HTML pitch deck without fictional scientific measurements.
- A full source release, Windows launchers, method documentation, and explicit scientific limitations.

## Verification scope

- 142 backend/API/static tests passed in the working container.
- Browser component tested on 1440px and 390px screens using clearly labeled synthetic source fixtures: filters, yearly selection, CSV/JSON/HTML downloads and responsive layout.
- JavaScript syntax checked; archive integrity verified before delivery.
- Live NASA POWER connection from the working environment returned ConnectError: **not independently verified here**.
- Full browser-to-live-backend E2E not independently verified in this environment.
- Optional pretrained AI model not bundled or configured.

All scientific or geospatial claims should be communicated within the methodological boundaries documented in `README.md` and `docs/SCIENTIFIC_METHOD.md`.

## UI refinement — simplified top header

- Removed the redundant top-bar labels `GLOBAL RESEARCH INTERFACE` and `SYSTEM READY`.
- Removed the top breadcrumb `WORKSPACE / [active view]` across all pages, reclaiming vertical space.
- Preserved sidebar navigation, accessible view headings and the white/yellow research interface.
- Added a regression test for the simplified header and rechecked application tests.

## UI refinement — Change-point Lab

- Removed the `REAL NASA · REPRODUCIBLE` status pill from the Change-point Lab heading.
- Removed the large purely decorative ellipse/lines graphic and its unused CSS.
- Kept the actual scientific controls, change-point charts, explanatory copy, and white/yellow theme.
- Added regression tests to ensure the removed elements do not return.
