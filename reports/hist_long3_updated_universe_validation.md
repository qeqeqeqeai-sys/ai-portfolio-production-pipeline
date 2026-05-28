# HIST-LONG-3 — Updated Universe Real Validation Window

## Validation Status
- Status: `blocked_provider_credentials_missing_or_execution_failed`
- Validation status: `blocked_real_execution_failed`
- Execution error: `RuntimeError: FMP_API_KEY missing; OPS-HIST-1 fails closed`

## Updated Universe Checks
- foxa_count: `1`
- foxa_present_exactly_once: `true`
- para_count: `0`
- para_absent: `true`
- duplicate_symbol_count: `0`
- duplicate_symbols: `[]`
- no_duplicate_symbols: `true`
- chunk_count: `5`
- expected_chunk_count: `5`
- expected_chunk_count_remains_5: `true`
- chunk_sizes: `[50, 50, 50, 50, 41]`
- effective_symbol_count: `241`

## Ingestion Metrics
- Normalized rows: 0
- Normalization completeness: None
- Partial count: 0
- Failed count: 0
- Exact date matches: 0
- Reconciled prior dates: 0
- Endpoint failures: `{}`
- Top failure reasons: `[]`
- Weak symbols: `[]`

## FOXA Validation
- status: `"not_validated_execution_blocked"`
- historical_price_coverage: `"not_measured_in_completed_window"`
- profile_coverage: `"not_measured_in_completed_window"`
- missing_date_behavior: `"not_measured_in_completed_window"`
- endpoint_failures: `[]`
- profile_failure_reasons: `{}`
- ops_hist_snapshot_count: `0`
- replacement_suitability_assessment: `"FOXA suitability remains unproven until a completed real 20-day window runs with provider credentials"`

## Comparison vs Original PARA Baseline
- Original baseline: `{"failed_count_total": 20, "normalized_count_total": 4700, "partial_count_total": 20, "provider_failures": {"HTTP_403": 20, "zero_records_returned": 20}, "weak_symbols": ["PARA"]}`
- did_weak_symbol_disappear: `null`
- did_provider_degradation_improve: `null`
- did_completeness_improve: `null`
- did_any_new_weak_symbols_emerge: `null`
- current_provider_failure_total: `0`
- baseline_provider_failure_total: `40`
- assessment: `"comparison_pending_completed_real_window"`

## Governance Certification
- Observational only: True
- Prediction enabled: False
- Trading execution enabled: False
- Replay activation enabled: False
- Replay execution enabled: False
- Topology persistence enabled: False
- Supabase writes enabled: False
- Raw cache writes enabled: False

## HIST-LONG-4 Gate
- HIST-LONG-4 justified: False
