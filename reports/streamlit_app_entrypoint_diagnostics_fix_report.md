# Streamlit App Entrypoint + Diagnostics Fix Report

## Root Cause
- Runtime diagnostics appeared as `None` when users launched a non-canonical or stale app path and/or reused cached snapshot output.
- The runtime diagnostics object itself was available, but rendering ambiguity and cache reuse made the UI appear inconsistent.

## Duplicate Entrypoint Risk
- `apps/streamlit_expectation_failure_dashboard.py` is the canonical implementation.
- A root-level compatibility entrypoint was added to delegate to the canonical app so legacy launch commands still execute the same code path.

## Canonical App Entrypoint
- `apps/streamlit_expectation_failure_dashboard.py`

## Cache-Bypass Control
- Added sidebar control: **"Bypass cache / reload runtime snapshot"**.
- When enabled, the app bypasses `@st.cache_data` and fetches a fresh runtime snapshot directly.

## Visible Build/Version Marker
- Added UI caption with:
  - `app_entrypoint`
  - `app_version`
  - `diagnostics_schema_version`
  - `runtime_module_version`

## Diagnostics Rendering Validation
- Runtime diagnostics panel now renders:
  - summarized fields
  - section statuses
  - full raw diagnostics object via `st.json(runtime_diagnostics)`
- Added tests to validate delegation, required diagnostics fields, metadata presence, and no secret leakage.
