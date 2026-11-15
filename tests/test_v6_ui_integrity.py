"""Static integration checks; do not confuse with browser E2E validation."""
from html.parser import HTMLParser
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


class CollectIds(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids=[]
    def handle_starttag(self,tag,attrs):
        for k,v in attrs:
            if k=='id':
                self.ids.append(v)


def test_new_module_html_structure_and_unique_ids():
    html=(ROOT/'static/index.html').read_text(encoding='utf-8')
    parser=CollectIds();parser.feed(html)
    assert len(parser.ids)==len(set(parser.ids)), 'Duplicate HTML ids cause broken interaction'
    required={'view-signals','signals-form','signals-run','signals-location','signals-lat','signals-lon',
              'signals-variable','signals-start','signals-end','signals-results','signals-loading',
              'signals-error','signals-months','signals-matrix','signals-month-chart',
              'signals-evidence','signals-export-csv','signals-export-json','signals-cell-detail'}
    assert required.issubset(parser.ids)
    assert 'data-view="signals"' in html
    assert 'id="open-signals"' in html


def test_frontend_endpoint_and_actions_are_wired():
    js=(ROOT/'static/app.js').read_text(encoding='utf-8')
    for hook in ('setupSignalLocations()', "$('signals-form').addEventListener('submit',runSignalLab)",
                 'renderSignalLab(data,place)', 'selectSignalMonth(', 'selectSignalCell(',
                 'exportSignalsJson', 'exportSignalsCsv', 'showSignalsFromCurrent', '/api/v1/seasonal-signals'):
        assert hook in js
    assert 'signal-heat-cell' in js
    assert 'escapeHtml(' in js


def test_no_fake_results_embedded_in_new_module():
    html=(ROOT/'static/index.html').read_text(encoding='utf-8')
    section=html.split('<section id="view-signals"',1)[1].split('<section id="view-forensics"',1)[0]
    assert 'signals-empty' in section and 'signals-results' in section
    assert 'signals-loading' in section and 'signals-error' in section
    assert 'NASA POWER' in section
    assert '12-MONTH EVIDENCE' in section
