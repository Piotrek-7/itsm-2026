<!-- ai-generated: 100% - Codex documented the captured public payload and its counting limits. -->
# Class rework capture

class-submissions.json is the unmodified stdout from the `gh api` invocation recorded in rework-class.json. The command paginates all issues carrying both receipted and kind:submission, with state=all; `--slurp` preserves the API pages in one JSON array. It accesses the public repository anonymously. The SHA-256 in rework-class.json binds the exact saved bytes.

scripts/capture_rework.py parses each issue's Tag field. Every captured receipted submission is a deployment, and a tag labN/v2 or later is rework. It excludes pull requests. It does not deduplicate by student or lab, remove late receipts, or apply the grading attempt limit: the exercise says to count every receipted submission. Thus a receipted v4, if present, is included as rework even though such a tag does not imply an additional eligible grading attempt.

The captured snapshot contains 103 submissions: 80 v1, 15 v2, 7 v3 and 1 v4. Rework is (15 + 7 + 1) / 103 = 23 / 103 = 0.223301 (22.3301%). This is the exercise's proxy for deployment rework, not a claim that students caused production incidents. Tags are read from the captured issue fields; edited issue fields and the timing of public API pagination are limitations of this observational dataset. No personal authentication token is stored.
