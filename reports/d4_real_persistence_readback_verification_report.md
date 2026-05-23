# D4 Real Persistence Readback Verification Report

## Objective
Implement controlled real readback verification for dashboard operationalization persistence using injected Supabase-compatible clients only.

## Scope
Deterministic planning, validation, execution, verification, handoff, certification, and report payload generation for D4.

## Non-goals
No internal client creation, no env reads, no market fetching, no LLM calls, no trading/optimization/forecasting, no hidden side effects.

## Relationship to D2 / D3 / O8 / O9
D2 provides approved table inventory, D3 provides controlled persistence execution context, O8 provides query-plan/readback contract structure, and O9 remains closeout/governance layer.

## Readback execution plan methodology
Build deterministic query items from D3-like payloads, O8-like plans, or explicit query_items. Canonical ordering and checksums are used.

## Injected-client-only readback boundary
Real reads occur only through caller-injected client interface `table().select().in_().execute()`.

## Dry-run / no-client behavior
`dry_run=True` never calls client. `dry_run=False` with no client returns deterministic `NOT_EXECUTED_NO_CLIENT`.

## Verification methodology
Compare expected IDs/checksums against readback rows and emit matched/missing/unexpected/checksum/duplicate/routing/lineage failures.

## Verification handoff methodology
Produce deterministic handoff with state and checksum chain for supervisor/governance continuity.

## Certification states
`CERTIFIED_REAL_READBACK_VERIFIED`, `DEGRADED_REAL_READBACK_VERIFIED`, `BLOCKED_REAL_READBACK_INVALID`.

## Checksum / replay guarantees
All execution plan, table result, summary, verification, handoff, and certification artifacts use canonical checksum serialization.

## Degraded / blocked behavior
Partial inputs degrade with explicit reason list; structural violations block execution with explicit reasons.

## Governance boundaries
Injected-client-only control, dry-run safety, deterministic no-client behavior, approved-table routing checks, and capability inventory.

## Forbidden capabilities
No internal Supabase client creation, env reads, live market/network discovery, LLM calls, trading, optimization, forecasting, hidden nondeterminism, or implicit time dependency.

## Deployment guidance
Use injected repository/client adapters in runtime orchestration; keep D4 as deterministic pure-Python control surface.

## Final supervisor closeout status
D4 implementation delivered with tests, additive exports, and deterministic report payload support.
