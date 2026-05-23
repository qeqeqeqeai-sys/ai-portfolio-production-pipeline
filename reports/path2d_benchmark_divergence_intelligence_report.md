# Path 2-D Benchmark Divergence Intelligence Report

```json
{
  "architecture_summary": "Input contract, alignment resolution, fixed component scoring, deterministic certification, replay checksum.",
  "benchmark_alignment_methodology": "Explicit benchmark_id and benchmark_version are validated against provided benchmark_mapping deterministically.",
  "benchmark_input_contract": {
    "contract_version": "1.0.0",
    "fixed_divergence_weights": {
      "fragility_divergence": 35,
      "percentile_divergence": 20,
      "persistence_divergence": 25,
      "velocity_divergence": 20
    },
    "forbidden_capabilities": [
      "trading_signals",
      "price_prediction",
      "portfolio_construction",
      "portfolio_optimization",
      "autonomous_execution",
      "ml_benchmark_selection",
      "adaptive_benchmark_weighting",
      "adaptive_divergence_weighting",
      "dynamic_benchmark_discovery",
      "dynamic_peer_generation",
      "dynamic_cohort_creation",
      "stochastic_divergence_scoring",
      "hidden_scoring_logic",
      "network_api_calls",
      "supabase_database_writes"
    ],
    "optional_component_fields": [
      "fragility_divergence",
      "persistence_divergence",
      "velocity_divergence",
      "percentile_divergence"
    ],
    "path_id": "P2-D",
    "required_fields": [
      "entity_id",
      "cohort_id",
      "cohort_version",
      "benchmark_id",
      "benchmark_version"
    ]
  },
  "certification_decision_logic": {
    "decision_status": "DEGRADED_BENCHMARK_DIVERGENCE",
    "forbidden_capability_inventory": [
      "trading_signals",
      "price_prediction",
      "portfolio_construction",
      "portfolio_optimization",
      "autonomous_execution",
      "ml_benchmark_selection",
      "adaptive_benchmark_weighting",
      "adaptive_divergence_weighting",
      "dynamic_benchmark_discovery",
      "dynamic_peer_generation",
      "dynamic_cohort_creation",
      "stochastic_divergence_scoring",
      "hidden_scoring_logic",
      "network_api_calls",
      "supabase_database_writes"
    ],
    "output": {
      "benchmark_alignment_status": "BENCHMARK_ALIGNED",
      "benchmark_divergence_explanation": "Entity SAMPLE_ENTITY in cohort SAMPLE_COHORT (v1.0) diverges from benchmark SAMPLE_BENCH (v1.0) with score 0.0 and tier BENCHMARK_ALIGNED.",
      "benchmark_divergence_score": 0.0,
      "benchmark_divergence_tier": "BENCHMARK_ALIGNED",
      "benchmark_id": "SAMPLE_BENCH",
      "benchmark_version": "1.0",
      "checksum": "654176769d50857ec57f3ad634d133296e931a654775b2cc0fe6f58c5af340d8",
      "cohort_id": "SAMPLE_COHORT",
      "cohort_version": "1.0",
      "divergence_components": {
        "fragility_divergence": 0.0,
        "percentile_divergence": 0.0,
        "persistence_divergence": 0.0,
        "velocity_divergence": 0.0
      },
      "divergence_driver_summary": "fragility=0.0, persistence=0.0, velocity=0.0, percentile=0.0",
      "divergence_weights": {
        "fragility_divergence": 35,
        "percentile_divergence": 20,
        "persistence_divergence": 25,
        "velocity_divergence": 20
      },
      "entity_id": "SAMPLE_ENTITY",
      "fragility_divergence": 0.0,
      "percentile_divergence": 0.0,
      "persistence_divergence": 0.0,
      "quality_flags": [
        "MISSING_FRAGILITY_DIVERGENCE_DEFAULTED",
        "MISSING_PERSISTENCE_DIVERGENCE_DEFAULTED",
        "MISSING_VELOCITY_DIVERGENCE_DEFAULTED",
        "MISSING_PERCENTILE_DIVERGENCE_DEFAULTED"
      ],
      "replay_metadata": {
        "deterministic_fallback_defaults": true,
        "input_immutability_preserved": true,
        "stable_serialization": true
      },
      "velocity_divergence": 0.0
    },
    "validation_gates": {
      "benchmark_alignment_resolved": true,
      "benchmark_explanation_present": true,
      "benchmark_id_present": true,
      "benchmark_mapping_valid": true,
      "benchmark_version_present": true,
      "checksum_stable": true,
      "cohort_id_present": true,
      "cohort_version_present": true,
      "divergence_components_present": true,
      "divergence_score_bounded_0_100": true,
      "divergence_score_generated": true,
      "divergence_tier_assigned": true,
      "divergence_weights_total_100": true,
      "entity_id_present": true,
      "forbidden_dynamic_capabilities_absent": true,
      "input_contract_present": true,
      "input_immutability_preserved": true
    }
  },
  "deterministic_benchmark_comparison_policy": "No adaptive weighting or dynamic benchmark discovery; stable JSON checksum enforces replay safety.",
  "divergence_component_methodology": "Four fixed components are clamped 0-100 with deterministic default 0 when missing optional values.",
  "divergence_tier_policy": "85-100 EXTREME, 70-84 ELEVATED, 50-69 MODERATE, 30-49 LIMITED, 0-29 BENCHMARK_ALIGNED.",
  "final_supervisor_interpretation": "P2-D is deterministic, additive, and benchmark-explicit with fixed-weight divergence scoring and auditable certification.",
  "fixed_weighting_policy": {
    "fragility_divergence": 35,
    "percentile_divergence": 20,
    "persistence_divergence": 25,
    "velocity_divergence": 20
  },
  "forbidden_capabilities": [
    "trading_signals",
    "price_prediction",
    "portfolio_construction",
    "portfolio_optimization",
    "autonomous_execution",
    "ml_benchmark_selection",
    "adaptive_benchmark_weighting",
    "adaptive_divergence_weighting",
    "dynamic_benchmark_discovery",
    "dynamic_peer_generation",
    "dynamic_cohort_creation",
    "stochastic_divergence_scoring",
    "hidden_scoring_logic",
    "network_api_calls",
    "supabase_database_writes"
  ],
  "missing_clamped_data_policy": "Missing required identity/benchmark fields block. Missing optional components degrade and default to 0. Out-of-range values clamp and flag.",
  "non_goals": [
    "no_benchmark_creation",
    "no_dynamic_benchmark_selection",
    "no_cohort_creation",
    "no_p2b_recalculation",
    "no_p2c_recalculation"
  ],
  "objective": "Deterministic benchmark divergence intelligence for entities, subsectors, and cohorts against explicit assigned benchmarks.",
  "path_id": "P2-D",
  "replay_checksum_guarantees": "Stable key ordering and SHA-256 checksum over output payload excluding checksum field.",
  "scope": "Additive-only layer consuming P2-A mappings/manifests, P2-B scores, and P2-C ranks without recalculation."
}
```
