# T5 Historical Explainability Report

## Objective
Implement a deterministic, replay-safe historical explainability layer for T4 regime transitions.

## Scope
- Additive T5 module for deterministic explanation records.
- Template-constrained bounded explanations.
- Replay-linked evidence summaries and checksum lineage preservation.
- Deterministic certification envelope output.

## Non-goals
- No prediction, recommendation, optimization, or trading guidance.
- No open-ended LLM narrative generation.
- No runtime network access, reads, writes, or adaptive learning.

## Architecture placement after T1/T2/T3/T4
T5 consumes T4 certification outputs (`t4_status`, transition records, checksum chain, temporal lineage, and result checksum) and extends lineage with deterministic explanation outputs.

## Public APIs
- `validate_historical_explainability_inputs`
- `build_historical_explanation_records`
- `build_historical_explanation_summary`
- `build_historical_explanation_checksum_chain`
- `certify_historical_explainability`
- `build_t5_historical_explainability_report`

## Input assumptions
- T4 envelope is deterministic and checksum-bearing.
- Transition records include required transition checksums and regime fields.

## Explanation methodology
- Deterministic template selection from bounded transition characteristics.
- Deterministic summary phrase assignment.
- Stable ordering by `subject_type`, `subject_id`, `first_observed_date`, `explanation_checksum`.

## Template inventory
- `EXPLANATION_RISING_FRAGILITY`
- `EXPLANATION_PERSISTENT_STRESS`
- `EXPLANATION_RECOVERY`
- `EXPLANATION_STABLE_CONDITION`
- `EXPLANATION_VOLATILE_CONDITION`
- `EXPLANATION_INSUFFICIENT_HISTORY`
- `EXPLANATION_DEGRADED_INPUT`

## Bounded language policy
- Explanation text is fixed-template with bounded substitution.
- Uses deterministic observed/classified/detected/persisted language.
- Excludes prediction/recommendation/forecasting phrasing.

## Evidence summarization policy
Each explanation includes bounded evidence fields:
- contributing pair count
- contributing curve label
- cumulative score delta
- directional consistency
- persistence count
- transition strength/confidence
- source checksums

## Replay lineage behavior
T5 preserves T4 lineage and emits:
- input transition chain checksum
- explanation checksums and explanation chain checksum
- inherited temporal lineage

## Certification gates
19 fixed gates covering envelope validity, deterministic controls, bounded template policy, lineage, mutation safety, and forbidden behavior constraints.

## Invariant flags
Explicit deterministic, bounded-language, replay-safety, immutable-input, and no-runtime-side-effect invariants.

## Forbidden capabilities
All prohibited capabilities explicitly set to false, including live fetch, Supabase operations, stochastic/open-ended generation, recommendation generation, and recursive replay expansion.

## Test coverage
Focused T5 tests cover exports, status transitions (certified/degraded/blocked), deterministic mappings/order/checksum repeatability, mutation safety, bounded phrase/language constraints, replay classification, lineage, and forbidden capabilities.

## Final status
T5 deterministic historical explainability layer implemented additively with tests and report documentation.
