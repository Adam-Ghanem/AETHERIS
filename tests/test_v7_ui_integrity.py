"""Static UI contract checks for Change-Point Lab; browser E2E tested separately."""
from html.parser import HTMLParser
from pathlib import Path
from fastapi.testclient import TestClient
from aetheris.server import app
ROOT=Path(__file__).resolve().parents[1]


class IdParser(HTMLParser):
    def __init__(self):
        super().__init__();self.ids=[]
    def handle_starttag(self,tag,attrs):
        self.ids.extend(v for k,v in attrs if k=='id')


def test_new_navigation_and_unique_html_ids():
    html=(ROOT/'static/index.html').read_text()
    parser=IdParser();parser.feed(html)
    assert len(parser.ids)==len(set(parser.ids))
    required=['view-breakpoints','breakpoint-form','breakpoint-run','breakpoint-summary',
              'breakpoint-results','breakpoint-main-chart','breakpoint-candidates',
              'breakpoint-evidence','breakpoint-export-json','breakpoint-export-csv']
    assert set(required).issubset(parser.ids)
    assert 'data-view="breakpoints"' in html
    assert 'id="open-breakpoints"' in html


def test_js_wires_api_controls_exports():
    js=(ROOT/'static/app.js').read_text()
    for token in ['setupBreakpointLocations()','runBreakpointLab','renderBreakpointLab',
                  'inspectBreakpointCandidate','showBreakpointsFromCurrent',
                  'exportBreakpointJson','exportBreakpointCsv','/api/v1/change-points']:
        assert token in js


def test_api_is_available_and_product_version_in_sync():
    client=TestClient(app)
    assert client.get('/api/v1/health').json()['version']=='14.0.0'
    assert '/api/v1/change-points' in app.openapi()['paths']
