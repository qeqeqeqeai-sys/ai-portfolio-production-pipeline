# LR6-EVID8 Synthetic Measured Payload Validation

## objective
Validate mechanical correctness of the LR6-EVID6/LR6-EVID7 evidence emission path using synthetic payloads only, specifically whether explicit required metric fields produce MEASURED records without introducing execution, ingestion, persistence, or claim expansion.

## EVID6/EVID7 basis
- EVID6 defines the deterministic in-memory hook and status logic across seven metric dimensions.
- EVID7 dry-run integration confirms scaffold-only emission when no measurable fields are supplied.
- Prior known dry-run posture remains: seven records, all SCAFFOLD_ONLY, zero MEASURED, zero PARTIAL, non-empirical.

## synthetic full-measurement payload validation
Method:
- Constructed synthetic payload containing all required fields for each of the seven metric dimensions.
- Used valid comparability identifiers (`replay_phase=ENRICHED`, non-empty `wave_id`, `candidate_scope_id`, and timestamp label).

Result:
- Exactly seven records emitted.
- All seven records emitted as MEASURED.
- All seven records emitted with `comparison_ready=True`.
- All records had `scaffold_only=False`.
- Each record’s `measured_fields` included the full required contract for its dimension.
- EVID3 compatibility keys were present across the record set.
- Emission remained deterministic under repeated invocation.

## synthetic partial payload validation
Method:
- Constructed synthetic payload where each dimension includes only a subset of required fields.

Result:
- Exactly seven records emitted.
- All records emitted as PARTIAL.
- All records emitted with `comparison_ready=False`.
- All records had `scaffold_only=False`.
- Behavior is conservative and contract-driven.

## invalid payload validation
Method:
- Constructed synthetic payload containing invalid count/ratio/bool/string values.
- Also used invalid comparability identifiers (`replay_phase=INVALID_PHASE`, empty `wave_id`, empty `candidate_scope_id`).

Result:
- No crash.
- Exactly seven records emitted.
- No false MEASURED status emitted.
- Records downgraded to NOT_COMPARABLE due to invalid comparability envelope.
- Invalid metric fields were excluded from `measured_fields` where field validation failed.
- `comparison_ready=False` for all records under invalid identifiers/phase.

## EVID3 compatibility result
- Required evidence record keys are present for the synthetic full-measurement output.
- Record count and key contract remain EVID2/EVID3-compatible.

## realism warning
Synthetic MEASURED records in this phase are:
- synthetic
- non-empirical
- not replay evidence
- not evidence of ecological improvement
- not suitable for EVID1 improvement claims

## boundary confirmation
Synthetic validation remains within boundary:
- no replay execution
- no live ingestion
- no persistence writes
- no SQL path
- no prediction/trading path
- no governance expansion
- no interpretation-claim expansion

## recommendation for next step
Proceed to the next bounded phase only when governed real observation artifacts are available. Until then, treat EVID8 as mechanical contract validation, not empirical performance evidence.

## synthetic labeling markers used
- `synthetic_validation=True`
- `empirical_evidence=False`
- `replay_execution_performed=False`
- `improvement_claim_authorized=False`
