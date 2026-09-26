<!-- ai-generated: 100% - Codex compared the receipted specification with implemented code and observed tests. -->
# Specification-to-implementation comparison

The baseline is specs/spec.md, receipted in issue 174 at commit 2d67e024a9386e5ab2470381e51c3e0bcb67d296. This comparison was written after implementation and verification, not as a prediction of results.

R-01, R-02, R-03, R-18, R-19, R-20 and R-25 map to src/svcdesk/main.py: JSON routes, strict models, UUID generation, exact-match combined filters and error handlers. All 49 published HTTP checks passed in itsmlab 0.3.2. Own tests additionally exercised booleans and numeric strings as invalid impact values, malformed JSON, nested unknown fields, combined filters and distinct identifiers.

R-04, R-05 and R-06 converge through C3=matrix: the matrix determines priority, reporter.vip is preserved, and server-owned priority input is ignored. The checker observed matrix, matching DECISIONS.md. Only the conflicting VIP minimum in R-06 is rejected.

R-07, R-08, R-09, R-10 and R-11 map to the transactional transition handler. C2=immutable rejects reopening a closed ticket while permitting resolved-ticket reopening up to and including seven elapsed days. Own tests covered the exact boundary and one second beyond, unchanged deadlines, clearing resolution timestamps and two simultaneous acknowledgements, of which exactly one succeeds. The checker observed immutable. Only the closed-ticket exception in R-10 is rejected.

R-12, R-13, R-14, R-15, R-16 and R-17 map to src/svcdesk/clock.py. Both P1 targets use elapsed time; P2-P4 consume Warsaw business windows. Own tests cover all eight course vectors, an additional spring daylight-saving transition, the closing-time tie, equality at a due instant, event-based breaches and pause boundaries. Reopening does not reset the target. The checker observed wallclock, matching DECISIONS.md; only R-13's application to P1 is rejected.

R-21 uses a request dependency rather than shared mutable time. Tests checked malformed and timezone-naive clocks, equivalent offset instants, returning to real time and requests moving backwards in time. A separate container check with SVCDESK_TEST_CLOCK=0 confirmed that even a malformed header is ignored. That check ran with Docker networking disabled and created a ticket successfully.

R-22 and R-24 map to the multi-stage Dockerfile and docker-compose.yml. Application and tests install dependencies during build, svcdesk has build configured, and data uses a named volume rather than a bind mount. The official checker passed compose validation and measured health readiness in 6.9 seconds, below 120 seconds. These observations establish startup on the tested environment, not a guarantee on arbitrary hardware.

R-23 is implemented by SQLite transactions in /data on the named volume. An additional integration check created a ticket, restarted the service container, waited for health and fetched the same ticket. The entire returned object matched the pre-restart object. This verifies persistence beyond the published Lab 1 checks.

Core structure and decision-consistency checks passed. Core spec-first remains locally skipped by design; its evidence is the accepted specs receipt and implementation commits descending from that receipt. Stretch uses this comparison (S1) and the passing HTTP pytest service (S3). S2 agent configuration is not selected. No runtime behavioral divergence from the receipted choices was found in the executed checks; this is bounded evidence, not a proof for every possible input. Human assessment of the reasoning and Tier B grading remain outstanding.
