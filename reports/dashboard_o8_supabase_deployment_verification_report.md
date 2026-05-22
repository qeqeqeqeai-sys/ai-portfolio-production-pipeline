# Dashboard O8 — Real Supabase Deployment Verification & Data Contract Smoke Test

## Deployment Verification Objective
Provide a deterministic, read-only deployment verification layer that confirms dashboard Supabase reachability and expected column compatibility through the certified O6 read path.

## Read Path
- O8 verification uses only O6-certified table and column inventories.
- Reads are injected-client-only and bounded sample reads.
- No client creation is performed in O8.

## Allowed Checks
- Credential presence verification.
- Read-only table reachability checks on allowed dashboard tables.
- Read-only column contract checks against O6 inventory.
- Bounded sample limit with clamp enforcement.

## Forbidden Operations
- insert/update/delete/upsert
- rpc
- raw SQL
- arbitrary table access
- unrestricted column access
- dashboard-triggered mutation

## Contract Verification Model
- Build expected table/column contracts from O6 inventories.
- For each allowed table, perform select(columns).limit(sample_limit).execute().
- If rows are returned, verify expected keys exist in sampled records.
- Deterministic status model: verified/degraded/blocked/invalid_client/contract_mismatch.

## Degraded/Blocked Behavior
- Missing credentials and missing client return deterministic degraded status.
- Invalid client shape (missing table method) returns invalid_client.
- Query execution failure on allowed tables returns blocked.
- Missing expected sampled columns returns contract_mismatch.

## Deterministic Guarantees
- Fixed output keys and status vocabulary.
- Ordered output payload fields.
- Safe sample limit clamping.
- Immutable input safety (copy-on-read behavior).
- Additive-only architecture.

## Implementation Status
- O8 verification module implemented.
- O8 tests implemented with fake clients for deterministic behavior, failure modes, and non-regression smoke checks.
- Public O8 APIs exported additively from dashboard operationalization package.
