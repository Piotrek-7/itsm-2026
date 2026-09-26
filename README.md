<!-- ai-generated: 30% - Course template with implementation and test instructions added by Codex. -->
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
| `docker-compose.yml` | the compose contract: service `svcdesk` on 8080, `SVCDESK_TEST_CLOCK`, a named volume; `tests` profile commented out |
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
