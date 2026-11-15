# AETHERIS — Vercel deployment

This is the full AETHERIS FastAPI web application, adapted for Vercel.

## Deploy
1. Upload the **contents** of this folder to the root of your public `Adam-Ghanem/AETHERIS` GitHub repository. Keep the `aetheris/`, `static/`, and `app.py` paths intact.
2. In Vercel, import `Adam-Ghanem/AETHERIS` and choose framework **FastAPI**. Root Directory should be project root.
3. No build command or output directory required. The `app.py` entrypoint exports the FastAPI application.
4. Check `/api/v1/health`, the home page, and then run a real NASA request.

## Notes
- NASA API availability is external; timeouts are handled but can occur.
- The 3D globe can use its fallback if `three.min.js` or `earth.jpg` are unavailable. For offline/reliable visual rendering, install verified assets locally before publishing, with attribution.
- The 3D Earth adapts GhostCat's MIT licensed work. See the attribution in `docs/GHOSTCAT_3D_EARTH.md`.
- Keep any API keys in Vercel project environment variables, never in the repository.
- A public Vercel deployment requires manual live validation; passing local tests does not establish cloud reliability.
