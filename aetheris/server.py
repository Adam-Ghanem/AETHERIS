"""FastAPI server for AETHERIS, serving both API and the integrated web UI."""
from __future__ import annotations

import asyncio
import logging
import math
from .reproducibility import build_reproducibility_zip
from .campaign import run_campaign
from pathlib import Path

from fastapi import FastAPI, Request, Query
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles

from .nasa import DataError, PARAMETERS, fetch_power, validate_inputs
from .science import investigate
from .discovery import scan_locations
from .spatial import spatial_scan
from .time_machine import time_machine_scan
from .systems import run_systems
from .briefing import run_briefing
from .seasonal_signals import run_seasonal_signals
from .change_points import analyze_change_points
from .forensics import analyze_forensics
from .reports import build_pdf_report
from .intelligence import configured_endpoint, run_external_inference

ROOT = Path(__file__).resolve().parent.parent
logger = logging.getLogger("aetheris")
app = FastAPI(title="AETHERIS — Earth Intelligence", version="14.0.0",
              description="Earth-system trend investigations using NASA POWER meteorological data. Not affiliated with NASA.")
app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")

LOCATIONS = [
    {"name": "Beni Mellal", "country": "Morocco", "lat": 32.337, "lon": -6.349, "subtitle": "Atlas foothills"},
    {"name": "Marrakech", "country": "Morocco", "lat": 31.6295, "lon": -7.9811, "subtitle": "Inland plains"},
    {"name": "Casablanca", "country": "Morocco", "lat": 33.5731, "lon": -7.5898, "subtitle": "Atlantic coast"},
    {"name": "Ouarzazate", "country": "Morocco", "lat": 30.9189, "lon": -6.8934, "subtitle": "Arid interior"},
    {"name": "Agadir", "country": "Morocco", "lat": 30.4278, "lon": -9.5981, "subtitle": "Atlantic region"},
    {"name": "Cairo", "country": "Egypt", "lat": 30.0444, "lon": 31.2357, "subtitle": "Nile delta"},
    {"name": "Nairobi", "country": "Kenya", "lat": -1.2921, "lon": 36.8219, "subtitle": "East Africa"},
    {"name": "New York", "country": "USA", "lat": 40.7128, "lon": -74.006, "subtitle": "North America"},
    {"name": "Tokyo", "country": "Japan", "lat": 35.6762, "lon": 139.6503, "subtitle": "East Asia"},
]


@app.exception_handler(DataError)
async def data_error_handler(request: Request, exc: DataError):
    return JSONResponse(status_code=exc.status, content={"error": {"code": exc.code, "message": str(exc)}})


@app.get("/")
async def index():
    return FileResponse(ROOT / "static" / "index.html")


@app.get("/api/v1/health")
async def health():
    return {"status": "ok", "service": "AETHERIS", "version": "14.0.0", "data_provider": "NASA POWER"}


@app.get("/api/v1/catalog")
async def catalog():
    return {"locations": LOCATIONS, "variables": PARAMETERS, "period": {"min_year": 1981, "max_year": 2025},
            "notes": "Historical NASA POWER monthly data; variable availability depends on product and region."}


@app.get("/api/v1/investigate")
async def analyze(lat: float = Query(ge=-90, le=90), lon: float = Query(ge=-180, le=180),
                  start: int = Query(default=2001, ge=1981), end: int = Query(default=2025, le=2100),
                  variable: str = "T2M"):
    validate_inputs(lat, lon, start, end, variable)
    observations, meta = await fetch_power(lat, lon, start, end, variable)
    return investigate(observations, meta, variable, lat, lon, start, end)


@app.get("/api/v1/forensics")
async def forensics(lat: float = Query(ge=-90, le=90), lon: float = Query(ge=-180, le=180),
                    start: int = Query(default=2001, ge=1981), end: int = Query(default=2025, le=2100),
                    variable: str = "T2M", window: int = Query(default=7, ge=3, le=15)):
    """Independent descriptive diagnostics, traceable to the same NASA monthly observations."""
    validate_inputs(lat, lon, start, end, variable)
    observations, meta = await fetch_power(lat, lon, start, end, variable)
    investigation = investigate(observations, meta, variable, lat, lon, start, end)
    return analyze_forensics(investigation, observations, window=window)


@app.get("/api/v1/compare")
async def compare(lat_a: float = Query(ge=-90, le=90), lon_a: float = Query(ge=-180, le=180),
                  lat_b: float = Query(ge=-90, le=90), lon_b: float = Query(ge=-180, le=180),
                  start: int = Query(default=2001, ge=1981), end: int = Query(default=2025, le=2100),
                  variable: str = "T2M"):
    validate_inputs(lat_a, lon_a, start, end, variable)
    validate_inputs(lat_b, lon_b, start, end, variable)
    data = await asyncio.gather(fetch_power(lat_a, lon_a, start, end, variable),
                                fetch_power(lat_b, lon_b, start, end, variable))
    a = investigate(*data[0], variable, lat_a, lon_a, start, end)
    b = investigate(*data[1], variable, lat_b, lon_b, start, end)
    return {"first": a, "second": b,
            "comparison_note": "Comparisons are exploratory; point observations do not represent entire administrative regions."}


@app.get('/api/v1/discover')
async def discover(locations: str = 'Beni Mellal,Marrakech,Casablanca,Ouarzazate',
                   start: int = Query(default=2001, ge=1981), end: int = Query(default=2025, le=2100),
                   variable: str = 'T2M'):
    """Scan 2-6 explicit verified presets, no interpolation or spatial claims."""
    choices = [name.strip() for name in locations.split(',')]
    if len(choices) < 2 or len(choices) > 6 or len(set(choices)) != len(choices):
        raise DataError('Select 2-6 unique preset locations.', 'INVALID_SCAN_LOCATIONS', 422)
    known = {place['name']:place for place in LOCATIONS}
    if any(name not in known for name in choices):
        raise DataError('Unknown scan location.', 'INVALID_SCAN_LOCATIONS', 422)
    return await scan_locations([known[name] for name in choices],start,end,variable)


@app.get('/api/v1/campaign')
async def campaign(locations: str = 'Beni Mellal,Marrakech,Casablanca,Ouarzazate',
                   start: int = Query(default=2001, ge=1981), end: int = Query(default=2025, le=2100)):
    """One campaign, both NASA variables, bounded concurrent point requests."""
    choices = [name.strip() for name in locations.split(',')]
    if not 2 <= len(choices) <= 6 or len(set(choices)) != len(choices):
        raise DataError('Choose 2–6 unique preset locations.', 'INVALID_CAMPAIGN_POINTS', 422)
    known = {loc['name']: loc for loc in LOCATIONS}
    if any(name not in known for name in choices):
        raise DataError('Unknown preset campaign location.', 'INVALID_CAMPAIGN_POINTS', 422)
    return await run_campaign([known[name] for name in choices], start, end)


@app.get('/api/v1/systems')
async def earth_systems(lat: float = Query(ge=-90, le=90), lon: float = Query(ge=-180, le=180),
                        start: int = Query(default=2001, ge=1981), end: int = Query(default=2025, le=2100)):
    """Real two-variable NASA investigation, with a joint evidence manifest."""
    return await run_systems(lat, lon, start, end)


@app.get('/api/v1/briefing')
async def evidence_briefing(lat: float = Query(ge=-90, le=90), lon: float = Query(ge=-180, le=180),
                            start: int = Query(default=2001, ge=1981), end: int = Query(default=2025, le=2100)):
    """Produce a source-backed, two-variable evidence story without generative AI."""
    return await run_briefing(lat, lon, start, end)


@app.get('/api/v1/reproducibility.zip')
async def reproducibility_capsule(lat: float = Query(ge=-90, le=90), lon: float = Query(ge=-180, le=180),
                                  start: int = Query(default=2001, ge=1981), end: int = Query(default=2025, le=2100)):
    """Re-fetch source-backed data and package annual inputs, complete evidence and an independent verifier."""
    report = await run_briefing(lat, lon, start, end)
    payload = build_reproducibility_zip(report)
    return Response(content=payload, media_type='application/zip', headers={
        'Content-Disposition': 'attachment; filename="AETHERIS_Reproducibility_Capsule.zip"',
        'Cache-Control': 'private, no-store',
        'X-Content-Type-Options': 'nosniff',
    })


@app.get('/api/v1/change-points')
async def change_points(lat: float = Query(ge=-90, le=90), lon: float = Query(ge=-180, le=180),
                        start: int = Query(default=2001, ge=1981), end: int = Query(default=2025, le=2100),
                        variable: str = 'T2M', min_segment_years: int = Query(default=6, ge=5, le=10)):
    """Compare linear trends with exploratory continuous trend-break candidates."""
    validate_inputs(lat, lon, start, end, variable)
    observations, meta = await fetch_power(lat, lon, start, end, variable)
    investigation = investigate(observations, meta, variable, lat, lon, start, end)
    return analyze_change_points(investigation, min_segment_years=min_segment_years)


@app.get('/api/v1/seasonal-signals')
async def seasonal_signals(lat: float = Query(ge=-90, le=90), lon: float = Query(ge=-180, le=180),
                           start: int = Query(default=2001, ge=1981), end: int = Query(default=2025, le=2100),
                           variable: str = 'T2M'):
    """Auditable month-by-month trends, multiplicity and anomaly matrix."""
    return await run_seasonal_signals(lat, lon, start, end, variable)


@app.get('/api/v1/spatial')
async def spatial(lat: float = Query(ge=-75, le=75), lon: float = Query(ge=-180, le=180),
                  start: int = Query(default=2001, ge=1981), end: int = Query(default=2025, le=2100),
                  variable: str = 'T2M', spacing_km: int = Query(default=100)):
    """Nine real independent source queries for a local geographic point grid."""
    return await spatial_scan(lat, lon, start, end, variable, spacing_km)


@app.get('/api/v1/time-machine')
async def time_machine(lat: float = Query(ge=-75, le=75), lon: float = Query(ge=-180, le=180),
                       start: int = Query(default=2001, ge=1981), end: int = Query(default=2025, le=2100),
                       variable: str = 'T2M', spacing_km: int = Query(default=100)):
    """Reconstruct 3x3 annual anomaly snapshots with fixed pointwise baselines."""
    return await time_machine_scan(lat,lon,start,end,variable,spacing_km)


@app.get('/api/v1/report.pdf')
async def report_pdf(lat: float = Query(ge=-90, le=90), lon: float = Query(ge=-180, le=180),
                     start: int = Query(default=2001, ge=1981), end: int = Query(default=2025, le=2100),
                     variable: str = 'T2M', place: str = 'Selected point'):
    validate_inputs(lat,lon,start,end,variable)
    observations, meta = await fetch_power(lat,lon,start,end,variable)
    data = investigate(observations,meta,variable,lat,lon,start,end)
    safe_place = ''.join(ch for ch in place if ch.isalnum() or ch in ' .,-_')[:60].strip() or 'Selected point'
    payload = build_pdf_report(data,safe_place)
    return Response(content=payload, media_type='application/pdf',headers={
        'Content-Disposition': 'attachment; filename="AETHERIS_scientific_report.pdf"',
        'Cache-Control': 'private, no-store',
    })


@app.get('/api/v1/intelligence/status')
async def intelligence_status():
    """No spurious claims that an external pretrained model is deployed."""
    available = configured_endpoint() is not None
    return {'status':'configured' if available else 'not_connected','model':None,'available':available,
            'message':'AETHERIS ML models are an optional, independently supplied module. Statistical trend and seasonal diagnostics work without them.',
            'integration_guide':'docs/AI_INTEGRATION.md'}


@app.get('/api/v1/intelligence/analyze')
async def intelligence_analyze(lat: float = Query(ge=-90, le=90), lon: float = Query(ge=-180, le=180),
                               start: int = Query(default=2001, ge=1981), end: int = Query(default=2025, le=2100),
                               variable: str = 'T2M'):
    if not configured_endpoint():
        raise DataError('No verified AI model endpoint is configured.', 'AI_NOT_CONFIGURED',503)
    validate_inputs(lat,lon,start,end,variable)
    observations,meta=await fetch_power(lat,lon,start,end,variable)
    investigation=investigate(observations,meta,variable,lat,lon,start,end)
    return await run_external_inference(investigation)
