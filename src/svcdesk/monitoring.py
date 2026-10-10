# ai-generated: 100% - Codex implemented one request timer and bounded route labels for Lab 3.
"""One ASGI observation per HTTP response; query strings and raw paths are never labels."""
from time import perf_counter
from prometheus_client import CollectorRegistry, Histogram

REGISTRY = CollectorRegistry()
# Final ladder: <=20% relative widths throughout 0.10–1.0 s, based on measured profile.
BUCKETS = (0.005, 0.01, 0.02, 0.03, 0.04, 0.06, 0.08, 0.1, 0.12, 0.14, 0.16, 0.18, 0.2, 0.23, 0.26, 0.3, 0.34, 0.39, 0.45, 0.52, 0.6, 0.69, 0.79, 0.9, 1.0, 1.5, 2.5, 5)
DURATION = Histogram(
    'http_server_request_duration_seconds', 'Elapsed HTTP response duration in seconds',
    ['http_request_method', 'http_route', 'http_response_status_code'],
    buckets=BUCKETS, registry=REGISTRY,
)


class RequestMetrics:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http' or scope['path'] == '/metrics':
            await self.app(scope, receive, send)
            return
        start = perf_counter()
        status = 500
        observed = False

        def observe():
            nonlocal observed
            if not observed:
                route = getattr(scope.get('route'), 'path', 'unmatched')
                DURATION.labels(scope['method'], route, str(status)).observe(perf_counter() - start)
                observed = True

        async def send_timed(message):
            nonlocal status
            if message['type'] == 'http.response.start':
                status = message['status']
            await send(message)
            if message['type'] == 'http.response.body' and not message.get('more_body', False):
                observe()

        try:
            await self.app(scope, receive, send_timed)
        finally:
            observe()
