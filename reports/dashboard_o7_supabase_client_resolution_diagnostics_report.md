# O7 Supabase Client Resolution Diagnostics Report

## Observed problem
Runtime diagnostics reported credentials present and fallback payload usage, but `client_resolved=False` had no deterministic cause visibility.

## Root cause visibility gap
`_resolve_client(...)` returned `None` on multiple failure classes (missing package, import failure, factory failure) without structured attribution.

## Added client diagnostics
Added `resolve_streamlit_supabase_client(...)` returning deterministic structured diagnostics:
- `client_resolved`
- `client_error_type`
- `client_error_message_short`
- `client_factory_source`
- `supabase_package_available`
- `credentials_present`

Integrated this result into `load_streamlit_dashboard_snapshot(...)` and runtime diagnostics payload.

## No-secret-leakage guarantees
- No Supabase URL emitted in diagnostics.
- No Supabase key emitted in diagnostics.
- Exception text is truncated.
- Credential-like tokens are redacted in short error messages.

## Runtime interpretation
When credentials exist but client cannot be resolved, runtime now deterministically reports:
- `runtime_mode=degraded_data_loading_mode`
- `snapshot_loaded=False`
- `normalization_status=client_unresolved`
- `payload_source=fallback_payload`
- full required sections degraded
- attributable client-resolution error metadata

## Final decision
**APPROVED_FOR_O7_SUPABASE_CLIENT_RESOLUTION_DIAGNOSTICS**
