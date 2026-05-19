# Tier 3H.5 Phase 4G — Governance BI Smoke Test Runbook

## Scope
Operational validation only: advisory-only governance, read-only exports, deterministic replayability, and exact-match-only behavior.

## Governance BI artifact inventory
Expected artifacts:
- Fact exports (`tier3h5_bi_governance_*_fact.json`, `tier3h5_bi_governance_summary_snapshot.json`)
- Dimension export (`tier3h5_bi_governance_dimensions.json`)
- Semantic and measure artifacts (`tier3h5_bi_semantic_layer.json`, `tier3h5_bi_measure_catalog.json`)
- Dashboard contracts (`tier3h5_dashboard_*.json`)

Phase 4G emits:
- `logs/tier3h5_bi_artifact_inventory.json`
- `logs/tier3h5_phase4g_operational_readiness_summary.json`

## Semantic layer purpose
`tier3h5_bi_semantic_layer.json` defines table inventory, relationship metadata, and BI field naming used by Power BI ingestion.

## Power BI ingestion expectations
- JSON deserializes deterministically.
- Top-level contract fields are present.
- Exports remain advisory-only and enforcement disabled.
- Row ordering and IDs remain deterministic/replay-safe.

## Dashboard export semantics
Dashboard exports are advisory dashboards only and must keep exact-match-derived categories and deterministic status fields.

## Smoke-test expectations
Smoke tests validate existence/readability/required fields only; no artifact mutation, remediation, or enforcement is performed.

## Sparse history handling
Sparse or empty history is allowed and should degrade gracefully via statuses like:
- `insufficient_bi_history`
- `dashboard_history_initializing`
- `partial_dashboard_history_available`
- `stable_dashboard_history_available`

CI must not fail solely because governance history is sparse.

## Guarantees
- Replay-safe artifact generation
- Deterministic export contracts
- Advisory-only governance behavior preserved
- Tier 3H.4 freeze boundary unchanged
