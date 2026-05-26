# LR6-LIVE6 — Post-Persistence Verification & Wave Consistency Audit

## audit summary
- {'rows_exist': True, 'row_count': 5, 'row_count_matches_expected': True, 'created_at_present': True, 'created_at_iso_parseable': True, 'replay_richness_only': True, 'metric_dimension_consistent': True, 'evidence_status_consistent': True}

## duplicate prevention findings
- {'keys': ['LR6_LIVE5_WAVE_001|LIVE5_E1|replay_richness|W0', 'LR6_LIVE5_WAVE_001|LIVE5_E2|replay_richness|W0', 'LR6_LIVE5_WAVE_001|LIVE5_E3|replay_richness|W0', 'LR6_LIVE5_WAVE_001|LIVE5_E4|replay_richness|W0', 'LR6_LIVE5_WAVE_001|LIVE5_E5|replay_richness|W0'], 'keys_present': True, 'keys_unique': True, 'keys_deterministic_sorted': True, 'simulated_rerun_duplicate_blocked': True, 'overwrite_semantics_detected': False}

## wave consistency findings
- {'wave_ids': ['LR6_LIVE5_WAVE_1FB274FE8C0A', 'LR6_LIVE5_WAVE_62418FB64AB0', 'LR6_LIVE5_WAVE_1FB274FE8C0A', 'LR6_LIVE5_WAVE_62418FB64AB0', 'LR6_LIVE5_WAVE_1FB274FE8C0A'], 'unique_wave_ids': ['LR6_LIVE5_WAVE_1FB274FE8C0A', 'LR6_LIVE5_WAVE_62418FB64AB0'], 'wave_id_count': 2, 'semantics_classification': 'row_level_fallback_wave_id', 'duplicate_key_wave_prefixes': ['LR6_LIVE5_WAVE_001', 'LR6_LIVE5_WAVE_001', 'LR6_LIVE5_WAVE_001', 'LR6_LIVE5_WAVE_001', 'LR6_LIVE5_WAVE_001'], 'normalization_required_before_live7': True, 'severity': 'moderate', 'recommended_shared_wave_strategy': 'derive single deterministic batch wave_id from governed batch scope (e.g., wave_scope) and propagate to all rows; do not rewrite existing rows'}

## lineage/rollback findings
- {'lineage_metadata_present': True, 'rollback_metadata_present': True, 'source_artifact_refs_integrity': True, 'null_lineage_fields_detected': False, 'auditability_quality': 'strong'}

## readback findings
- {'retrieval_safe': True, 'ordering_consistent': True, 'ordered_row_count': 5, 'evidence_summaries': [{'entity_id': 'LIVE5_E1', 'wave_id': 'LR6_LIVE5_WAVE_1FB274FE8C0A', 'duplicate_prevention_key': 'LR6_LIVE5_WAVE_001|LIVE5_E1|replay_richness|W0', 'richness_score': 0.2}, {'entity_id': 'LIVE5_E2', 'wave_id': 'LR6_LIVE5_WAVE_62418FB64AB0', 'duplicate_prevention_key': 'LR6_LIVE5_WAVE_001|LIVE5_E2|replay_richness|W0', 'richness_score': 0.4}, {'entity_id': 'LIVE5_E3', 'wave_id': 'LR6_LIVE5_WAVE_1FB274FE8C0A', 'duplicate_prevention_key': 'LR6_LIVE5_WAVE_001|LIVE5_E3|replay_richness|W0', 'richness_score': 0.6000000000000001}, {'entity_id': 'LIVE5_E4', 'wave_id': 'LR6_LIVE5_WAVE_62418FB64AB0', 'duplicate_prevention_key': 'LR6_LIVE5_WAVE_001|LIVE5_E4|replay_richness|W0', 'richness_score': 0.8}, {'entity_id': 'LIVE5_E5', 'wave_id': 'LR6_LIVE5_WAVE_1FB274FE8C0A', 'duplicate_prevention_key': 'LR6_LIVE5_WAVE_001|LIVE5_E5|replay_richness|W0', 'richness_score': 1.0}]}

## append-only verification findings
- {'adapter_name_consistent': True, 'execution_mode_consistent': True, 'update_delete_upsert_used': False, 'direct_sql_used': False, 'append_only_semantics_preserved': True}

## governance/boundary findings
- {'topology_metrics_persisted': False, 'contradiction_migration_persisted': False, 'forbidden_metric_detected': False, 'direct_sql_paths_introduced': False, 'update_delete_upsert_semantics_introduced': False, 'prediction_logic_enabled': False, 'trading_logic_enabled': False, 'scaling_enabled': False, 'max_5_boundedness_preserved': True}

## recommendation for LIVE7 or remediation phase
- remediate_to_deterministic_shared_batch_wave_id_before_live7; do_not_rewrite_live5_rows

## boundary certification
- {'verification_audit_only': True, 'scaling_authorized': False, 'new_metrics_enabled': False, 'topology_drift_enabled': False, 'contradiction_persistence_migration_enabled': False, 'prediction_enabled': False, 'trading_enabled': False, 'schema_expansion_enabled': False, 'direct_sql_bypass_enabled': False, 'append_only_required': True, 'replay_richness_only': True, 'max_5_bounded': True}

