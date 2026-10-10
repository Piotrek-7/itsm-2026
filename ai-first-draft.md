---
lab3_first_draft:
  source: ai
  tool: "Codex (GPT-6), this project conversation, 10 October 2026"
  ladder: [0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1, 2.5, 5, 7.5, 10]
  verdict: pending_measurement
  evidence: {p99_seconds: null, bucket: [], relative_width: null}
lab3_flawed_ladder:
  verdict: pending_measurement
  evidence: {p99_seconds: null, bucket: [], relative_width: null}
---
<!-- ai-generated: 100% - Codex recorded its initial answer before measurement; verdicts are not yet measured. -->
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
