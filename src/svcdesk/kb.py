# ai-generated: 100% - Codex implemented a single bounded upstream request without retry or redirect.
"""Blocking stdlib HTTP runs in a worker, keeping the ASGI event loop free."""
import http.client
import json
import os
from urllib.parse import urlencode, urlsplit


def fetch_hits(query):
    base = urlsplit(os.environ.get('KB_INDEX_URL', 'http://kb-index:8080'))
    if base.scheme not in ('http', 'https') or not base.hostname:
        raise ValueError('Invalid index URL')
    connection_type = http.client.HTTPSConnection if base.scheme == 'https' else http.client.HTTPConnection
    connection = connection_type(base.hostname, base.port, timeout=5.0)
    try:
        path = base.path.rstrip('/') + '/search?' + urlencode({'q': query})
        connection.request('GET', path, headers={'Accept': 'application/json'})
        response = connection.getresponse()
        if response.status != 200:
            raise ValueError('Index returned a non-200 response')
        return json.loads(response.read())['hits']
    finally:
        connection.close()
