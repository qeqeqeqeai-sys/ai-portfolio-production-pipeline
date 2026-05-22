# Dashboard O7 Runtime Diagnostics Report

## Problem
After O7 payload wiring fixes, the Streamlit shell could still land in fallback/degraded behavior without enough deterministic, runtime-visible details to isolate the exact failure stage.

## Diagnostic Fields Added
`load_streamlit_dashboard_snapshot(...)` now returns `runtime_diagnostics` with:

- `credentials_present`
- `client_resolved`
- `snapshot_loaded`
- `snapshot_section_statuses`
- `degraded_sections`
- `normalization_status`
- `payload_source`
- `error_type`
- `error_message_short`
- `expected_tables`
- `runtime_mode`

These fields are deterministic and additive, and they do not mutate caller input payload/config.

## No-Secret-Leakage Guarantee
Diagnostics exclude full runtime config and do not echo Supabase URL/key material. Error output is constrained to a short bounded message (`error_message_short`) and type (`error_type`) only.

## Read-Only Boundary
This patch keeps the runtime read-only boundary unchanged:

- no write paths
- no SQL/RPC additions
- no scoring/model logic changes
- fallback safety preserved when credentials/client/snapshot/normalization fails

## Troubleshooting Interpretation
- `runtime_mode=fallback_demo_mode` + `credentials_present=false`: credentials missing.
- `runtime_mode=degraded_data_loading_mode` + `error_type` set: client/snapshot read failure.
- `runtime_mode=degraded_data_loading_mode` + `normalization_status=snapshot_degraded`: one or more required snapshot sections not `ok` (see `degraded_sections`).
- `runtime_mode=degraded_data_loading_mode` + `normalization_status=failed`: snapshot read succeeded but normalization failed; fallback payload preserved.
- `runtime_mode=read_only_supabase_mode` + `payload_source=supabase_snapshot`: healthy runtime path.
