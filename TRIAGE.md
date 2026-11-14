---
lab5_triage:
  image: ghcr.io/piotrek-7/itsm-2026@sha256:a2ef1c2e22c838b470607688d9ea845c3d12444cedd7adf5af3827783b1ee74b
  sarif_receipt: 405
---
<!-- ai-generated: 100% - Codex triaged real CI reports and drafted the interpretation of the receipted scanner measurements. -->
# Triage of the service and pipeline

The production image uses the pinned Python base `python:3.13-slim@sha256:e48f59cdba69a3cbd9ed2cf0f348d90d45a8d350d98134cf1070bc106ee9ed90`, applies available OS upgrades and removes pip from the final `application` stage. The `tests` stage retains pip and pytest; it is not the image published as the service. The final runtime runs as UID/GID 10001 with a writable owned data directory. These controls were introduced before the measured canary parent was frozen. The first main scan already had zero Trivy dependency findings and zero fixable HIGH/CRITICAL image findings; no specific CVE-removal count is claimed without a before-scan.

All scanner actions, images and gates remain the course's pinned implementation. Grype, OSV-Scanner and Semgrep report without blocking, while the Trivy dependency/image gates and gitleaks enforce the published policy. Neither ignore file contains an ignored ID/fingerprint, so no vulnerability or credential was silenced. The package was explicitly made public and both its provenance and SPDX 2.3 SBOM are verified separately.

The table covers the actual rules seen on our own files, including an initial finding that was subsequently fixed. Findings inside `lab5-canary/` are intentionally not repaired: that branch is the measurement input and is never merged into main.

| Tool | Rule | Decision | Reason |
|---|---|---|---|
| semgrep | dockerfile.security.missing-user.missing-user | accept | The primary Dockerfile now runs both service and tests as UID/GID 10001. The remaining result is genai/Dockerfile, an archived Lab 3 local experiment that writes a synthetic response to a host-mounted output directory and is not built or deployed by the production pipeline. Accept that experiment's root execution until 2027-01-15, when its output ownership should be redesigned before reuse; do not treat this as a blanket container exception. |
| semgrep | dockerfile.security.missing-user-entrypoint.missing-user-entrypoint | fix | The initial main run reported ai-rca/mcp-environment/Dockerfile. Added USER 1000:1000 before its entrypoint; the course MCP server is read-only, and the capture client can write files owned by the local student UID without running as root. This fixes the current build recipe without rewriting Lab 4's receipted tag. |
| semgrep | python.lang.security.audit.dynamic-urllib-use-detected.dynamic-urllib-use-detected | false-positive | scripts/build_lab2_artifacts.py obtains its base URL from a trusted operator's command line and posts synthetic course fixtures; it is not an HTTP endpoint accepting attacker-controlled URLs. Its dynamic urlopen call warrants an audit, but the arbitrary-file-read threat described by the rule is not reachable from an untrusted service request in this usage. Reassess before exposing this helper to external input. |

## Bake-off

The frozen reports come from canary commit `aa61b5ba553220d76f5a596c55c7c4ce7b34d8d6`, whose only parent is green main commit `ec7b80471293e9ad9dd988973c16318779fd484b`. The canary run [43613308513](https://github.com/Piotrek-7/itsm-2026/actions/runs/43613308513) failed both the dependency and secret gates as required. Its code, image and capture jobs succeeded. The reports were committed at `0d2edeb4898805e06810502af14427edab7f6670` and frozen by [SARIF receipt #405](https://github.com/swasik/itsm-2026-submissions/issues/405), before the course revealed this set's nine defect labels. The downloaded labels and the six SARIF files are unchanged; the manifest records the report hashes. The AI transcript and its converted SARIF were included in that first receipt, before any labels were available.

The table is the output of `python3 -S -E bakeoff.py --labels bakeoff/labels.json bakeoff/sarif/*.sarif`, using course P-14 through P-24: count matched defects rather than individual CVE results, normalize paths and classes, exclude files outside the canary and deduplicate only unmatched results. Therefore 14 Grype or 29 OSV raw results do not imply that many distinct defects.

| Detector | TP | FP | FN | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|---:|
| ai-reviewer | 9 | 0 | 0 | 1.0 | 1.0 | 1.0 |
| gitleaks | 2 | 1 | 7 | 0.6667 | 0.2222 | 0.3333 |
| grype | 2 | 0 | 7 | 1.0 | 0.2222 | 0.3636 |
| osv-scanner | 2 | 0 | 7 | 1.0 | 0.2222 | 0.3636 |
| semgrep | 3 | 3 | 6 | 0.5 | 0.3333 | 0.4 |
| trivy | 4 | 1 | 5 | 0.8 | 0.4444 | 0.5714 |

Gitleaks found two of the three planted credentials (C02 and C03), but also flagged the public JWT parser fixture: precision 0.6667, recall 0.2222, F1 0.3333. It missed the SMTP credential C05. Its seven false negatives include unrelated classes it is not designed to detect, so the all-defect recall must not be read as its accuracy on secrets alone. I would retain gitleaks as a secret gate, with human review of fixture exceptions rather than broad fingerprint ignores.

Grype and OSV-Scanner each found both dependency defects D02 and D08, with precision 1.0, recall 0.2222 and F1 0.3636. Their repeated advisories collapse to two package defects, and their seven misses are outside dependency scanning. The identical aggregate cells show coverage of this set, not equivalence of their advisory databases. I would keep these as reporting tools alongside the required Trivy gate until a larger evaluation justifies another blocking dependency check.

Semgrep found A04 (disabled TLS verification), A09 (unsafe YAML loading) and C02 (a credential), for precision 0.5, recall 0.3333 and F1 0.4. Its three unmatched results are two SQL rules on the same safe int-converted query in ticket_counts.py, plus the public JWT fixture. These are three distinct rule/location keys under the published scoring policy. The duplicate SQL suspicion surprised me: two alerts add review work without finding an extra flaw. I would gate selected validated rules, but keep this unfiltered rule pack reporting because half its scored results were false positives here.

Trivy found C02, C03 and both vulnerable packages, so precision 0.8, recall 0.4444 and F1 0.5714. It too flagged the JWT fixture. Its breadth makes the course's HIGH/CRITICAL dependency gate and fixable HIGH/CRITICAL image gate useful starting controls, with narrow, expiring exceptions only when justified. Image health is a separate measurement: this matrix concerns the canary source reports, and does not establish that every running container is safe.

None of the five conventional scanners found A12 (missing ownership enforcement), A16 (unrestricted webhook destination) or C05 (the SMTP password). The first two require interpreting application trust and data flow beyond an isolated syntax match; the third shows a pattern-coverage gap even for a familiar secret class. Their union found six of nine labelled defects, so adding more dependency scanners alone would not close these gaps.

The local Codex review found all nine labelled defects with zero scored false positives (precision, recall and F1 all 1.0). It explicitly rejected both decoys and connected the ownership and webhook behavior to their security consequences. This was a blind review of source files with the supplied prompt; the original JSON and local-model provenance are committed. I would use it as an additional reviewer, not an automatic blocker: model output can vary, package vulnerability claims need database verification, and a one-off nine-defect sample supplies no stability estimate. The zero-FP cell does not prove zero hallucinations on real services.

Every recall here is an optimistic upper bound for deployment decisions: the course selected compact, seeded examples from a known pool with conspicuous defects, while production flaws span longer control flows, configuration and changing dependencies. There is no representative negative corpus or repeated-model trial. The matrix measures agreement with the published labels and matching rules on this set; it does not certify the application's security.

## Verification and remaining limits

The service image named in the front matter was produced by main run [43613030762](https://github.com/Piotrek-7/itsm-2026/actions/runs/43613030762). Both `gh attestation verify` checks succeeded: the default SLSA provenance and the separate `https://spdx.dev/Document/v2.3` predicate, constrained to this repository's ci.yml signer and refs/heads/main source. Summaries are in evidence/lab5; full signed attestations remain attached to the public image. The measured canary's parent and its reports are preserved independently of later main commits.

The published practice matrix matches exactly. Ten focused parser/matcher tests cover malformed locations, suppression, path roots, aliases, package tokens, CWE precedence and ASCII boundaries. All 92 existing service checks pass. The mutation tests pass on the original module and both equivalent rewrites and kill all 12 published practice mutants; this does not predict the result on the grader's 40 withheld mutants. No custom Semgrep rule set is submitted: the two attempted Stretch components are the mutation suite and the local AI detector.
