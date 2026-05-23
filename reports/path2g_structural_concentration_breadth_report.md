# P2-G Structural Concentration & Breadth Intelligence Report

## Objective
Deliver deterministic, replay-safe concentration and breadth diagnostics that determine whether weakness is isolated, concentrated, mixed, or broad-based.

## Scope
Consumes P2-A manifests, P2-B scores, P2-C percentiles/rankings, P2-F explanation packets, replay metadata, checksums, and quality flags.

## Non-Goals
No recalculation of P2-B/P2-C/P2-F outputs. No prediction, trading, optimization, portfolio logic, dynamic cohorts, dynamic benchmarks, network calls, or database writes.

## Architecture Summary
Input contract -> deterministic cohort fragility distribution -> concentration/breadth metrics -> fixed-threshold regime classification -> deterministic explanation -> certification.

## Input Contract
See `build_concentration_breadth_input_contract`.

## Cohort Fragility Distribution Methodology
Deterministic extraction by cohort_members order with stable score sorting (descending score then entity_id). Missing scores are excluded deterministically and flagged.

## Top-Fragility Share Methodology
Top-N share of total fragility score with deterministic top_n policy: >=10 => 3, 5-9 => 2, <5 => 1 + SMALL_COHORT flag.

## Elevated Breadth Methodology
Share of usable members with score >=70 or percentile >=75.

## Weakness Participation Methodology
Share of usable members with score >=50.

## Fragility Dispersion Methodology
max(score) - min(score) over usable members.

## Concentration/Breadth Regime Policy
CONCENTRATED_FRAGILITY, BROAD_BASED_WEAKNESS, MIXED_CONCENTRATION_BREADTH, LOW_STRUCTURAL_WEAKNESS, INSUFFICIENT_BREADTH_EVIDENCE via fixed thresholds.

## Fixed Threshold Policy
high_top_fragility_share>=0.55; moderate_top_fragility_share>=0.40; high_elevated_breadth>=0.50; moderate_elevated_breadth>=0.30; high_weakness_participation>=0.60; moderate_weakness_participation>=0.40.

## Missing/Clamped Data Policy
Missing cohort identity/members or all scores blocks. Partial scores degrade. Missing percentile/ranking degrades. Out-of-range scores/percentiles clamp to [0,100] and are flagged.

## Deterministic Explanation Policy
Narrative text is deterministic templates only.

## Replay/Checksum Guarantees
deepcopy input immutability and stable JSON serialization for checksum.

## Certification Decision Logic
Blocked for required identity/members/score failures; degraded for small cohort, partial scores, or missing percentile/ranking; certified otherwise.

## Forbidden Capabilities
Trading, prediction, optimization, dynamic/adaptive methods, clustering, hidden logic, network/API calls, and database writes.

## Final Supervisor Interpretation
P2-G provides deterministic structural diagnostics describing whether fragility is concentrated or broad across the cohort while preserving additive-only integration boundaries.
