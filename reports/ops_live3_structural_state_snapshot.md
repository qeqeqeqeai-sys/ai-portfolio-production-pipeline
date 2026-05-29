# OPS-LIVE-3 Live Structural State Snapshot
## Objective
Synthesize accumulated live observation facts into a bounded ecosystem-state snapshot without ingestion, replay, prediction, trading, topology mutation, or fact emission.
## Source Behavior
- source_table: sefi_observation_facts
- source_behavior: bounded_local_fact_rows
- source_input_policy: fact-native sefi_observation_facts rows or bounded local fact rows only; markdown reports and large JSON artifacts are not source inputs.
## Inspected Fact Source Summary
- inspected_fact_count: 0
- metric_coverage_count: 0
- source_digest: 4f53cda18c2baa0c
- obs_query_row_count: 0
## Live Structural State Summary
- snapshot_status: INSUFFICIENT_DATA
- live_health_class: INSUFFICIENT_DATA
- ingestion_completeness_class: INSUFFICIENT_DATA
- provider_health_class: INSUFFICIENT_DATA
- weakness_pressure_class: INSUFFICIENT_DATA
- replay_pressure_class: INSUFFICIENT_DATA
- contradiction_pressure_class: INSUFFICIENT_DATA
- concentration_pressure_class: INSUFFICIENT_DATA
- entity_coverage_count: 0
- source_run_count: 0
- insufficient_data_count: 8
- latest_observed_at: None
## Dimension Classifications
- live_ingestion_completeness: class=INSUFFICIENT_DATA value=None
- live_provider_health: class=INSUFFICIENT_DATA value=None
- live_symbol_weakness: class=INSUFFICIENT_DATA value=None
- live_replay_density: class=INSUFFICIENT_DATA value=None
- live_replay_saturation: class=INSUFFICIENT_DATA value=None
- live_contradiction_burden: class=INSUFFICIENT_DATA value=None
- live_sector_concentration: class=INSUFFICIENT_DATA value=None
- live_subsector_concentration: class=INSUFFICIENT_DATA value=None
## Entity/Source Coverage
- entity_coverage_count: 0
- source_run_count: 0
## Insufficient-Data Review
- insufficient_data_count: 8
- snapshot_status: INSUFFICIENT_DATA
## Governance Review
- fmp_calls_enabled: False
- provider_api_calls_enabled: False
- live_ingestion_enabled: False
- replay_execution_enabled: False
- prediction_enabled: False
- trading_execution_enabled: False
- topology_persistence_enabled: False
- artifact_mutation_enabled: False
- fact_emission_enabled: False
- schema_changes_enabled: False
- destructive_database_operations_enabled: False
- core_supabase_client_creation_enabled: False
## Limitations
- This synthesis is bounded by available live observation facts and does not validate external market truth.
- Missing live metrics fail closed as INSUFFICIENT_DATA.
## Next-Step Recommendation
- Continue read-only monitoring of OPS-LIVE-2/live_* fact coverage before any future governed emission or persistence phase.
