# Dashboard O7 Runtime Diagnostics Rendering Fix Report

## Root cause
The runtime diagnostics were attached at the top-level runtime snapshot (`runtime_snapshot["runtime_diagnostics"]`), but some Streamlit rendering paths consumed diagnostics from the payload object. This key/nesting mismatch caused the diagnostics panel to resolve missing keys and show `None` placeholders.

## Key/nesting mismatch
- Producer: `load_streamlit_dashboard_snapshot(...)` attached diagnostics at root only.
- Consumer: Streamlit paths can read root-level diagnostics, but compatibility with payload-scoped diagnostics was not guaranteed.

## Rendering fix
1. Added deterministic diagnostics attachment to both:
   - root snapshot field: `runtime_diagnostics`
   - payload field: `payload["runtime_diagnostics"]`
2. Updated Streamlit diagnostics read path to:
   - read root diagnostics first
   - fallback to payload diagnostics if root diagnostics are absent/empty

## Deterministic guarantees
Diagnostics are now populated and returned for all runtime paths:
- fallback demo mode
- degraded loading mode
- read-only supabase mode
- snapshot read exception path
- normalization failure path

## No-secret-leakage guarantees
Diagnostics include operational booleans/status fields only and do not include raw credentials or Supabase keys.

## Final decision
**APPROVED_FOR_O7_RUNTIME_DIAGNOSTICS_RENDERING_FIX**
