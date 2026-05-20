# Tier 4H Export Package Manifest (2026-05-20)

This manifest confirms the Tier 4H — Structural Fragility & Failure Threshold Intelligence package contents and validation status.

## Required modules
- transmission_layers/intelligence/tier4/fragility_analysis.py
- transmission_layers/intelligence/tier4/failure_thresholds.py
- transmission_layers/intelligence/tier4/tipping_points.py
- transmission_layers/intelligence/tier4/survivability_metrics.py
- transmission_layers/intelligence/tier4/fragility_replay.py
- transmission_layers/intelligence/tier4/fragility_explanations.py
- transmission_layers/intelligence/tier4/fragility_signatures.py

## Required tests
- tests/test_tier4_fragility_analysis.py
- tests/test_tier4_failure_thresholds.py
- tests/test_tier4_tipping_points.py
- tests/test_tier4_survivability_metrics.py
- tests/test_tier4_fragility_replay.py
- tests/test_tier4_fragility_explanations.py
- tests/test_tier4_fragility_signatures.py

## Validation command set
The full Tier 4 validation suite (including all Tier 4H tests) was executed via `python -m pytest -q` for each required test module, followed by:

- `python -m transmission_layers.intelligence.tier4.structural_simulation`

Expected and observed smoke-test line:

`[tier4] simulation_health_state=stressed propagated_stress=0.5854 overload=0.5953 resilience=0.5371 status=success`
