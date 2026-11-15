# AETHERIS 3D Earth integration

The hero globe is a lightweight **Three.js/WebGL adaptation** of [GhostCatcg/3d-earth](https://github.com/GhostCatcg/3d-earth), MIT-licensed © 2022 GhostCat. It follows the original repository's globe texture, atmospheric glow, stars, rotating satellites, and flight-line concepts while fitting the AETHERIS white/yellow homepage.

- Original repository code uses TypeScript, Three.js, a GLSL shader, GSAP and Webpack. Since AETHERIS serves plain static JavaScript via FastAPI, we adapted the scene into `static/ghostcat-earth.js` rather than embedding a second webpack application.
- The actual `earth.jpg` Earth texture and compatible `three.min.js` are installed locally from the public original repository and JSDelivr CDN by `scripts/install_ghostcat_assets.py`; filenames and upstream origins remain documented. Bundled `earth-fallback.jpg` is an offline cartographic illustration derived from the app's bundled Natural Earth geography, not a satellite image.
- On Windows, `Start_AETHERIS.bat` tries to prepare the assets on the first run; download failures do **not** prevent the core application starting. With connectivity, the browser may alternatively load Three.js from a public CDN. If WebGL or Three.js is unavailable, `static/globe.js` keeps the previous offline 2D globe working.
- No scientific data, climate trend, or NASA imagery is inferred from the decorative globe. All analysis still comes from the existing AETHERIS science modules and their documented NASA sources.
- Drag to orbit, scroll to zoom, use arrow keys after focusing the globe, and pause/reset controls. Rendering is rate-limited and throttled outside the viewport or when the page is hidden, with reduced-motion support.
- The upstream MIT license text is included in `static/vendor/ghostcat-earth/LICENSE` and must accompany redistributions of this integration and associated assets.

## Verifying the globe

1. Start AETHERIS with `Start_AETHERIS.bat`.
2. Open the main Mission Overview screen.
3. Move the mouse over Earth, drag to rotate, scroll to zoom, and use Pause/Reset.
4. Browser console `document.documentElement.dataset.globeEngine` reports `ghostcat-webgl` or `offline-fallback`.
5. Check `static/vendor/ghostcat-earth/earth.jpg` and `three.min.js` to confirm the original textured WebGL experience has been installed. If installation failed, rerun `Install_3D_Earth.bat` with internet access.

The original source is licensed MIT, not NASA-branded. The AETHERIS application remains an independent project.
