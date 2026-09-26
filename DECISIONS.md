---
svcdesk_decisions:
  C1: wallclock
  C2: immutable
  C3: matrix
---
<!-- ai-generated: 100% - Codex drafted decisions from the receipted specification. -->
# Decisions

## C1 - SLA clock for P1

**Decision:** Apply R-14 to both P1 targets: 15 elapsed minutes for acknowledgement and four elapsed hours for resolution. Apply R-13 business hours to P2-P4.

**Rejected alternative:** Reject only the part of R-13 that would pause P1 outside business hours. Retain the Warsaw business calendar for every other priority.

**Reason:** P1 represents organisation-wide impact with work stopped. Suspending its clock over a weekend would hide continuing disruption. Continuous measurement exposes this cost, but requires funded out-of-hours response capacity; the timer cannot supply staffing.

**Service owner:** The incident-management service owner owns this commitment because that role controls critical-incident escalation, response capacity and out-of-hours coverage.

**Customer outcome:** An unresolved critical Friday-evening incident becomes overdue that evening. Affected staff receive the same measured commitment regardless of reporting time, while the organisation bears the coverage cost.

## C2 - Closed tickets and reopening

**Decision:** Preserve R-09: closed tickets are immutable. Keep R-10 reopening for resolved tickets through exactly seven elapsed days; subsequent work after closure requires a new ticket with related_to.

**Rejected alternative:** Reject only R-10's permission to reopen closed tickets. Keep resolved-ticket reopening and R-11's original resolution target after reopening.

**Reason:** Closure follows confirmation of the fix and provides a stable boundary for completed-work reporting. A linked follow-up distinguishes subsequent work. Reporters and desk agents bear the extra effort of creating that ticket, so agents should close only after confirmation rather than immediately upon resolution.

**Service owner:** The service-desk process owner approves closure policy because that role controls confirmation procedures, follow-up handling and interpretation of closure metrics.

**Customer outcome:** Reporters can challenge an unconfirmed resolution within seven days against the original deadline. Further work after confirmed closure gets a separate linked record, preserving the original completion history.

## C3 - VIP reporters and the priority matrix

**Decision:** Follow R-04 and R-05 for every reporter. Store reporter.vip but compute priority solely from impact and urgency.

**Rejected alternative:** Reject R-06's minimum P2 for VIP reporters. Retain the VIP field and the whole priority matrix, including P1 for a VIP with impact 1 and urgency 1.

**Reason:** The matrix allocates response capacity by operational disruption. A cosmetic single-person issue should not gain a shorter target solely because of reporter status. Executives lose automatic preferential treatment, and agents must assess their actual impact and urgency consistently.

**Service owner:** The service-desk product owner approves priority allocation because that role is accountable for distributing limited service capacity and explaining the policy to executive stakeholders.

**Customer outcome:** Equal impact and urgency receive equal priority and deadlines. Non-VIP reporters with serious disruption retain their relative priority instead of being displaced by low-impact VIP issues.
