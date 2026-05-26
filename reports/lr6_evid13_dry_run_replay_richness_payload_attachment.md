# LR6-EVID13 — Dry-Run Replay Richness Payload Attachment

## objective
- Attach validated LR6-EVID11 replay_richness payload builder to dry-run replay observation artifact path only.

## inspected EVID11/EVID12 builder and harness
- lr6_evid11_first_real_replay_richness_payload_builder.py
- lr6_evid12_real_replay_richness_payload_validation_harness.py

## inspected dry-run replay observation paths
- lr6_obs7_dry_run_enriched_replay_observation_simulation.py
- lr6_obs9_execution_review_framework.py
- lr6_exec2_first_dry_run_execution_review.py

## attachment targets
- [{'attachment_target': 'lr6_obs7_simulated_wave_manifest', 'source_module': 'lr6_obs7_dry_run_enriched_replay_observation_simulation', 'artifact_shape': 'structured_replay_observation_manifest', 'supports_structured_fields': True, 'source_artifact_refs': ['module://lr6_obs7_dry_run_enriched_replay_observation_simulation', 'artifact://simulated_wave_manifest'], 'notes': 'Primary dry-run replay observation shape for structured replay richness counts.'}]

## structured artifact adapter
- {'replay_entity_count': None, 'distinct_candidate_count': None, 'distinct_role_count': None, 'distinct_cluster_count': None, 'source_artifact_refs': [], 'measurement_basis': 'narrative_only', 'scaffold_only': False, 'before_after_comparison': None, 'dry_run': True}

## dry-run emission preview
- {'attachment_target': 'lr6_obs7_simulated_wave_manifest', 'source_artifact_refs': ['artifact://obs7/sample'], 'extracted_structured_fields': {'replay_entity_count': 12, 'distinct_candidate_count': 12, 'distinct_role_count': 5, 'distinct_cluster_count': 4, 'source_artifact_refs': ['artifact://obs7/sample'], 'measurement_basis': 'structured_observation', 'scaffold_only': False, 'before_after_comparison': None, 'dry_run': True}, 'replay_richness_payload': {'metric_dimension': 'replay_richness', 'replay_entity_count': 12, 'distinct_candidate_count': 12, 'distinct_role_count': 5, 'distinct_cluster_count': 4, 'source_artifact_refs': ['artifact://obs7/sample'], 'measurement_basis': 'structured_observation', 'scaffold_only': False, 'comparison_ready': False, 'evidence_status': 'MEASURED', 'richness_score': 0.875, 'diversity_ratio': 0.75, 'concentration_warning': False}, 'evid6_compatible_emission_candidate': {'metric_target': 'replay_richness', 'input_payload': {'metric_dimension': 'replay_richness', 'replay_entity_count': 12, 'distinct_candidate_count': 12, 'distinct_role_count': 5, 'distinct_cluster_count': 4, 'source_artifact_refs': ['artifact://obs7/sample'], 'measurement_basis': 'structured_observation', 'scaffold_only': False, 'comparison_ready': False, 'evidence_status': 'MEASURED', 'richness_score': 0.875, 'diversity_ratio': 0.75, 'concentration_warning': False}, 'evid6_record': {'evidence_record_id': 'BASELINE:replay_richness:LR6_EVID11_SCOPE:LR6_EVID11_IN_MEMORY_WAVE', 'replay_phase': 'BASELINE', 'wave_id': 'LR6_EVID11_IN_MEMORY_WAVE', 'candidate_scope_id': 'LR6_EVID11_SCOPE', 'candidate_count': 12, 'timestamp_or_snapshot_label': 'LR6_EVID11_T0', 'metric_dimension': 'replay_richness', 'measured_fields': {'replay_entity_count': 12, 'distinct_role_count': 5, 'distinct_cluster_count': 4, 'novel_bridge_count': 0, 'richness_score': 0.875}, 'evidence_status': 'MEASURED', 'source_artifact': 'lr6_evid11_replay_richness_payload_builder', 'source_module': 'lr6_evid11_first_real_replay_richness_payload_builder', 'comparison_ready': True, 'scaffold_only': False, 'notes': 'coverage=5/5; invalid_fields=[]'}, 'evid6_contract_compatible': True}, 'emission_status': 'READY_DRY_RUN', 'dry_run_only': True, 'persisted': False, 'live_ingestion': False, 'governed_activation': False, 'dry_run_caveat': 'Preview-only attachment; no replay execution, persistence, ingestion, or governed activation.'}

## scaffold/narrative rejection behavior
- Scaffold-only and narrative-only artifacts are downgraded and never promoted to MEASURED.

## EVID6 compatibility
- EVID6-compatible emission candidate is generated via LR6-EVID11 candidate helper with no hook contract changes.

## attachment safety review
- {'dry_run_attachment_must_never_persist': True, 'dry_run_attachment_must_never_call_live_ingestion': True, 'dry_run_attachment_must_never_execute_replay': True, 'dry_run_attachment_must_never_authorize_governed_activation': True, 'comparison_ready_requires_explicit_baseline_fields': True, 'scaffold_or_narrative_must_not_be_measured': True, 'missing_lineage_must_not_remain_measured': True, 'no_evid6_contract_change': True}

## boundary certification
- {'dry_run_only': True, 'attachment_only': True, 'in_memory_only': True, 'evidence_only': True, 'execution_authorized': False, 'persistence_authorized': False, 'live_ingestion_authorized': False, 'governed_activation_authorized': False, 'metric_target': 'replay_richness', 'all_seven_metrics_implemented': False, 'no_prediction': True, 'no_trading': True, 'no_direct_sql': True, 'no_live_ingestion': True, 'no_persistence_write': True, 'no_governed_activation': True, 'no_interpretation_claims': True, 'architecture_expansion_frozen': True}

## recommendation for next step
- Wire this dry-run preview into the actual replay observation rendering path while preserving dry-run-only and non-persistence controls.
