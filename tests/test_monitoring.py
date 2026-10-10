# ai-generated: 100% - Codex tested exactly-one upstream call, timeout/error mapping and bounded metrics.
import json
import sys
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import pytest
from fastapi.testclient import TestClient
from prometheus_client.parser import text_string_to_metric_families

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from svcdesk.main import app
from svcdesk import kb


def samples(client):
    response = client.get('/metrics', headers={'Accept': 'text/plain;version=0.0.4'})
    assert response.headers['content-type'].startswith('text/plain')
    return [s for f in text_string_to_metric_families(response.text) for s in f.samples]


@pytest.fixture
def stub(monkeypatch):
    state = {'calls': [], 'closed': 0, 'status': 200, 'failure': None}

    class Connection:
        def __init__(self, host, port, timeout):
            state['timeout'] = timeout
            state['host'] = host
        def request(self, method, path, headers):
            state['calls'].append((method, path))
            if state['failure']:
                raise state['failure']
        def getresponse(self):
            return self
        @property
        def status(self):
            return state['status']
        def read(self):
            return json.dumps({'hits': [{'id': 'unchanged', 'title': 'Workaround', 'score': 0.75}]}).encode()
        def close(self):
            state['closed'] += 1

    monkeypatch.setattr(kb.http.client, 'HTTPConnection', Connection)
    monkeypatch.setenv('KB_INDEX_URL', 'http://test-index:8080')
    with TestClient(app) as client:
        yield client, state


def test_search_forwarding_exactly_once_and_url_encoding(stub):
    client, state = stub
    q = 'vpn & wi-fi / żółć?'
    r = client.get('/kb/search', params={'q': q})
    assert r.status_code == 200 and r.json() == {'query': q, 'hits': [{'id': 'unchanged', 'title': 'Workaround', 'score': 0.75}]}
    assert len(state['calls']) == 1
    method, path = state['calls'][0]
    assert method == 'GET' and urlsplit(path).path == '/search'
    assert parse_qs(urlsplit(path).query) == {'q': [q]}
    assert state['timeout'] >= 2 and state['closed'] == 1
    client.get('/kb/search', params={'q': q})
    assert len(state['calls']) == 2 and state['closed'] == 2


@pytest.mark.parametrize('params', [{}, {'q': ''}, {'q': 'x'*201}])
def test_invalid_search_never_calls_index(stub, params):
    client, state = stub
    r = client.get('/kb/search', params=params)
    assert r.status_code == 422 and 'error' in r.json() and not state['calls']


@pytest.mark.parametrize('failure', ['503', 'timeout', 'connection'])
def test_upstream_failure_is_502_without_retry(stub, failure):
    client, state = stub
    if failure == '503':
        state['status'] = 503
    else:
        state['failure'] = TimeoutError('test') if failure == 'timeout' else ConnectionError('test')
    r = client.get('/kb/search', params={'q': 'test'})
    assert r.status_code == 502 and r.json()['error']['code'] == 'upstream_unavailable'
    assert len(state['calls']) == 1 and state['closed'] == 1


def test_exactly_once_and_low_cardinality(stub):
    client, _ = stub
    client.get('/tickets/warmup')
    client.get('/not-a-route/warmup')
    client.get('/health?probe=warmup')
    before = samples(client)
    def keys(rows): return {(s.name, tuple(sorted(s.labels.items()))) for s in rows}
    for n in range(12):
        client.get('/tickets/unique-'+str(n))
        client.get('/not-a-route/unique-'+str(n))
        client.get('/health?probe=unique-'+str(n))
    after = samples(client)
    assert keys(before) == keys(after)
    def counts(rows): return sum(s.value for s in rows if s.name == 'http_server_request_duration_seconds_count')
    assert counts(after)-counts(before) == 36
    for sample in after:
        assert not any('unique-' in str(v) for v in sample.labels.values())
        if sample.name.endswith(('_bucket', '_sum', '_count')):
            expected = {'http_request_method', 'http_route', 'http_response_status_code'}
            assert set(sample.labels) == expected | ({'le'} if sample.name.endswith('_bucket') else set())
