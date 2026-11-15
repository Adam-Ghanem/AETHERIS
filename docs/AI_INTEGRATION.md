# AETHERIS External AI Engine — Integration Specification

**The application works without a model.** This module only connects a separately trained and evaluated external inference service (e.g., your teammate's CPU model or cloud-hosted AI). It is not a promise that NASA Prithvi is running locally.

## Why this architecture

The NASA–IBM Prithvi Weather & Climate foundation model accepts highly structured atmospheric data fields (e.g., MERRA-2 tensors). It **does not directly consume a NASA POWER monthly point CSV** as-is. Its hardware and data preparation are beyond the scope of the lightweight AETHERIS web server. Your teammate can separately run a suitable model, evaluate it, then expose a small and verified inference HTTP endpoint.

A CPU-friendly pretrained time-series model, or a compact anomaly detector, may be a more suitable first deployment **after benchmarking**. No special label such as "NASA AI" should be assigned to non-NASA models.

## Input contract — POST /infer

AETHERIS performs a NASA lookup and statistical analysis, then POSTs a payload with:

```json
{
  "schema_version": "1.0",
  "variable": "T2M",
  "unit": "°C",
  "location": {"latitude": 32.337, "longitude": -6.349},
  "annual_observations": [{"year": 2001, "value": 18.5}],
  "data_sha256": "...",
  "provider": "NASA POWER",
  "processing_note": "Annual NASA POWER gridded/reanalysis data, not ground-station readings."
}
```

`annual_observations` contains at least eight years of actual data; the one-row snippet above is illustrative **only**, not a sample dataset.

Auth: `Authorization: Bearer <token>` if `AETHERIS_AI_TOKEN` is configured. Transport: HTTPS, or loopback-only HTTP when both services run on one trusted computer.

## Required output contract

```json
{
  "schema_version": "1.0",
  "model_name": "Your actual evaluated model name",
  "model_version": "1.2.0",
  "model_type": "Isolation Forest",
  "methodology": "Document the precise real preprocessing and inference method here.",
  "data_provenance": "Document the actual training data sources and model version.",
  "limitations": ["This is model-specific anomaly scoring and not climate attribution."],
  "signals": [
    {"year": 2019, "anomaly_score": 0.73, "is_anomaly": true,
     "explanation": "Explanation grounded in actual model features and thresholds."}
  ]
}
```

Output constraints:

- Scores must be **normalized to the 0–1 range**, with higher meaning more anomalous, and calibrated/documented for that model.
- Scores are neither p-values nor confidence probabilities unless a separately validated probability interpretation exists.
- `signals.year` must correspond to an actual year in the supplied observations.
- Response must include version, source provenance, methodology, at least one limitation and at most 100 signals.
- The external inference service must have trained and tested its model independently. No model training is done by AETHERIS on the local client.

## Connection

Set environment variables on the computer hosting the FastAPI server:

```powershell
$env:AETHERIS_AI_ENDPOINT="https://YOUR-TRUSTED-HOST/infer"
$env:AETHERIS_AI_TOKEN="YOUR-REAL-SECRET"
.venv\Scripts\python.exe -m uvicorn aetheris.server:app --host 127.0.0.1 --port 8765
```

Then open a NASA investigation and click `Run connected AI`. For local use, the endpoint may be `http://127.0.0.1:8002/infer` if a real model server runs there. The UI shows `not connected` until an allowed endpoint is configured. Secrets are never passed in client-side JavaScript.

## Scientific responsibilities

Do not equate outliers with changing climate trends; do not claim independent ground truth without labels. Use chronological validation, baselines, known data provenance, a model card, and honestly reported false alert rates. Validate that the model adds value beyond robust statistical baselines.
