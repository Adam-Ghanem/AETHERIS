"""Validated NASA POWER monthly point data access.

Monthly T2M is temperature (deg C). PRECTOTCORR is a precipitation rate
(mm/day), not a monthly precipitation total. Source unit metadata is included.
"""
from __future__ import annotations

import asyncio
import copy
import math
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import httpx

POWER_URL = "https://power.larc.nasa.gov/api/temporal/monthly/point"
SOURCE_URL = "https://power.larc.nasa.gov/docs/services/api/temporal/monthly/"
PARAMETERS = {
    "T2M": {"label": "2 m air temperature", "annual_unit": "°C", "monthly_unit": "°C", "kind": "temperature"},
    "PRECTOTCORR": {"label": "Corrected precipitation", "annual_unit": "mm", "monthly_unit": "mm/day", "kind": "precipitation"},
}


class DataError(Exception):
    def __init__(self, message: str, code: str = "UPSTREAM_ERROR", status: int = 502):
        super().__init__(message)
        self.code = code
        self.status = status


@dataclass(frozen=True)
class Observation:
    year: int
    month: int
    value: float

    def as_dict(self) -> dict:
        return {"year": self.year, "month": self.month, "value": self.value,
                "date": f"{self.year:04d}-{self.month:02d}"}


def validate_inputs(lat: float, lon: float, start: int, end: int, variable: str) -> None:
    if not (-90 <= lat <= 90 and -180 <= lon <= 180) or not (math.isfinite(lat) and math.isfinite(lon)):
        raise DataError("Latitude or longitude is outside valid bounds.", "INVALID_LOCATION", 422)
    if variable not in PARAMETERS:
        raise DataError("Unsupported scientific variable.", "UNSUPPORTED_VARIABLE", 422)
    if start < 1981 or end > datetime.now(timezone.utc).year - 1 or end - start < 7 or end - start > 44:
        raise DataError("Choose 8–45 complete historical years, starting 1981 or later, ending by last year.", "INVALID_YEARS", 422)
    if end < start:
        raise DataError("End year must be after start year.", "INVALID_YEARS", 422)


def parse_power(payload: dict[str, Any], variable: str, start: int, end: int) -> tuple[list[Observation], dict]:
    """Parse documented YYYYMM keys; ignore YYYY13 yearly aggregations."""
    try:
        data = payload["properties"]["parameter"][variable]
    except (KeyError, TypeError) as exc:
        raise DataError("NASA response lacks the requested parameter.", "MALFORMED_NASA_RESPONSE") from exc
    if not isinstance(data, dict):
        raise DataError("NASA monthly observations are malformed.", "MALFORMED_NASA_RESPONSE")
    info = payload.get("parameters", {}).get(variable, {})
    declared_unit = info.get("units") if isinstance(info, dict) else None
    if variable == "T2M" and declared_unit and declared_unit not in ("C", "°C", "degC", "deg C"):
        raise DataError(f"Unexpected temperature unit: {declared_unit}", "UNIT_MISMATCH")
    if variable == "PRECTOTCORR" and declared_unit and declared_unit not in ("mm/day", "mm/d"):
        raise DataError(f"Unexpected precipitation unit: {declared_unit}", "UNIT_MISMATCH")
    seen = set()
    out: list[Observation] = []
    bad_keys = []
    missing = 0
    for key, raw in data.items():
        if not (isinstance(key, str) and len(key) == 6 and key.isdigit()):
            continue
        year, month = int(key[:4]), int(key[4:])
        if not start <= year <= end or not 1 <= month <= 12:
            continue
        if (year, month) in seen:
            raise DataError("Duplicate NASA monthly observation.", "DUPLICATE_MONTH")
        seen.add((year, month))
        try:
            value = float(raw)
        except (TypeError, ValueError):
            bad_keys.append(key)
            continue
        # POWER sentinel is -999; documented invalid/sentinel records are rejected.
        if not math.isfinite(value) or value <= -990:
            missing += 1
            continue
        if variable == "PRECTOTCORR" and value < 0:
            raise DataError("Unexpected negative precipitation measurement.", "INVALID_SOURCE_VALUE")
        out.append(Observation(year, month, value))
    if bad_keys:
        raise DataError("NASA returned nonnumeric observations for: " + ", ".join(bad_keys[:3]), "MALFORMED_NASA_RESPONSE")
    out.sort(key=lambda p: (p.year, p.month))
    if not out:
        raise DataError("NASA returned no usable monthly observations for this period.", "NO_DATA", 422)
    expected = (end - start + 1) * 12
    metadata = {
        "source": "NASA POWER", "source_url": SOURCE_URL,
        "source_product": "POWER monthly point / MERRA-2 meteorological reanalysis",
        "variable": variable, "monthly_unit": PARAMETERS[variable]["monthly_unit"],
        "source_declared_unit": declared_unit or "not provided", "expected_months": expected,
        "valid_months": len(out), "missing_or_unavailable_months": expected - len(out),
        "sentinel_months": missing,
        "spatial_note": "Gridded, model-derived/reanalysis values sampled at a geographic point, not direct station measurements.",
        "temporal_note": "Monthly values; complete calendar years are used for long-term trends.",
        "raw_header": {k: payload.get("header", {}).get(k) for k in ("title", "api", "sources", "fill_value")},
    }
    return out, metadata


_cache: dict[tuple, tuple[float, list[Observation], dict]] = {}
_locks: dict[tuple, asyncio.Lock] = {}
_cache_ttl = 60 * 60 * 8


async def fetch_power(lat: float, lon: float, start: int, end: int, variable: str) -> tuple[list[Observation], dict]:
    validate_inputs(lat, lon, start, end, variable)
    key = (round(lat, 4), round(lon, 4), start, end, variable)
    item = _cache.get(key)
    if item and time.monotonic() - item[0] < _cache_ttl:
        meta = copy.deepcopy(item[2]); meta["cache"] = "hit"
        return list(item[1]), meta
    lock = _locks.setdefault(key, asyncio.Lock())
    async with lock:
        item = _cache.get(key)
        if item and time.monotonic() - item[0] < _cache_ttl:
            meta = copy.deepcopy(item[2]); meta["cache"] = "hit"
            return list(item[1]), meta
        params = {"parameters": variable, "community": "AG", "latitude": lat, "longitude": lon,
                  "start": start, "end": end, "format": "JSON"}
        last_error: Exception | None = None
        async with httpx.AsyncClient(timeout=httpx.Timeout(35, connect=10), follow_redirects=False) as client:
            for attempt in range(3):
                try:
                    response = await client.get(POWER_URL, params=params)
                    if response.status_code in (429, 500, 502, 503, 504):
                        raise httpx.HTTPStatusError("Retryable upstream status", request=response.request, response=response)
                    if response.status_code != 200:
                        raise DataError(f"NASA POWER returned HTTP {response.status_code}.", "NASA_REJECTED")
                    payload = response.json()
                    observations, meta = parse_power(payload, variable, start, end)
                    meta["retrieved_at"] = datetime.now(timezone.utc).isoformat()
                    meta["source_request"] = str(response.request.url)
                    meta["cache"] = "miss"
                    if len(_cache) > 150:
                        _cache.clear()
                    _cache[key] = (time.monotonic(), list(observations), copy.deepcopy(meta))
                    return observations, meta
                except (httpx.TransportError, httpx.HTTPStatusError, ValueError) as exc:
                    last_error = exc
                    if attempt < 2:
                        await asyncio.sleep(0.4 * (2 ** attempt))
                    continue
        raise DataError(f"NASA POWER is unavailable: {type(last_error).__name__ if last_error else 'unknown error'}", "NASA_UNAVAILABLE")
