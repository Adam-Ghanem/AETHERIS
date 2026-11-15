"""Portable reproduction pack tests: numerical audit and tamper detection."""
import io
import json
import subprocess
import sys
import zipfile
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from aetheris.reproducibility import build_reproducibility_zip
from aetheris.briefing import build_briefing
from aetheris.systems import analyze_systems
from aetheris.server import app
from tests.test_systems import investigation


def case():
    return build_briefing(analyze_systems(investigation('T2M'), investigation('PRECTOTCORR')))


def unpack(tmp_path, payload):
    with zipfile.ZipFile(io.BytesIO(payload)) as z:
        names=z.namelist()
        assert len(names)==len(set(names))
        assert all('..' not in name and not name.startswith('/') for name in names)
        z.extractall(tmp_path)
    return names


def verify(tmp_path):
    return subprocess.run([sys.executable, str(tmp_path/'verify.py')], capture_output=True, text=True, cwd=tmp_path,timeout=15)


def test_capsule_contains_source_linked_files_and_independent_verified_trends(tmp_path):
    report=case()
    names=unpack(tmp_path,build_reproducibility_zip(report))
    assert {'briefing.json','paired_annual.csv','temperature_annual.csv','precipitation_annual.csv','verify.py','manifest.json','README.txt'}==set(names)
    result=verify(tmp_path)
    assert result.returncode==0, (result.stdout,result.stderr)
    assert 'PASS T2M OLS trend' in result.stdout
    assert 'PASS PRECTOTCORR OLS trend' in result.stdout
    manifest=json.loads((tmp_path/'manifest.json').read_text())
    assert manifest['schema']=='aetheris-reproducibility-v1'
    assert 'SYNTHETIC TEST FIXTURE' in manifest['source']
    assert manifest['source_fingerprint']['briefing_sha256']==report['evidence']['briefing_sha256']


def test_integrity_check_detects_tampering(tmp_path):
    unpack(tmp_path,build_reproducibility_zip(case()))
    path=tmp_path/'temperature_annual.csv'
    path.write_text(path.read_text().replace('2001,', '2001,9999'),encoding='utf-8')
    result=verify(tmp_path)
    assert result.returncode==1
    assert 'File hash mismatch' in result.stderr


def test_missing_input_rejected():
    report=case()
    report['annual_inputs']={}
    with pytest.raises(ValueError,match='annual inputs'):
        build_reproducibility_zip(report)


def test_source_annual_inputs_retained_in_briefing():
    report=case()
    assert len(report['annual_inputs']['temperature'])==25
    assert len(report['annual_inputs']['precipitation'])==25
    assert report['annual_inputs']['temperature'][0]['year']==2001


def test_zip_endpoint_with_fixture_responses(tmp_path):
    client=TestClient(app)
    with patch('aetheris.server.run_briefing',new=AsyncMock(return_value=case())):
        response=client.get('/api/v1/reproducibility.zip?lat=32.337&lon=-6.349&start=2001&end=2025')
    assert response.status_code==200,response.text
    assert response.headers['content-type']=='application/zip'
    unpack(tmp_path,response.content)
    assert verify(tmp_path).returncode==0


def test_zip_endpoint_rejects_bad_coordinates():
    assert TestClient(app).get('/api/v1/reproducibility.zip?lat=999&lon=0').status_code==422


def test_frontend_chart_and_exports_wired():
    from pathlib import Path
    root=Path(__file__).resolve().parents[1]
    html=(root/'static/index.html').read_text()
    js=(root/'static/briefing.js').read_text()
    assert 'id="constellation-chart"' in html
    assert 'id="brief-capsule"' in html
    assert 'id="constellation-filter"' in html
    assert 'id="constellation-year"' in html
    assert '/api/v1/reproducibility.zip?' in js
    assert 'function renderConstellation()' in js
