# P2-B Relative Fragility Scoring Report

## Objective
Implement a deterministic, replay-safe scoring layer that maps absolute/path-temporal fragility inputs into bounded cohort-relative fragility scores.

## Scope
Additive-only P2-B module consuming explicit cohort structures from P2-A. No new cohort generation.

## Non-goals
- Trading signals
- Price prediction
- Portfolio optimization
- Autonomous execution
- Adaptive weighting
- ML clustering
- Dynamic peer generation

## Architecture Summary
Input contract -> deterministic cohort baselines -> fixed weighted component scoring -> peer deltas and driver summary -> certification gates -> stable checksum.

## Input Contract
Required identity/cohort fields: entity_id, cohort_id, cohort_version, cohort_members.
Allowed deterministic components:
- fragility_level_divergence
- deterioration_velocity_divergence
- persistence_weakness_divergence
- regime_instability_divergence
- benchmark_divergence

## Cohort Baseline Methodology
Cohort members are consumed as explicit inputs and sorted by entity_id for deterministic ordering. Peer baselines are generated with deterministic median and mean statistics.

## Scoring Component Methodology
Each component is clamped to [0,100] deterministically. Missing optional components default to 0 and are quality-flagged.

## Fixed Weighting Policy
- fragility_level_divergence: 30
- deterioration_velocity_divergence: 25
- persistence_weakness_divergence: 20
- regime_instability_divergence: 15
- benchmark_divergence: 10

Total fixed weight: 100. No adaptive or learned weighting is used.

## Tier Policy
- 85–100: EXTREME_RELATIVE_FRAGILITY
- 70–84: ELEVATED_RELATIVE_FRAGILITY
- 50–69: MODERATE_RELATIVE_FRAGILITY
- 30–49: STABLE_NEUTRAL
- 0–29: RELATIVE_STRENGTH

## Missing/Clamped Data Policy
Missing optional components degrade quality/certification but do not crash scoring. Out-of-range values are clamped and flagged.

## Deterministic Peer Comparison Policy
Peer deltas use deterministic cohort medians and canonical member ordering. No stochastic logic and no hidden ranking.

## Replay/Checksum Guarantees
Stable JSON serialization with SHA-256 checksums ensures replay-safe deterministic outputs.

## Certification Decision Logic
- BLOCKED_RELATIVE_FRAGILITY for missing required identity/cohort fields or invalid cohort membership.
- DEGRADED_RELATIVE_FRAGILITY for non-critical validation/quality issues.
- CERTIFIED_RELATIVE_FRAGILITY when all gates pass.

## Forbidden Capabilities
No trading, prediction, optimization, dynamic peer generation, stochastic scoring, network/API calls, or Supabase/database writes.

## Final Supervisor Interpretation
P2-B is additive-only, deterministic, bounded, replay-safe, and integrated with explicit cohort inputs from P2-A.
