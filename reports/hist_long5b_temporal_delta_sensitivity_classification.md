# HIST-LONG-5B Temporal Delta & Sensitivity Classification

## Executive Summary
- Status: ok
- Completed windows: [20, 60, 120]
- Recommendation: Proceed only as observational analysis if HIST-LONG-6 continues; preserve no-provider-call and no-replay-activation governance.

## Source Artifact Verification
- `{"completed_window_count": 3, "completed_windows": [20, 60, 120], "preflight_checks": {"all_three_real_windows_completed": true, "completed_window_count": 3, "completed_window_count_is_3": true, "forbidden_governance_enabled": [], "governance_mode": "observational_only", "governance_observational_only": true, "source_exists": true, "source_status": "ok", "source_status_ok_or_success": true, "window_level_results_contains_3_completed_windows": true, "window_level_results_count": 3, "windows_detected": [20, 60, 120], "windows_exactly_20_60_120": true}, "source_digest": "ccb37a3969309734c46220f3a348ef8e49aa228eaf633e6566d6cfcad39af3c9", "source_path": "artifacts/hist_long4_real_multi_window_ecology_review.json", "source_status": "ok", "verified": true}`

## Temporal Delta Tables

### ingestion_continuity
| from | to | metric | from value | to value | absolute delta | relative delta | direction | interpretation |
|---:|---:|---|---:|---:|---:|---:|---|---|
| 20 | 60 | normalized_rows | 4820.0 | 14460.0 | 9640.0 | 2.0 | increase | material_change |
| 20 | 60 | completeness_ratio | 1.0 | 1.0 | 0.0 | 0.0 | flat | stable |
| 20 | 60 | partial_count | 0.0 | 0.0 | 0.0 | None | flat | stable |
| 20 | 60 | failed_count | 0.0 | 0.0 | 0.0 | None | flat | stable |
| 20 | 60 | exact_date_match_ratio | 0.95 | 0.966667 | 0.016667 | 0.017544 | increase | stable |
| 20 | 60 | reconciled_date_ratio | 0.05 | 0.033333 | -0.016667 | -0.33334 | decrease | material_change |
| 20 | 60 | endpoint_failure_count | 0.0 | 0.0 | 0.0 | None | flat | stable |
| 60 | 120 | normalized_rows | 14460.0 | 28920.0 | 14460.0 | 1.0 | increase | material_change |
| 60 | 120 | completeness_ratio | 1.0 | 1.0 | 0.0 | 0.0 | flat | stable |
| 60 | 120 | partial_count | 0.0 | 0.0 | 0.0 | None | flat | stable |
| 60 | 120 | failed_count | 0.0 | 0.0 | 0.0 | None | flat | stable |
| 60 | 120 | exact_date_match_ratio | 0.966667 | 0.95 | -0.016667 | -0.017242 | decrease | stable |
| 60 | 120 | reconciled_date_ratio | 0.033333 | 0.05 | 0.016667 | 0.500015 | increase | material_change |
| 60 | 120 | endpoint_failure_count | 0.0 | 0.0 | 0.0 | None | flat | stable |
| 20 | 120 | normalized_rows | 4820.0 | 28920.0 | 24100.0 | 5.0 | increase | material_change |
| 20 | 120 | completeness_ratio | 1.0 | 1.0 | 0.0 | 0.0 | flat | stable |
| 20 | 120 | partial_count | 0.0 | 0.0 | 0.0 | None | flat | stable |
| 20 | 120 | failed_count | 0.0 | 0.0 | 0.0 | None | flat | stable |
| 20 | 120 | exact_date_match_ratio | 0.95 | 0.95 | 0.0 | 0.0 | flat | stable |
| 20 | 120 | reconciled_date_ratio | 0.05 | 0.05 | 0.0 | 0.0 | flat | stable |
| 20 | 120 | endpoint_failure_count | 0.0 | 0.0 | 0.0 | None | flat | stable |

### replay_ecology
| from | to | metric | from value | to value | absolute delta | relative delta | direction | interpretation |
|---:|---:|---|---:|---:|---:|---:|---|---|
| 20 | 60 | replay_density | 1.0 | 1.0 | 0.0 | 0.0 | flat | stable |
| 20 | 60 | replay_saturation | 1.0 | 1.0 | 0.0 | 0.0 | flat | stable |
| 20 | 60 | contradiction_burden | 0.0 | 0.0 | 0.0 | None | flat | stable |
| 20 | 60 | topology_richness | 2.0 | 2.0 | 0.0 | 0.0 | flat | stable |
| 20 | 60 | morphology_persistence | 1.0 | 1.0 | 0.0 | 0.0 | flat | stable |
| 20 | 60 | temporal_persistence | 1.0 | 1.0 | 0.0 | 0.0 | flat | stable |
| 60 | 120 | replay_density | 1.0 | 1.0 | 0.0 | 0.0 | flat | stable |
| 60 | 120 | replay_saturation | 1.0 | 1.0 | 0.0 | 0.0 | flat | stable |
| 60 | 120 | contradiction_burden | 0.0 | 0.0 | 0.0 | None | flat | stable |
| 60 | 120 | topology_richness | 2.0 | 2.0 | 0.0 | 0.0 | flat | stable |
| 60 | 120 | morphology_persistence | 1.0 | 1.0 | 0.0 | 0.0 | flat | stable |
| 60 | 120 | temporal_persistence | 1.0 | 1.0 | 0.0 | 0.0 | flat | stable |
| 20 | 120 | replay_density | 1.0 | 1.0 | 0.0 | 0.0 | flat | stable |
| 20 | 120 | replay_saturation | 1.0 | 1.0 | 0.0 | 0.0 | flat | stable |
| 20 | 120 | contradiction_burden | 0.0 | 0.0 | 0.0 | None | flat | stable |
| 20 | 120 | topology_richness | 2.0 | 2.0 | 0.0 | 0.0 | flat | stable |
| 20 | 120 | morphology_persistence | 1.0 | 1.0 | 0.0 | 0.0 | flat | stable |
| 20 | 120 | temporal_persistence | 1.0 | 1.0 | 0.0 | 0.0 | flat | stable |

### concentration_diversity
| from | to | metric | from value | to value | absolute delta | relative delta | direction | interpretation |
|---:|---:|---|---:|---:|---:|---:|---|---|
| 20 | 60 | sector_hhi | 0.06107 | 0.06107 | 0.0 | 0.0 | flat | stable |
| 20 | 60 | subsector_hhi | 0.06107 | 0.06107 | 0.0 | 0.0 | flat | stable |
| 20 | 60 | monoculture_risk | 0.0 | 0.0 | 0.0 | None | flat | stable |
| 20 | 60 | diversity_retention | 1.0 | 1.0 | 0.0 | 0.0 | flat | stable |
| 60 | 120 | sector_hhi | 0.06107 | 0.06107 | 0.0 | 0.0 | flat | stable |
| 60 | 120 | subsector_hhi | 0.06107 | 0.06107 | 0.0 | 0.0 | flat | stable |
| 60 | 120 | monoculture_risk | 0.0 | 0.0 | 0.0 | None | flat | stable |
| 60 | 120 | diversity_retention | 1.0 | 1.0 | 0.0 | 0.0 | flat | stable |
| 20 | 120 | sector_hhi | 0.06107 | 0.06107 | 0.0 | 0.0 | flat | stable |
| 20 | 120 | subsector_hhi | 0.06107 | 0.06107 | 0.0 | 0.0 | flat | stable |
| 20 | 120 | monoculture_risk | 0.0 | 0.0 | 0.0 | None | flat | stable |
| 20 | 120 | diversity_retention | 1.0 | 1.0 | 0.0 | 0.0 | flat | stable |

### weak_symbol_provider_quality
| from | to | metric | from value | to value | absolute delta | relative delta | direction | interpretation |
|---:|---:|---|---:|---:|---:|---:|---|---|
| 20 | 60 | weak_symbol_count | 0.0 | 0.0 | 0.0 | None | flat | stable |
| 20 | 60 | recurring_weak_symbol_count | 0.0 | 0.0 | 0.0 | None | flat | stable |
| 20 | 60 | provider_degradation_count | 0.0 | 0.0 | 0.0 | None | flat | stable |
| 20 | 60 | foxa_weak_window_count | 0.0 | 0.0 | 0.0 | None | flat | stable |
| 60 | 120 | weak_symbol_count | 0.0 | 0.0 | 0.0 | None | flat | stable |
| 60 | 120 | recurring_weak_symbol_count | 0.0 | 0.0 | 0.0 | None | flat | stable |
| 60 | 120 | provider_degradation_count | 0.0 | 0.0 | 0.0 | None | flat | stable |
| 60 | 120 | foxa_weak_window_count | 0.0 | 0.0 | 0.0 | None | flat | stable |
| 20 | 120 | weak_symbol_count | 0.0 | 0.0 | 0.0 | None | flat | stable |
| 20 | 120 | recurring_weak_symbol_count | 0.0 | 0.0 | 0.0 | None | flat | stable |
| 20 | 120 | provider_degradation_count | 0.0 | 0.0 | 0.0 | None | flat | stable |
| 20 | 120 | foxa_weak_window_count | 0.0 | 0.0 | 0.0 | None | flat | stable |

## Sensitivity Ranking
| rank | metric | classification | total absolute change | max relative change | volatility score | stability score |
|---:|---|---|---:|---:|---:|---:|
| 1 | normalized_rows | highly_sensitive | 24100.0 | 2.0 | 0.166667 | 0.0 |
| 2 | reconciled_date_ratio | sensitive | 0.033334 | 0.500015 | 0.66668 | 0.33332 |
| 3 | exact_date_match_ratio | stable | 0.033334 | 0.017544 | 0.034483 | 0.965517 |
| 4 | completeness_ratio | stable | 0.0 | 0.0 | 0.0 | 1.0 |
| 5 | contradiction_burden | stable | 0.0 | 0.0 | 0.0 | 1.0 |
| 6 | diversity_retention | stable | 0.0 | 0.0 | 0.0 | 1.0 |
| 7 | endpoint_failure_count | stable | 0.0 | 0.0 | 0.0 | 1.0 |
| 8 | failed_count | stable | 0.0 | 0.0 | 0.0 | 1.0 |
| 9 | foxa_weak_window_count | stable | 0.0 | 0.0 | 0.0 | 1.0 |
| 10 | monoculture_risk | stable | 0.0 | 0.0 | 0.0 | 1.0 |
| 11 | morphology_persistence | stable | 0.0 | 0.0 | 0.0 | 1.0 |
| 12 | partial_count | stable | 0.0 | 0.0 | 0.0 | 1.0 |
| 13 | provider_degradation_count | stable | 0.0 | 0.0 | 0.0 | 1.0 |
| 14 | recurring_weak_symbol_count | stable | 0.0 | 0.0 | 0.0 | 1.0 |
| 15 | replay_density | stable | 0.0 | 0.0 | 0.0 | 1.0 |
| 16 | replay_saturation | stable | 0.0 | 0.0 | 0.0 | 1.0 |
| 17 | sector_hhi | stable | 0.0 | 0.0 | 0.0 | 1.0 |
| 18 | subsector_hhi | stable | 0.0 | 0.0 | 0.0 | 1.0 |
| 19 | temporal_persistence | stable | 0.0 | 0.0 | 0.0 | 1.0 |
| 20 | topology_richness | stable | 0.0 | 0.0 | 0.0 | 1.0 |
| 21 | weak_symbol_count | stable | 0.0 | 0.0 | 0.0 | 1.0 |

## Structural Persistence Classification
- `{"completeness_ratio": "stable", "contradiction_burden": "stable", "diversity_retention": "stable", "endpoint_failure_count": "stable", "exact_date_match_ratio": "volatile", "failed_count": "stable", "foxa_weak_window_count": "stable", "monoculture_risk": "stable", "morphology_persistence": "stable", "normalized_rows": "emerging", "partial_count": "stable", "provider_degradation_count": "stable", "reconciled_date_ratio": "volatile", "recurring_weak_symbol_count": "stable", "replay_density": "stable", "replay_saturation": "stable", "sector_hhi": "stable", "subsector_hhi": "stable", "temporal_persistence": "stable", "topology_richness": "stable", "weak_symbol_count": "stable"}`

## Replay Evolution Classification
- `{"classification": "stable", "metric_classifications": {"contradiction_burden": "stable", "replay_density": "stable", "replay_saturation": "stable", "temporal_persistence": "stable", "topology_richness": "stable"}}`

## Concentration Evolution Classification
- `{"classification": "stable_balanced", "metric_classifications": {"sector_hhi": "stable", "subsector_hhi": "stable"}}`

## FOXA Longitudinal Assessment
- `{"contribution_consistency": "insufficient granular signal", "insufficient_granular_signal": true, "present_all_windows": true, "stability_classification": "stable", "supervisor_assessment": "FOXA is present across all windows and not weak. Source lacks symbol-level FOXA contribution data.", "weak_window_count": 0, "weak_windows": []}`

## Fragility Emergence Detection
- `{"classification": ["no_fragility_detected"], "fragile_windows": [], "reasons_by_window": {"20": [], "60": [], "120": []}}`

## Governance Certification
- governance_mode: observational_only
- phase: HIST-LONG-5B_temporal_delta_sensitivity_classification
- source_artifact_only: True
- fmp_calls_enabled: False
- provider_api_calls_enabled: False
- hist_long4_reexecution_enabled: False
- prediction_enabled: False
- trading_execution_enabled: False
- replay_activation_enabled: False
- replay_execution_enabled: False
- topology_persistence_enabled: False
- supabase_write_enabled: False
- raw_cache_write_enabled: False
- local_artifacts_only: True

## Recommendation For HIST-LONG-6
- Proceed only as observational analysis if HIST-LONG-6 continues; preserve no-provider-call and no-replay-activation governance.
