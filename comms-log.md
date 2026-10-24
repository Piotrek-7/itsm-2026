---
lab4_comms:
  awareness: '2026-10-12T07:10:07Z'
  detection: '2026-10-12T07:09:19Z'
  classification: '2026-10-12T07:11:00Z'
  nis2:
    early_warning_due: '2026-10-13T07:10:07Z'
    notification_due: '2026-10-15T07:10:07Z'
    notification_sent: '2026-10-12T10:00:00Z'
    final_report_due: '2026-11-12T10:00:00Z'
  ksc:
    early_warning_due: '2026-10-13T07:09:19Z'
    notification_due: '2026-10-15T07:09:19Z'
    notification_sent: '2026-10-12T10:00:00Z'
    final_report_due: '2026-11-12T10:00:00Z'
  dora:
    initial_due: '2026-10-12T11:11:00Z'
    initial_sent: '2026-10-12T08:00:00Z'
    intermediate_due: '2026-10-15T08:00:00Z'
    intermediate_sent: '2026-10-14T12:00:00Z'
    final_due: '2026-11-14T12:00:00Z'
  log:
  - at: '2026-10-12T07:30:00Z'
    to: exercise CSIRT contact
    what: 'Hypothetical NIS2 and KSC early warning: recorded checkout failures, known
      scope and current uncertainty.'
  - at: '2026-10-12T08:00:00Z'
    to: exercise financial supervisor
    what: Hypothetical DORA initial notification, following major-incident classification.
  - at: '2026-10-12T10:00:00Z'
    to: exercise CSIRT contact
    what: Hypothetical NIS2 and KSC incident notification, including timeline and
      restored checkout.
  - at: '2026-10-14T12:00:00Z'
    to: exercise financial supervisor
    what: Hypothetical DORA intermediate report, impact reconciliation and proposed
      controls.
---
<!-- ai-generated: 100% - Codex calculated the hypothetical exercise deadlines directly from INCIDENT-SPEC I-30. -->
# Communications clocks for the recorded incident

## Defended starting instants

These are a classroom exercise under the assumptions required by I-30: the shop is treated as in scope of all three regimes and the incident as significant/major. They are not a determination of legal applicability to a real shop. Nothing in this log was sent to a regulator.

KSC detection is the recorded detecting alert at 2026-10-12T07:09:19Z. NIS2 awareness is chosen at 07:10:07Z, when acknowledgement represents an accountable human accepting the P1 after the page; this is a defended exercise choice, not a fact that a legal significance assessment was recorded. DORA classification is chosen at 07:11:00Z, a hypothetical decision after initial impact review and before the detecting alert resolves. The original ticket and snapshot establish the first two operational instants; they do not contain a regulatory classification event.

## Report schedule

The hypothetical early warning at 07:30 on 12 October precedes both 24-hour deadlines. The DORA initial report at 08:00 precedes classification plus four hours (11:11), which is earlier than awareness plus 24 hours. NIS2/KSC notifications at 10:00 the same day precede the respective 72-hour deadlines; both final reports are due one UTC calendar month after that notification, 12 November at 10:00.

The DORA intermediate report is due 15 October at 08:00, 72 elapsed hours after the initial report. It is hypothetically submitted on 14 October at 12:00; its final report is therefore due 14 November at 12:00, one calendar month after that intermediate report, not one month after its deadline. Weekend relief is ignored as the assignment instructs.

The YAML log contains four proposed communications, their intended recipients and content. Every instant is UTC; 24/72 hours are elapsed time and a month uses the UTC calendar. The recording happened on 12 October, so it does not cross the 25 October Warsaw clock change. Using the date of this retrospective instead would shift all incident-based deadlines incorrectly. The arithmetic and assumptions follow the laboratory specification rather than an attempt to give operational legal advice.
