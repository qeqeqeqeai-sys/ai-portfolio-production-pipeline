# Dashboard O6 — Supabase Read Adapter & Deterministic Data Loading

## Objective
Implement a deterministic, read-only, injected-client-only Supabase read adapter for the certified dashboard stack (O1–O5), without introducing new intelligence, scoring, prediction, or trading logic.

## Scope
- Added `dashboard_o6_supabase_read_adapter.py` with fixed table/column inventories and bounded read loaders.
- Added deterministic snapshot assembly API for dashboard consumption.
- Added fake-client tests to validate deterministic behavior, limits, degraded mode, immutable safety, and additive export surface.
- Added additive package/API inventory integration and report artifact tracking.

## Mandatory Constraints Compliance
- Deterministic only: fixed inventories, stable key ordering, deterministic row normalization/order clauses.
- Injected Supabase client only: no module-level client creation, no env reads.
- Read-only behavior: only `table().select().eq().order().limit().execute()` query pattern.
- No writes/inserts/updates/deletes/upserts/rpc/raw SQL paths.
- No arbitrary table access: strict logical table allowlist.
- No unrestricted column access: strict per-table column allowlist.
- Bounded query limits: clamped limits for default (500), replay (200), certification metadata (100).
- Graceful degraded mode: stable empty rows + explicit degraded status and bounded error text.
- Immutable-input safe: callers are not mutated.
- Additive-only architecture: O1–O5 behavior remains unchanged.

## Allowed Logical Tables
- `dashboard_entity_facts`
- `dashboard_subsector_facts`
- `dashboard_alert_facts`
- `dashboard_benchmark_facts`
- `dashboard_replay_facts`
- `dashboard_evidence_facts`
- `dashboard_certification_reports`
- `dashboard_run_manifests`

## Forbidden Access/Operations
- Any write-side database operation.
- RPC and raw SQL execution.
- Access to tables or columns outside fixed allowlists.
- Uncontrolled network behavior outside injected Supabase query calls.

## Deterministic Guarantees
- Stable table inventory ordering.
- Stable column inventory mapping.
- Stable top-level snapshot key ordering.
- Repeated invocations with same client data yield identical outputs.

## Degraded-Mode Behavior
- Missing client returns degraded payload with empty rows and `client_not_provided`.
- Query failures return degraded payload with empty rows and bounded exception summary.
- Empty-table results return stable `ok` payload with empty rows and `row_count=0`.

## Final Implementation Status
✅ Implemented and validated with targeted O6 tests and O4/O5 non-regression test runs.
