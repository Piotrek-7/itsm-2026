---
lab2_edge_cases:
  E1: {rule: R-08, count: 3}
  E2: {rule: R-06, count: 2}
  E3: {rule: R-09, count: 4}
  E4: {rule: R-10, count: 4}
  E5: {rule: R-12, count: 1}
  E6: {rule: R-13, count: 11}
---
<!-- ai-generated: 100% - Codex drafted this analysis from course rules, fixture examples and measured HTTP results; student review is required. -->

# Edge cases in the practice event log

The counts above come from the running service's response saved as metrics.json, over 2026-09-01T00:00:00Z through 2026-09-22T00:00:00Z (exclusive). Rules cited here belong to the Lab 2 METRIC-SPEC.md, not Lab 1's requirements.

## E1 - clock skew produces a negative lead time

- What the log contains: Three first-successful-deployment pairs have commits dated after their deployment: sha-0040 / DEP-0012 by 834 seconds, sha-0094 / DEP-0024 by 51 seconds, and sha-0123 / DEP-0031 by 780 seconds. R-08 retains all three pairs at zero and reports three negative_lead_time_pairs.
- What a default definition would have done: Straight timestamp subtraction would present impossible negative delivery times. Discarding the pairs instead would silently change the measured population and could move the median; a dashboard reader would not know that timestamp quality, rather than delivery performance, caused the difference.
- Why the rule is defensible: Zero is a bounded placeholder for an unmeasurable duration, not evidence of instantaneous delivery. Keeping both the pair and an explicit anomaly count preserves the population and tells the service owner to investigate clock synchronization before interpreting small improvements in lead time. The anomaly remains visible instead of being rewarded as exceptional speed.

## E2 - a revert of a revert

- What the log contains: sha-0070 reverts sha-0069 and sha-0071 reverts sha-0070. Both inherit CHG-0033 from the original commit. The count is two non-null reverts, not one chain and not three changes. The service resolves all commits transitively, even those outside the observation window.
- What a default definition would have done: Equating every commit to new work would count rollback and restoration as additional delivered value. Resolving only one link would also lose the original change identity on the second revert. Either approach could reward unstable implementation as increased throughput.
- Why the rule is defensible: The change is the unit of intended work; undoing and reinstating it does not create two new customer outcomes. R-06 preserves that identity while leaving the individual commits available for the pair-based lead-time metric. A delivery manager can distinguish effort spent correcting a change from the number of distinct changes delivered.

## E3 - a hotfix that never touched main

- What the log contains: Four distinct off-main shas reach production in the window: sha-0019, sha-0077, sha-0108 and sha-0127, each on a hotfix branch. The anomaly count includes production failures as well as successes; only successful deliveries form lead-time pairs.
- What a default definition would have done: Filtering commits to branch main would omit emergency work that actually reached customers. A dashboard might report less throughput or apparently better lead times merely because the incident response workflow used another branch.
- Why the rule is defensible: R-09 measures production delivery, not conformity to a branch naming convention. Counting the hotfixes makes emergency delivery visible; recording the off-main population still allows a team to inspect its workflow. Failed hotfix attempts remain operational activity without being misrepresented as successful delivery.

## E4 - a deployment with zero linked commits

- What the log contains: DEP-0026 and DEP-0032 are successful empty deployments; DEP-0043 and DEP-0044 are failed empty deployments. They produce no lead-time pairs but remain four production deployment attempts in the frequency and instability denominators.
- What a default definition would have done: An inner join from deployments to commits would drop these four rows. That would hide two failures and change both denominators, giving the release manager an incomplete picture of production activity. Attempting a per-deployment average over zero commits could also fail the entire calculation.
- Why the rule is defensible: A deployment can change runtime configuration or fail without having a linked source commit. R-10 keeps deployment activity separate from commit-based delivery. This inclusive denominator has a tradeoff: no-op successes can dilute instability rates and raise frequency, so deployment counts alone cannot establish customer value. The gaming demonstration exploits that distinction explicitly.

## E5 - a deployment that failed and never recovered

- What the log contains: DEP-0015 is covered by INC-0004, which opened at 2026-09-07T06:35:41Z and has no resolution. It is the practice log's one open failure. Seven other failures have measured recovery times, so eight failures split into seven recovered and one open.
- What a default definition would have done: Closing the incident at the window end would invent a recovery and make the metric depend on report timing. Dropping the failure entirely would hide unresolved harm and improve the failure ratio without any operational recovery.
- Why the rule is defensible: R-12 reports observed recovery durations only and carries unresolved failures separately. The median is therefore conditional on recovery, not a promise that all failures are fixed. A service owner must read open_failures alongside that median; an apparently short recovery time is not reassuring while an old failure remains open. R-14 retains that failure in the failure-rate numerator.

## E6 - overlapping incidents

- What the log contains: The service reports eleven unordered intersecting incident pairs. One concrete pair is INC-0010 (06:17:35 to 10:37:11 on 7 September) and INC-0011 (06:37:43 to 13:10:33 that day). The unresolved INC-0004 also intersects other intervals when its provisional end for overlap counting is the window's to instant.
- What a default definition would have done: Summing overlapping incident durations would double-count some wall-clock time; merging them would erase which failed deployment recovered when. Either could turn a deployment-recovery indicator into an undocumented outage-duration indicator, misleading the person comparing releases.
- Why the rule is defensible: R-12 and R-13 give each failed deployment its own recovery observation from its earliest covering incident, with incident-id order breaking ties. Overlap is a separate anomaly count, not a duration correction. This answers how failed deployments recovered while leaving customer downtime to a different measure. The [opened, resolved) rule also avoids counting intervals that only touch at an endpoint as simultaneous incidents.

## Gaming demonstration

The selected metric is deployment_frequency_per_day and the exploited rule is R-11, with R-10 explaining why empty deployments count. The baseline has 42 production deployments in 21 days, so frequency is 2.0 per day. The transformed log postpones seven existing substantive successful deployments beyond the window: DEP-0042, DEP-0041, DEP-0040, DEP-0039, DEP-0037, DEP-0033 and DEP-0031. It adds twenty successful production deployments with no commits. The new in-window count is 42 - 7 + 20 = 55, or 2.619048 per day: an increase of approximately 30.95%, above the required 25% margin.

The customer outcome worsens. Distinct original changes successfully delivered inside the window fall from 65 to 52, a 20% reduction, exceeding the harm requirement of at least 10%. There are no added commits, so filtering to original shas leaves the same ground-truth result. This is delayed real work, not fake slow work added to manufacture harm. All original events remain; commits and incidents are unchanged, and the seven moved deployments keep their identities, outcomes, environments and commit lists. Only their times move later. The remaining original deployments are unchanged. These properties satisfy R-19 conservation.

A team rewarded for a minimum number of releases could prioritize cheap no-op releases while deferring risky, substantive changes beyond the reporting cutoff. A release manager could receive credit for higher frequency even though customers receive thirteen fewer changes in the measured period. The log transformation demonstrates a permitted metric incentive, not proof that extra release activity necessarily caused the delay in a real team. Frequency should be read alongside delivered changes and change-level lead time, and rewards should not be based on release count alone.

scripts/build_lab2_artifacts.py reproduces the transformation, calls the running HTTP endpoint for both complete answers and checks conservation and the two numerical gates. metrics.json and gaming.json contain those responses; gaming/evidence.json records the original-work calculation. The demonstration changes input data only; the metric implementation has no special case for this fixture or for gaming events.
