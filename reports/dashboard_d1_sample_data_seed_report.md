# Dashboard D1 Sample Data Seed Report

## Objective
Seed certified dashboard tables with deterministic, bounded institutional sample records for supervisor-visible demonstrations.

## Scope
D1 only. Additive sample-data seeding layer with no modifications to O1–O10 logic boundaries or read-only dashboard behavior.

## Sample-Data Philosophy
- fixed inventory IDs and labels
- fixed timestamp `2026-01-01T00:00:00+08:00`
- deterministic ordering and checksums
- sample records flagged with `sample_data_flag=true`

## Table Inventory
- entity facts
- subsector facts
- alert facts
- replay facts
- benchmark facts
- evidence facts
- certification/report metadata
- export manifest

## Write Safety
- dry-run default
- execute requires explicit `confirm_execute=True` and `dry_run=False`
- writes routed via O3 controlled write adapter only
- no raw Supabase client creation

## Forbidden Behaviors
No predictive scoring, no trading/recommendation language, no target prices, no optimization loops, no uncontrolled network/database operations.

## Deterministic Guarantees
Canonical JSON checksuming and fixed deterministic sort paths are used for manifest and seed artifacts.

## Test Coverage
Implemented dedicated D1 tests for determinism, bounds, IDs, fixed timestamp, flags, dry-run defaults, and O1–O10 smoke non-regression hooks.

## Acceptance Decision
Accepted for supervisor-controlled sample-data seeding under deterministic-only operationalization constraints.
