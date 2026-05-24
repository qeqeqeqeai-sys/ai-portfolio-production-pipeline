## Objective
Wire D8.2 replay-density and evidence-density outputs into the visible D7 operational dashboard path, with deterministic/read-only behavior and debug-only raw payload exposure.

## Root cause / limitation before D8.3
D8.2 existed as backend intelligence but was not connected to `build_d7_dashboard_view_model` or rendered in Streamlit dashboard tabs.

## D8.2-to-D7 wiring path
1. `build_d7_dashboard_view_model` now builds `d8_2_payload` via `build_d8_2_payload(...)` using existing findings/narratives/evidence + E2/E3/E4/E5 payloads + optional historical runs.
2. `build_d8_2_dashboard_view_model` is then produced and attached as `d8_2_dashboard`.
3. Debug archive now includes `raw_d8_2_payload` under `debug_payload_sections`.
4. Streamlit entrypoint imports and invokes `render_d8_2_replay_evidence_density_summary` in a dedicated tab.

## Live replay payload source handling
No new write/network paths were introduced. Existing integrity/replay loader outputs and existing `historical_runs_payloads` contract are consumed as read-only inputs. If history is absent, D8.2 deterministic degraded statuses are surfaced.

## Dashboard sections added
Added a dedicated dashboard tab/section: **Replay & Evidence Density** with summary cards for:
- semantic persistence
- evidence density
- replay continuity
- regime transitions
- persistent contradictions
- theme evolution
- replay-linked evidence lineage

## Sparse-history fallback behavior
When historical runs are missing, primary summary shows degraded states such as `insufficient_history` / `NO_HISTORY_AVAILABLE` and does not fabricate continuity or persistence.

## Debug/archive handling
Raw D8.2 payload, checksums, and internal lineage details are only in debug/archive expander payloads, not main cards.

## Deterministic guarantees
Changes are additive adapters only; no new D8.2 intelligence logic, no mutable state, no hidden clients, and no write paths added.

## Governance confirmation
Read-only boundary preserved. No prediction/trading/execution logic added.

## Test results
Covered by added/updated tests for:
- D8.2 inclusion in view model
- graceful degradation with missing history
- primary surface excludes raw/internal identifiers
- D8.2 renderer integration in operational app runtime
