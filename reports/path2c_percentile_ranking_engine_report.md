# P2-C Percentile & Ranking Engine Report

## Objective
Deliver a deterministic, replay-safe percentile and ranking layer that converts certified P2-B relative fragility scores into cohort-relative rank, percentile, tier, and explanation outputs.

## Scope
- Additive-only P2-C module.
- Consumes P2-A cohort manifests and P2-B scoring fields.
- Does not recalculate P2-B scores.
- Does not generate new cohorts.

## Non-goals
- Trading signals, prediction, optimization, or execution.
- Adaptive/ML/dynamic ranking logic.
- Dynamic peer/cohort generation.
- Any network or database write behavior.

## Architecture Summary
Input contract validation, deterministic multi-key sort, deterministic tie-breaker defaults, bounded percentile assignment, percentile-tier mapping, replay checksum generation, and certification gates.

## Ranking Input Contract
`build_percentile_ranking_input_contract` defines required root/member fields, tie-breaker defaults, sort order, and forbidden capability inventory.

## Deterministic Sort Methodology
1. `relative_fragility_score` descending
2. `persistence_weakness_divergence` descending
3. `deterioration_velocity_divergence` descending
4. `benchmark_divergence` descending
5. `entity_id` ascending

## Tie-breaker Methodology
Optional tie-breaker fields are deterministically defaulted to `0.0` when missing/invalid and flagged for degraded certification.

## Percentile Methodology
For cohort size > 1:
`round(100 * (cohort_size - rank_position - 1) / (cohort_size - 1))`

Single-member cohort receives percentile `100` and `SINGLE_MEMBER_COHORT` quality flag.

## Percentile Tier Policy
- 90–100: `EXTREME_FRAGILITY_PERCENTILE`
- 75–89: `ELEVATED_FRAGILITY_PERCENTILE`
- 50–74: `MODERATE_FRAGILITY_PERCENTILE`
- 25–49: `LOWER_FRAGILITY_PERCENTILE`
- 0–24: `RELATIVE_STRENGTH_PERCENTILE`

## Missing/Clamped Data Policy
- Missing required identity/score fields block certification.
- Missing optional tie-breakers default deterministically and degrade.
- Out-of-range score values clamp to [0, 100] and are flagged.
- Duplicate entity IDs in a cohort block certification.

## Single-member Cohort Policy
Allowed, deterministic percentile `100`, flagged and degraded.

## Replay/Checksum Guarantees
Stable JSON serialization plus deterministic ordering and explicit replay metadata produce checksum-stable outputs.

## Certification Decision Logic
Statuses:
- `CERTIFIED_RELATIVE_RANKING`
- `DEGRADED_RELATIVE_RANKING`
- `BLOCKED_RELATIVE_RANKING`

## Forbidden Capabilities
No trading, prediction, optimization, autonomous execution, ML/adaptive ranking, dynamic cohort creation, stochastic logic, hidden logic, network/API calls, or Supabase/database writes.

## Final Supervisor Interpretation
P2-C produces deterministic cohort-relative ranking outputs with explicit quality/certification gates, preserving replay safety and additive integration posture with Path 1, P2-A, and P2-B.
