# HIST-DENSITY-4 — First 241-Symbol Historical Ecology Findings Review

## Scope Certification
- Review mode: observational_only
- Data scope: local_artifact_report_analysis_only
- New ingestion enabled: False
- Replay activation enabled: False
- Trading execution enabled: False
- Supabase writes enabled: False
- Topology persistence enabled: False

## Source Artifacts Inspected
- Source root: `temp/hist-density3-curated-241-reports.zip`
- Source mode: `completed_artifact_bundle`
- Source status: `ok`
- Completed telemetry mode: True
- Parsed chunk manifests: 5
- Parsed OPS-HIST snapshots: 100
- OPS-HIST markdown inventory count: 7

## Ingestion Quality Summary
- Chunk count: 5
- Effective symbol count: 241
- Configured symbol count: 241
- Trading days: 20
- Estimated symbol-date rows: 4820
- Requested symbol-date capacity total: 4820
- Normalized count total: 4700
- Partial count total: 20
- Failed count total: 20
- Exact date matches total: 4465
- Reconciled prior dates total: 235
- Missing dates total: 20
- Endpoint failures: `{"HTTP_403": 40, "zero_records_returned": 40}`
- Affected symbols/dates: 1 symbols across 20 dates
- Top failure reasons: `[{"count": 40, "reason": "HTTP_403"}, {"count": 40, "reason": "zero_records_returned"}]`
- Missing-date patterns: Missing-date samples cluster by weak symbols listed in weak_symbol_review.

## Chunk Quality Rows
- Chunk 1: symbols=50, normalized=980/1000, partial=0, failed=0, exact=931, reconciled=49, missing=0, affected_symbols=0, affected_dates=0, endpoint_status_counts={"stable_historical_price_eod_full": 980}, normalization_density=0.98
- Chunk 2: symbols=50, normalized=920/1000, partial=0, failed=0, exact=874, reconciled=46, missing=0, affected_symbols=0, affected_dates=0, endpoint_status_counts={"stable_historical_price_eod_full": 920}, normalization_density=0.92
- Chunk 3: symbols=50, normalized=1000/1000, partial=0, failed=0, exact=950, reconciled=50, missing=0, affected_symbols=0, affected_dates=0, endpoint_status_counts={"stable_historical_price_eod_full": 1000}, normalization_density=1.0
- Chunk 4: symbols=50, normalized=1000/1000, partial=0, failed=0, exact=950, reconciled=50, missing=0, affected_symbols=0, affected_dates=0, endpoint_status_counts={"stable_historical_price_eod_full": 1000}, normalization_density=1.0
- Chunk 5: symbols=41, normalized=800/820, partial=20, failed=20, exact=760, reconciled=40, missing=20, affected_symbols=1, affected_dates=20, endpoint_status_counts={"HTTP_403": 40, "stable_historical_price_eod_full": 800, "zero_records_returned": 40}, normalization_density=0.97561

## Weak Symbols
- PARA: missing_samples=20, endpoint_failure_samples=25, replacement_review_later=True, reasons=[{"count": 36, "reason": "zero_records_returned"}, {"count": 9, "reason": "HTTP_403"}]

## Operational Stability Assessment
- full_rollout_completed: True
- fail_closed_controls: did_not_collapse_run
- provider_degradation: isolated_to_weak_symbols
- telemetry_identified_weak_symbols: ['PARA']
- historical_market_cap_optionalization: behaved_as_intended
- ops_hist_ops_live_boundary: appears_stable_after_canonicalization_fixes

## First Ecology Findings
- replay_density_shifts: Density comparison is chunk-bounded; completed chunk telemetry supports direct spread observation.
- chunk_density_spread: 0.08
- sector_subsector_clustering: Review uses chunk-normalized telemetry plus SDE2 curation as the sector/subsector diversity frame.
- fragility_persistence: Weak-symbol persistence observed in bounded samples for PARA.
- contradiction_replay_recurrence: OPS-HIST recurrence/morphology/saturation report surfaces are present for descriptive recurrence review.
- topology_richness: OPS-HIST topology and morphology report surfaces indicate multi-layer descriptive topology richness.
- monoculture_risk: Chunk density concentration requires follow-up review.
- temporal_stability_across_20_days: 20-day realized telemetry is available for chunk-level stability review.
- ops_hist_surface_counts: {'topology_reports': 7, 'recurrence_reports': 4, 'morphology_reports': 2, 'saturation_reports': 1}

## Ecology Findings From OPS-HIST Snapshots
- Posture stability: stable_single_posture with counts {"pressure_building": 100}
- Sector HHI range: {"max": 0.846731, "min": 0.264}
- Normalization completeness range: {"max": 100.0, "min": 97.560976}
- Temporal stability over 20 days: observed max chunk date count 20
- Historical marketCap optionalization: historical marketCap degradation is treated as optional enrichment telemetry, not ingestion failure
- Chunk 1 ecology: dates=20, sector_hhi={"max": 0.846731, "min": 0.846731}, normalization={"max": 100.0, "min": 100.0}, structural_richness={"posture_variety": 1, "sector_transition_rows": 1}, preflight_failure_symbols=[]
- Chunk 2 ecology: dates=20, sector_hhi={"max": 0.407372, "min": 0.407372}, normalization={"max": 100.0, "min": 100.0}, structural_richness={"posture_variety": 1, "sector_transition_rows": 1}, preflight_failure_symbols=[]
- Chunk 3 ecology: dates=20, sector_hhi={"max": 0.3576, "min": 0.3576}, normalization={"max": 100.0, "min": 100.0}, structural_richness={"posture_variety": 1, "sector_transition_rows": 1}, preflight_failure_symbols=[]
- Chunk 4 ecology: dates=20, sector_hhi={"max": 0.264, "min": 0.264}, normalization={"max": 100.0, "min": 100.0}, structural_richness={"posture_variety": 1, "sector_transition_rows": 1}, preflight_failure_symbols=[]
- Chunk 5 ecology: dates=20, sector_hhi={"max": 0.41875, "min": 0.41875}, normalization={"max": 97.560976, "min": 97.560976}, structural_richness={"posture_variety": 1, "sector_transition_rows": 1}, preflight_failure_symbols=['PARA']

## Chunk Comparison
- richest_chunks: [{'chunk_index': 3, 'normalized_count': 1000, 'requested_symbol_date_capacity': 1000, 'normalization_density': 1.0}, {'chunk_index': 4, 'normalized_count': 1000, 'requested_symbol_date_capacity': 1000, 'normalization_density': 1.0}]
- weakest_chunks: [{'chunk_index': 5, 'normalized_count': 800, 'requested_symbol_date_capacity': 820, 'normalization_density': 0.97561, 'missing_dates': 20}, {'chunk_index': 2, 'normalized_count': 920, 'requested_symbol_date_capacity': 1000, 'normalization_density': 0.92, 'missing_dates': 0}]
- dominant_chunk: None
- deterministic_notes: ['chunk_03 and chunk_04 strongest: 1000 normalized rows each', 'chunk_01 acceptable: 980', 'chunk_02 weaker: 920', 'chunk_05 degraded but completed: 800/820, provider issue isolated to weak symbols']
- assessment: Chunk comparison is deterministic: normalized row count, density, missing-date burden, then chunk index.

## Recommended Next Phase
- Consider replacement or vendor-symbol investigation for PARA before longer backfills; otherwise proceed only with bounded observational operator review and no replay, prediction, trading, topology persistence, or Supabase writes.

## Governance Confirmation
- Observational only: certified.
- No new ingestion: certified.
- No replay activation: certified.
- No topology persistence: certified.
- No Supabase writes: certified.
- No trading execution: certified.
