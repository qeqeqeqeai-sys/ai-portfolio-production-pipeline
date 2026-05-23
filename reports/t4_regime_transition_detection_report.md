# T4 Regime Transition Detection Report

## Objective
Add a deterministic additive T4 layer that consumes T3-certified fragility curves and classifies bounded regime-state transitions.

## Scope
- New module: `t4_regime_transition_detection.py`
- Deterministic transition records per subject
- Certification envelope with gates, invariants, checksums, and forbidden capability controls
- Additive exports and tests

## Non-goals
- Narrative/causal explanations
- Forecasting/prediction
- Trading signals/actions
- ML/adaptive logic

## Architecture placement after T1/T2/T3
T4 consumes T3 certification envelopes and preserves temporal lineage/checksum replay chain from T1/T2/T3.

## Public APIs
- `validate_regime_transition_inputs`
- `build_regime_transition_records`
- `build_regime_transition_summary`
- `build_regime_transition_checksum_chain`
- `certify_regime_transition_detection`
- `build_t4_regime_transition_report`

## Input assumptions
T4 expects `t3_status`, `curve_records`, `fragility_curve_summary`, `checksum_chain`, `temporal_lineage`, and `result_checksum` in the T3 envelope.

## Regime-state methodology
Deterministic bounded inference from `curve_label` + metrics (`cumulative_score_delta`, `directional_consistency`, `persistence_count`, `missing_delta_count`, pair/observation counts) only.

## Transition classification policy
Uses bounded labels/states/direction/strength/confidence/quality only, with deterministic ordering and Decimal rounding (`ROUND_HALF_UP`).

## Confidence classification policy
Confidence is deterministic and based only on pair/observation depth, directional consistency, curve quality, missing deltas, lineage presence, and T3 status.

## Threshold constants
- `STRONG_CUMULATIVE_DELTA_THRESHOLD = 5.00`
- `MODERATE_CUMULATIVE_DELTA_THRESHOLD = 2.00`
- `HIGH_DIRECTIONAL_CONSISTENCY_THRESHOLD = 0.75`
- `MEDIUM_DIRECTIONAL_CONSISTENCY_THRESHOLD = 0.60`
- `STRESS_PERSISTENCE_THRESHOLD = 3`
- `MINIMUM_TRANSITION_PAIR_COUNT = 2`

## Checksum lineage behavior
Per-record transition checksums plus deterministic transition chain checksum; T3 curve chain checksum carried into T4 lineage.

## Certification gates
Implements ordered gates 1-19 as requested, including bounded labels, deterministic processing/order, checksum lineage, immutability, and forbidden logic/runtime constraints.

## Invariant flags
Includes deterministic processing/ordering, immutability, replay safety, bounded labels, Decimal policy, no runtime reads/writes/network, no prediction/trading/explanations/adaptive learning, additive-only.

## Forbidden capabilities
Explicitly blocked booleans for live fetch/supabase read-write/trading/prediction/optimization/adaptive-learning/hidden-state mutation/stochastic modeling/narrative explanation/recursive replay expansion.

## Test coverage
Added focused tests for API exports, blocked/degraded/certified statuses, deterministic ordering/checksum/immutability, regime mapping outcomes (rising/falling/stable/volatile/insufficient/degraded), confidence and strength bounded behavior, lineage preservation, and capability controls.

## Final status
Implemented as additive T4 transition classification only; no T5 narrative/causal/predictive/action logic included.
