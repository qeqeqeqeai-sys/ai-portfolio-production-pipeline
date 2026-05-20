#!/usr/bin/env bash
set -euo pipefail

required_files=(
  transmission_layers/intelligence/tier4/fragility_analysis.py
  transmission_layers/intelligence/tier4/failure_thresholds.py
  transmission_layers/intelligence/tier4/tipping_points.py
  transmission_layers/intelligence/tier4/survivability_metrics.py
  transmission_layers/intelligence/tier4/fragility_replay.py
  transmission_layers/intelligence/tier4/fragility_explanations.py
  transmission_layers/intelligence/tier4/fragility_signatures.py
  tests/test_tier4_fragility_analysis.py
  tests/test_tier4_failure_thresholds.py
  tests/test_tier4_tipping_points.py
  tests/test_tier4_survivability_metrics.py
  tests/test_tier4_fragility_replay.py
  tests/test_tier4_fragility_explanations.py
  tests/test_tier4_fragility_signatures.py
)

for f in "${required_files[@]}"; do
  test -f "$f"
done

echo "[tier4h] hard_checks=pass"

find transmission_layers/intelligence/tier4 -maxdepth 1 -type f | sort
find tests -maxdepth 1 -type f | grep 'tier4_.*fragility\|tier4_failure_thresholds\|tier4_tipping_points\|tier4_survivability' | sort

tests_to_run=(
  tests/test_tier4_structural_simulation.py
  tests/test_tier4_structural_memory.py
  tests/test_tier4_temporal_replay.py
  tests/test_tier4_replay_integrity.py
  tests/test_tier4_influence_attribution.py
  tests/test_tier4_causal_lineage.py
  tests/test_tier4_causal_replay.py
  tests/test_tier4_structural_regimes.py
  tests/test_tier4_regime_transitions.py
  tests/test_tier4_regime_persistence.py
  tests/test_tier4_regime_state_machine.py
  tests/test_tier4_scenario_semantics.py
  tests/test_tier4_scenario_perturbations.py
  tests/test_tier4_scenario_comparison.py
  tests/test_tier4_scenario_sensitivity.py
  tests/test_tier4_scenario_replay.py
  tests/test_tier4_scenario_signatures.py
  tests/test_tier4_response_policy.py
  tests/test_tier4_intervention_strategies.py
  tests/test_tier4_response_effectiveness.py
  tests/test_tier4_response_replay.py
  tests/test_tier4_response_explanations.py
  tests/test_tier4_response_signatures.py
  tests/test_tier4_recovery_dynamics.py
  tests/test_tier4_recovery_persistence.py
  tests/test_tier4_recovery_decay.py
  tests/test_tier4_recovery_replay.py
  tests/test_tier4_recovery_explanations.py
  tests/test_tier4_recovery_signatures.py
  tests/test_tier4_fragility_analysis.py
  tests/test_tier4_failure_thresholds.py
  tests/test_tier4_tipping_points.py
  tests/test_tier4_survivability_metrics.py
  tests/test_tier4_fragility_replay.py
  tests/test_tier4_fragility_explanations.py
  tests/test_tier4_fragility_signatures.py
)

for t in "${tests_to_run[@]}"; do
  python -m pytest -q "$t"
done

python -m transmission_layers.intelligence.tier4.structural_simulation

git status --short
git diff --stat
