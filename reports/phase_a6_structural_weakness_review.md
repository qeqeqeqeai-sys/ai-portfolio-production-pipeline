# Phase A6 Structural Weakness Review

## Executive conclusion
Phase A6 is implemented as a deterministic, bounded bridge-only scoring module that maps normalized upstream structural outputs into `structural_weakness_score` without composite scoring or autonomous behaviors.

## Files added/modified
- Added `transmission_layers/expectation_failure/phase_a6_structural_weakness.py`
- Modified `transmission_layers/expectation_failure/__init__.py`
- Added `tests/test_phase_a6_structural_weakness_score.py`
- Added `reports/phase_a6_structural_weakness_review.md`

## Public APIs
- `score_structural_weakness`
- `build_structural_weakness_thresholds`
- `build_structural_weakness_subcomponent_contract`
- `build_structural_weakness_evidence_summary`
- `build_phase_a6_structural_weakness_report`

## Bridge scope
Deterministic bridge-only mapping from normalized upstream structural signals into a single Phase A6 score module.

## Score direction
0 = structurally resilient / low weakness; 100 = severe structural weakness / high expectation failure risk.

## Upstream dependency boundaries
Consumes only:
- `fragility_score`
- `transmission_instability_score`
- `divergence_score`
- `regime_stress_score`
- `structural_deterioration_score`
- `propagation_weakness_score`

No reinterpretation, retraining, optimization, or mutation of upstream outputs.

## Subcomponent coverage
- `fragility_risk_score`
- `transmission_instability_risk_score`
- `divergence_risk_score`
- `regime_stress_risk_score`
- `deterioration_propagation_risk_score`

## Threshold and weight coverage
- Component triggers: elevated >= 40, high >= 60, severe >= 80
- Weights: 25/20/20/15/20 percent respectively
- Composite rounding: `ROUND_HALF_UP`

## Evidence-chain coverage
Output includes:
- subcomponent scores
- thresholds triggered
- missing inputs
- data quality flags
- raw evidence refs
- deterministic replay metadata

## Determinism and replayability gates
- deterministic output
- replay compatible
- immutable input safe
- bounded score
- fixed thresholds/templates
- additive-only architecture
- no upstream mutation
- bridge-only mapping

## Explicit exclusions
- No full composite AI Expectation Failure score
- No heatmaps, pair-analysis, benchmark comparison
- No prediction, trading, optimization, adaptive control, agents, or autonomous reasoning

## Validation commands
- `python -m pytest -q tests/test_phase_a1_expectation_failure_contracts.py`
- `python -m pytest -q tests/test_phase_a2_valuation_stretch_score.py`
- `python -m pytest -q tests/test_phase_a3_fundamental_support_score.py`
- `python -m pytest -q tests/test_phase_a4_narrative_saturation_score.py`
- `python -m pytest -q tests/test_phase_a5_certainty_fragility_score.py`
- `python -m pytest -q tests/test_phase_a6_structural_weakness_score.py`
- `python -m pytest -q`

## Supervisor decision
APPROVED_FOR_PHASE_A6_PR
