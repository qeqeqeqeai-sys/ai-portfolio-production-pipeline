# Phase B2 Asymmetry Interpretation Report

## Objective
Implement deterministic, bounded, replayable asymmetry interpretation for expectation-fragility intelligence without producing trading logic.

## Architecture Identity
Deterministic institutional expectation-fragility intelligence. Additive-only; explainable; immutable-input safe.

## Public APIs
- build_downside_asymmetry_classification
- build_long_risk_fragility_interpretation
- build_expectation_support_mismatch
- build_relative_resilience_interpretation
- build_ranking_asymmetry_interpretation
- build_cluster_asymmetry_summary
- build_subsector_asymmetry_summary
- build_b2_evidence_chain
- build_phase_b2_asymmetry_report

## Deterministic Label Systems
All labels, precedence, tie-breakers, thresholds, and template identifiers are fixed in code.

## Classification Rules
- Score normalization: clamp 0..100, fallback 50 for missing/invalid.
- Downside asymmetry precedence: insufficient -> extreme -> high -> moderate -> low -> no_clear.
- Mismatch score uses ROUND_HALF_UP.
- Relative resilience and ranking interpretations use fixed thresholds.
- Cluster and subsector summaries use fixed precedence and deterministic ordering.

## Evidence-Chain Design
Entity output links B2 labels to B1 ranking context (if supplied), A7 composite/A2-A6 components via normalized scores, quality flags, rule ids, template id, and replay metadata.

## Replayability Guarantees
- Stable deterministic sort order.
- Stable tie-breakers.
- Deterministic SHA-256 input/output checksums over canonical JSON.

## Tests Run
See test commands in implementation validation output.

## Exclusions Explicitly Preserved
No trading recommendations, no target-price forecasting, no optimization loops, no autonomous agents, no portfolio construction.

## Final Implementation Status
Implemented and test-covered for deterministic Phase B2 additive interpretation layer.
