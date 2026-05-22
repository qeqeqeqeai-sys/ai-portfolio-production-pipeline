# Dashboard O7 Real Snapshot Payload Wiring Report

## Problem found
The O7 runtime always returned the fallback payload even when Supabase snapshot reads succeeded, so Streamlit rendered dummy `Alpha/AAA/run-001` data.

## Root cause
`load_streamlit_dashboard_snapshot(...)` fetched O6 snapshot data but never transformed it into the O4 payload shape. The returned `payload` was hard-wired to `fallback_payload`.

## Fix scope
Runtime integration only:
- Added deterministic O6 snapshot → O4 payload normalizer.
- Updated O7 runtime loader return contract to include payload source + normalization status.
- Preserved read-only and degraded/fallback boundaries.
- No scoring/prediction/trading/write-path changes.

## Normalization design
Added `build_dashboard_payload_from_supabase_snapshot(snapshot, fallback_payload=None)`:
- Validates required O6 sections are all `status == "ok"`.
- Maps section rows into O4 payload keys:
  - `dashboard_entity_facts`
  - `dashboard_subsector_facts`
  - `dashboard_alert_facts`
  - `dashboard_replay_facts`
  - `dashboard_benchmark_facts`
  - `dashboard_evidence_facts`
  - `dashboard_report_metadata` (from first certification metadata row)
  - `dashboard_export_manifest` (checksum passthrough)

## Fallback behavior
Fallback payload is returned when:
- credentials missing
- snapshot read fails
- snapshot mode is degraded
- snapshot normalization fails

## Read-only boundary
No writes were introduced. No inserts, updates, deletes, RPC, or raw SQL paths added.

## Deterministic guarantees
- No randomness/time-based generation/UUID generation added.
- Deep-copy safety preserved for runtime config, snapshot transformation inputs, and fallback payload passthrough.
- Stable section mapping order via `OrderedDict`.

## Safety boundaries
No changes to D1/D1G/D2/D3/D4/P1/P2 behavior. Changes are additive at O7 runtime wiring/export level.

## Tests added
`tests/test_dashboard_o7_streamlit_supabase_runtime_payload_wiring.py` covering:
- API export presence
- fallback behavior and payload source
- healthy snapshot normalization path
- O4 consumption compatibility
- deterministic repeated output and read-only textual checks

## Final decision
**APPROVED_FOR_O7_REAL_SNAPSHOT_PAYLOAD_WIRING_FIX**
