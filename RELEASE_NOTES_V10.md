# AETHERIS 10.0 — Solar Research Edition

## What changed

- Reworked the complete app's visual system from navy/teal to **white, warm yellow and ink**. This is not a screenshot overlay: `static/theme-solar.css` is loaded by the real application after the legacy stylesheets and applies to all 13 workspace sections, forms, scientific results, alerts, navigation, interactive matrices and mobile layout.
- Preserved distinct temperature (gold) and rainfall (blue) scientific series so users can distinguish variables without relying solely on color; chart axis labels and map outlines also have light-background contrast.
- Fixed mobile Mission Control's decorative globe overlapping text by placing the globe in a separate layout row.
- New **Run Beni Mellal research** button on Mission Control. It opens the actual Evidence Command Center and submits a new paired NASA POWER request through the existing validated form.
- New **Copy research link** on a completed briefing. It serializes validated geographic coordinates and analysis dates, not results. Opening that link on the same reachable AETHERIS deployment re-runs the source-backed query. Locally hosted `127.0.0.1` links are usable only on the same device; no public hosting is implied.
- Added an explicit interpretation notice for the deterministic, non-forecast nature of the paired evidence results.
- Retained scientific modules, their inputs and calculations, exports, and independent ML bridge. No AI model is represented as installed.

## Verification

- Existing Python/API tests plus Solar V10 regression tests run under Pytest.
- JavaScript syntax checks for all application scripts.
- Fixture-backed Chromium rendering for 1440×900 and 390×844 viewports: one-click investigation, yearly selection, source fixture labeling, mobile layout, no JS page errors, and no horizontal overflow.
- CSS inspection of empty-state views for all research sections to remove remaining dark panels.
- Real NASA data connectivity on user's Windows computer remains unverified; the synthetic fixture is explicitly marked in screenshots.

## Known limitations

- No pre-trained NASA–IBM Prithvi model is bundled; AI bridge remains optional.
- The core backend and statistical methods are unchanged from V9. This release prioritizes usability, interface consistency, accessibility and reopening research configurations.
- Share links re-query data, and are not permanent snapshots of source results. Saved investigation links require access to an operational AETHERIS instance.
