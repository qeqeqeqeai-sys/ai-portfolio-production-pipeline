# LR6-EVID12 Real Replay Richness Payload Validation Harness

## objective
Validate LR6-EVID11 replay_richness payload behavior with deterministic in-memory scenarios to prevent unsafe evidence promotion.

## inspected EVID11 builder
- `transmission_layers/expectation_failure/replay_ecology/lr6_evid11_first_real_replay_richness_payload_builder.py`

## validation scenario matrix
- valid_structured_artifact
- partial_structured_artifact
- scaffold_only_artifact
- narrative_only_artifact
- malformed_counts_artifact
- missing_lineage_artifact
- dry_run_structured_artifact
- baseline_comparison_artifact
- baseline_missing_artifact

## status transition review
- structured -> MEASURED expected and validated.
- partial -> PARTIAL/NOT_COMPARABLE only.
- scaffold -> SCAFFOLD_ONLY/NOT_COMPARABLE only.
- narrative -> NOT_COMPARABLE only.
- malformed -> NOT_COMPARABLE/PARTIAL only.
- missing lineage -> PARTIAL/NOT_COMPARABLE only.
- baseline-present -> comparison_ready=True only when explicit comparison fields exist.

## rejection safety review
Unsafe promotion review checks:
- scaffold_only promoted to MEASURED
- narrative_only promoted to MEASURED
- malformed promoted to MEASURED
- missing_lineage promoted to MEASURED
- baseline_missing marked comparison_ready=True

## comparison readiness review
comparison_ready is constrained to explicitly comparative artifacts and remains false for baseline_missing.

## aggregate validation result
Harness computes deterministic totals for passed/failed scenario outcomes, status counts, unsafe promotion count, and comparison-ready count.

## unsafe promotion review
Critical safety rule: `unsafe_promotion_count == 0`.

## boundary certification
- validation_only=True
- in_memory_only=True
- evidence_only=True
- execution_authorized=False
- persistence_authorized=False
- live_ingestion_authorized=False
- governed_activation_authorized=False
- metric_target=replay_richness
- all_seven_metrics_implemented=False
- no_prediction=True
- no_trading=True
- no_direct_sql=True
- no_live_ingestion=True
- no_persistence_write=True
- no_governed_activation=True
- no_interpretation_claims=True
- architecture_expansion_frozen=True

## recommendation for next step
Keep this harness as a non-executing validation gate for LR6-EVID11 payload behavior; only consider governed wiring after explicit approval.
