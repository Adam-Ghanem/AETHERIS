"""Guard globe sizing and control positioning against desktop/mobile regressions."""
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]


def test_globe_keeps_square_canvas():
    css = (ROOT / 'static/ghostcat-earth.css').read_text(encoding='utf-8')
    assert 'aspect-ratio:1 / 1' in css
    assert 'width:min(100%,365px)' in css
    assert 'grid-template-columns:minmax(0,1fr) minmax(320px,380px)' in css


def test_pause_reset_in_flow_not_clipped():
    css = (ROOT / 'static/ghostcat-earth.css').read_text(encoding='utf-8')
    new = css.split('/* 2026-11-15 — 3D globe responsive layout correction.')[1]
    assert 'position:relative;' in new and 'bottom:auto;' in new
    assert '.globe-actions {' in new
    assert '.hero {overflow:visible!important}' in new


def test_default_three_camera_fits_planet():
    js = (ROOT / 'static/ghostcat-earth.js').read_text(encoding='utf-8')
    assert 'let zoom = 312' in js
    assert 'zoom=312;' in js
    assert 'zoom=Math.max(280,Math.min(420' in js
    assert '{radius:100,axis:.83' in js


def test_mobile_globe_and_ctas_can_shrink():
    css = (ROOT / 'static/ghostcat-earth.css').read_text(encoding='utf-8')
    assert 'max-width:310px!important' in css
    assert 'max-width:265px!important' in css
    assert '.mission-spotlight .btn{width:100%' in css
