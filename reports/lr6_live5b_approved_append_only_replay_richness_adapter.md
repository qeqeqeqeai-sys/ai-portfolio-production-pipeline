# LR6-LIVE5B Approved Append-Only Replay Richness Adapter

## objective
Implement the approved append-only persistence adapter for governed replay_richness writes to `replay_richness_wave0_shadow` with fail-closed safety.

## inspected LIVE5 workflow/runner
Inspected `scripts/run_lr6_live5_first_approved_non_dry_persistence_execution.py` and `transmission_layers/expectation_failure/replay_ecology/lr6_live5_first_approved_non_dry_persistence_execution_attempt.py`.

## approved adapter design
Adapter module: `replay_richness_wave0_shadow_append_only_adapter` under the replay ecology persistence adapter pattern.

## target restrictions
Only `replay_richness_wave0_shadow` is accepted.

## append-only semantics
Insert-only path; update/delete/upsert/direct SQL are refused.

## duplicate-prevention strategy
Deterministic `duplicate_prevention_key` required per intent; duplicate intents are deduplicated before insert.

## lineage requirements
`source_artifact_refs` and `lineage_metadata` are mandatory.

## rollback metadata requirements
`rollback_metadata` is mandatory per intent.

## schema/target fail-closed behavior
If schema confirmation is absent or target mismatches, adapter halts before any write.

## test-only fake client strategy
All tests inject fake table client objects; no real Supabase calls are made.

## GitHub workflow integration notes
Runner now uses approved adapter when available, still blocks on missing credentials/governance failure, and blocks on adapter safety failures.

## boundary certification
- adapter_only=True
- execution_not_run_by_tests=True
- approved_adapter_name="replay_richness_wave0_shadow_append_only_adapter"
- metric_target="replay_richness"
- approved_target="replay_richness_wave0_shadow"
- max_entities=5
- append_only_required=True
- direct_sql_used=False
- update_delete_upsert_allowed=False
- topology_metrics_enabled=False
- contradiction_migration_enabled=False
- prediction_enabled=False
- trading_enabled=False
- auto_expansion_enabled=False
- scaling_authorized=False

## recommendation for next step
Execute a separately approved schema-presence validation and then run the governed GitHub workflow in controlled non-test conditions.
