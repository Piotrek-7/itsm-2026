<!-- ai-generated: 100% - Codex derived this plan from the Lab 2 course package. -->
# Lab 2 plan

Extend the existing Lab 1 service; preserve its accepted tag. METRIC-SPEC.md version 1.0.0 defines Lab 2 rules R-01 through R-21 (these identifiers are separate from Lab 1 requirements).

1. Copy the published fixtures unchanged. Upgrade the checker to at least 0.3.2 and set lab: 2.
2. Implement stateless POST /dora/metrics: validate the whole log after first-occurrence event deduplication, resolve transitive change identity, select production deployments in the half-open window, and compute metrics with decimal half-up rounding. Never filter commits or incidents by the observation window. Do not read fixture answers at runtime.
3. Export GET /dora/ticket-events from the lifecycle timestamps actually held in SQLite, ordered by UTC instant and ticket identifier. Do not invent a start timestamp or lost resolution history after reopening.
4. Exercise synthetic logs independent of the practice fixture: empty denominators, duplicate events, window boundaries, rounding ties, reverts, off-main failures, earliest covering incidents and unresolved recovery. Retain Lab 1 tests.
5. Generate metrics.json and gaming.json from actual HTTP responses. Demonstrate more deployments but less delivery by postponing existing successful deployments and adding no-op deployments, within conservation rules. Keep a reproducible generator and calculate harm on original work.
6. Write EDGE-CASES.md with actual response counts, concrete event examples, reasoning and gaming arithmetic. AI authorship is disclosed; the student must review the reasoning under the course's AI-assisted policy.
7. For Stretch use own tests and a captured gh api response from the public submissions repository. Count every receipted submission as a deployment, and tags v2 or later as rework. Preserve response bytes, timestamp and SHA-256. Do not claim an unperformed prediction experiment.
8. Verify Lab 2 and Lab 1 regression behavior. Commit and push, verify the clean tree, publish lab2/v1 without moving lab1/v1, and generate the submission form. Final issue acceptance and Moodle entry complete submission.
