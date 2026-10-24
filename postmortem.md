---
lab4_postmortem:
  ticket: 1224ad8d-06a8-4ae3-865a-da2015a4ddb5
  detecting_alert: ShopCheckoutErrors
  onset: '2026-10-12T07:05:45Z'
  detection: '2026-10-12T07:09:19Z'
  acknowledgement: '2026-10-12T07:10:07Z'
  recovery: '2026-10-12T07:12:19Z'
  mttd_seconds: 214
  mtta_seconds: 48
  mttr_seconds: 394
  identified_flags:
  - productCatalogFailure
  - adManualGc
---
<!-- ai-generated: 100% - Codex investigated the assigned recording and drafted this report from replayed queries; student review is required. -->
# Postmortem: failed checkouts and delayed frontend responses

## Date

The recorded incident occurred on 12 October 2026, 07:05:45–07:12:19 UTC by the course's alert-based clock. This retrospective was written on 24 October 2026 from the assigned recording `lab4-rec-3`, not from a new live run.

## Authors

Piotrek-7 is the submitting student and reviewer. Codex (GPT-6) performed the telemetry analysis and drafted the artifacts with full AI disclosure. The original on-call actions, ticket and recording were produced by the lecturer; this report does not attribute those actions to the student.

## Status

Recorded service incident recovered; proposed engineering action items remain open. Two flag identifications are supported strongly enough to declare. The third, resource-class fault remains unresolved in this retrospective rather than being guessed from a weak memory trend.

## Summary

The recorded shop experienced catalog errors propagating to checkout and frontend, alongside a separate ad-latency spike. The first detecting alert was `ShopCheckoutErrors`. The recomputed alert-based incident lasted 394 seconds; acknowledgement followed detection by 48 seconds. These are single-incident differences, not statistical means over a population.

## Impact

The failed server spans visible by the recovery instant are 38 for product-catalog, 2 for checkout and 76 for frontend. Query: `sum by(service_name)(traces_span_metrics_calls_total{span_kind="SPAN_KIND_SERVER",status_code="STATUS_CODE_ERROR"})`, evaluated at 2026-10-12T07:12:19Z. They stay at those values at 07:15:00Z. The catalog, checkout and frontend error series are absent on the healthy baseline at 07:00:45Z; their subsequently exposed initial zero followed by increments supports interpreting these as newly observed errors. These are span counts, not unique failed customers: a failed order or page can produce several related spans, so the three services must not be added to estimate user count.

At 07:09:00Z the five-minute error ratios were approximately 9.83% for checkout, 5.46% for catalog and 5.59% for frontend. Each query divides its error-span rate by all server-span traffic for that same service; the exact queries and responses are in `evidence/lab4/impact.json`. The five-minute rates include some healthy traffic because the instant is only 195 seconds after onset. No exact number of unique users or lost revenue is available from this recording.

The ad service's server p99 rose from 5.04 ms at 07:00:45Z to 912 ms at 07:09:00Z. Query: `histogram_quantile(0.99,sum by(le)(rate(traces_span_metrics_duration_milliseconds_bucket{service_name="ad",span_kind="SPAN_KIND_SERVER"}[5m])))`. Frontend server p99 at 07:09 was 761.49 ms. These are interpolated histogram estimates in milliseconds, not exact request durations or sums of component p99s. The ad tail remains elevated after the first checkout alarm resolves: 394 seconds is the prescribed detecting-alert clock, not proof that every symptom ended simultaneously.

## Root Causes

Within the published fault pool, `productCatalogFailure` best explains catalog server errors and their downstream propagation while catalog server p99 remains about 9 ms. `productCatalogLockContention` would instead stall reads for tens of seconds; the measured short latency does not support that mechanism. `adManualGc` best explains the jump in ad latency without an ad-error signal. Shipping remains near 4 ms and frontend traffic near four server spans/s: the 5/10-second international shipping fault and a 15x load flood are poor explanations of the observed latency change.

These are inferences from symptoms and the published fault pool, not directly read flag values. The actual production root cause would require further evidence of GC events and flag evaluation; this recorded path exposes neither Jaeger nor `/flags.json`. Container memory stays around 60–63 MB for email and 85–86 MB for recommendation in the observed window, with no uptime reset. That does not reliably distinguish the third resource-class flag, especially after a short exposure and rollback. Only the two supported keys are declared, as I-22 permits.

The enabling weakness was that behavior-changing flags could introduce errors and frontend delay without a gate that verified user-facing health. That is a process/control gap to investigate, not evidence that a particular person acted carelessly.

## Trigger

The recording's injector began its fault at 2026-10-12T07:05:45Z, the first `seeded_fault_active` sample. The injector introduced one flag from each class after a healthy baseline. That marker establishes onset only: none of our alert rules or AI predictions reads injector metrics. The sealed fault has not been decrypted and the third key is not claimed.

## Resolution

The recording already contains the lecturer's mitigation and recovery. The data proves that the detecting alert resolves at 07:12:19Z; it does not expose the exact rollback command order or exact per-flag off timestamps. They are therefore not invented here. The P1 ticket remains acknowledged in the supplied JSON; no student transition to resolved or closed is fabricated.

For a future live incident with these signals, the proposed runbook is to disable the catalog failure first to restore orders, then remove the ad GC behavior to reduce page delay, while checking the resource-class symptoms and watching both error and latency recovery. That is a proposed response, distinct from a claim about what the recorded on-call actually did. A first resolving alert is insufficient to declare every affected service healthy; verify the remaining latency and memory signals before closing the operational incident.

## Detection

The first recorded firing run after onset belongs to `ShopCheckoutErrors` at 07:09:19Z. MTTD = 07:09:19 - 07:05:45 = 214 s. The pager received a firing notification, a P1 ticket was created at 07:09:37Z, and acknowledgement at 07:10:07Z yields MTTA = 48 s. Recovery minus onset gives MTTR = 394 s. The official recomputation is preserved in `evidence/lab4/incident.txt`.

The shop's OTLP span metrics arrive about once a minute and five-minute rates include older samples; rule pending periods and export cadence add delay. Without symptom alerting, users placing orders or viewing slow pages would have been the first observers. Our own `demo-alerts.yml` adds P1 rules for checkout errors and latency, P2 ad latency and a sustained P3 checkout latency warning; these did not run during the lecturer's recording. Their historical expressions are evaluated separately, and their names do not replace the recording's detecting alert in this report.

## Action Items

| Action Item | Type | Owner | Bug |
|---|---|---|---|
| Gate behavior-changing catalog flags on checkout server error rate and automatically abort a failing rollout. | prevent | Catalog service owner | ITSM-L4-01 |
| Add an on-call rollback runbook that checks catalog errors and ad/frontend latency separately before incident closure. | mitigate | On-call SRE | ITSM-L4-02 |
| Store a feature-flag audit trail with per-flag activation and rollback times alongside telemetry references. | process | Platform owner | ITSM-L4-03 |
| Require rate/delta queries and a healthy-baseline comparison before accepting AI explanations based on counters. | process | Observability owner | ITSM-L4-04 |

These Bug values are proposed tracking identifiers in this exercise, not claims that external issues have already been opened. They remain stable references for later labs.

## Lessons Learned

### What went well

The pager, P1 ticket, acknowledgement telemetry and one immutable snapshot allow the checker to recompute the incident. Catalog error propagation and ad latency can be separated using server spans and baseline comparisons. The original artifacts remain byte-for-byte identical to the assigned recording.

### What went wrong

The supplied Qwen investigator treated a cumulative error count of two as evidence of sustained errors and guessed payment involvement without checking actual payment traffic. Its fourth claim inferred load/resource pressure from an asserted steady increase that the counter does not show. It did not examine latency or resource data. The recording also lacks an exposed per-flag mitigation audit, limiting what this retrospective can conclude.

### Where we got lucky

The catalog failures left healthy traffic and readable telemetry; a complete dependency failure could have hidden other symptoms. We had a pre-incident baseline and a captured recovered period. A short resource-fault exposure may have avoided a visible restart, so lack of an OOM/reset is not treated as proof of absence.

## Timeline

| UTC | Recorded event or later analysis |
|---|---|
| 2026-10-12T07:00:45Z | Healthy comparison instant, exactly five minutes before onset; no server error-rate result for the affected services. |
| 2026-10-12T07:05:45Z | Fault onset, recomputed from the recording. |
| 2026-10-12T07:09:00Z | Retrospective measurement instant: catalog errors 0.103641/s, checkout errors 0.011358/s, ad p99 912 ms. |
| 2026-10-12T07:09:19Z | First detecting alert `ShopCheckoutErrors`; later ledger H2 is supported by `sum(rate(traces_span_metrics_calls_total{service_name="product-catalog",span_kind="SPAN_KIND_SERVER",status_code="STATUS_CODE_ERROR"}[5m])) > 0.05` at 07:09:00Z, returning 0.103641/s. This hypothesis was evaluated retrospectively, not acted on by the recorded on-call. |
| 2026-10-12T07:09:37Z | The lecturer's P1 ticket was created in the recorded svcdesk. |
| 2026-10-12T07:10:07Z | Ticket acknowledged; 48 seconds after detection. |
| 2026-10-12T07:12:19Z | Detecting alert's firing run ends: the lab's recovery instant. |
| 2026-10-12T07:15:00Z | Checkout and catalog error counters have plateaued; some ad-latency tail remains. |
| 2026-10-24, retrospective | Codex C2 tests ad latency with `histogram_quantile(0.99,sum by(le)(rate(traces_span_metrics_duration_milliseconds_bucket{service_name="ad",span_kind="SPAN_KIND_SERVER"}[5m]))) > 500 unless on() sum(rate(traces_span_metrics_calls_total{service_name="ad",span_kind="SPAN_KIND_SERVER",status_code="STATUS_CODE_ERROR"}[5m])) > 0` at 07:09:00Z on the recording; result 912, healthy baseline empty. No AI advice is represented as a past operational action. |

## Supporting information

Original data: `incident/tsdb-snapshot.tar.gz` and `incident/ticket.json`, recording `lab4-rec-3` assigned to `piotrek-7` by checker 0.8.6. `evidence/lab4/recording-integrity.json` proves equality with the provided files. Preserve and submit the archive itself; the extracted database is a disposable copy outside the repository.

Counter query and rates: `evidence/lab4/impact.json`, `service-curves.json` and `impact-counter-history.json`. Ledger predictions: `ai-rca-eval.json`, `ai-rca-eval-2.json` and their verbatim transcripts; raw at/baseline responses are in `evidence/lab4/ledger-replay.json`. The second transcript records genuine calls to the unmodified course MCP server. The local checker cannot validate sealed ground truth: the flag keys and correct components still require Tier B assessment.

## Problem record

- Incident record: 1224ad8d-06a8-4ae3-865a-da2015a4ddb5; this is the lecturer's recorded P1 ticket, preserved unchanged.
- Root cause: Catalog failure behavior and ad latency behavior were enabled without a user-facing rollout gate; exact flags are inferred from symptoms within the published pool, and the resource-class choice remains uncertain.
- Known error: Catalog failures propagate into checkout/frontend errors; expensive ad behavior propagates into frontend delay. Returning the first alarm to green does not guarantee all symptoms have ended.
- Workaround: Disable the implicated behaviors and verify both errors and latency across the affected services; retain the proposed engineering follow-ups until a durable guard and flag audit are implemented.
