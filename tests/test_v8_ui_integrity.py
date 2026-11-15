"""Static integration checks for Time Machine navigation, UI and API exports."""
from html.parser import HTMLParser
from pathlib import Path
from fastapi.testclient import TestClient
from aetheris.server import app

ROOT=Path(__file__).resolve().parents[1]

class IdParser(HTMLParser):
    def __init__(self):super().__init__();self.ids=[]
    def handle_starttag(self,tag,attrs):self.ids.extend(v for k,v in attrs if k=='id')


def test_time_machine_ui_controls_and_duplicate_ids():
    html=(ROOT/'static/index.html').read_text()
    parser=IdParser();parser.feed(html)
    assert len(parser.ids)==len(set(parser.ids))
    required=['view-timemachine','tm-form','tm-run','tm-location','tm-lat','tm-lon','tm-start','tm-end','tm-variable','tm-spacing',
              'tm-year-slider','tm-year-number','tm-grid','tm-point-detail','tm-point-chart','tm-play','tm-next','tm-previous',
              'tm-export-json','tm-export-csv','tm-results','tm-error','tm-loading','tm-limitations','open-timemachine']
    assert set(required).issubset(parser.ids)
    assert 'data-view="timemachine"' in html


def test_js_time_machine_binds_controls():
    js=(ROOT/'static/app.js').read_text()
    for fragment in ['runTimeMachine','renderTimeMachine','showTimeMachineYear','selectTimeMachinePoint',
                     'playTimeMachine','stopTimeMachinePlayback','exportTimeMachineJson','exportTimeMachineCsv',
                     "/api/v1/time-machine", "$('tm-year-slider').addEventListener",'showTimeMachineFromCurrent']:
        assert fragment in js


def test_api_module_has_documented_endpoint():
    client=TestClient(app)
    assert client.get('/api/v1/health').json()['version']=='14.0.0'
    assert '/api/v1/time-machine' in app.openapi()['paths']
