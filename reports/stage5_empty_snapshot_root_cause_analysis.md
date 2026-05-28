# Stage 5 Empty Snapshot Root Cause Analysis (OPS-HIST-1)

## Root-cause path
The empty-snapshot collapse occurred upstream of terminal failure attribution in the Stage 5 fail-closed branch. After symbol-level isolation, rows could still collapse to zero through fetch-level emptiness and pre-normalization filtering, while `top_normalization_failure_reasons` remained empty because it is derived from raw row field-missing checks and not from upstream fetch/reconciliation outcomes.

## Collapse stage identified
For observed failure mode (`empty normalized snapshot for 2026-05-01; reasons=[]`), collapse can occur at:
1. fetch stage (zero returned rows),
2. pre-normalization stage (all rows invalid),
3. normalization stage (retained set collapses to zero).

New bounded telemetry now emits deterministic stage counters and flags:
- `fetched_row_count`
- `pre_normalization_row_count`
- `reconciliation_retained_row_count`
- `normalization_retained_row_count`
- `final_preserved_symbol_count`
- `empty_snapshot_stage`
- `fetch_empty_response_detected`
- `reconciliation_full_filter_detected`
- `normalization_full_filter_detected`

## Why `reasons=[]` happened
`reasons=[]` was caused by attribution mismatch between:
- fail-closed trigger source (empty normalized snapshot), and
- reason extraction source (`top_normalization_failure_reasons`, derived from raw row content only).

If fetch returned no rows, raw-row failure extraction had no candidates, so reason list remained empty.

## Reconciliation findings
The system now classifies unavailable-date reconciliation exhaustion as `unavailable_trading_day` with `empty_snapshot_stage=reconciliation` when endpoint attempts indicate `missing_reconciled_historical_date` only.

## Provider behavior findings
Bounded empty-cause classes now differentiate:
- `provider_empty_response`
- `empty_batch_fetch`
- `upstream_fetch_failure`
- `malformed_provider_payload`
- `unsupported_schema`
- `reconciliation_mismatch` (via reconciliation-stage diagnostics)
- `all_symbols_filtered_pre_normalization`
- `all_symbols_failed_normalization`
- `unavailable_trading_day`

## Governance confirmation
No governance weakening introduced:
- no replay execution
- no topology activation
- no cognition persistence
- no cache-write policy expansion
- deterministic fail-closed behavior preserved

## Safe remediation
- Preserve fail-closed on zero preserved symbols.
- Classify empty cause before raising terminal error.
- Populate reason fallback with classification when normalization reasons are absent.
- Keep bounded deterministic telemetry only.

## Readiness for Stage 5 rerun
Ready for controlled rerun with improved attribution and stage telemetry. Fail-closed safety gates remain strict; diagnostics now expose exact collapse stage and class for rapid operator triage.
