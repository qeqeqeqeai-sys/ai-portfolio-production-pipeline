# B4 Controlled Supabase Snapshot Persistence

## Objective
Implement deterministic, additive, injected-client-only persistence for B3 certified snapshot envelopes.

## Scope
- B3 envelope validation for persistence eligibility.
- Deterministic record construction for snapshot, audit, and fragility tables.
- Idempotent upsert persistence via injected client only.

## Non-goals
No vendor API fetches, no client instantiation, no env reads, no dashboard UI mutations, no trading/prediction/optimization/autonomous jobs.

## Approved chain
B2 inputs -> B3 certified snapshot envelope -> B4 controlled Supabase persistence -> future dashboard read-path.

## Table strategy
Default approved tables:
- dashboard_market_snapshots
- dashboard_market_snapshot_audit
- dashboard_market_fragility_payloads

Table names are overrideable for deterministic tests.

## Eligibility rules
Persist only for:
- CERTIFIED_SNAPSHOT_READY
- DEGRADED_SNAPSHOT_READY when allow_degraded=True

Block on malformed envelope, missing checksums/contracts/payloads, blocked decisions, and forbidden capability violations.

## Degraded policy
Degraded snapshots are visible and replay-preserved but blocked unless explicitly authorized.

## Idempotency
Conflict identity uses deterministic persistence_identity derived from snapshot_date, snapshot_checksum, b3_checksum, and universe_id.

## Error handling
Repository errors are caught and mapped to BLOCKED_REPOSITORY_ERROR with deterministic blocked_reason.

## Injected-client boundary
Only uses methods on provided client object; no autonomous connection setup.
