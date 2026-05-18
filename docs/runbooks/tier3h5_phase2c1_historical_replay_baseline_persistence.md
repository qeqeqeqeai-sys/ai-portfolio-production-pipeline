# Tier 3H.5 Phase 2C.1 — Historical Replay Baseline Persistence

## Scope
- Adds deterministic replay baseline persistence for Tier 3H.5 replay governance.
- Keeps governance advisory-only and replay-safe.
- Preserves exact-match-only and non-enforcement boundaries.

## Artifacts
Phase 2C.1 emits these deterministic artifacts under `logs/`:
- `tier3h5_replay_baseline_manifest.json`
- `tier3h5_replay_history_summary.json`
- `tier3h5_replay_continuity_lineage.json`
- `tier3h5_replay_chain_metrics.json`
- `tier3h5_phase2c1_replay_persistence_summary.json`
- `tier3h5_registry_replay_baseline_history.json`

## Baseline selection
- Uses latest deterministic prior baseline from replay history.
- Prefers same normalized source context when available.
- Falls back deterministically to latest prior baseline.
- If unavailable, governance remains graceful with replay-history-unavailable status tags.

## Guardrails
- `replay_mode: advisory_only`
- `enforcement_enabled: false`
- `canonical_override_enabled: false`
- No fuzzy or semantic matching.
- No scoring/reconciliation/propagation mutation.
