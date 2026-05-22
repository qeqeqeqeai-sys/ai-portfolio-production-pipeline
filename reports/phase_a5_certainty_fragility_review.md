# Phase A5 Certainty Fragility Review

## Executive conclusion
Phase A5 is implemented as a deterministic, bounded, replayable certainty fragility scoring module with fixed thresholds, fixed weights, immutable-input-safe behavior, fixed explanation templates, and explicit non-autonomous boundaries.

## Files added/modified
- Added: `transmission_layers/expectation_failure/phase_a5_certainty_fragility.py`
- Modified: `transmission_layers/expectation_failure/__init__.py`
- Added: `tests/test_phase_a5_certainty_fragility_score.py`
- Added: `reports/phase_a5_certainty_fragility_review.md`

## Public APIs
- `score_certainty_fragility`
- `build_certainty_fragility_thresholds`
- `build_certainty_fragility_subcomponent_contract`
- `build_certainty_fragility_evidence_summary`
- `build_phase_a5_certainty_fragility_report`

## Scoring scope
- Scope: `certainty_fragility_score_only`
- Excludes all composite expectation failure scoring.

## Score direction
- `0 = durable / well-supported certainty`
- `100 = severe certainty fragility / high expectation failure risk`

## Subcomponent coverage
1. `estimate_dispersion_risk_score`
2. `revision_instability_risk_score`
3. `execution_dependency_risk_score`
4. `concentration_risk_score`
5. `competitive_uncertainty_risk_score`

## Threshold and weight coverage
- Fixed normalized 0–100 bands mapped to deterministic scores: 15/35/55/75/95.
- Missing/invalid fallback score: 50.
- Fixed weights:
  - estimate dispersion: 20%
  - revision instability: 20%
  - execution dependency: 25%
  - concentration: 15%
  - competitive uncertainty: 20%

## Evidence-chain coverage
- Input evidence fields tracked deterministically.
- Output evidence includes subcomponent scores, thresholds triggered, missing inputs, quality flags, and raw evidence references.
- Replay metadata includes module name, version, and deterministic replay key fields.

## Determinism and replayability gates
- ROUND_HALF_UP rounding for deterministic aggregation.
- Stable dict field ordering and fixed template IDs.
- Immutable-input-safe handling (`deepcopy`) and no runtime threshold mutation.
- Invariant flags are all `True`.

## Explicit exclusions
- No full AI Expectation Failure composite score.
- No structural weakness, heatmaps, pair analysis, benchmark comparison, or composite scoring.
- No prediction, trading, optimization loops, agents, adaptive behavior, autonomous reasoning, or target-price forecasting.

## Validation commands
- `python -m pytest -q tests/test_phase_a1_expectation_failure_contracts.py`
- `python -m pytest -q tests/test_phase_a2_valuation_stretch_score.py`
- `python -m pytest -q tests/test_phase_a3_fundamental_support_score.py`
- `python -m pytest -q tests/test_phase_a4_narrative_saturation_score.py`
- `python -m pytest -q tests/test_phase_a5_certainty_fragility_score.py`
- `python -m pytest -q`

## Supervisor decision
APPROVED_FOR_PHASE_A5_PR
