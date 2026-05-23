# P2-F Cross-Sectional Explainability Report

## Objective
Deliver deterministic, replay-safe cross-sectional explainability packets for supervisor-readable interpretation.

## Scope
Uses additive inputs from P2-B, P2-C, P2-D, P2-E, Path 1 replay metadata, checksums, and quality flags.

## Non-Goals
No score/rank/divergence/evolution recalculation. No prediction, trading, portfolio logic, cohort creation, benchmark creation, network/database calls, or LLM/stochastic narratives.

## Architecture Summary
Build input contract, deterministic explanation templates, driver attribution hierarchy, structural evidence summary, consistency validation, and certification decision.

## Input Contract
See `build_cross_sectional_explainability_input_contract` for required identity fields, required component inputs, output schema, and forbidden capability inventory.

## Peer-Relative Explanation Methodology
Deterministic template using relative fragility score with fixed wording.

## Percentile/Ranking Explanation Methodology
Deterministic template using percentile/rank/cohort size.

## Benchmark Divergence Explanation Methodology
Deterministic template using benchmark divergence score and replay trend.

## Relative Evolution Explanation Methodology
Deterministic template using evolution direction, rank migration movement, and percentile movement.

## Driver Attribution Hierarchy Methodology
Deterministic ordering by absolute signal strength, then stable tie-break via explicit priority list.

## Structural Evidence Summary Methodology
Explicit metric-aligned summary of core structural signals and deltas.

## Deterministic Template Policy
All narrative fields are fixed templates with deterministic interpolation.

## Consistency Validation Policy
Validation requires all explanation segments, attribution hierarchy, evidence summary, primary driver, and secondary driver/degradation marker.

## Replay/Checksum Guarantees
Deepcopy input isolation and stable JSON checksum generation ensure replay-safe deterministic outputs.

## Certification Decision Logic
Blocked when required identity fields are missing; degraded on quality flags or secondary-driver degradation; certified otherwise.

## Forbidden Capabilities
LLM/stochastic narratives, predictive/trading/portfolio logic, adaptive hidden logic, dynamic cohort/benchmark creation, and network/database writes are forbidden.

## Final Supervisor Interpretation
P2-F explains cross-sectional structure deterministically, compactly, and auditably while preserving additive-only integration boundaries.
