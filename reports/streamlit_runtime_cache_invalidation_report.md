# Streamlit Runtime Cache Invalidation Report

## Root Cause
The Streamlit runtime snapshot loader used `@st.cache_data` without an explicit schema-version argument. When runtime snapshot/diagnostics shape changed, cache keys could remain valid and return stale snapshots where `runtime_diagnostics` was missing or empty.

## Fix Summary
- Added explicit cache schema versioning constant: `RUNTIME_CACHE_SCHEMA_VERSION = "o7-runtime-diagnostics-v2"`.
- Threaded cache schema version into `_load_runtime_snapshot_cached(...)` so runtime payload shape changes deterministically invalidate cache.
- Added UI toggle **Bypass runtime cache** to force direct uncached loader path.
- Added defensive diagnostics synthesis to guarantee required diagnostics keys exist even when runtime diagnostics are missing.
- Added `diagnostics_source` marker to identify provenance:
  - `root_runtime_diagnostics`
  - `payload_runtime_diagnostics`
  - `synthesized_from_runtime_snapshot`
  - `missing_runtime_snapshot`

## Safety
- Synthesis uses non-secret root fields and payload structure only.
- No secret-bearing keys are copied into diagnostics output.
- Default fallback values preserve existing safety behavior when snapshots are absent.

## Validation
- `pytest -q tests/test_streamlit_runtime_cache_invalidation.py`
- `pytest -q tests/test_dashboard_o7_streamlit_runtime_diagnostics_rendering.py`
