<!-- ai-generated: 100% - Drafted by Codex from the course package and the agreed implementation direction. -->
# svcdesk constitution

1. The course package is authoritative. REQUIREMENTS.md defines R-01 through R-25; API.md defines the exact HTTP contract; CHECKS.md defines the published conformance checks. Where precision differs, follow API.md.
2. Publish this specification and obtain an accepted `kind:specs`, `lab:1` receipt before creating implementation files under `src/`. The receipt commit must remain an ancestor of every commit adding implementation files. The template's src/README.md is the sole exception.
3. Resolve contradictions explicitly and minimally. C1 is `wallclock`, C2 is `immutable`, and C3 is `matrix`. Preserve the non-conflicting parts of each requirement. DECISIONS.md must explain the tradeoffs, responsible service-owner role and customer consequences, and match the running service.
4. Expose a JSON HTTP API on port 8080. Use Python 3.13, FastAPI and SQLite. Keep validation, state transitions, SLA arithmetic and persistence separable so that boundary cases can be checked independently.
5. Store tickets durably in SQLite on a Docker named volume. Build application and test images from this repository. Install dependencies during image construction; require no external network access at runtime and use no host-path bind mounts.
6. Treat time as timezone-aware instants. Return UTC timestamps with Z; use Europe/Warsaw and its daylight-saving rules for business hours. Test time belongs to one request and must never change a global clock.
7. Verify all published Core checks and add meaningful tests for boundaries not covered by those checks. A passing local checker does not establish the spec-first requirement; the GitHub receipt and commit ancestry do.
8. Disclose AI authorship honestly in every checked source and specification file. Keep credentials, personal data and environment diagnostic output out of the repository. Documentation must describe implemented behavior without fabricated test results.
9. Submit only a committed, verified tree using a new annotated tag for each attempt. Never move a receipted tag. Completion requires accepted specs and submission receipts and the corresponding Moodle entry.
