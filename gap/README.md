<!-- ai-generated: 100% - Codex documented a measured Toxiproxy experiment and the limits of subtracting percentiles. -->
# Client versus server latency

This experiment places Toxiproxy **in front of svcdesk**, with one downstream latency toxic: 200 ms, zero jitter, toxicity 1.0. `svcdesk` still calls the real course `kb-index` once and its histogram still measures the whole ASGI response. The proxy is not inserted between the service and the index. The original dependency delay therefore remains part of both measurements, while the added downstream delay is outside the service timer.

The client uses the official open-loop load command: a five-second warm-up, then 60 seconds at 40 scheduled requests per second with 64 connections and latency correction. Server p99 comes from increments of the service histogram over that same measurement. It is not the histogram accumulated over the lifetime of the container, and not a separate run selected because it gave a convenient result. The raw command output is retained in `evidence/lab3/gap-load.txt`; `gap.json` records its two p99 values and their subtraction in seconds.

The expected difference is approximately 0.2 seconds: Toxiproxy delays delivery after svcdesk finishes its work. Client measurements also include scheduling, connection and network overhead; the ASGI timer does not. Histogram quantiles interpolate within finite buckets, so their estimates add approximation error. Subtracting two p99s is **not** the p99 of per-request network latency in general: quantiles are nonlinear and the requests at the two ranks need not match. A constant extra delay makes a near-constant shift plausible here; the measured result is evidence for this controlled experiment, not proof that all production latency gaps are network delay.

## Reproduce

Start `docker compose --profile gap up -d --build svcdesk toxiproxy` and configure the proxy once (delete an existing proxy of the same name before recreating it):

```sh
curl -fsS -H 'Content-Type: application/json' -X POST http://localhost:8474/proxies \
  -d '{"name":"svcdesk","listen":"0.0.0.0:8666","upstream":"svcdesk:8080","enabled":true}'
curl -fsS -H 'Content-Type: application/json' -X POST http://localhost:8474/proxies/svcdesk/toxics \
  -d '{"name":"lab3-downstream","type":"latency","stream":"downstream","toxicity":1.0,"attributes":{"latency":200,"jitter":0}}'
docker run --rm --network itsm-2026_default \
  -v "$PWD:$PWD" -w "$PWD" -v /var/run/docker.sock:/var/run/docker.sock \
  ghcr.io/swasik/itsmlab:2026 load 3 \
  --base-url http://toxiproxy:8666 --service-url kb-index=http://kb-index:8080
```

The checker is attached to the existing compose network here so both services resolve by name. If the compose project has another name, substitute its network. Stop Grafana and any local inference process while measuring to reduce unrelated CPU contention. Remove the toxic or stop the optional proxy after the experiment; normal service access stays on port 8080.

## Observed result

Client p99: 0.4470 s; server histogram p99: 0.2120 s; difference: 0.2350 s. These values are from the same run recorded above.

This proxy capture used the finalized histogram with the earlier HTTPX transport. The final transport subsequently changed to a single stdlib HTTP request per call to stabilize CPU overhead. The recorded experiment is retained as historical evidence; the official checker independently re-measures the declared toxic and gap against the final submitted service.
