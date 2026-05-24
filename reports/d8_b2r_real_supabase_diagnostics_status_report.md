# D8.B2-R Real Supabase Diagnostics Status Report

- **Execution timestamp (UTC):** 2026-05-24T09:32:14Z
- **Mode:** READ-ONLY diagnostics
- **Explicit no-write confirmation:** true

## Runtime Credential and Connectivity
- credential_status: `CREDENTIALS_MISSING`
- client_status: `CLIENT_UNRESOLVED`
- read_only_connectivity_status: `READ_ONLY_CONNECTIVITY_NOT_ATTEMPTED`
- supabase_url_present: `False`
- supabase_key_present: `False`
- selected_key_source: `missing`
- client_exception_class: `None`
- connectivity_exception_class: `None`
- connectivity_exception_short_message: `None`
- supabase_url_fingerprint: `None`
- supabase_key_fingerprint: `None`

## Source Diagnostics
- expected_tables: `['dashboard_replay_metadata_records', 'dashboard_export_manifests']`
- accessible_tables: `[]`
- inaccessible_tables: `['dashboard_replay_metadata_records', 'dashboard_export_manifests']`
- replay_metadata_row_count: `0`
- manifest_row_count: `0`
- dashboard_replay_row_count: `0`
- d7_derived_historical_source_count: `0`
- d8_b2_candidate_source_count: `0`
- rejected_derivation_ids: `[]`
- missing_candidate_run_ids: `[]`
- source_shape_compatible: `True`

## Final Status
- final_status: `SOURCE_BLOCKED_CREDENTIALS_MISSING`
- recommendation: `BLOCKED_MISSING_CREDENTIALS`
- dry_run_source_status: `SOURCE_BLOCKED_CREDENTIALS_MISSING`
