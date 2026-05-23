# T3 Fragility Evolution Curves Report

## Objective
Implement a deterministic additive T3 layer that interprets fragility evolution over time from T2 structural delta intelligence.

## Scope
- Add `t3_fragility_evolution_curves.py`.
- Build deterministic subject-level temporal curve records from T2 `delta_records`.
- Compute bounded temporal metrics and bounded curve classifications.
- Preserve T1/T2 checksum lineage and replay safety.
- Emit deterministic certification envelope.
- Add focused tests and exports.

## Non-goals
No regime transitions, confidence scoring, explanations, predictions, trading logic, adaptive learning, or forward forecasts.

## Architecture Placement
T3 runs strictly after T2 certification, consumes only T2 envelope fields, and produces additive deterministic outputs without IO side-effects.

## Public APIs
- `validate_fragility_curve_inputs`
- `build_fragility_evolution_curves`
- `build_fragility_curve_summary`
- `build_fragility_curve_checksum_chain`
- `certify_fragility_evolution_curves`
- `build_t3_fragility_evolution_report`

## Input Assumptions
Consumes T2 envelope with: `t2_status`, `delta_records`, `structural_delta_summary`, `checksum_chain`, `temporal_lineage`, `result_checksum`.

## Curve Methodology
Group score deltas by deterministic `(subject_type, subject_id)` keys, order by pair index/date/checksum, compute deterministic Decimal metrics, classify with fixed bounded labels, then stable-sort curve records by subject metadata and checksum.

## Metric Definitions
- cumulative_score_delta
- average_pair_delta
- directional_consistency
- persistence_count
- positive/negative/unchanged/missing counts
- max single-pair increase/decrease

## Classification Policy
Bounded labels only:
`FRAGILITY_RISING`, `FRAGILITY_FALLING`, `FRAGILITY_STABLE`, `FRAGILITY_VOLATILE`, `FRAGILITY_PERSISTENTLY_ELEVATED`, `FRAGILITY_INSUFFICIENT_HISTORY`, `FRAGILITY_DEGRADED_INPUT`.

## Threshold Constants
- `DIRECTIONAL_CONSISTENCY_THRESHOLD = 0.60`
- `STABLE_ABS_DELTA_THRESHOLD = 1.00`
- `PERSISTENCE_THRESHOLD = 2`
- Decimal quantization with `ROUND_HALF_UP`.

## Checksum Lineage Behavior
Each curve has a `curve_checksum`; chain checksum is produced and linked with T2 `delta_chain_checksum` and T2 `result_checksum` in lineage fields.

## Certification Gates
Implemented fixed ordered gates for envelope presence, delta presence, depth, pair checksums, deterministic behavior, bounded labels, rounding policy, lineage, immutability, and prohibited runtime capabilities.

## Invariant Flags
Explicit booleans included for determinism, immutability, replay safety, lineage, bounded labels, decimal policy, no reads/writes/network, no prediction/trading/regime/explanations/adaptive behavior, additive-only.

## Forbidden Capabilities
Explicitly blocked inventory includes live fetch, supabase read/write, trading execution, prediction, optimization, adaptive learning, hidden state mutation, stochastic modeling, regime detection, explanation generation, recursive replay expansion.

## Test Coverage
Added focused tests for API exports, certified/degraded/blocked outcomes, deterministic grouping/order/checksum behavior, immutability, metric correctness, label coverage (rising/falling/stable/volatile/persistently elevated/insufficient/degraded), lineage preservation, forbidden capability blocking, helper/report/smoke compatibility.

## Final Status
T3 additive fragility evolution curve layer implemented and validated with deterministic replay-safe behavior.
