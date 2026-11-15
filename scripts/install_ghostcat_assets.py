"""Install original GhostCat 3d-earth texture and compatible Three.js runtime.

This installer is optional: AETHERIS works using its existing offline globe when
external resources cannot be downloaded. MIT credit remains in package.
"""
from __future__ import annotations

from pathlib import Path
from urllib.request import Request, urlopen
import os
import sys

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / 'static' / 'vendor' / 'ghostcat-earth'
DEST.mkdir(parents=True, exist_ok=True)
ASSETS = (
    ('earth.jpg', (
        'https://raw.githubusercontent.com/GhostCatcg/3d-earth/main/static/images/earth/earth.jpg',
        'https://cdn.jsdelivr.net/gh/GhostCatcg/3d-earth@main/static/images/earth/earth.jpg',
    ), 600_000, b'\xff\xd8'),
    ('three.min.js', (
        'https://cdn.jsdelivr.net/npm/three@0.143.0/build/three.min.js',
        'https://unpkg.com/three@0.143.0/build/three.min.js',
    ), 200_000, None),
)

def install_one(name: str, urls: tuple[str, ...], minimum: int, magic: bytes | None) -> bool:
    target = DEST / name
    if target.exists() and target.stat().st_size >= minimum:
        print('[OK] Installed:', name)
        return True
    for url in urls:
        try:
            with urlopen(Request(url, headers={'User-Agent': 'AETHERIS-3D-asset-installer/1.0'}), timeout=5) as response:
                size = 0
                parts = []
                while True:
                    chunk = response.read(128_000)
                    if not chunk:
                        break
                    parts.append(chunk)
                    size += len(chunk)
                    if size > 6_000_000:
                        raise ValueError('Unexpected asset size')
            data = b''.join(parts)
            if len(data) < minimum or (magic and not data.startswith(magic)):
                raise ValueError('Unexpected content (possible download error)')
            if name.endswith('.js') and b'THREE' not in data[:80_000]:
                raise ValueError('Response is not a Three.js runtime')
            tmp = target.with_suffix(target.suffix + '.tmp')
            tmp.write_bytes(data)
            os.replace(tmp, target)
            print('[OK]', name, 'downloaded from', url, '(', len(data), 'bytes )')
            return True
        except Exception as exc:
            print('[WARN] Could not download', name, 'from', url.split('/')[2], ':', type(exc).__name__)
    return False

if __name__ == '__main__':
    results = [install_one(*asset) for asset in ASSETS]
    # Auto-setup only runs once; use Install_3D_Earth.bat to retry manually.
    (DEST / '.setup-attempted').write_text('attempted\n', encoding='utf-8')
    if all(results):
        print('[OK] 3D Earth assets ready. MIT license: static/vendor/ghostcat-earth/LICENSE')
    else:
        print('[INFO] Missing optional files; AETHERIS falls back to the existing offline globe.')
    # The globe is optional and must not block core AETHERIS research tools.
    sys.exit(0)
