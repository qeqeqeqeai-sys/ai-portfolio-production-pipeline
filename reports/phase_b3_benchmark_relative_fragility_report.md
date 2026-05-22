# Phase B3 — Benchmark-Relative Expectation Fragility Interpretation

## Objective
Implement a deterministic additive interpretation layer comparing entity expectation-fragility versus benchmark, peer, subsector, and universe contexts.

## Architecture identity
Deterministic institutional expectation-fragility intelligence with bounded labels, replayability, and explainability.

## Public APIs
- build_benchmark_context_summary
- build_relative_fragility_delta
- build_benchmark_relative_fragility_label
- build_peer_relative_fragility_interpretation
- build_subsector_relative_fragility_interpretation
- build_universe_relative_fragility_interpretation
- build_benchmark_relative_resilience_interpretation
- build_b3_evidence_chain
- build_phase_b3_benchmark_relative_report

## Benchmark-relative interpretation philosophy
B3 provides context-relative fragility interpretation only, not trading logic.

## Deterministic label systems
Fixed threshold labels for direction, relative fragility, peer/subsector/universe comparisons, and resilience interpretations.

## Relative delta methodology
Component deltas are benchmark-relative with support inversion applied as benchmark_support - entity_support. Composite fragility delta is deterministic average with ROUND_HALF_UP.

## Evidence-chain design
Entity chain includes normalized scores, component deltas, dominant driver, offsetting factor, fixed template IDs, B1/B2 passthrough context, and replay metadata.

## Replayability guarantees
Stable deterministic sorting and stable checksums via canonical JSON serialization and SHA256.

## Tests run
- `python -m pytest -q tests/test_phase_b3_benchmark_relative_fragility.py`
- `python -m pytest -q tests/test_phase_b2_asymmetry_interpretation.py`
- `python -m pytest -q tests/test_phase_b1_expectation_failure_heatmap.py`
- `python -m pytest -q` (if practical)

## Exclusions preserved
No trading recommendations, no optimization loops, no adaptive control, no portfolio construction, no backtesting.

## Final implementation status
Completed as additive-only Phase B3 module and exported public APIs.
