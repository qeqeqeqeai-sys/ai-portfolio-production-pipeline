# Tier 3H.5 Phase 4E Governance BI Exports

Tier 3H.5 Phase 4E publishes read-only, advisory-only governance dashboard data as stable Power BI-ready contracts. The exports serialize existing Phase 4C/4D governance history, query, and dashboard outputs without enforcing governance actions, remediating records, changing canonical identifiers, mutating scores, mutating propagation state, or changing Tier 3H.4 behavior.

## Export artifacts

Phase 4E writes deterministic JSON table artifacts under `logs/`:

- `tier3h5_bi_governance_incident_fact.json`
- `tier3h5_bi_governance_escalation_fact.json`
- `tier3h5_bi_governance_watchlist_fact.json`
- `tier3h5_bi_governance_trend_fact.json`
- `tier3h5_bi_governance_continuity_fact.json`
- `tier3h5_bi_governance_summary_snapshot.json`
- `tier3h5_bi_governance_dimensions.json`
- `tier3h5_phase4e_bi_export_summary.json`

Each fact artifact declares its table name, primary key, stable field order, date fields, categorical fields, numeric measure fields, row count, deterministic rows, `replay_mode: advisory_only`, and `enforcement_enabled: false`.

## Semantic layer and measures

The semantic metadata files are:

- `tier3h5_bi_semantic_layer.json` — table metadata, primary keys, field roles, dashboard labels/descriptions, and recommended relationships.
- `tier3h5_bi_measure_catalog.json` — metadata-only BI measure definitions for dashboard aggregation in Power BI.

The measure catalog does not run governance scoring. Measures are declarative BI definitions only, and all rows include metadata flags showing runtime scoring is disabled.

## Intended Power BI relationships

Recommended relationships are dimension-to-fact filters:

- `governance_domain_dimension.member_key` to `governance_incident_fact.governance_domain`
- `governance_severity_dimension.member_key` to `governance_incident_fact.severity`
- `governance_status_dimension.member_key` to `governance_incident_fact.governance_status`
- `governance_trend_dimension.member_key` to `governance_trend_fact.governance_trend_status`

These relationships are documentation for BI modeling only. They do not introduce fuzzy matching, semantic matching, canonical override, or reconciliation behavior.

## Sparse history degradation

Sparse governance history is valid and should not fail CI. Phase 4E reports one of these BI history statuses:

- `insufficient_bi_history`
- `bi_history_initializing`
- `partial_bi_history_available`
- `stable_bi_history_available`

Empty fact tables are emitted with stable schemas and zero rows. The summary snapshot still emits a deterministic row so dashboards can initialize safely.

## Operating posture

Phase 4E is strictly read-only and advisory-only. It exposes, exports, serializes, normalizes for BI, aggregates for BI, and documents semantic fields. It preserves exact-match-only governance boundaries and the Tier 3H.4 freeze boundary.
