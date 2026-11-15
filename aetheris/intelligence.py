"""Optional, administrator-configured external inference engine.

No AI weights are bundled. The AETHERIS scientific engine remains functional
without external inference. A configured trusted inference endpoint must honor
this explicit contract and report its model provenance and limitations.
"""
from __future__ import annotations

import os
from urllib.parse import urlparse
from typing import Any

import httpx
from pydantic import BaseModel, Field, ConfigDict

from .nasa import DataError


class ModelSignal(BaseModel):
    model_config = ConfigDict(extra='forbid')
    year: int = Field(ge=1900, le=2200)
    anomaly_score: float = Field(ge=0, le=1)
    is_anomaly: bool
    explanation: str = Field(max_length=300)


class ModelOutput(BaseModel):
    model_config = ConfigDict(extra='forbid')
    schema_version: str = '1.0'
    model_name: str = Field(min_length=2, max_length=120)
    model_version: str = Field(min_length=1, max_length=60)
    model_type: str = Field(min_length=2, max_length=100)
    methodology: str = Field(min_length=12, max_length=1000)
    data_provenance: str = Field(min_length=12, max_length=1000)
    limitations: list[str] = Field(min_length=1, max_length=10)
    signals: list[ModelSignal] = Field(max_length=100)


def configured_endpoint() -> str | None:
    url=os.getenv('AETHERIS_AI_ENDPOINT','').strip()
    if not url:
        return None
    parsed=urlparse(url)
    local=(parsed.hostname in ('localhost','127.0.0.1','::1'))
    if not (parsed.scheme=='https' or (parsed.scheme=='http' and local)):
        return None
    if parsed.username or parsed.password or not parsed.netloc or parsed.fragment:
        return None
    return url


async def run_external_inference(result: dict) -> dict:
    endpoint=configured_endpoint()
    if not endpoint:
        raise DataError('An external AI model has not been connected. Scientific analysis is available without it.', 'AI_NOT_CONFIGURED',503)
    payload={
        'schema_version':'1.0',
        'variable':result['variable']['id'],
        'unit':result['trend']['annual_unit'],
        'location':result['location'],
        'annual_observations':result['annual'],
        'data_sha256':result['evidence']['sha256_monthly'],
        'provider':result['evidence']['provider'],
        'processing_note':'Annual NASA POWER gridded/reanalysis data, not ground-station readings.',
    }
    token=os.getenv('AETHERIS_AI_TOKEN','').strip()
    headers={'Authorization':f'Bearer {token}'} if token else {}
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(45,connect=8),follow_redirects=False) as client:
            response=await client.post(endpoint,json=payload,headers=headers)
            response.raise_for_status()
            raw=response.json()
        validated=ModelOutput.model_validate(raw)
        years={x['year'] for x in result['annual']}
        if any(s.year not in years for s in validated.signals):
            raise ValueError('Model returned signals for years outside the analyzed observations.')
    except (httpx.HTTPError, ValueError, TypeError) as err:
        raise DataError(f'Configured AI engine failed: {type(err).__name__}', 'AI_INFERENCE_FAILED',502) from err
    except Exception as err:
        # Pydantic validation errors: do not leak remote output or credentials.
        raise DataError(f'Configured AI engine returned an invalid contract: {type(err).__name__}', 'AI_INVALID_RESPONSE',502) from err
    return {'status':'ok','model':validated.model_dump(),
            'scientific_context':{'observation_sha256':result['evidence']['sha256_monthly'],
                                  'variable':result['variable']['id'],
                                  'period':result['period'],
                                  'warning':'ML anomalies are not statistical trend significance or proof of climate-change causation.'}}
