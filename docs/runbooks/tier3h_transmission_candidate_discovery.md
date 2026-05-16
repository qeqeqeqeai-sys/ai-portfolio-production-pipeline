# Tier 3H — Transmission Candidate Discovery (Advisory-Only)

## Purpose
Tier 3H identifies candidate assets/themes that may deserve future monitored-universe consideration. It is strictly advisory and designed to be low-risk, observable, and reversible.

## Advisory-only guarantees
- Tier 3H writes only to `tier3h_transmission_candidates`.
- Tier 3H never writes/updates/deletes main monitored-universe tables.
- Tier 3H emits no trading signals.
- `recommended_action=candidate_add` remains advisory-only and requires manual review.

## Inputs
Tier 3H attempts to read local upstream outputs when present:
- `logs/transmission_candidate_inputs.json`
- `logs/phase5d_structural_propagation_regime_forecasting_summary.json`
- `logs/phase3e_transmission_potential_surface_summary.json`

If inputs are missing or empty, Tier 3H soft-fails with a clear summary and still produces logs.


## Tier 3H.2 entity resolution
Tier 3H.2 resolves candidate identifiers in this deterministic order:
1. `TICKER::<SYMBOL>` from ticker/symbol fields
2. `NODE::<NORMALIZED_NODE>` from node/entity fields
3. `THEME::<NORMALIZED_THEME>` from theme fields
4. `REGIME::<NORMALIZED_REGIME>` from regime fields (fallback only)

Additional observability in summary/validation logs includes:
- `source_columns_seen`
- `candidate_identifier_type_counts`
- `fallback_identifier_count`
- `unresolved_identifier_count`
- regime fallback guardrails (`REGIME` cannot become `candidate_add`)

## Outputs
- `logs/tier3h_candidate_discovery_summary.json`
- `logs/tier3h_candidate_discovery_validation.json`
- `logs/tier3h_candidate_discovery_manifest.json`

## Supabase table
Tier 3H advisory table:
- `public.tier3h_transmission_candidates`
- upsert conflict key:
  - `(run_date_sgt, candidate_symbol, discovery_theme, candidate_source)`

## Recommended action definitions
- `watch`: weak positive signal; monitor only
- `review`: moderate positive signal; manual analyst review suggested
- `candidate_add`: strong positive signal and evidence; queue for manual expansion review only
- `reject`: insufficient signal or adverse net transmission

## Workflow usage
Use `.github/workflows/tier3h_transmission_candidate_discovery.yml` via `workflow_dispatch`.

## Manual review process
1. Run Tier 3H workflow.
2. Inspect summary/validation/manifest artifacts.
3. Query `tier3h_transmission_candidates` and sort by `recommended_action`, `confidence_score`, and `net_transmission_score`.
4. Move only human-approved names to the future expansion queue process.

## Explicit non-automation note
Tier 3H does **not** auto-add assets to the monitored universe.

## Future Phase 2 path
Tier 3H candidates → human review → approved expansion queue → monitored universe.

## Tier 3H.3 structural entity linking
Tier 3H.3 adds deterministic structural mapping from themes/nodes into advisory investable entities.

- Link source fields: `theme_name`, `anchor_theme_name`, `source_node_key`, `target_node_key`, `source_node_type`, `target_node_type`, `propagation_metadata`.
- Link method: curated static dictionary only (no external APIs).
- Candidate source label for mapped entities: `tier3h_structural_entity_linking`.
- Entity metadata columns: `linked_from_theme`, `linked_from_node`, `entity_link_confidence`, `entity_link_method`.

Allowed `entity_link_method`:
- `curated_static_map`
- `direct_ticker`
- `node_alias`
- `unresolved`

Validation includes:
- advisory-only status enforcement,
- allowed identifier/method values,
- no monitored-universe writes,
- no `candidate_add` for `REGIME`/`UNKNOWN`.
