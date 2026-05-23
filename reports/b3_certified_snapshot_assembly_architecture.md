# B3 Certified Snapshot Assembly Architecture

## Objective
Implement deterministic B2->B1 snapshot assembly and certification envelope.

## Scope
- Validate B2 candidate shape/checksum visibility.
- Deterministically map accepted records into B1-compatible score inputs and traceable snapshot inputs.
- Invoke B1 snapshot builder, fragility payload builder, and B1 certification.
- Emit B3 envelope with replay contract, degraded visibility, and forbidden capability contract.

## Non-goals
No live fetching, Supabase writes, dashboard mutation, trading, prediction, target prices, optimization, or autonomous actions.

## Data Flow
B2 candidate accepted_records -> B3 mapper -> B1 snapshot -> B1 fragility -> B1 certification -> B3 envelope.

## Metric Policy
required_for_certified: forward_pe, ev_to_ebitda, price_momentum_30d, price_momentum_90d, realized_volatility, benchmark_relative_return, price.
required_for_degraded: price, realized_volatility.

## Determinism / Replay
Deep-copy inputs, fixed B1 entity/benchmark order, canonical JSON checksums, immutable output assembly.

## Certification Gates
Checksum presence, accepted_records presence, registry symbol membership, supported metrics only, quarantine visibility, no network/write/trading behaviors.

## Persistence Posture
`persistence_ready` true only for CERTIFIED/DEGRADED snapshot-ready decisions.
