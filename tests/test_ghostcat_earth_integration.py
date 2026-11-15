"""Integration integrity for GhostCat MIT Three.js globe and offline fallback."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_ghostcat_globe_controls_and_load_order():
    html = (ROOT / 'static/index.html').read_text(encoding='utf-8')
    assert 'id="hero-globe"' in html
    assert 'id="hero-globe-fallback"' in html
    assert 'id="globe-motion-toggle"' in html
    assert 'id="globe-reset"' in html
    assert html.index('/static/globe.js') < html.index('/static/ghostcat-earth.js') < html.index('/static/app.js')
    assert '/static/ghostcat-earth.css' in html


def test_real_source_license_and_safe_fallback_are_present():
    js = (ROOT / 'static/ghostcat-earth.js').read_text(encoding='utf-8')
    fallback = (ROOT / 'static/globe.js').read_text(encoding='utf-8')
    license_text = (ROOT / 'static/vendor/ghostcat-earth/LICENSE').read_text(encoding='utf-8')
    assert 'GhostCatcg/3d-earth' in js
    assert 'MIT License' in license_text and 'GhostCat' in license_text
    assert 'AetherisLegacyGlobe.initialize()' in js
    assert 'WebGL' in js and 'SphereGeometry' in js and 'TextureLoader' in js
    assert 'hero-globe-fallback' in fallback
    assert (ROOT / 'static/vendor/ghostcat-earth/earth-fallback.jpg').stat().st_size > 30_000


def test_optional_installer_does_not_block_scientific_app():
    installer = (ROOT / 'scripts/install_ghostcat_assets.py').read_text(encoding='utf-8')
    bat = (ROOT / 'Start_AETHERIS.bat').read_text(encoding='utf-8')
    assert 'GhostCatcg/3d-earth/main/static/images/earth/earth.jpg' in installer
    assert 'three@0.143.0' in installer
    assert 'sys.exit(0)' in installer
    assert 'install_ghostcat_assets.py' in bat


def test_globe_is_labeled_decorative_and_scientific_sections_remain():
    html = (ROOT / 'static/index.html').read_text(encoding='utf-8')
    assert 'not NASA measurements' in html
    for name in ('view-overview','view-campaign','view-briefing','view-explore'):
        assert f'id="{name}"' in html
