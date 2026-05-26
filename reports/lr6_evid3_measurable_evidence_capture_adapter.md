# LR6-EVID3 Measurable Evidence Capture Adapter

## objective
Implement the smallest deterministic evidence adapter that converts existing replay/output payloads into LR6-EVID2-style evidence records.

## EVID1/EVID1A/EVID2 basis
- EVID1 outcome: BASELINE_OR_ENRICHED_EVIDENCE_MISSING.
- EVID1A outcome: RUN1_SCAFFOLD_ONLY with all seven metrics blocked.
- EVID2 basis: explicit minimum measurable fields per metric dimension.

## supported payload contracts
- baseline replay payload
- enriched replay payload
- RUN1 review artifact payload
- EXP6/EXP6A snapshot payload
- EXP7 interestingness payload
- EXP8 findings payload

## evidence record output structure
- evidence_record_id
- replay_phase
- wave_id
- candidate_scope_id
- candidate_count
- timestamp_or_snapshot_label
- metric_dimension
- measured_fields
- evidence_status
- source_artifact
- source_module
- comparison_ready
- scaffold_only
- notes

## metric extractors
All seven EVID1 dimensions have deterministic extractors keyed to EVID2 required fields:
1. weak_signal_attribution
2. contradiction_persistence_migration
3. propagation_diversity
4. topology_drift
5. replay_saturation_monoculture
6. megacap_semantic_gravity
7. replay_richness

Status policy:
- MEASURED: all required fields present
- PARTIAL: some required fields present
- MISSING: no required fields present
- SCAFFOLD_ONLY: review/governance/text-only without measurable fields
- NOT_COMPARABLE: reserved status (explicitly supported in status vocabulary)

## scaffold-only detection
Payloads are scaffold-only when they present review/governance/expected-artifact/narrative structure but no measurable metric fields.

Scaffold-only records are forced to:
- scaffold_only=True
- comparison_ready=False
- evidence_status=SCAFFOLD_ONLY

## comparison readiness rules
A record is comparison-ready only when:
- evidence_status is MEASURED
- scaffold_only is False
- replay_phase is BASELINE or ENRICHED
- candidate_scope_id exists
- wave_id or timestamp_or_snapshot_label exists

## EVID1-ready payload format
The adapter prepares grouped payloads for EVID1 with:
- baseline_records
- enriched_records
- paired_dimensions
- blocked_dimensions
- missing_baseline_dimensions
- missing_enriched_dimensions
- scaffold_only_dimensions
- comparison_ready_dimensions

## quality report behavior
- extraction_quality_report: deterministic status counts and totals
- comparison_readiness_report: deterministic counts and ready dimensions

## boundary certification
The adapter certifies:
- adapter_only=True
- evidence_only=True
- execution_authorized=False
- no_prediction=True
- no_trading=True
- no_direct_sql=True
- no_live_ingestion=True
- no_persistence_write=True
- no_governed_activation=True
- no_interpretation_claims=True
- architecture_expansion_frozen=True

## recommendation for next step
Run LR6-EVID1 delta population exclusively on comparison-ready baseline/enriched evidence records and maintain strict scaffold-only blocking.
