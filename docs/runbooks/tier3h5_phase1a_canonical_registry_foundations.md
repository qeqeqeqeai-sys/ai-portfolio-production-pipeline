# Tier 3H.5 Phase 1A — Canonical Registry Foundations

## Scope
This phase adds deterministic, replay-safe canonical issuer/security registry foundations **above Tier 3H.4** while preserving Tier 3H.4 discovery and adjudication workflows unchanged.

## Components
- SQL migration: `sql/tier3h5_phase1a_canonical_registry_foundations.sql`
- Python modules under `transmission_layers/asset_discovery/tier3h5/`:
  - canonical models
  - deterministic normalization
  - deterministic ID generation
  - fixture-first ingestion scaffolding
  - observability summary writing

## Deterministic Governance
- No fuzzy matching, semantic ranking, heuristics, or AI adjudication.
- IDs are SHA-256-derived from normalized deterministic key material.
- Source record hashing uses sorted JSON serialization.

## Replayability & Idempotency Protections
- Ingestion run IDs derive from `(source_name, source_checksum)`.
- Duplicate row detection is hash-based and deterministic.
- Conflict detection is deterministic and explicitly counted.
- Observability summary is emitted to `logs/tier3h5_registry_foundation_summary.json`.

## Deferred by Design
- ADR logic
- issuer graphing / ownership linkage
- symbol continuity/cross-exchange lineage
- semantic inference or confidence expansion
- transmission integration and discovery redesign

## Operating Notes
1. Apply migration.
2. Run fixture-first ingestion.
3. Validate summary counters and status.
4. Replay the same fixture and verify stable IDs and stable summary outcomes.
