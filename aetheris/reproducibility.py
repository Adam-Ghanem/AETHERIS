"""Portable, independently re-checkable evidence capsule for AETHERIS research.

Package hashes detect accidental changes. They are not cryptographic signatures
and cannot independently prove data-provider authenticity.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import zipfile

ANNUAL_COLUMNS = ['year', 'value']
PAIRED_COLUMNS = [
    'year', 'temperature_c', 'precipitation_mm', 'temperature_departure_c',
    'precipitation_departure_mm', 'temperature_z', 'precipitation_z',
    'joint_hot_dry_deviation',
]


def _json_bytes(value: dict) -> bytes:
    return (json.dumps(value, sort_keys=True, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8')


def _csv_bytes(rows: list[dict], cols: list[str]) -> bytes:
    handle = io.StringIO(newline='')
    writer = csv.DictWriter(handle, fieldnames=cols, extrasaction='ignore', lineterminator='\n')
    writer.writeheader()
    for row in rows:
        writer.writerow({key: row.get(key, '') if row.get(key) is not None else '' for key in cols})
    return handle.getvalue().encode('utf-8')


VERIFIER = r'''#!/usr/bin/env python3
"""AETHERIS portable evidence verifier. Uses Python standard library only."""
import csv
import hashlib
import io
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def sha256(data):
    return hashlib.sha256(data).hexdigest()

def slope_decade(records):
    xs = [float(row['year']) for row in records]
    ys = [float(row['value']) for row in records]
    if len(xs) < 3 or len(set(xs)) < 3:
        raise ValueError('Insufficient years for independent OLS check')
    x0 = sum(xs) / len(xs)
    y0 = sum(ys) / len(ys)
    variance = sum((x - x0) ** 2 for x in xs)
    return 10 * sum((x - x0) * (y - y0) for x, y in zip(xs, ys)) / variance

def main():
    manifest = json.loads((ROOT / 'manifest.json').read_text(encoding='utf-8'))
    for name, expected in manifest['files_sha256'].items():
        actual = sha256((ROOT / name).read_bytes())
        if actual != expected:
            raise ValueError(f'File hash mismatch: {name}')
    report = json.loads((ROOT / 'briefing.json').read_text(encoding='utf-8'))
    if report['evidence']['briefing_sha256'] != manifest['source_fingerprint']['briefing_sha256']:
        raise ValueError('Briefing fingerprint mismatch')
    if report['evidence']['temperature']['sha256_monthly'] != manifest['source_fingerprint']['temperature_monthly_sha256']:
        raise ValueError('Temperature source fingerprint mismatch')
    if report['evidence']['precipitation']['sha256_monthly'] != manifest['source_fingerprint']['precipitation_monthly_sha256']:
        raise ValueError('Precipitation source fingerprint mismatch')
    for name, metric in [('temperature', 'T2M'), ('precipitation', 'PRECTOTCORR')]:
        path = ROOT / f'{name}_annual.csv'
        rows = list(csv.DictReader(io.StringIO(path.read_text(encoding='utf-8'))))
        numbers = slope_decade(rows)
        expected = next(f['trend_per_decade'] for f in report['findings'] if f['id'] == name)
        # Source annual fields may be rounded to 5 decimals; tolerate the implied rounding.
        if not math.isclose(numbers, expected, rel_tol=0, abs_tol=0.002):
            raise ValueError(f'{name} OLS mismatch: recomputed {numbers}, reported {expected}')
        print(f'PASS {metric} OLS trend: {numbers:+.4f} units/decade')
    paired = list(csv.DictReader((ROOT / 'paired_annual.csv').open(encoding='utf-8', newline='')))
    assert [int(r['year']) for r in paired] == [int(r['year']) for r in report['observations']], 'Paired-year mismatch'
    assert len(paired) == report['period']['shared_complete_years'], 'Paired count mismatch'
    print('PASS package hashes, paired years, source-fingerprint linkage and OLS trends.')
    print('NOTE: This verifies package consistency, not independent NASA authenticity, causal attribution, or HAC inference.')

if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print(f'FAIL: {exc}', file=sys.stderr)
        sys.exit(1)
'''

README = '''AETHERIS — Research Reproducibility Capsule
=============================================

Contents
--------
briefing.json          Full source-linked scientific narrative and numerical findings
paired_annual.csv      Annual paired NASA POWER-derived data used for compound indicators
temperature_annual.csv Annual observations used for the reported T2M OLS trend
precipitation_annual.csv Annual observations used for the reported rainfall OLS trend
manifest.json          SHA-256 checksums and evidence source fingerprints
verify.py              Offline verifier, Python standard library only

How to verify
-------------
1. Unzip the capsule to a folder.
2. Open a terminal in that folder.
3. Run: python verify.py

What the verifier checks
------------------------
- Files still match hashes recorded in the capsule manifest.
- Source fingerprints in manifest match those stored in the briefing.
- Independently recomputed linear trends agree with reported trend values.
- Paired observation years agree with the report.

Limitations
-----------
A package checksum is not a digital signature. Anyone who edits the package and
recalculates its manifest can produce matching checksums. This verifier does NOT
independently query NASA or guarantee the authenticity of the originating source.
Annual values are derived from NASA POWER gridded/model products, not a physical
weather station or region-average observation. The independent verification
covers OLS trend arithmetic; it does not independently verify HAC p-values or
prove causation, forecasts, or anthropogenic attribution.

If the application has no live NASA connection, the export must fail rather than
silently substituting test data.
'''


def build_reproducibility_zip(briefing: dict) -> bytes:
    """Build an offline export containing everything required to recheck OLS trends."""
    if not briefing.get('annual_inputs') or not briefing.get('evidence'):
        raise ValueError('Evidence briefing is missing independently verifiable annual inputs')
    required = ('temperature', 'precipitation')
    for key in required:
        records = briefing['annual_inputs'].get(key)
        if not isinstance(records, list) or len(records) < 8:
            raise ValueError(f'Missing annual observation inputs for {key}')
        years = [row['year'] for row in records]
        if years != sorted(set(years)):
            raise ValueError(f'Invalid annual time ordering for {key}')
        if not all(math.isfinite(float(row['value'])) for row in records):
            raise ValueError(f'Nonfinite annual values for {key}')
    if not briefing.get('observations'):
        raise ValueError('Paired data are unavailable')
    files = {
        'briefing.json': _json_bytes(briefing),
        'temperature_annual.csv': _csv_bytes(briefing['annual_inputs']['temperature'], ANNUAL_COLUMNS),
        'precipitation_annual.csv': _csv_bytes(briefing['annual_inputs']['precipitation'], ANNUAL_COLUMNS),
        'paired_annual.csv': _csv_bytes(briefing['observations'], PAIRED_COLUMNS),
        'verify.py': VERIFIER.encode('utf-8'),
        'README.txt': README.encode('utf-8'),
    }
    evid = briefing['evidence']
    is_fixture = any('synthetic' in str(evid[key].get('product', '')).lower() for key in ('temperature', 'precipitation'))
    manifest = {
        'schema': 'aetheris-reproducibility-v1',
        'source': ('SYNTHETIC TEST FIXTURE — NOT NASA OBSERVATIONS' if is_fixture
                   else 'NASA POWER (as recorded by the upstream AETHERIS investigation)'),
        'source_fingerprint': {
            'briefing_sha256': evid['briefing_sha256'],
            'temperature_monthly_sha256': evid['temperature']['sha256_monthly'],
            'precipitation_monthly_sha256': evid['precipitation']['sha256_monthly'],
        },
        'location': briefing['location'],
        'period': briefing['period'],
        'files_sha256': {name: hashlib.sha256(contents).hexdigest() for name, contents in sorted(files.items())},
        'verification_scope': 'file integrity, source-fingerprint linkage, annual OLS arithmetic and paired years',
        'authenticity_caveat': 'These checksums are not signatures and do not independently establish NASA authenticity.',
    }
    files['manifest.json'] = _json_bytes(manifest)
    output = io.BytesIO()
    with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        for name, contents in sorted(files.items()):
            archive.writestr(name, contents)
    return output.getvalue()
