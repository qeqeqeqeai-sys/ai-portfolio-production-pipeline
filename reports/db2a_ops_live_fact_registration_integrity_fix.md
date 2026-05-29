# DB-2A — OPS-LIVE Fact Registration Integrity Fix

## Root Cause

OPS-LIVE-2 built and emitted rows for `sefi_observation_facts` with deterministic `artifact_id` and `run_id` values, but the live persistence path did not insert the corresponding parent rows into `sefi_artifact_registry` and `sefi_run_registry` before fact insertion. Because `sefi_observation_facts.artifact_id` and `sefi_observation_facts.run_id` are foreign keys, direct fact insertion could fail when those parent records were absent.

## Fix Implemented

The OPS-LIVE-2 write path now follows the DB-1 / DB-2 registration order used by the historical loader:

1. Build and insert one deterministic `sefi_artifact_registry` row for the bounded live observation payload.
2. Build and insert one deterministic `sefi_run_registry` row referencing that artifact.
3. Insert the normalized `sefi_observation_facts` rows.

The fix is limited to the OPS-LIVE-2 persistence path. It uses insert-only writes, retains deterministic IDs and duplicate-prevention keys, and does not introduce upsert, update, delete, or schema mutation behavior.

## FK Integrity Validation

Automated tests cover the parent-before-child order and an FK-checking fake client that rejects child inserts unless the artifact and run parents have already been recorded. The persistence path succeeds with the enforced order:

- `sefi_artifact_registry`
- `sefi_run_registry`
- `sefi_observation_facts`

Dry-run mode continues to validate/build fact rows without performing registry or fact table writes.

## Risks

- The path remains append-only and insert-only, so a repeated live write with the same deterministic artifact, run, or fact identity will still rely on existing unique constraints / duplicate-prevention keys to reject duplicates rather than mutating existing rows.
- Registry timestamps are generated at emission time unless a test supplies a fixed timestamp; deterministic identity and duplicate-prevention keys do not depend on those timestamps.

## Schema Confirmation

No schema changes, migration changes, FK changes, or architecture changes were required.
