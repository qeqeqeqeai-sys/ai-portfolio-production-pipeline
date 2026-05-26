# LR6-EVID11 First Real Replay Richness Payload Builder
## objective
Build first deterministic in-memory replay_richness payload builder from structured artifacts only.
## inspected prior EVID9/EVID10 design
['lr6_evid9_real_replay_metric_payload_production_plan.py', 'lr6_evid10_first_real_replay_metric_payload_emission_design.py', 'lr6_evid6_minimal_in_memory_metrics_emission_hook.py']
## structured source artifact assumptions
['required counts are structured integers >= 0', 'source_artifact_refs carries explicit lineage references', 'measurement_basis differentiates structured evidence from narrative_only']
## payload extraction logic
{'replay_entity_count': None, 'distinct_candidate_count': None, 'distinct_role_count': None, 'distinct_cluster_count': None, 'source_artifact_refs': [], 'measurement_basis': 'narrative_only', 'scaffold_only': False, 'baseline_comparison_present': False, 'narrative_text_present': False}
## validation logic
missing/non-integer/negative counts downgrade status; scaffold_only and narrative_only cannot be MEASURED
## scaffold/narrative rejection logic
scaffold_only=True or measurement_basis=narrative_only blocks MEASURED
## EVID6 compatibility
local deterministic mapping to EVID6 replay_richness required fields without hook contract changes
## sample valid in-memory payload
{'metric_dimension': 'replay_richness', 'replay_entity_count': 10, 'distinct_candidate_count': 6, 'distinct_role_count': 4, 'distinct_cluster_count': 3, 'source_artifact_refs': ['artifact://sample'], 'measurement_basis': 'observed_structured_fields', 'scaffold_only': False, 'comparison_ready': False, 'evidence_status': 'MEASURED', 'richness_score': 0.65, 'diversity_ratio': 0.7, 'concentration_warning': False}
## sample rejected scaffold payload
{'metric_dimension': 'replay_richness', 'replay_entity_count': 10, 'distinct_candidate_count': 6, 'distinct_role_count': 4, 'distinct_cluster_count': 3, 'source_artifact_refs': ['artifact://sample'], 'measurement_basis': 'observed_structured_fields', 'scaffold_only': True, 'comparison_ready': False, 'evidence_status': 'SCAFFOLD_ONLY', 'richness_score': 0.65, 'diversity_ratio': 0.7, 'concentration_warning': False}
## boundary certification
{'planning_only': False, 'builder_only': True, 'evidence_only': True, 'in_memory_only': True, 'execution_authorized': False, 'persistence_authorized': False, 'live_ingestion_authorized': False, 'governed_activation_authorized': False, 'metric_target': 'replay_richness', 'all_seven_metrics_implemented': False, 'no_prediction': True, 'no_trading': True, 'no_direct_sql': True, 'no_live_ingestion': True, 'no_persistence_write': True, 'no_governed_activation': True, 'no_interpretation_claims': True, 'architecture_expansion_frozen': True}
## recommendation for next step
Wire this builder to real replay observation artifact producers, then call EVID6 emission hook in-memory only.
