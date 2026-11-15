"""Check that extracted AETHERIS files match packaged SHA-256 checksums.

The checksums detect accidental changes and corruption, not malicious substitution.
"""
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent
checks = ROOT / 'SHA256SUMS.txt'
if not checks.exists():
    raise SystemExit('FAIL: SHA256SUMS.txt is missing')
issues = []
verified = 0
for raw in checks.read_text(encoding='utf-8').splitlines():
    if not raw.strip():
        continue
    try:
        expected, relative = raw.split('  ', 1)
    except ValueError:
        issues.append('malformed manifest entry')
        continue
    path = (ROOT / relative).resolve()
    if not path.is_relative_to(ROOT.resolve()) or not path.is_file():
        issues.append('missing or unsafe path: ' + relative)
        continue
    observed = hashlib.sha256(path.read_bytes()).hexdigest()
    if observed != expected:
        issues.append('checksum mismatch: ' + relative)
    else:
        verified += 1
print('Verified files:', verified)
if issues:
    print('\n'.join(issues))
    raise SystemExit(1)
print('RELEASE INTEGRITY PASS')
