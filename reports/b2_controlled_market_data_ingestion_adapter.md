# B2 Controlled Market Data Ingestion Adapter

## Objective
Provide an additive deterministic adapter that converts bounded raw market observations into normalized candidate inputs for B1 snapshot certification.

## Scope
- Vendor-neutral in-memory ingestion contract.
- Deterministic normalization, validation, quarantine, and candidate-envelope construction.
- Deterministic certification readiness payload for replay compatibility with B1.

## Non-goals
- Trading, prediction, optimization, target-price generation.
- Autonomous API fetching, unrestricted live API usage, autonomous writes.
- Dashboard fact mutation or certified snapshot mutation.

## Data Flow
1. Raw records enter `build_b2_controlled_ingestion_adapter`.
2. Records are deep-copied and normalized into canonical keys and bounded numeric values.
3. Records are validated against fixed B1 entity/benchmark symbols and supported metrics.
4. Invalid observations become deterministic quarantine records.
5. Candidate envelope is assembled with coverage/freshness/degradation summaries and checksum.
6. Candidate is certified into deterministic ingestion status.

## Validation strategy
- Symbol allowlist from B1 fixed registries only.
- Canonical metrics allowlist.
- ISO date checks and staleness policy.
- Deterministic duplicate detection and quarantine emission.

## Quarantine strategy
- Never drop invalid records silently.
- Emit deterministic reason code, severity, remediation hint, and original record reference.
- Quarantine reasons include unknown symbol, unsupported metric, missing value, invalid numeric/date, stale timestamps, unsupported currency, and duplicates.

## Certification gates
- No network execution.
- No database write behavior.
- Fixed-registry symbol source.
- Deterministic ordering and checksum stability.
- Quarantine visibility and immutable-input safety.
- Bounded normalization and B1 replay compatibility.

## Forbidden capability inventory
- trading
- prediction
- optimization
- target_prices
- portfolio_allocation
- autonomous_api_fetching
- autonomous_writes
- adaptive_learning
- unrestricted_llm_reasoning

## Acceptance criteria
B2 output is deterministic, replay-safe, additive to B1, and produces explicit certification status with degraded/blocking visibility.
