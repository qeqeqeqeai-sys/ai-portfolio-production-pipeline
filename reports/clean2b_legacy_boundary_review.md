# CLEAN-2B Legacy Boundary Review Queues

Generated: 2026-05-29T12:36:17.113220+00:00

## Executive Summary

- CLEAN-2B is analysis-only: no files were archived, moved, renamed, deleted, or refactored.
- Source inputs: `reports/clean2_dependency_verification.md`, `artifacts/clean2_dependency_verification.json`, and active-path checks against `docs/runbooks/repository_dependency_dataflow_map.md`.
- Queue A contains **0** safe archive candidates after applying the stricter CLEAN-2B gates.
- Queue B contains **51** unknown review items carried forward from CLEAN-2.
- CLEAN-2 listed **27** unreferenced candidates; CLEAN-2B excluded **27** of them because they are package initializers, current-core defaults, graph-foundation boundaries, or active dataflow-map paths.
- Main legacy ecosystems separated for decision-making: Legacy Expectation Failure, Legacy Graph Foundation, Legacy Alpha Research, Historical Intelligence, Governance / Observability, and Tests-only Intelligence Modules.

## Queue A: Safe Archive Candidates

No files qualify for safe archive in CLEAN-2B. CLEAN-3 should not archive any files solely from CLEAN-2 until the blockers below are resolved.

### Excluded CLEAN-2 candidate queue items

| Path | Exclusion reason(s) |
|---|---|
| `transmission_layers/graph_foundation/__init__.py` | graph_foundation boundary retained for manual legacy ecosystem review; package initializer for package with referenced/non-candidate modules |
| `transmission_layers/graph_foundation/finish_graph_evolution_run.py` | graph_foundation boundary retained for manual legacy ecosystem review |
| `transmission_layers/graph_foundation/graph_supabase_client.py` | graph_foundation boundary retained for manual legacy ecosystem review; listed as active path or active path pattern in repository dependency dataflow map |
| `transmission_layers/graph_foundation/intermediaries/canonical_structural_ontology_engine.py` | graph_foundation boundary retained for manual legacy ecosystem review; listed as active path or active path pattern in repository dependency dataflow map |
| `transmission_layers/graph_foundation/intermediaries/directed_intermediary_seeding_engine.py` | graph_foundation boundary retained for manual legacy ecosystem review; listed as active path or active path pattern in repository dependency dataflow map |
| `transmission_layers/graph_foundation/intermediaries/intermediary_classification.py` | graph_foundation boundary retained for manual legacy ecosystem review; listed as active path or active path pattern in repository dependency dataflow map |
| `transmission_layers/graph_foundation/intermediaries/intermediary_detection_engine.py` | graph_foundation boundary retained for manual legacy ecosystem review; listed as active path or active path pattern in repository dependency dataflow map |
| `transmission_layers/graph_foundation/intermediaries/intermediary_normalization.py` | graph_foundation boundary retained for manual legacy ecosystem review; listed as active path or active path pattern in repository dependency dataflow map |
| `transmission_layers/graph_foundation/intermediaries/intermediary_scoring.py` | graph_foundation boundary retained for manual legacy ecosystem review; listed as active path or active path pattern in repository dependency dataflow map |
| `transmission_layers/graph_foundation/intermediaries/intermediary_telemetry.py` | graph_foundation boundary retained for manual legacy ecosystem review; listed as active path or active path pattern in repository dependency dataflow map |
| `transmission_layers/graph_foundation/intermediaries/intermediary_utils.py` | graph_foundation boundary retained for manual legacy ecosystem review; listed as active path or active path pattern in repository dependency dataflow map |
| `transmission_layers/graph_foundation/intermediaries/intermediary_validation.py` | graph_foundation boundary retained for manual legacy ecosystem review; listed as active path or active path pattern in repository dependency dataflow map |
| `transmission_layers/graph_foundation/phase3a1_evidence_density_expansion.py` | graph_foundation boundary retained for manual legacy ecosystem review; listed as active path or active path pattern in repository dependency dataflow map |
| `transmission_layers/graph_foundation/phase3a2_cross_theme_relationship_expansion.py` | graph_foundation boundary retained for manual legacy ecosystem review; listed as active path or active path pattern in repository dependency dataflow map |
| `transmission_layers/graph_foundation/phase3a_evidence_graph_expansion.py` | graph_foundation boundary retained for manual legacy ecosystem review; listed as active path or active path pattern in repository dependency dataflow map |
| `transmission_layers/graph_foundation/phase3b_relationship_persistence.py` | graph_foundation boundary retained for manual legacy ecosystem review; listed as active path or active path pattern in repository dependency dataflow map |
| `transmission_layers/graph_foundation/phase3c_regime_transition_structural_drift.py` | graph_foundation boundary retained for manual legacy ecosystem review; listed as active path or active path pattern in repository dependency dataflow map |
| `transmission_layers/graph_foundation/phase3d_structural_pressure_accumulation.py` | graph_foundation boundary retained for manual legacy ecosystem review; listed as active path or active path pattern in repository dependency dataflow map |
| `transmission_layers/graph_foundation/phase3e_transmission_potential_surface.py` | graph_foundation boundary retained for manual legacy ecosystem review; listed as active path or active path pattern in repository dependency dataflow map |
| `transmission_layers/graph_foundation/phase4a_controlled_single_hop_propagation.py` | graph_foundation boundary retained for manual legacy ecosystem review; listed as active path or active path pattern in repository dependency dataflow map |
| `transmission_layers/graph_foundation/phase4b_propagation_memory_decay.py` | graph_foundation boundary retained for manual legacy ecosystem review; listed as active path or active path pattern in repository dependency dataflow map |
| `transmission_layers/graph_foundation/start_graph_evolution_run.py` | graph_foundation boundary retained for manual legacy ecosystem review |
| `transmission_layers/graph_foundation/write_graph_evolution_phase_event.py` | graph_foundation boundary retained for manual legacy ecosystem review |
| `transmission_layers/history_long/__init__.py` | inside current SEFI core/protected path; package initializer for package with referenced/non-candidate modules |
| `transmission_layers/history_read_model/__init__.py` | inside current SEFI core/protected path; package initializer for package with referenced/non-candidate modules |
| `transmission_layers/intelligence/tier3i/__init__.py` | package initializer for package with referenced/non-candidate modules |
| `transmission_layers/intelligence/tier4/__init__.py` | package initializer for package with referenced/non-candidate modules |

## Queue B: Unknown Review Queue

| Path | Subsystem | Risk | Likely category | Recommended next action | Inbound | Outbound | Workflow refs | Test refs | Textual refs |
|---|---|---|---|---|---:|---:|---:|---:|---:|
| `transmission_layers/expectation_failure/real_data/b2_market_input_validation.py` | expectation_failure | HIGH | legacy expectation failure | protect | 1 | 1 | 0 | 0 | 0 |
| `transmission_layers/expectation_failure/real_data/b3_certified_snapshot_envelope.py` | expectation_failure | HIGH | legacy expectation failure | protect | 1 | 0 | 0 | 0 | 0 |
| `transmission_layers/expectation_failure/real_data/b3_snapshot_assembly_certification.py` | expectation_failure | HIGH | legacy expectation failure | protect | 2 | 0 | 0 | 0 | 0 |
| `transmission_layers/expectation_failure/real_data/b3_snapshot_assembly_validation.py` | expectation_failure | HIGH | legacy expectation failure | protect | 2 | 3 | 0 | 0 | 0 |
| `transmission_layers/expectation_failure/real_data/b4_snapshot_persistence_certification.py` | expectation_failure | HIGH | legacy expectation failure | protect | 1 | 1 | 0 | 0 | 0 |
| `transmission_layers/expectation_failure/real_data/b4_snapshot_persistence_contract.py` | expectation_failure | HIGH | legacy expectation failure | protect | 3 | 0 | 0 | 0 | 0 |
| `transmission_layers/expectation_failure/real_data/b4_snapshot_persistence_orchestrator.py` | expectation_failure | HIGH | legacy expectation failure | protect | 1 | 1 | 0 | 0 | 0 |
| `transmission_layers/expectation_failure/real_data/b4_snapshot_persistence_validator.py` | expectation_failure | HIGH | legacy expectation failure | protect | 3 | 1 | 0 | 0 | 0 |
| `transmission_layers/expectation_failure/real_data/b4_supabase_snapshot_repository.py` | expectation_failure | HIGH | legacy expectation failure | protect | 2 | 2 | 0 | 0 | 0 |
| `transmission_layers/expectation_failure/real_data/t2_structural_delta_intelligence.py` | expectation_failure | HIGH | legacy expectation failure | protect | 1 | 0 | 0 | 0 | 0 |
| `transmission_layers/expectation_failure/real_data/t3_fragility_evolution_curves.py` | expectation_failure | HIGH | legacy expectation failure | protect | 1 | 0 | 0 | 0 | 0 |
| `transmission_layers/expectation_failure/real_data/t4_regime_transition_detection.py` | expectation_failure | HIGH | legacy expectation failure | protect | 1 | 0 | 0 | 0 | 0 |
| `transmission_layers/expectation_failure/real_data/t5_historical_explainability.py` | expectation_failure | HIGH | legacy expectation failure | protect | 1 | 0 | 0 | 0 | 0 |
| `transmission_layers/expectation_failure/real_data/t6_temporal_evolution_certification_closeout.py` | expectation_failure | HIGH | legacy expectation failure | protect | 1 | 0 | 0 | 0 | 0 |
| `transmission_layers/graph_foundation/ai_anchor_graph_seed.py` | graph_foundation | HIGH | legacy graph foundation | protect | 1 | 2 | 0 | 0 | 0 |
| `transmission_layers/graph_foundation/edge_scoring.py` | graph_foundation | HIGH | legacy graph foundation | protect | 1 | 1 | 0 | 0 | 0 |
| `transmission_layers/graph_foundation/graph_models.py` | graph_foundation | HIGH | legacy graph foundation | protect | 2 | 0 | 0 | 0 | 0 |
| `transmission_layers/graph_foundation/graph_snapshot_service.py` | graph_foundation | HIGH | legacy graph foundation | protect | 1 | 2 | 0 | 0 | 0 |
| `transmission_layers/graph_foundation/graph_validation.py` | graph_foundation | HIGH | legacy graph foundation | protect | 1 | 0 | 0 | 0 | 0 |
| `transmission_layers/graph_foundation/supabase_rest_client.py` | graph_foundation | HIGH | legacy graph foundation | protect | 2 | 0 | 0 | 0 | 0 |
| `transmission_layers/alpha/layer_a/predictive_validation.py` | alpha | MEDIUM | legacy alpha research | candidate for later archive | 1 | 0 | 0 | 0 | 0 |
| `transmission_layers/alpha/layer_b/regime_conditional_efficacy.py` | alpha | MEDIUM | legacy alpha research | candidate for later archive | 1 | 1 | 0 | 0 | 0 |
| `transmission_layers/alpha/layer_c/__init__.py` | alpha | MEDIUM | legacy alpha research | candidate for later archive | 1 | 1 | 0 | 0 | 0 |
| `transmission_layers/alpha/layer_c/structural_divergence_intelligence.py` | alpha | MEDIUM | legacy alpha research | candidate for later archive | 1 | 0 | 0 | 0 | 0 |
| `transmission_layers/alpha/layer_d/__init__.py` | alpha | MEDIUM | legacy alpha research | candidate for later archive | 1 | 1 | 0 | 0 | 0 |
| `transmission_layers/alpha/layer_d/narrative_fragility_hype_decomposition.py` | alpha | MEDIUM | legacy alpha research | candidate for later archive | 1 | 0 | 0 | 0 | 0 |
| `transmission_layers/alpha/layer_e/__init__.py` | alpha | MEDIUM | legacy alpha research | candidate for later archive | 1 | 1 | 0 | 0 | 0 |
| `transmission_layers/alpha/layer_e/signal_interaction_effect_intelligence.py` | alpha | MEDIUM | legacy alpha research | candidate for later archive | 1 | 0 | 0 | 0 | 0 |
| `transmission_layers/intelligence/tier4/attribution_metrics.py` | intelligence | MEDIUM | historical intelligence | candidate for later archive | 1 | 1 | 0 | 0 | 0 |
| `transmission_layers/intelligence/tier4/causal_paths.py` | intelligence | MEDIUM | historical intelligence | candidate for later archive | 1 | 2 | 0 | 0 | 0 |
| `transmission_layers/intelligence/tier4/regime_metrics.py` | intelligence | MEDIUM | historical intelligence | candidate for later archive | 3 | 0 | 0 | 0 | 0 |
| `transmission_layers/intelligence/tier4/scenario_metrics.py` | intelligence | MEDIUM | historical intelligence | candidate for later archive | 1 | 1 | 0 | 0 | 0 |
| `transmission_layers/intelligence/tier4/topology_drift.py` | intelligence | MEDIUM | historical intelligence | candidate for later archive | 1 | 1 | 0 | 0 | 0 |
| `transmission_layers/intelligence/tier5/federation_diagnostics.py` | intelligence | MEDIUM | historical intelligence | candidate for later archive | 11 | 1 | 0 | 0 | 0 |
| `transmission_layers/intelligence/tier6/propagation_distortion_diagnostics.py` | intelligence | MEDIUM | historical intelligence | candidate for later archive | 6 | 1 | 0 | 0 | 5 |
| `transmission_layers/intelligence/tier6/transmission_governance_audit_trail.py` | intelligence | MEDIUM | historical intelligence | candidate for later archive | 2 | 4 | 0 | 0 | 1 |
| `transmission_layers/intelligence/tier6/transmission_governance_finalization.py` | intelligence | MEDIUM | historical intelligence | candidate for later archive | 1 | 10 | 0 | 0 | 0 |
| `transmission_layers/intelligence/tier6/transmission_governance_review_gate.py` | intelligence | MEDIUM | historical intelligence | candidate for later archive | 3 | 8 | 0 | 0 | 2 |
| `transmission_layers/intelligence/tier6/transmission_governance_summary.py` | intelligence | MEDIUM | historical intelligence | candidate for later archive | 4 | 7 | 0 | 0 | 3 |
| `transmission_layers/intelligence/tier6/transmission_path_integrity.py` | intelligence | MEDIUM | historical intelligence | candidate for later archive | 6 | 1 | 0 | 0 | 5 |
| `transmission_layers/intelligence/tier6/transmission_reliability_diagnostics.py` | intelligence | MEDIUM | historical intelligence | candidate for later archive | 6 | 1 | 0 | 0 | 5 |
| `transmission_layers/intelligence/tier6/transmission_risk_register.py` | intelligence | MEDIUM | historical intelligence | candidate for later archive | 5 | 6 | 0 | 0 | 4 |
| `transmission_layers/intelligence/tier7/strategic_anomaly_attribution.py` | intelligence | MEDIUM | historical intelligence | candidate for later archive | 4 | 6 | 0 | 0 | 0 |
| `transmission_layers/intelligence/tier7/strategic_causality_replay.py` | intelligence | MEDIUM | historical intelligence | candidate for later archive | 1 | 9 | 0 | 0 | 0 |
| `transmission_layers/intelligence/tier7/strategic_coherence.py` | intelligence | MEDIUM | historical intelligence | candidate for later archive | 3 | 7 | 0 | 0 | 0 |
| `transmission_layers/intelligence/tier7/strategic_continuity.py` | intelligence | MEDIUM | historical intelligence | candidate for later archive | 6 | 4 | 0 | 0 | 0 |
| `transmission_layers/intelligence/tier7/strategic_drift_diagnostics.py` | intelligence | MEDIUM | historical intelligence | candidate for later archive | 7 | 3 | 0 | 0 | 0 |
| `transmission_layers/intelligence/tier7/strategic_graph_state.py` | intelligence | MEDIUM | historical intelligence | candidate for later archive | 9 | 1 | 0 | 0 | 0 |
| `transmission_layers/intelligence/tier7/strategic_regime_persistence.py` | intelligence | MEDIUM | historical intelligence | candidate for later archive | 5 | 5 | 0 | 0 | 0 |
| `transmission_layers/intelligence/tier7/strategic_stability_resilience.py` | intelligence | MEDIUM | historical intelligence | candidate for later archive | 2 | 8 | 0 | 0 | 0 |
| `transmission_layers/intelligence/tier7/strategic_state_transition.py` | intelligence | MEDIUM | historical intelligence | candidate for later archive | 8 | 2 | 0 | 0 | 0 |

## Queue C: Legacy Ecosystem Map

| Ecosystem | File count | Classification counts |
|---|---:|---|
| SEFI Core | 0 | none |
| Historical Intelligence | 164 | ACTIVE_REFERENCED: 136, PROTECTED_ACTIVE: 2, UNKNOWN_REQUIRES_REVIEW: 23, UNREFERENCED_CANDIDATE: 3 |
| DB-2 / Observation Read Model | 5 | PROTECTED_ACTIVE: 4, UNREFERENCED_CANDIDATE: 1 |
| Live OPS | 3 | ACTIVE_REFERENCED: 1, PROTECTED_ACTIVE: 2 |
| Legacy Expectation Failure | 51 | ACTIVE_REFERENCED: 15, PROTECTED_ACTIVE: 22, UNKNOWN_REQUIRES_REVIEW: 14 |
| Legacy Graph Foundation | 36 | ACTIVE_REFERENCED: 1, LEGACY_REFERENCED: 1, PROTECTED_ACTIVE: 5, UNKNOWN_REQUIRES_REVIEW: 6, UNREFERENCED_CANDIDATE: 23 |
| Legacy AI Transmission | 0 | none |
| Legacy Alpha Research | 11 | ACTIVE_REFERENCED: 3, UNKNOWN_REQUIRES_REVIEW: 8 |
| Governance / Observability | 0 | none |
| Tests-only Intelligence Modules | 45 | ACTIVE_REFERENCED: 45 |
| Unknown | 0 | none |

<details><summary>Historical Intelligence files (164)</summary>

- `transmission_layers/history_long/__init__.py`
- `transmission_layers/history_long/hist_intel1_historical_structural_findings.py`
- `transmission_layers/history_long/hist_intel1b_fact_native_historical_findings.py`
- `transmission_layers/history_long/hist_long8_cross_window_persistence.py`
- `transmission_layers/history_long/hist_long9_persistence_drift.py`
- `transmission_layers/intelligence/tier3i/__init__.py`
- `transmission_layers/intelligence/tier3i/contagion_mapping.py`
- `transmission_layers/intelligence/tier3i/historical_replay.py`
- `transmission_layers/intelligence/tier3i/intelligence_summary.py`
- `transmission_layers/intelligence/tier3i/multi_hop_quality.py`
- `transmission_layers/intelligence/tier3i/path_explainability.py`
- `transmission_layers/intelligence/tier3i/regime_drift.py`
- `transmission_layers/intelligence/tier3i/structural_regime.py`
- `transmission_layers/intelligence/tier4/__init__.py`
- `transmission_layers/intelligence/tier4/adaptation_constraints.py`
- `transmission_layers/intelligence/tier4/adaptation_exhaustion.py`
- `transmission_layers/intelligence/tier4/attribution_metrics.py`
- `transmission_layers/intelligence/tier4/cascade_boundaries.py`
- `transmission_layers/intelligence/tier4/cascade_corridors.py`
- `transmission_layers/intelligence/tier4/cascade_signatures.py`
- `transmission_layers/intelligence/tier4/causal_lineage.py`
- `transmission_layers/intelligence/tier4/causal_paths.py`
- `transmission_layers/intelligence/tier4/causal_replay.py`
- `transmission_layers/intelligence/tier4/chronic_instability.py`
- `transmission_layers/intelligence/tier4/contagion_signatures.py`
- `transmission_layers/intelligence/tier4/containment_integrity.py`
- `transmission_layers/intelligence/tier4/dependency_concentration.py`
- `transmission_layers/intelligence/tier4/durability_replay.py`
- `transmission_layers/intelligence/tier4/failure_thresholds.py`
- `transmission_layers/intelligence/tier4/flexibility_collapse.py`
- `transmission_layers/intelligence/tier4/fragility_analysis.py`
- `transmission_layers/intelligence/tier4/fragility_explanations.py`
- `transmission_layers/intelligence/tier4/fragility_replay.py`
- `transmission_layers/intelligence/tier4/fragility_signatures.py`
- `transmission_layers/intelligence/tier4/fragmentation_diagnostics.py`
- `transmission_layers/intelligence/tier4/influence_attribution.py`
- `transmission_layers/intelligence/tier4/persistence_signatures.py`
- `transmission_layers/intelligence/tier4/propagation_containment.py`
- `transmission_layers/intelligence/tier4/recovery_bottlenecks.py`
- `transmission_layers/intelligence/tier4/recovery_corridors.py`
- `transmission_layers/intelligence/tier4/recovery_decay.py`
- `transmission_layers/intelligence/tier4/recovery_explanations.py`
- `transmission_layers/intelligence/tier4/recovery_fragments.py`
- `transmission_layers/intelligence/tier4/recovery_persistence.py`
- `transmission_layers/intelligence/tier4/recovery_signatures.py`
- `transmission_layers/intelligence/tier4/regeneration_pathways.py`
- `transmission_layers/intelligence/tier4/regime_metrics.py`
- `transmission_layers/intelligence/tier4/regime_persistence.py`
- `transmission_layers/intelligence/tier4/regime_transitions.py`
- `transmission_layers/intelligence/tier4/reintegration_resistance.py`
- `transmission_layers/intelligence/tier4/reintegration_stability.py`
- `transmission_layers/intelligence/tier4/resilience_dispersion.py`
- `transmission_layers/intelligence/tier4/resilience_erosion.py`
- `transmission_layers/intelligence/tier4/resilience_saturation.py`
- `transmission_layers/intelligence/tier4/resistance_signatures.py`
- `transmission_layers/intelligence/tier4/response_effectiveness.py`
- `transmission_layers/intelligence/tier4/response_explanations.py`
- `transmission_layers/intelligence/tier4/response_signatures.py`
- `transmission_layers/intelligence/tier4/rigidity_cascades.py`
- `transmission_layers/intelligence/tier4/rigidity_explanations.py`
- `transmission_layers/intelligence/tier4/rigidity_signatures.py`
- `transmission_layers/intelligence/tier4/scenario_metrics.py`
- `transmission_layers/intelligence/tier4/scenario_semantics.py`
- `transmission_layers/intelligence/tier4/stabilization_longevity.py`
- `transmission_layers/intelligence/tier4/stress_amplification.py`
- `transmission_layers/intelligence/tier4/stress_concentration.py`
- `transmission_layers/intelligence/tier4/stress_leakage.py`
- `transmission_layers/intelligence/tier4/structural_criticality.py`
- `transmission_layers/intelligence/tier4/structural_entropy.py`
- `transmission_layers/intelligence/tier4/structural_memory.py`
- `transmission_layers/intelligence/tier4/structural_regimes.py`
- `transmission_layers/intelligence/tier4/structural_simulation.py`
- `transmission_layers/intelligence/tier4/survivability_metrics.py`
- `transmission_layers/intelligence/tier4/systemic_bottlenecks.py`
- `transmission_layers/intelligence/tier4/systemic_stress_clustering.py`
- `transmission_layers/intelligence/tier4/temporal_replay.py`
- `transmission_layers/intelligence/tier4/tipping_points.py`
- `transmission_layers/intelligence/tier4/topology_coherence.py`
- `transmission_layers/intelligence/tier4/topology_drift.py`
- `transmission_layers/intelligence/tier4/topology_hashing.py`
- `transmission_layers/intelligence/tier4/transition_signatures.py`
- `transmission_layers/intelligence/tier5/distributed_survivability_evolution.py`
- `transmission_layers/intelligence/tier5/distributed_survivability_history.py`
- `transmission_layers/intelligence/tier5/federation_bottleneck_evolution.py`
- `transmission_layers/intelligence/tier5/federation_bottleneck_persistence.py`
- `transmission_layers/intelligence/tier5/federation_boundary_evolution.py`
- `transmission_layers/intelligence/tier5/federation_boundary_history.py`
- `transmission_layers/intelligence/tier5/federation_bridge_evolution.py`
- `transmission_layers/intelligence/tier5/federation_bridge_persistence.py`
- `transmission_layers/intelligence/tier5/federation_common.py`
- `transmission_layers/intelligence/tier5/federation_constraint_history.py`
- `transmission_layers/intelligence/tier5/federation_constraints.py`
- `transmission_layers/intelligence/tier5/federation_continuity_constraints.py`
- `transmission_layers/intelligence/tier5/federation_continuity_observability.py`
- `transmission_layers/intelligence/tier5/federation_degradation.py`
- `transmission_layers/intelligence/tier5/federation_dependency_evolution.py`
- `transmission_layers/intelligence/tier5/federation_dependency_resilience.py`
- `transmission_layers/intelligence/tier5/federation_determinism.py`
- `transmission_layers/intelligence/tier5/federation_diagnostic_readiness.py`
- `transmission_layers/intelligence/tier5/federation_diagnostics.py`
- `transmission_layers/intelligence/tier5/federation_engine.py`
- `transmission_layers/intelligence/tier5/federation_escalation.py`
- `transmission_layers/intelligence/tier5/federation_evolution_explanations.py`
- `transmission_layers/intelligence/tier5/federation_evolution_signatures.py`
- `transmission_layers/intelligence/tier5/federation_export_contracts.py`
- `transmission_layers/intelligence/tier5/federation_failure_containment.py`
- `transmission_layers/intelligence/tier5/federation_governance.py`
- `transmission_layers/intelligence/tier5/federation_governance_explanations.py`
- `transmission_layers/intelligence/tier5/federation_governance_signatures.py`
- `transmission_layers/intelligence/tier5/federation_guardrails.py`
- `transmission_layers/intelligence/tier5/federation_health_alignment.py`
- `transmission_layers/intelligence/tier5/federation_health_classification.py`
- `transmission_layers/intelligence/tier5/federation_health_explanations.py`
- `transmission_layers/intelligence/tier5/federation_health_signatures.py`
- `transmission_layers/intelligence/tier5/federation_integrity.py`
- `transmission_layers/intelligence/tier5/federation_lineage.py`
- `transmission_layers/intelligence/tier5/federation_observability.py`
- `transmission_layers/intelligence/tier5/federation_observability_explanations.py`
- `transmission_layers/intelligence/tier5/federation_observability_signatures.py`
- `transmission_layers/intelligence/tier5/federation_persistence.py`
- `transmission_layers/intelligence/tier5/federation_persistence_explanations.py`
- `transmission_layers/intelligence/tier5/federation_phase_transitions.py`
- `transmission_layers/intelligence/tier5/federation_policy_boundaries.py`
- `transmission_layers/intelligence/tier5/federation_propagation_visibility.py`
- `transmission_layers/intelligence/tier5/federation_recoverability.py`
- `transmission_layers/intelligence/tier5/federation_recovery.py`
- `transmission_layers/intelligence/tier5/federation_recovery_evolution.py`
- `transmission_layers/intelligence/tier5/federation_recovery_history.py`
- `transmission_layers/intelligence/tier5/federation_recovery_paths.py`
- `transmission_layers/intelligence/tier5/federation_replay_contracts.py`
- `transmission_layers/intelligence/tier5/federation_replay_history.py`
- `transmission_layers/intelligence/tier5/federation_replay_observability.py`
- `transmission_layers/intelligence/tier5/federation_resilience.py`
- `transmission_layers/intelligence/tier5/federation_resilience_explanations.py`
- `transmission_layers/intelligence/tier5/federation_resilience_signatures.py`
- `transmission_layers/intelligence/tier5/federation_score_contracts.py`
- `transmission_layers/intelligence/tier5/federation_structural_health.py`
- `transmission_layers/intelligence/tier5/federation_telemetry.py`
- `transmission_layers/intelligence/tier5/federation_temporal_evolution.py`
- `transmission_layers/intelligence/tier5/federation_temporal_signatures.py`
- `transmission_layers/intelligence/tier5/federation_traceability.py`
- `transmission_layers/intelligence/tier5/federation_violation_detection.py`
- `transmission_layers/intelligence/tier5/federation_visibility.py`
- `transmission_layers/intelligence/tier5/inter_system_contagion_evolution.py`
- `transmission_layers/intelligence/tier5/inter_system_contagion_history.py`
- `transmission_layers/intelligence/tier6/propagation_distortion_diagnostics.py`
- `transmission_layers/intelligence/tier6/structural_signal_quality.py`
- `transmission_layers/intelligence/tier6/transmission_explainability.py`
- `transmission_layers/intelligence/tier6/transmission_governance_audit_trail.py`
- `transmission_layers/intelligence/tier6/transmission_governance_finalization.py`
- `transmission_layers/intelligence/tier6/transmission_governance_review_gate.py`
- `transmission_layers/intelligence/tier6/transmission_governance_summary.py`
- `transmission_layers/intelligence/tier6/transmission_path_integrity.py`
- `transmission_layers/intelligence/tier6/transmission_reliability_diagnostics.py`
- `transmission_layers/intelligence/tier6/transmission_risk_register.py`
- `transmission_layers/intelligence/tier7/strategic_anomaly_attribution.py`
- `transmission_layers/intelligence/tier7/strategic_causality_replay.py`
- `transmission_layers/intelligence/tier7/strategic_coherence.py`
- `transmission_layers/intelligence/tier7/strategic_continuity.py`
- `transmission_layers/intelligence/tier7/strategic_drift_diagnostics.py`
- `transmission_layers/intelligence/tier7/strategic_graph_state.py`
- `transmission_layers/intelligence/tier7/strategic_regime_persistence.py`
- `transmission_layers/intelligence/tier7/strategic_stability_resilience.py`
- `transmission_layers/intelligence/tier7/strategic_state_transition.py`

</details>

<details><summary>DB-2 / Observation Read Model files (5)</summary>

- `transmission_layers/history_read_model/__init__.py`
- `transmission_layers/history_read_model/fact_emitter.py`
- `transmission_layers/history_read_model/loader.py`
- `transmission_layers/history_read_model/observation_query.py`
- `transmission_layers/history_read_model/queries.py`

</details>

<details><summary>Live OPS files (3)</summary>

- `transmission_layers/live_ops/__init__.py`
- `transmission_layers/live_ops/ops_live2_observation_fact_accumulation.py`
- `transmission_layers/live_ops/ops_live3_structural_state_snapshot.py`

</details>

<details><summary>Legacy Expectation Failure files (51)</summary>

- `transmission_layers/expectation_failure/real_data/__init__.py`
- `transmission_layers/expectation_failure/real_data/b1_benchmark_registry.py`
- `transmission_layers/expectation_failure/real_data/b1_fragility_payload_builder.py`
- `transmission_layers/expectation_failure/real_data/b1_market_snapshot_builder.py`
- `transmission_layers/expectation_failure/real_data/b1_real_entity_registry.py`
- `transmission_layers/expectation_failure/real_data/b1_snapshot_certification.py`
- `transmission_layers/expectation_failure/real_data/b2_ingestion_candidate_builder.py`
- `transmission_layers/expectation_failure/real_data/b2_ingestion_certification.py`
- `transmission_layers/expectation_failure/real_data/b2_market_ingestion_adapter.py`
- `transmission_layers/expectation_failure/real_data/b2_market_input_normalizer.py`
- `transmission_layers/expectation_failure/real_data/b2_market_input_validation.py`
- `transmission_layers/expectation_failure/real_data/b3_certified_snapshot_envelope.py`
- `transmission_layers/expectation_failure/real_data/b3_snapshot_assembler.py`
- `transmission_layers/expectation_failure/real_data/b3_snapshot_assembly_certification.py`
- `transmission_layers/expectation_failure/real_data/b3_snapshot_assembly_validation.py`
- `transmission_layers/expectation_failure/real_data/b3_snapshot_input_mapper.py`
- `transmission_layers/expectation_failure/real_data/b4_snapshot_persistence_certification.py`
- `transmission_layers/expectation_failure/real_data/b4_snapshot_persistence_contract.py`
- `transmission_layers/expectation_failure/real_data/b4_snapshot_persistence_orchestrator.py`
- `transmission_layers/expectation_failure/real_data/b4_snapshot_persistence_validator.py`
- `transmission_layers/expectation_failure/real_data/b4_supabase_snapshot_repository.py`
- `transmission_layers/expectation_failure/real_data/hist_density1_controlled_historical_density_expansion.py`
- `transmission_layers/expectation_failure/real_data/hist_density2_longitudinal_ecology_enrichment.py`
- `transmission_layers/expectation_failure/real_data/hist_density3_curated_ecology_expansion.py`
- `transmission_layers/expectation_failure/real_data/hist_density4_findings_review.py`
- `transmission_layers/expectation_failure/real_data/hist_long1_longitudinal_ecology.py`
- `transmission_layers/expectation_failure/real_data/hist_long2_real_longitudinal_ecology.py`
- `transmission_layers/expectation_failure/real_data/hist_long3_updated_universe_validation.py`
- `transmission_layers/expectation_failure/real_data/hist_long4_real_multi_window_ecology.py`
- `transmission_layers/expectation_failure/real_data/hist_long5_analysis_only_review.py`
- `transmission_layers/expectation_failure/real_data/hist_long5b_temporal_delta_sensitivity_classification.py`
- `transmission_layers/expectation_failure/real_data/hist_long6_cross_sectional_ecology_differentiation.py`
- `transmission_layers/expectation_failure/real_data/hist_long7_intra_group_structural_contrast.py`
- `transmission_layers/expectation_failure/real_data/ops_hist1_controlled_historical_observation.py`
- `transmission_layers/expectation_failure/real_data/ops_hist2_historical_continuity_intelligence.py`
- `transmission_layers/expectation_failure/real_data/ops_hist3_historical_continuity_archetypes.py`
- `transmission_layers/expectation_failure/real_data/ops_hist4_archetype_recurrence_ecology.py`
- `transmission_layers/expectation_failure/real_data/ops_hist5_temporal_continuity_regimes.py`
- `transmission_layers/expectation_failure/real_data/ops_hist6_regime_morphology_observation.py`
- `transmission_layers/expectation_failure/real_data/ops_hist7_regime_ecology_saturation.py`
- `transmission_layers/expectation_failure/real_data/ops_hist_cache_raw_fmp.py`
- `transmission_layers/expectation_failure/real_data/ops_live1_controlled_ecosystem_ingestion.py`
- `transmission_layers/expectation_failure/real_data/ops_live1b_snapshot_observation_review.py`
- `transmission_layers/expectation_failure/real_data/sde2_curated_symbol_ecology_expansion.py`
- `transmission_layers/expectation_failure/real_data/sefi_observation_universe.py`
- `transmission_layers/expectation_failure/real_data/t1_temporal_snapshot_sequencing.py`
- `transmission_layers/expectation_failure/real_data/t2_structural_delta_intelligence.py`
- `transmission_layers/expectation_failure/real_data/t3_fragility_evolution_curves.py`
- `transmission_layers/expectation_failure/real_data/t4_regime_transition_detection.py`
- `transmission_layers/expectation_failure/real_data/t5_historical_explainability.py`
- `transmission_layers/expectation_failure/real_data/t6_temporal_evolution_certification_closeout.py`

</details>

<details><summary>Legacy Graph Foundation files (36)</summary>

- `transmission_layers/graph_foundation/__init__.py`
- `transmission_layers/graph_foundation/ai_anchor_graph_seed.py`
- `transmission_layers/graph_foundation/continuity/continuity_engine.py`
- `transmission_layers/graph_foundation/edge_scoring.py`
- `transmission_layers/graph_foundation/finish_graph_evolution_run.py`
- `transmission_layers/graph_foundation/graph_models.py`
- `transmission_layers/graph_foundation/graph_snapshot_service.py`
- `transmission_layers/graph_foundation/graph_supabase_client.py`
- `transmission_layers/graph_foundation/graph_validation.py`
- `transmission_layers/graph_foundation/intermediaries/canonical_structural_ontology_engine.py`
- `transmission_layers/graph_foundation/intermediaries/directed_intermediary_seeding_engine.py`
- `transmission_layers/graph_foundation/intermediaries/intermediary_classification.py`
- `transmission_layers/graph_foundation/intermediaries/intermediary_detection_engine.py`
- `transmission_layers/graph_foundation/intermediaries/intermediary_normalization.py`
- `transmission_layers/graph_foundation/intermediaries/intermediary_scoring.py`
- `transmission_layers/graph_foundation/intermediaries/intermediary_telemetry.py`
- `transmission_layers/graph_foundation/intermediaries/intermediary_utils.py`
- `transmission_layers/graph_foundation/intermediaries/intermediary_validation.py`
- `transmission_layers/graph_foundation/phase3a1_evidence_density_expansion.py`
- `transmission_layers/graph_foundation/phase3a2_cross_theme_relationship_expansion.py`
- `transmission_layers/graph_foundation/phase3a_evidence_graph_expansion.py`
- `transmission_layers/graph_foundation/phase3b_relationship_persistence.py`
- `transmission_layers/graph_foundation/phase3c_regime_transition_structural_drift.py`
- `transmission_layers/graph_foundation/phase3d_structural_pressure_accumulation.py`
- `transmission_layers/graph_foundation/phase3e_transmission_potential_surface.py`
- `transmission_layers/graph_foundation/phase4a_controlled_single_hop_propagation.py`
- `transmission_layers/graph_foundation/phase4b_propagation_memory_decay.py`
- `transmission_layers/graph_foundation/phase4c_propagation_monitoring_dashboard.py`
- `transmission_layers/graph_foundation/phase4e_historical_propagation_replay.py`
- `transmission_layers/graph_foundation/phase5b_propagation_corridor_engine.py`
- `transmission_layers/graph_foundation/phase5c_regime_corridor_dynamics_engine.py`
- `transmission_layers/graph_foundation/phase5d_structural_propagation_regime_forecasting_engine.py`
- `transmission_layers/graph_foundation/run_pass1_graph_foundation.py`
- `transmission_layers/graph_foundation/start_graph_evolution_run.py`
- `transmission_layers/graph_foundation/supabase_rest_client.py`
- `transmission_layers/graph_foundation/write_graph_evolution_phase_event.py`

</details>

<details><summary>Legacy Alpha Research files (11)</summary>

- `transmission_layers/alpha/__init__.py`
- `transmission_layers/alpha/layer_a/__init__.py`
- `transmission_layers/alpha/layer_a/predictive_validation.py`
- `transmission_layers/alpha/layer_b/__init__.py`
- `transmission_layers/alpha/layer_b/regime_conditional_efficacy.py`
- `transmission_layers/alpha/layer_c/__init__.py`
- `transmission_layers/alpha/layer_c/structural_divergence_intelligence.py`
- `transmission_layers/alpha/layer_d/__init__.py`
- `transmission_layers/alpha/layer_d/narrative_fragility_hype_decomposition.py`
- `transmission_layers/alpha/layer_e/__init__.py`
- `transmission_layers/alpha/layer_e/signal_interaction_effect_intelligence.py`

</details>

<details><summary>Tests-only Intelligence Modules files (45)</summary>

- `transmission_layers/intelligence/tier3i/edge_quality.py`
- `transmission_layers/intelligence/tier3i/structural_influence.py`
- `transmission_layers/intelligence/tier4/cascade_explanations.py`
- `transmission_layers/intelligence/tier4/contagion_boundaries.py`
- `transmission_layers/intelligence/tier4/contagion_explanations.py`
- `transmission_layers/intelligence/tier4/intervention_saturation.py`
- `transmission_layers/intelligence/tier4/intervention_strategies.py`
- `transmission_layers/intelligence/tier4/persistence_durability.py`
- `transmission_layers/intelligence/tier4/persistence_explanations.py`
- `transmission_layers/intelligence/tier4/pressure_resistance.py`
- `transmission_layers/intelligence/tier4/recovery_dynamics.py`
- `transmission_layers/intelligence/tier4/recovery_replay.py`
- `transmission_layers/intelligence/tier4/regime_replay.py`
- `transmission_layers/intelligence/tier4/regime_state_machine.py`
- `transmission_layers/intelligence/tier4/regime_transition_pressure.py`
- `transmission_layers/intelligence/tier4/resistance_explanations.py`
- `transmission_layers/intelligence/tier4/resistance_replay.py`
- `transmission_layers/intelligence/tier4/response_policy.py`
- `transmission_layers/intelligence/tier4/response_replay.py`
- `transmission_layers/intelligence/tier4/scenario_comparison.py`
- `transmission_layers/intelligence/tier4/scenario_perturbations.py`
- `transmission_layers/intelligence/tier4/scenario_replay.py`
- `transmission_layers/intelligence/tier4/scenario_sensitivity.py`
- `transmission_layers/intelligence/tier4/scenario_signatures.py`
- `transmission_layers/intelligence/tier4/stabilization_capacity.py`
- `transmission_layers/intelligence/tier4/stabilization_exhaustion.py`
- `transmission_layers/intelligence/tier4/state_snapshot.py`
- `transmission_layers/intelligence/tier4/structural_recovery.py`
- `transmission_layers/intelligence/tier4/structural_rigidity.py`
- `transmission_layers/intelligence/tier4/systemic_cascades.py`
- `transmission_layers/intelligence/tier4/transition_explanations.py`
- `transmission_layers/intelligence/tier5/__init__.py`
- `transmission_layers/intelligence/tier5/cross_system_transmission.py`
- `transmission_layers/intelligence/tier5/distributed_survivability.py`
- `transmission_layers/intelligence/tier5/federation_bottlenecks.py`
- `transmission_layers/intelligence/tier5/federation_boundaries.py`
- `transmission_layers/intelligence/tier5/federation_bridges.py`
- `transmission_layers/intelligence/tier5/federation_explanations.py`
- `transmission_layers/intelligence/tier5/federation_recovery_dependencies.py`
- `transmission_layers/intelligence/tier5/federation_signatures.py`
- `transmission_layers/intelligence/tier5/federation_stabilization_report.py`
- `transmission_layers/intelligence/tier5/federation_topology.py`
- `transmission_layers/intelligence/tier5/inter_system_contagion.py`
- `transmission_layers/intelligence/tier6/__init__.py`
- `transmission_layers/intelligence/tier7/__init__.py`

</details>

## High-Risk Protected Areas

| Path/prefix | Reason | Matched files |
|---|---|---:|
| `transmission_layers/history_read_model/` | DB-2 observation read model defaults to protect. | 5 |
| `transmission_layers/history_long/` | Historical long/intel modules default to protect. | 5 |
| `transmission_layers/expectation_failure/real_data/` | Real-data expectation-failure modules are conservative/protected. | 51 |
| `transmission_layers/live_ops/` | Live operations current SEFI core. | 3 |
| `transmission_layers/graph_foundation/` | Repository dataflow map names graph foundation phase/dependency contracts; keep as legacy boundary pending manual review. | 36 |

## Tests-Only Modules

48 modules are referenced only by tests under the static CLEAN-2 evidence model. They are not automatically active production, but they are also not safe archive without an explicit test/coverage decision.

| Path | Classification | Likely category | Test refs |
|---|---|---|---:|
| `transmission_layers/alpha/__init__.py` | ACTIVE_REFERENCED | legacy alpha research | 3 |
| `transmission_layers/expectation_failure/real_data/__init__.py` | ACTIVE_REFERENCED | legacy expectation failure | 12 |
| `transmission_layers/intelligence/tier3i/edge_quality.py` | ACTIVE_REFERENCED | historical intelligence | 1 |
| `transmission_layers/intelligence/tier3i/structural_influence.py` | ACTIVE_REFERENCED | historical intelligence | 1 |
| `transmission_layers/intelligence/tier4/cascade_explanations.py` | ACTIVE_REFERENCED | historical intelligence | 1 |
| `transmission_layers/intelligence/tier4/contagion_boundaries.py` | ACTIVE_REFERENCED | historical intelligence | 1 |
| `transmission_layers/intelligence/tier4/contagion_explanations.py` | ACTIVE_REFERENCED | historical intelligence | 1 |
| `transmission_layers/intelligence/tier4/intervention_saturation.py` | ACTIVE_REFERENCED | historical intelligence | 1 |
| `transmission_layers/intelligence/tier4/intervention_strategies.py` | ACTIVE_REFERENCED | historical intelligence | 1 |
| `transmission_layers/intelligence/tier4/persistence_durability.py` | ACTIVE_REFERENCED | historical intelligence | 1 |
| `transmission_layers/intelligence/tier4/persistence_explanations.py` | ACTIVE_REFERENCED | historical intelligence | 1 |
| `transmission_layers/intelligence/tier4/pressure_resistance.py` | ACTIVE_REFERENCED | historical intelligence | 3 |
| `transmission_layers/intelligence/tier4/recovery_dynamics.py` | ACTIVE_REFERENCED | historical intelligence | 1 |
| `transmission_layers/intelligence/tier4/recovery_replay.py` | ACTIVE_REFERENCED | historical intelligence | 1 |
| `transmission_layers/intelligence/tier4/regime_replay.py` | ACTIVE_REFERENCED | historical intelligence | 1 |
| `transmission_layers/intelligence/tier4/regime_state_machine.py` | ACTIVE_REFERENCED | historical intelligence | 1 |
| `transmission_layers/intelligence/tier4/regime_transition_pressure.py` | ACTIVE_REFERENCED | historical intelligence | 1 |
| `transmission_layers/intelligence/tier4/resistance_explanations.py` | ACTIVE_REFERENCED | historical intelligence | 1 |
| `transmission_layers/intelligence/tier4/resistance_replay.py` | ACTIVE_REFERENCED | historical intelligence | 1 |
| `transmission_layers/intelligence/tier4/response_policy.py` | ACTIVE_REFERENCED | historical intelligence | 1 |
| `transmission_layers/intelligence/tier4/response_replay.py` | ACTIVE_REFERENCED | historical intelligence | 1 |
| `transmission_layers/intelligence/tier4/scenario_comparison.py` | ACTIVE_REFERENCED | historical intelligence | 1 |
| `transmission_layers/intelligence/tier4/scenario_perturbations.py` | ACTIVE_REFERENCED | historical intelligence | 2 |
| `transmission_layers/intelligence/tier4/scenario_replay.py` | ACTIVE_REFERENCED | historical intelligence | 1 |
| `transmission_layers/intelligence/tier4/scenario_sensitivity.py` | ACTIVE_REFERENCED | historical intelligence | 1 |
| `transmission_layers/intelligence/tier4/scenario_signatures.py` | ACTIVE_REFERENCED | historical intelligence | 1 |
| `transmission_layers/intelligence/tier4/stabilization_capacity.py` | ACTIVE_REFERENCED | historical intelligence | 4 |
| `transmission_layers/intelligence/tier4/stabilization_exhaustion.py` | ACTIVE_REFERENCED | historical intelligence | 1 |
| `transmission_layers/intelligence/tier4/state_snapshot.py` | ACTIVE_REFERENCED | historical intelligence | 3 |
| `transmission_layers/intelligence/tier4/structural_recovery.py` | ACTIVE_REFERENCED | historical intelligence | 1 |
| `transmission_layers/intelligence/tier4/structural_rigidity.py` | ACTIVE_REFERENCED | historical intelligence | 1 |
| `transmission_layers/intelligence/tier4/systemic_cascades.py` | ACTIVE_REFERENCED | historical intelligence | 1 |
| `transmission_layers/intelligence/tier4/transition_explanations.py` | ACTIVE_REFERENCED | historical intelligence | 1 |
| `transmission_layers/intelligence/tier5/__init__.py` | ACTIVE_REFERENCED | historical intelligence | 4 |
| `transmission_layers/intelligence/tier5/cross_system_transmission.py` | ACTIVE_REFERENCED | historical intelligence | 2 |
| `transmission_layers/intelligence/tier5/distributed_survivability.py` | ACTIVE_REFERENCED | historical intelligence | 4 |
| `transmission_layers/intelligence/tier5/federation_bottlenecks.py` | ACTIVE_REFERENCED | historical intelligence | 2 |
| `transmission_layers/intelligence/tier5/federation_boundaries.py` | ACTIVE_REFERENCED | historical intelligence | 2 |
| `transmission_layers/intelligence/tier5/federation_bridges.py` | ACTIVE_REFERENCED | historical intelligence | 2 |
| `transmission_layers/intelligence/tier5/federation_explanations.py` | ACTIVE_REFERENCED | historical intelligence | 2 |
| `transmission_layers/intelligence/tier5/federation_recovery_dependencies.py` | ACTIVE_REFERENCED | historical intelligence | 2 |
| `transmission_layers/intelligence/tier5/federation_signatures.py` | ACTIVE_REFERENCED | historical intelligence | 2 |
| `transmission_layers/intelligence/tier5/federation_stabilization_report.py` | ACTIVE_REFERENCED | historical intelligence | 2 |
| `transmission_layers/intelligence/tier5/federation_topology.py` | ACTIVE_REFERENCED | historical intelligence | 2 |
| `transmission_layers/intelligence/tier5/inter_system_contagion.py` | ACTIVE_REFERENCED | historical intelligence | 4 |
| `transmission_layers/intelligence/tier6/__init__.py` | ACTIVE_REFERENCED | historical intelligence | 9 |
| `transmission_layers/intelligence/tier7/__init__.py` | ACTIVE_REFERENCED | historical intelligence | 9 |
| `transmission_layers/live_ops/__init__.py` | ACTIVE_REFERENCED | current SEFI core | 1 |

## CLEAN-3 Recommendation

CLEAN-3 should **not** proceed with archival yet because CLEAN-2B found no exact safe archive scope.

Blockers:
- Queue A is empty after applying CLEAN-2B safety filters; no exact files qualify for archive.
- 51 UNKNOWN_REQUIRES_REVIEW files need manual review or protection decisions.
- 27 CLEAN-2 unreferenced candidates were excluded by package, current-core, graph-boundary, or active dataflow-map safeguards.

## Token-Reduction Impact Estimate

- Safe archive candidates: 0
- Estimated files reducible in CLEAN-3: 0
- Estimated token reduction: none
- Note: CLEAN-2B intentionally narrows CLEAN-2 to exact safe files only; excluded legacy boundaries may still reduce review tokens after manual decisions, but are not archive-ready now.
