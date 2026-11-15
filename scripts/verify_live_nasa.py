"""Optional *live* smoke test. This script makes real NASA POWER API requests.

Run it only with working internet. It is intentionally separate from unit tests,
which use synthetic fixture data and never claim network verification.
"""
from __future__ import annotations

import asyncio
import json
from pathlib import Path
import sys

# Allow execution from any directory, including Windows batch launchers.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from aetheris.nasa import fetch_power, DataError
from aetheris.science import investigate
from aetheris.forensics import analyze_forensics


async def main() -> int:
    for variable in ('T2M', 'PRECTOTCORR'):
        print(f'Checking NASA POWER / Beni Mellal / 2001-2025 / {variable}...', flush=True)
        try:
            obs, meta = await fetch_power(32.337, -6.349, 2001, 2025, variable)
            result = investigate(obs, meta, variable, 32.337, -6.349, 2001, 2025)
            forensic = analyze_forensics(result, obs)
        except DataError as e:
            print(f'FAIL {e.code}: {e}', flush=True)
            return 1
        print(json.dumps({
            'status':'LIVE NASA VERIFIED',
            'variable':variable,
            'months':len(obs),
            'years':len(result['annual']),
            'slope_per_decade':result['trend']['slope_per_decade'],
            'slope_unit':result['trend']['slope_unit'],
            'source_product':meta.get('source_product'),
            'fingerprint':result['evidence']['sha256_monthly'][:20],
            'forensics_months':len(forensic['seasonal_shift']['months']),
        }, indent=2))
    return 0


if __name__=='__main__':
    sys.exit(asyncio.run(main()))
