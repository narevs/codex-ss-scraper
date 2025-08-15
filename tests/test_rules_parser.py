import json
from pathlib import Path


def test_springerlink_base_url_not_search():
    data = json.loads(Path('rules/popular.json').read_text())
    springer = next(site for site in data['sites'] if site['label'] == 'SpringerLink')
    base_url = springer['base_url']
    assert base_url.endswith('/')
    assert '/search' not in base_url
