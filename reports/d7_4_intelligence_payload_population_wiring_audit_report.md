# D7.4 Intelligence Payload Population & E5/E6 Wiring Audit Report

## Root Cause
E6 summary/render logic was reading a legacy/alternate E5 key shape (`composite_regime_synthesis`, `supervisor_closeout`, `caveat_inventory`, etc.), while the live E5 envelope produced by `build_e5_expectation_intelligence_envelope` stores populated data under `e5_expectation_intelligence_envelope.*` (e.g., `e5_expectation_regime_synthesis`, `e5_supervisor_closeout`, `e5_caveat_inventory`).

Result: E5 envelope existed and `e5_operational_status`/`readiness_score` rendered, but most narrative/evidence/regime fields resolved to empty and were shown as `Unavailable`.

## Source-to-View-Model Mapping (Before → After)
- **Before:** E6 primarily resolved paths like:
  - `composite_regime_synthesis.dominant_expectation_regime`
  - `supervisor_closeout.strongest_supporting_evidence_summary`
  - `temporal_semantic_synthesis.persistent_themes`
  - `caveat_inventory.caveat_severity`
- **After:** E6 now keeps existing primary lookups and adds deterministic alias fallbacks to the current E5 envelope paths:
  - `e5_expectation_intelligence_envelope.e5_expectation_regime_synthesis.*`
  - `e5_expectation_intelligence_envelope.e5_supervisor_closeout.*`
  - `e5_expectation_intelligence_envelope.e5_temporal_semantic_synthesis.*`
  - `e5_expectation_intelligence_envelope.e5_caveat_inventory.*`
  - plus `blocking_or_degrading_factors` fallback for operational status factors.

## E5/E6 Population Path
1. Supabase read loaders load findings/narratives/evidence/integrity rows.
2. `build_d7_dashboard_view_model` transforms rows and builds E1→E5 payloads.
3. `build_e5_expectation_intelligence_envelope` emits envelope using `e5_*` namespaced sections.
4. `build_e6_executive_summary_render_plan` now reads both historical and current key paths, so populated E5 data appears in E6 cards/panels.

## Remaining Unavailable Fields
`Unavailable` still appears only when underlying payload sections are genuinely missing/empty (e.g., no findings/evidence/history), preserving graceful degradation behavior.

## Governance / Read-Only Confirmation
No write paths, no live fetch addition, no hidden client creation, and no synthetic/hardcoded intelligence text were introduced. Fix is wiring-only key alias mapping in E6 read path.

## Tests
- Added `tests/test_d7_intelligence_payload_population.py` for:
  - positive population from existing E5 envelope
  - graceful degradation on missing optional payloads
  - parity of operational and direct streamlit view-model paths for E6 summary output
