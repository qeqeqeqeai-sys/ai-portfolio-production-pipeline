# T2 Structural Delta Intelligence Report

## Objective
Create an additive deterministic structural delta layer that compares adjacent T1 replay snapshots and answers: "what changed between replay states?"

## Scope
- Additive T2 module in `real_data`.
- Deterministic adjacent snapshot pairing.
- Bounded score/band/rank/driver delta labels.
- Replay-safe checksum lineage and deterministic certification envelope.

## Non-goals
No velocity curves, acceleration logic, regime detection, prediction, trading logic, ML/adaptive behavior, or narrative explanation engines.

## Architecture Placement After T1
T2 consumes T1-certified envelope (`ordered_sequence`, lineage metadata/checksums) and emits structural delta records and T2 certification.

## Public APIs
- `validate_structural_delta_inputs`
- `build_structural_delta_records`
- `build_structural_delta_summary`
- `build_structural_delta_checksum_chain`
- `certify_structural_delta_intelligence`
- `build_t2_structural_delta_report`

## Input Assumptions
- T1 ordered deterministic snapshots.
- snapshot identifiers, dates, and checksums present for full certification.
- Optional structural payloads for score/band/rank/driver comparisons.

## Delta Methodology
- Compare adjacent pairs only.
- Normalize ordering deterministically by entity identifier.
- Classify bounded delta labels for score/band/rank/driver.
- Track membership changes and degraded comparability.

## Comparison Policy
- Score: deterministic numeric deltas with ROUND_HALF_UP to 4 decimals.
- Band: `LOW < MODERATE < ELEVATED < HIGH < EXTREME`; unknown/unmapped -> `BAND_UNKNOWN`.
- Rank: lower numeric rank is improved.
- Driver: compare existing driver map values only.

## Checksum Lineage Behavior
- Pair-level deterministic checksums per delta record.
- Delta checksum chain derived from ordered pair checksums.
- Temporal lineage links T1 sequence checksum with T2 delta-chain checksum.

## Certification Gates
20 fixed ordered gates covering sequence presence, minimum snapshots, required fields, deterministic pairing/ordering, delta policy application, lineage preservation, immutability, and hard no-capability constraints.

## Invariant Flags
Explicit booleans for deterministic behavior, immutable input handling, replay safety, bounded labels, no runtime reads/writes/network access, and no prediction/trading/regime/velocity logic.

## Forbidden Capabilities
All prohibited runtime capabilities explicitly returned as `False` including live fetch, Supabase reads/writes, prediction, trading execution, and regime/velocity behaviors.

## Test Coverage
Focused tests added for API exports, certification status paths, deterministic behavior, input immutability, bounded labels, membership changes, checksum determinism, lineage, and T1 compatibility smoke.

## Final Status
Implemented as additive T2 module with deterministic certification envelope and supervisor-readable report.
