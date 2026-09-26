<!-- ai-generated: 100% - Codex planned implementation after the accepted specs receipt. -->
# Plan and tasks

Prerequisite: accepted specs receipt https://github.com/swasik/itsm-2026-submissions/issues/174 for commit 2d67e024a9386e5ab2470381e51c3e0bcb67d296. No implementation files were added before this receipt.

1. Record C1=wallclock, C2=immutable and C3=matrix in DECISIONS.md with reasons and consequences.
2. Implement strict request validation and JSON errors, SQLite persistence, UUID tickets and exact-match filters.
3. Isolate RFC 3339 handling and Warsaw business-hours arithmetic. Match all eight SLA vectors and exact boundaries.
4. Implement transactional transitions, seven-day reopening and SLA evaluation without resetting deadlines.
5. Build Python 3.13/FastAPI application and tests images with dependencies installed at build time. Compose uses a named volume, healthcheck and no bind mounts.
6. Add pytest HTTP tests reading SVCDESK_URL, covering boundaries, clocks, validation and all vectors. Emit the required tests summary.
7. Run the official checker and persistence restart verification; write a factual convergence report.
8. Commit and push, verify the clean commit, publish an annotated tag, obtain its receipt and record both issue URLs and tag in Moodle.

SQLite BEGIN IMMEDIATE serializes lifecycle mutations. Tests and application use separate Docker build targets. Runtime requires no external network.
