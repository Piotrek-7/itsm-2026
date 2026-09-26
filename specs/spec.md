<!-- ai-generated: 100% - Drafted by Codex from REQUIREMENTS.md, API.md and CHECKS.md before implementation. -->
# svcdesk Lab 1 specification

## Scope and authority

Build an internal service-desk JSON API for creating, prioritising and tracking tickets and their SLA obligations. This specification interprets the course package's R-01 through R-25; exact HTTP behavior follows API.md. It is written before implementation and must receive the course bot's specs receipt before any implementation is added under src/.

There is no user interface, authentication, pagination, holiday calendar or external integration in this laboratory. Persistence is required even though the Lab 1 Tier A checker does not test it.

## Conflict resolutions

| Decision | Conflicting requirements | Selected behavior | Minimal rejected part and consequence |
|---|---|---|---|
| C1 = wallclock | R-13 and R-14 | Both P1 targets run continuously; P2-P4 count business hours. | Reject R-13 only for P1. Critical organisation-wide interruptions remain visible as overdue overnight and on weekends. This commits the incident-management service owner to arranging out-of-hours coverage; the software does not supply that staffing. |
| C2 = immutable | R-09 and R-10 | Closed tickets cannot reopen; resolved tickets may reopen within seven days. | Reject only R-10's permission to reopen a closed ticket. Preserve the confirmed closure record; further work uses a new ticket with related_to, at the cost of an additional ticket for the reporter. The service-desk process owner owns this closure policy. |
| C3 = matrix | R-05 and R-06 | Impact and urgency alone determine priority. Store VIP without a priority override. | Reject R-06's minimum P2 for VIP reporters. Equal operational impact receives equal priority; executives lose automatic escalation. The service-desk product owner owns this allocation of service capacity. |

These choices must also be declared and defended in DECISIONS.md using its required five labels. No choice permits ignoring the rest of a conflicting requirement: P2-P4 still use business hours, resolved tickets still reopen, and VIP P1 tickets remain P1.

## Ticket data and validation (R-03, R-18, R-20)

POST /tickets requires a title of 1-200 characters, a reporter object with a name of 1-100 characters, and integer impact and urgency in 1..3. Reject booleans, strings and fractional numbers as impact or urgency. Description is optional, defaults to an empty string and has at most 4000 characters. Reporter email is an optional string or null, defaults to null, and has no additional email-format requirement. Reporter vip is a boolean defaulting to false. related_to is an optional string or null and is not checked for existence in Lab 1.

Assign an opaque non-empty UUID, state new and created_at from the request's clock. acknowledged_at, resolved_at and closed_at start null. Store the derived priority and both SLA due instants. Return the complete Ticket model defined in API.md, including the reporter and SLA objects.

Ignore all unknown fields and all client-supplied server-owned fields, including id, priority, state, timestamps and sla. Validation errors, including malformed JSON bodies, return 422 with a top-level error object. Unknown tickets return 404 with an error object. Unknown routes return 404 JSON; unsupported methods may return 405 JSON.

## HTTP interface (R-01, R-02, R-19, R-25)

| Method and route | Successful response |
|---|---|
| GET /health | 200 with {"status":"ok","service":"svcdesk"} |
| POST /tickets | 201 with the created Ticket |
| GET /tickets | 200 with an array of every matching Ticket |
| GET /tickets/{id} | 200 with the complete Ticket |
| GET /tickets/{id}/sla | 200 with the SLA evaluation described below |
| POST /tickets/{id}/ack, /start, /resolve, /close, /reopen | 200 with the updated Ticket |

All responses use application/json. List filters state and priority are optional exact matches, combined by AND when both appear. Return all matches without pagination; ordering is unspecified.

## Priority (R-04, R-05, R-06)

| impact / urgency | 1 | 2 | 3 |
|---|---|---|---|
| 1 | P1 | P2 | P3 |
| 2 | P2 | P3 | P4 |
| 3 | P3 | P4 | P4 |

Use this matrix for every reporter under C3=matrix. Preserve reporter.vip in the stored and returned ticket but do not change priority because of it. Ignore an explicitly requested priority.

## Lifecycle (R-07 through R-11)

The forward transitions are new --ack--> acknowledged --start--> in_progress --resolve--> resolved --close--> closed. ack sets acknowledged_at, resolve sets resolved_at, and close sets closed_at to the request clock. Reject every other forward transition, including repeated actions, with 409 and an error object. Actions on nonexistent tickets return 404.

reopen is allowed only from resolved and only when now <= resolved_at + seven elapsed days, including the exact boundary. It returns the ticket to in_progress and clears resolved_at and closed_at. Retain acknowledged_at and the original SLA deadlines. After the seven-day boundary return 409. Under C2=immutable, every reopen of closed returns 409 regardless of age; further work is represented by a new ticket with related_to. Reopen of any other state is invalid.

## SLA targets and time arithmetic (R-12 through R-17)

| Priority | Acknowledgement target | Resolution target | Clock |
|---|---|---|---|
| P1 | 15 minutes | 4 hours | Elapsed wall-clock time |
| P2 | 1 hour | 8 hours | Business hours |
| P3 | 4 hours | 24 hours | Business hours |
| P4 | 8 hours | 72 hours | Business hours |

Both targets start at created_at, not at acknowledgement or work start. For P1 add the target duration directly to the creation instant. For P2-P4 count only Monday-Friday, 08:00 inclusive to 16:00 exclusive, in Europe/Warsaw. Public holidays are ordinary weekdays. If creation is outside the business window, advance to the next opening. Consume successive business windows, skipping weekends. A target exhausted exactly at 16:00 is due at that closing instant, not the next opening. Apply daylight-saving transitions using the IANA timezone database and return every timestamp in UTC with Z.

Acceptance examples from API.md, with the selected C1=wallclock:

| Vector | Priority | Created at (UTC) | Acknowledgement due (UTC) | Resolution due (UTC) |
|---|---|---|---|---|
| T1 | P1 | 2026-10-14T10:00:00Z | 2026-10-14T10:15:00Z | 2026-10-14T14:00:00Z |
| T2 | P3 | 2026-10-16T13:30:00Z | 2026-10-19T09:30:00Z | 2026-10-21T13:30:00Z |
| T3 | P1 | 2026-10-16T15:00:00Z | 2026-10-16T15:15:00Z | 2026-10-16T19:00:00Z |
| T4 | P2 | 2026-10-17T10:00:00Z | 2026-10-19T07:00:00Z | 2026-10-19T14:00:00Z |
| T5 | P4 | 2027-01-14T14:30:00Z | 2027-01-15T14:30:00Z | 2027-01-27T14:30:00Z |
| T6 | P1 | 2027-01-15T15:50:00Z | 2027-01-15T16:05:00Z | 2027-01-15T19:50:00Z |
| T7 | P2 | 2026-10-14T10:00:00Z | 2026-10-14T11:00:00Z | 2026-10-15T10:00:00Z |
| T8 | P3 | 2026-10-23T13:00:00Z | 2026-10-26T10:00:00Z | 2026-10-28T14:00:00Z |

GET /tickets/{id}/sla returns priority, ack_due_at, resolve_due_at, ack_breached, resolve_breached and paused. For each target, compare its event timestamp to the due instant when the event exists; otherwise compare now. Breach means strictly later, never equality. A timely acknowledgement stays timely when queried later. A reopened ticket has no resolution event and is evaluated against its original resolution deadline.

paused is true exactly when the ticket is neither resolved nor closed, its resolution uses business hours, and now is outside a business window. P1 is never paused. Pause does not erase an existing breach or move a precomputed deadline.

## Request clock (R-21)

When SVCDESK_TEST_CLOCK is 1 or true, accept an optional X-Test-Clock RFC 3339 instant with an explicit offset. Use it only for that request's creation, transition, breach, pause and reopen calculations. Reject malformed or timezone-naive values with 422 and an error object. Without a header use real UTC time. With the environment variable disabled ignore the header, even if malformed.

Never retain a global test clock, impose monotonic time across requests or reject an action merely because its timestamp precedes another event. GET list and GET ticket expose stored values and do not change deadlines or timestamps.

## Deployment and persistence (R-22 through R-24)

Use a Dockerfile based on Python 3.13 and install pinned application dependencies at build time. Include timezone data. Listen on 0.0.0.0:8080. The compose service is named svcdesk and has build: ., SVCDESK_TEST_CLOCK enabled and a healthcheck. Store SQLite data under /data in a named volume. No service uses host bind mounts or fetches dependencies at runtime. Tickets and lifecycle updates survive a service-container restart. The service and health endpoint become ready within 120 seconds of compose startup.

## Acceptance and submission

Run the official Tier A checker for all Core specifications. Core 1 verifies compose and startup; Core 2 verifies the published 49 HTTP checks; Core 3 verifies DECISIONS.md structure; Core 4 must observe wallclock, immutable and matrix. Core 5 remains locally skipped and is established by the accepted specs receipt and commit ancestry.

Target Stretch S1 and S3. After implementation, write a truthful comparison in specs/converge.md (at least 400 characters, referencing at least three distinct R-01..R-25 requirements). Provide a compose tests service under profiles: [tests] with at least ten meaningful API tests reading SVCDESK_URL. Its last stdout line must be ITSMLAB-TESTS: passed=<n> failed=0, and it must finish within 300 seconds. Include boundary coverage for reopening, exact SLA deadlines, daylight saving, validation and persistence where applicable.

Commit and push the implementation, verify the clean committed tree, create and push an annotated lab1/v1 tag, and obtain its submission receipt. Record the submission issue URL, tag and specs issue URL in Moodle. Do not move a receipted tag; any correction uses a subsequent attempt tag.
