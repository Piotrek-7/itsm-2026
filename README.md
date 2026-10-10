<!-- ai-generated: 65% - Course template with implementation and test instructions added by Codex. -->
# svcdesk - ITSM 2026/27 course repository

This repository was created from the course template. It holds your `svcdesk` service for the whole semester:
built in Lab 1, extended in the later labs. Keep it public, and keep personal data out of it.

## The one command

    ./itsmlab.sh verify 1            # Linux, macOS
    .\itsmlab.ps1 verify 1           # Windows PowerShell (once before: Set-ExecutionPolicy -Scope CurrentUser RemoteSigned)

It runs the published Tier A checker (a container) against this directory: builds and starts your service with
`docker compose`, runs the published checks, prints a table, and exits 0 when every Core spec passes. Add
`--json report.json` to keep the machine-readable report. Tier A runs are unlimited and never count as attempts.

Before the first run: fill in `repository:` in `itsmlab.yaml`, copy `Dockerfile.example` to `Dockerfile` (or
write your own), and read the course package (`README.md`, `PREWORK.md`, `lab1/`), published on Moodle.

## Layout

| path | what it is |
|---|---|
| `docker-compose.yml` | the compose contract: service `svcdesk` on 8080, `SVCDESK_TEST_CLOCK`, a named volume; optional tests, observability and gap profiles |
| `Dockerfile.example` | a Python 3.13 image skeleton; copy to `Dockerfile` or replace for your language |
| `DECISIONS.md` | your reasoning artifact: front matter with the three decisions, three sections, five labels each |
| `itsmlab.yaml` | lab number, baselines, your repository, the submissions repository, the checker image |
| `itsmlab.sh`, `itsmlab.ps1` | wrappers that run the checker container |
| `specs/` | your specifications, published and receipted before any code |
| `src/` | your implementation |
| `.github/workflows/tier-a.yml` | runs the checker on every push and publishes `report.json` as an artifact with a step summary |
| `.gitignore` | keeps `report.json`, virtual environments and local data out of git |
| `.gitattributes` | LF line endings on every system, so the checker's git sees a clean tree on Windows too; keep it |

## Every push runs the checker

The workflow `tier-a` runs on every push and on demand (Actions tab, "Run workflow"). It needs no secrets. The
job is red when a Core spec fails; the step summary shows which checks, and `report.json` is attached as an
artifact.

## Implemented Lab 1 service

The service uses Python 3.13, FastAPI and SQLite. Decisions are C1=wallclock, C2=immutable and C3=matrix; see DECISIONS.md for consequences. The accepted pre-implementation specs receipt is https://github.com/swasik/itsm-2026-submissions/issues/174.

Run `docker compose up --build --wait svcdesk` to serve the API on port 8080. Run `docker compose --profile tests run --rm --build tests` for the independent HTTP tests; the last line reports their actual outcomes. Test data persists in the named volume. `docker compose down` stops the application while preserving that data; deleting the volume deletes its tickets.

The test-clock header is enabled in course compose configuration. Set SVCDESK_TEST_CLOCK to 0 to ignore it outside testing. Images install dependencies at build time. Stretch deliverables are specs/converge.md and the tests service; no S2 agent configuration is claimed.

## Lab 2 delivery metrics

`POST /dora/metrics` accepts a JSON object with `window: {from, to}` and an `events` array. It is stateless: metrics depend only on that log and the window, not on stored tickets. The calculator follows Lab 2 METRIC-SPEC.md 1.0.0, including first-occurrence event deduplication, transitive revert identity, half-open production windows and half-up rounding. `GET /dora/ticket-events` exports the lifecycle timestamps currently held for all tickets, sorted by instant and ticket id; it does not invent a timestamp for starting work or reconstruct timestamps cleared by reopening.

Run `./itsmlab.sh verify 2 --json report.json` for the official checks. The compose tests service runs both Lab 1 regression tests and Lab 2 synthetic-log tests. The application image contains no practice fixture or expected-answer file; only the tests build target contains fixtures.

To regenerate `metrics.json`, `gaming/after.jsonl`, `gaming.json` and the gaming evidence, start svcdesk and run `python3 scripts/build_lab2_artifacts.py --base-url http://127.0.0.1:8080`. These artifacts are obtained from actual HTTP responses. The transformation delays seven substantive deployments and adds twenty no-op deployments, illustrating why higher release frequency need not mean more delivered work. EDGE-CASES.md explains the six anomalies and the arithmetic.

Stretch uses the independent tests and a snapshot of public class submissions. Run `python3 scripts/capture_rework.py --gh /path/to/gh` to make a new capture; this intentionally changes its timestamp, digest and counts as the class history grows. A tagged submission preserves the original snapshot. No METR prediction experiment is claimed.

AI disclosure: Lab 2 code, test cases, tooling and the draft reasoning were generated by Codex from the course specification. The student must review the explanation and remains responsible for it under the course's AI-assisted policy. Automated conformance does not replace the lecturer's assessment of EDGE-CASES.md.

## Lab 3 monitoring and SLOs

`GET /kb/search?q=...` calls the course's `kb-index` once per valid request, with a five-second timeout and no retries or cache. `/metrics` exposes a Prometheus duration histogram in seconds. Its labels contain route templates, methods and numeric status codes, never ticket IDs or query text. `/metrics` itself is excluded from request observations.

```sh
docker compose --profile observability up -d --build svcdesk prometheus grafana
./itsmlab.sh load 3
./itsmlab.sh verify 3 --json report.json
docker compose --profile tests run --rm --build tests
docker run --rm -v "$PWD/prometheus:/p" -w /p --entrypoint promtool prom/prometheus:v3.15.0 test rules alerts_test.yml
```

Open Grafana at http://localhost:3000 and select **svcdesk — knowledge search SLO** in the svcdesk folder. Anonymous access is read-only. Prometheus is at http://localhost:9090. These two services are in the optional `observability` profile; the official checker starts only the application and dependency. Their configuration and dashboard are baked into images, so rebuild after changing them.

`slo.md` defines the objectives, error budgets, measured bucket design and two multiwindow availability alerts. `ai-first-draft.md` preserves the initial AI proposal committed before measurements, followed by its measured verdict. The local tests cover exact forwarding, URL encoding, dependency failures and bounded metric cardinality as well as the earlier laboratories.

Stretch artifacts are the genuine local-model trace and semantic-conventions comparison in `genai/`, and the client/server latency experiment in `gap.json` and `gap/README.md`. No Kubernetes experiment is claimed. Stop the local model before load testing; its image and weights are not part of the running service. Start the optional proxy using `docker compose --profile gap up -d toxiproxy`; see the gap README for its configuration.

Lab 3 implementation, tests and draft reasoning were generated by Codex. The student should review `slo.md`, `ai-first-draft.md` and `genai/DIFF.md` and understand the measured choices; the lecturer assesses reasoning separately from automated conformance. Existing receipted Lab 1 and Lab 2 tags are preserved.
