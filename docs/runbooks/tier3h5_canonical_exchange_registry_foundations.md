# Tier 3H.5 Phase 1A — Canonical Exchange Registry Foundations

## Purpose
This runbook introduces deterministic, replayable foundation tables and ingestion scaffolding for canonical issuer/security identity without modifying Tier 3H.4 behavior.

## What Phase 1A Adds
- SQL migration creating:
  - `tier3h5_registry_ingestion_runs`
  - `tier3h5_institutional_issuer_registry`
  - `tier3h5_institutional_security_registry`
  - `tier3h5_registry_provenance`
- Deterministic normalization helpers:
  - `normalize_exchange_code`
  - `normalize_ticker`
  - `normalize_issuer_name`
  - `compute_source_record_hash`
- Deterministic fixture-first ingestion scaffold (`run_registry_ingestion`).
- Observability summary artifact: `logs/tier3h5_registry_foundation_summary.json`.

## Operating Steps
1. Apply SQL migration `sql/tier3h5_canonical_exchange_registry_foundations.sql`.
2. Execute ingestion using local structured fixture rows first.
3. Validate observability JSON includes ingestion counts, collision counts, and status.
4. Replay same input and verify deterministic summary + idempotent upsert counts.

## Deferred by Design (Out of Phase 1A)
- ADR intelligence
- historical symbol continuity
- issuer graph logic
- fuzzy/heuristic/LLM adjudication
- cross-exchange canonical graphing

## Tier 3H.4 Freeze Boundary
Tier 3H.5 Phase 1A adds isolated SQL and isolated `tier3h5` modules only. Existing Tier 3H.4 discovery/resolution behavior is not modified.
