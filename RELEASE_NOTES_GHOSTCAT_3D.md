# AETHERIS Final — GhostCat 3D Earth Integration

**Base:** AETHERIS 14.0 Final Clean Visual Edition.

## Changes

- Replaced the flat homepage hero globe with a 3D/WebGL Three.js scene adapted from GhostCatcg/3d-earth (MIT license).
- Added spinning textured Earth, atmospheric glow, restrained starfield, animated satellite orbits, and schematic connection arcs for locations in Morocco.
- Preserved the original white/yellow AETHERIS design, navigation, NASA analytics and the previously requested clean-header/clean-visual removals.
- Added drag-to-rotate, mouse wheel zoom, keyboard arrow control, Pause rotation and Reset view.
- Kept the existing bundled 2D cartographic globe as an automatic fallback; animations pause outside view to protect lower-spec computers.
- Added a Windows installer that downloads the upstream Earth texture and compatible Three.js runtime; it never blocks the scientific application on download failure.
- Included the GhostCat MIT license and source attribution with technical integration documentation.

## Verification

- Python/API tests: 150 passed.
- Node.js syntax checks: both new and fallback JavaScript passed.
- Browser visual/WebGL run: **not verified in this environment**, because localhost access was blocked by the browser runner.
- Original upstream texture/runtime download: **not verified in this environment** due unavailable network; installer and CDN fallbacks provided for Windows.
- Scientific modules were preserved; no NASA data is simulated by the decorative globe.

## Installation

1. Extract ZIP and run `Start_AETHERIS.bat`.
2. If the 3D assets were not installed, run `Install_3D_Earth.bat` on a connected machine and restart the app.
3. Use the Mission Overview globe. If WebGL is unavailable, AETHERIS will display its existing 2D atlas.
