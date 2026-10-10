---
lab3_slo:
  service: svcdesk
  route: /kb/search
  window: 30d
  slis:
    availability:
      objective: 0.99
      good: sum(rate(http_server_request_duration_seconds_count{http_route="/kb/search",http_response_status_code!~"5.."}[5m]))
      valid: sum(rate(http_server_request_duration_seconds_count{http_route="/kb/search"}[5m]))
      error_budget:
        fraction: 0.01
        minutes: 432
    latency:
      objective: 0.99
      threshold_seconds: 0.45
      good: sum(rate(http_server_request_duration_seconds_bucket{http_route="/kb/search",le="0.45"}[5m]))
      valid: sum(rate(http_server_request_duration_seconds_count{http_route="/kb/search"}[5m]))
      error_budget:
        fraction: 0.01
        minutes: 432
  alerts:
  - alert: KbAvailabilityFastBurn
    sli: availability
    burn_rate: 14.4
    long_window: 1h
    short_window: 5m
  - alert: KbAvailabilitySlowBurn
    sli: availability
    burn_rate: 6
    long_window: 6h
    short_window: 30m
---
<!-- ai-generated: 100% - Codex drafted objectives and reasoning from real measurements; student review is required. -->
# SLO for knowledge-base search

## Measurement and scope

Login `piotrek-7`, official checker 0.8.1, 40 scheduled requests/s with 64 connections, a 5-second warm-up and a 60-second latency-corrected run. Evidence: `evidence/lab3/profile-load.txt`. The final measured client p50 / p95 / p99 were **37.6 / 138.1 / 173.6 ms**, versus dependency p99 **162.4 ms**. The run completed 2399 responses: 2395 successes and 4 errors (0.1667%). The slow tail is visible well above the median; the raw histogram and higher percentiles are preserved in the evidence. Requests really traverse the course index; they are neither cached nor retried. The service timer covers dependency waiting and serialization until the final ASGI response body. Client scheduling and network delivery can still add time outside that timer. Open-loop load matters: slow replies do not reduce offered traffic and hide queueing.

The earlier implementation produced p99 of 670 and 594 ms, versus 163 and 177 ms for the dependency. That was overhead to investigate, not a credible reason to choose a very lax SLO. Profiling identified connection-pool maintenance and repeated failed imports. A smaller idle pool and sniffio improved an isolated run, but the first full checker still measured 516 ms. The final implementation uses one standard-library HTTPConnection per request in an asyncio worker thread, with a five-second timeout and unconditional close. It follows no redirects and cannot retry or cache. At 40 requests/s this avoids unnecessary pool maintenance; connection setup is paid explicitly, and both thread queueing and dependency work remain inside the measured request. Earlier measurements are retained as diagnostic history. The availability objective does not pretend to fix unavoidable index errors.

## Availability

Good means a search response whose status is not 5xx; valid means every response on `/kb/search`. This includes client validation errors in both numerator and denominator: malformed input is rejected correctly, so it is not a service failure. In a production SLO one could explicitly exclude malformed requests; here the declared population stays simple and the checker traffic is valid. The dependency's non-200, connection and timeout failures are 502 and therefore bad.

The objective is **99% over 30 days**. Budget = 1 - 0.99 = 0.01, equivalent to 0.01 × 30 × 24 × 60 = **432 minutes** at uniform request volume. This is a request-weighted budget, not a promise of exactly 432 minutes of downtime: a busy-minute outage consumes more requests. The measured normal index error rate is below 1%, leaving room for occasional service/network failures while treating a sustained dependency incident as an availability failure experienced by users. One minute of good traffic cannot prove a month-long SLO; monitor the rolling window and revisit after longer observations.

## Latency

Good means a response completed inside **450 ms**, and valid means every search response, including failures. The objective is **99% over 30 days**, with the same 1% / 432-minute equivalent budget. Availability is separate: a quick error can meet latency and still violate availability. 450 ms is an actual finite bucket boundary, so this SLI counts observations and does not interpolate. It is below the Lab 6 maximum of one second and gives headroom over the measured slow tail while keeping search reasonably responsive. The normal baseline must meet this objective before reusing it as a canary gate; transient CPU saturation should be repaired rather than hidden by repeatedly raising the threshold.

## Multiwindow alerts

| Alert | Burn | Long / short | Threshold bad fraction | Severity | Budget consumed over long window at threshold |
|---|---:|---|---:|---|---:|
| KbAvailabilityFastBurn | 14.4 | 1h / 5m | 14.4% | P1, page | 14.4 × 1 / 720 = 2% |
| KbAvailabilitySlowBurn | 6 | 6h / 30m | 6% | P2, chat | 6 × 6 / 720 = 5% |

Both windows must be above threshold for five minutes. The table gives the budget fraction represented by a full long window at threshold, not an exact universal amount at the first firing instant: the traffic shape, volume and `for` delay change that. At a steady 14.4x burn the entire budget lasts only 50 hours; waiting eight hours wastes another 16% of it, while roughly one in seven requests fails. That warrants waking someone. At 6x the budget lasts 120 hours and eight hours consume 6.67%; a chat/ticket response is proportionate to a slower problem, with escalation if it becomes fast burn. These labels classify intended routing; this lab does not configure or send real notifications.

The 5-minute/30-minute short windows make recovery visible promptly; a long window alone could continue paging after the incident ended. The `for` period filters transient evaluations. Tests cover first firing and the evaluation immediately before, sub-threshold traffic, recovery, and unrelated ticket traffic. All eight mutations are rejected. These two alerts intentionally cover the same availability SLI at different severities; the dashboard exposes latency for investigation, rather than pretending these are latency alerts.

## Histogram buckets

Final boundaries, seconds: `[0.005, 0.01, 0.02, 0.03, 0.04, 0.06, 0.08, 0.1, 0.12, 0.14, 0.16, 0.18, 0.2, 0.23, 0.26, 0.3, 0.34, 0.39, 0.45, 0.52, 0.6, 0.69, 0.79, 0.9, 1.0, 1.5, 2.5, 5]` (28 finite boundaries). Adjacent widths in the 0.10–1.0 s region are at most 20% of the lower boundary, so every q throughout that region meets width ≤ 0.20q, including a broad band around the normal profile. The measured p99 is in (0.16, 0.18] s: width / q = 0.020 / 0.1736 = 11.52%, below 20%. In particular its ±30% band (0.1215–0.2257 s) is fully resolved. Fine boundaries at 0.12–0.20 s describe the observed slow tail; the following geometric spacing also tolerates machine overhead without spending the whole budget on one sample. Boundaries below 0.10 s retain median/fast-path detail. The 450 ms boundary makes the latency objective exact; 1.5, 2.5 and 5 s retain coarse incident/timeout visibility. Values above five seconds still contribute to +Inf and the total count.

Interpolation inside a narrow bucket is still an estimate, not the raw percentile. Both the bucket containing the load generator's p99 and agreement with the service histogram must pass the independent checker run. No profile-specific artificial delay or metric rewrite is used to force agreement.
