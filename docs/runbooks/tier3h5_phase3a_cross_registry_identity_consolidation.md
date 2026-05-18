# Tier 3H.5 Phase 3A — Cross-Registry Canonical Identity Consolidation

## Scope
Phase 3A adds deterministic, advisory-only cross-registry alias and dual-listing governance.

## Execution
```bash
python -m transmission_layers.asset_discovery.tier3h5.cross_registry_identity_governance
```

## Artifacts
- `logs/tier3h5_cross_registry_alias_summary.json`
- `logs/tier3h5_dual_listing_governance_summary.json`
- `logs/tier3h5_cross_registry_lineage_summary.json`
- `logs/tier3h5_alias_replay_governance_summary.json`
- `logs/tier3h5_phase3a_cross_registry_summary.json`

## Governance guarantees
- Deterministic exact-match-only linkage (`linkage_mode=deterministic_exact_match_only`)
- `enforcement_enabled=false`
- `canonical_override_enabled=false`
- No fuzzy/semantic matching
- Replay-safe deterministic hashes for alias and lineage structures
