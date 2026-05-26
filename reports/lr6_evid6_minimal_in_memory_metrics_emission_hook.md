# LR6-EVID6 Minimal In-Memory Metrics Emission Hook
## objective
Implement a deterministic in-memory emission hook that returns evidence records from explicit metric fields only.
## EVID5 basis
{'evid5_design': 'minimal replay-time measurable metrics emission hook', 'target': 'emit EVID2/EVID3-compatible evidence records from explicit metric payload fields only'}
## hook signature
emit_lr6_replay_metric_evidence(*, replay_phase, wave_id, candidate_scope_id, candidate_count, timestamp_or_snapshot_label, replay_observation_payload, candidate_metadata=None, baseline_reference_payload=None, source_artifact='in_memory_replay_observation_payload', source_module='lr6_evid6_minimal_in_memory_metrics_emission_hook') -> list[dict]
## supported metric dimensions
['weak_signal_attribution', 'contradiction_persistence_migration', 'propagation_diversity', 'topology_drift', 'replay_saturation_monoculture', 'megacap_semantic_gravity', 'replay_richness']
## required field contract
{'weak_signal_attribution': ['weak_signal_attribution_count', 'weak_signal_candidate_count', 'weak_signal_attribution_ratio', 'weak_signal_entities_observed', 'weak_signal_entities_missing'], 'contradiction_persistence_migration': ['contradiction_cluster_count', 'persistent_contradiction_count', 'migrated_contradiction_count', 'cross_cluster_contradiction_count', 'contradiction_persistence_ratio'], 'propagation_diversity': ['propagation_bridge_count', 'distinct_propagation_role_count', 'non_obvious_bridge_count', 'cross_cluster_bridge_count', 'propagation_diversity_score'], 'topology_drift': ['topology_drift_indicator', 'new_bridge_count', 'disappeared_bridge_count', 'changed_bridge_count', 'topology_drift_score'], 'replay_saturation_monoculture': ['saturation_score', 'concentration_score', 'dominant_theme_share', 'repeated_entity_share', 'diversity_gain_indicator'], 'megacap_semantic_gravity': ['megacap_attribution_count', 'total_attribution_count', 'megacap_concentration_ratio', 'non_megacap_bridge_count', 'megacap_gravity_status'], 'replay_richness': ['replay_entity_count', 'distinct_role_count', 'distinct_cluster_count', 'novel_bridge_count', 'richness_score']}
## extraction rules
['payload["metrics"][metric_dimension]', 'payload[metric_dimension]', 'payload["measured_fields"][metric_dimension]']
## status rules
MEASURED when all required fields are valid; PARTIAL when some are valid; MISSING when none are valid; SCAFFOLD_ONLY when scaffold markers exist with no measurable fields; NOT_COMPARABLE when identifiers/phase/count fail comparability constraints.
## validation rules
['counts must be non-negative integers', 'ratio/share/score fields must be in [0,1]', 'replay_phase must be BASELINE or ENRICHED', 'candidate_count must be non-negative integer', 'required identifiers must be non-empty strings']
## scaffold detection
['approval_gate', 'dry_run', 'execution_authorized', 'expected_artifacts', 'final_decision', 'governance_review', 'review_sections', 'supervisor_review']
## EVID3 compatibility
Records carry EVID2/EVID3-compatible fields and statuses with deterministic key coverage.
## boundary certification
{'hook_only': True, 'in_memory_only': True, 'evidence_only': True, 'execution_authorized': False, 'no_prediction': True, 'no_trading': True, 'no_direct_sql': True, 'no_live_ingestion': True, 'no_persistence_write': True, 'no_governed_activation': True, 'no_interpretation_claims': True, 'architecture_expansion_frozen': True}
## recommendation for next step
Invoke this hook from replay execution output only after observed metric fields are explicitly populated.