---
lab3_first_draft:
  source: ai
  tool: Codex (GPT-6), this project conversation, 10 October 2026
  ladder:
  - 0.005
  - 0.01
  - 0.025
  - 0.05
  - 0.075
  - 0.1
  - 0.25
  - 0.5
  - 0.75
  - 1
  - 2.5
  - 5
  - 7.5
  - 10
  verdict: refuted
  evidence:
    p99_seconds: 0.1736
    bucket:
    - 0.1
    - 0.25
    relative_width: 0.864055
lab3_flawed_ladder:
  verdict: refuted
  evidence:
    p99_seconds: 0.1736
    bucket:
    - 0.04
    - 0.5
    relative_width: 2.64977
---
<!-- ai-generated: 100% - Codex recorded its initial answer before measurement; initial proposal preserved verbatim; verdicts now use actual measurements. -->
# First draft, recorded before measurement

## Prompt

w folderze materials jest fodler z lab3 zapoznaj sie i wykonuj zadanie daj znac jak cos potrzebujesz odemni

## Answer

Lab 3 wymaga zapisania pierwszej propozycji AI przed pomiarem. Zapiszę w Git poniższy szkic jako moją wstępną odpowiedź na Twoje polecenie; później ocenimy go na podstawie pomiarów.

Dla `GET /kb/search` proponuję początkowo granice histogramu w sekundach: `[0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1, 2.5, 5, 7.5, 10]`. To ogólny punkt startowy; bez pomiaru nie zapewnia dokładności p99. Wstępny alert: odsetek odpowiedzi 5xx dla `/kb/search` przekracza 1% przez 5 minut, liczony w oknie 5 minut:

```yaml
alert: KbSearchErrorsDraft
expr: sum(rate(http_server_request_duration_seconds_count{http_route="/kb/search",http_response_status_code=~"5.."}[5m])) / sum(rate(http_server_request_duration_seconds_count{http_route="/kb/search"}[5m])) > 0.01
for: 5m
labels:
  service: svcdesk
  slo: availability
  severity: P1
```

Przed użyciem operacyjnym trzeba dobrać granice do zmierzonego rozkładu i zastąpić ten prosty alert regułami spalania budżetu błędów w dwóch oknach.

## Measurement status

This is the actual user's task prompt and the assistant's first scoped proposal in response, not a fabricated exchange with another model. The assistant had read the rules, but had not measured this profile or designed a replacement ladder. No measurement or final verdict is claimed in this initial commit. The answer will remain verbatim when evidence is appended.

## Verdict on the draft ladder

AI draft: measured p99 = 0.1736 s, bucket (0.1, 0.25] s. Relative width = (0.25 - 0.1) / 0.1736 = 0.864055, exceeding 0.20. Verdict: **refuted**. Histogram interpolation can place its p99 anywhere within that wide bucket according to the bucket mass, with no observations describing the shape inside it.

Instructor's flawed ladder: measured p99 = 0.1736 s, bucket (0.04, 0.5] s. Relative width = (0.5 - 0.04) / 0.1736 = 2.649770, exceeding 0.20. Verdict: **refuted**. Histogram interpolation can place its p99 anywhere within that wide bucket according to the bucket mass, with no observations describing the shape inside it.

## Evidence and the replacement design

The initial proposal was committed as `834d1d7` before the first load run. Its prompt and answer above remain verbatim. Raw evidence is in `evidence/lab3/`: initial and repeated measurements exposed excessive application overhead, then profiling found costly scanning of a large HTTPX keep-alive pool and repeated failed imports of sniffio during backend detection. Reducing idle connections to eight and installing sniffio improved an isolated run, but the first full checker still measured 516 ms. The final implementation therefore replaces the asynchronous HTTPX pool with one standard-library HTTPConnection per request, executed in an asyncio worker thread. It disables access logging, follows no redirects and performs no retries or caching. Closing each connection trades connection setup for predictable work at this modest 40 requests/s load. The ASGI timer includes both worker queueing and the entire upstream call. The front matter uses the final implementation’s `profile-load.txt` run, not the earlier overloaded implementation. This was an explained implementation change, not selecting the most flattering unchanged run.

The final ladder in `slo.md` resolves a band rather than just this one p99. The flawed ladder spends most boundaries below 40 ms and leaves the slow tail in a huge bucket. More boundaries around the median cannot recover a tail distribution hidden inside that bucket.

## The draft alert rule

The initial 1% / 5-minute rule uses the correct route and error counter, but pages at only 1x burn of a 99% objective. A brief dependency spike can wake a person without threatening much of a 30-day budget; it also lacks a long window to establish sustained impact. The final rules retain the 5xx ratio but require both a long and a short window, at 14.4x and 6x burn. The short window ends the alarm after recovery instead of letting old failures keep it active. Tests check both sides of first firing, sustained sub-threshold traffic and recovery, and detect all eight declared mutations.
