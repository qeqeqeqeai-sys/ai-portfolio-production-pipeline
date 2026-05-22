# Dashboard O4 Streamlit Dashboard Report

## Objective
Deliver a deterministic, read-only Streamlit dashboard shell for institutional expectation-fragility visibility using Dashboard O1/O2/O3-compatible payloads.

## Scope
- Added O4 deterministic view-model transformation module.
- Added thin Streamlit UI renderer with eight tabs.
- Added O4 test coverage for deterministic behavior and safety boundaries.

## Non-goals
- No trading recommendations.
- No target prices.
- No portfolio allocation.
- No backtesting or predictive modelling.
- No database writes or network orchestration.

## Streamlit architecture
- `apps/streamlit_expectation_failure_dashboard.py` provides rendering only.
- App delegates all transformation logic to O4 view-model module.
- App uses local sample payload fallback without DB clients.

## View-model boundary
- `dashboard_o4_streamlit_view_model.py` normalizes input groups into deterministic list-of-dict tables, KPI cards, filters, page registry, certification panel, and UI manifest.
- No Streamlit dependency in view-model module.

## Read-only dashboard guarantees
- Explicit invariant flags in view model.
- Page registry includes forbidden interactions.
- Certification panel surfaces O2/O3 validation context without mutating data.

## Page inventory
1. Executive Fragility Overview
2. Entity Fragility Table
3. Subsector Concentration
4. Alert Monitoring
5. Benchmark-Relative Outliers
6. Replay Timeline
7. Evidence Audit Appendix
8. Report / Export Certification

## Table/source mapping
- `entity_table` ← `dashboard_entity_facts`
- `subsector_table` ← `dashboard_subsector_facts`
- `alert_table` ← `dashboard_alert_facts`
- `benchmark_table` ← `dashboard_benchmark_facts`
- `replay_table` ← `dashboard_replay_facts`
- `evidence_table` ← `dashboard_evidence_facts`

## Filter inventory
- run_id
- run_date_sgt
- subsector
- alert_state
- benchmark_id
- certification_status
- evidence_quality_flag

## KPI inventory
- total_entities
- fragile_entity_count
- active_alert_count
- fragile_subsector_count
- benchmark_outlier_count
- evidence_quality_issue_count
- certification_status
- latest_run_id

## Deterministic guarantees
- Ordered top-level view-model keys.
- Stable page order and deterministic sorting in tables.
- Stable UI manifest checksum.
- Input deepcopy protection for immutable safety.

## Safety boundaries
- No database writes in O4 logic.
- No network calls in O4 logic.
- No file writes from core O4 module.
- Forbidden trading/recommendation language validation gate.

## Implementation limitations
- O4 app currently uses local sample payload fallback instead of production ingestion wiring.
- O4 filtering interactions are represented in metadata and table rendering, not full interactive query engines.

## Next recommended phase
Implement controlled payload loader integration for production run artifacts while preserving current deterministic/read-only boundaries.
