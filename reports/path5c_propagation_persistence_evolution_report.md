# P5-C Propagation Persistence & Structural Pressure Evolution

## Objective
Deliver deterministic replay-window comparison intelligence describing how propagation state persisted and evolved.

## Scope
Descriptive comparison across historical/replay P5-B payload windows only.

## Non-goals
No forecasting, prediction, optimization, trading recommendation, ML, stochastic simulation, or autonomous decisioning.

## Placement after P5-B
P5-C consumes certified/degraded P5-B-style outputs and builds replay-window evolution descriptors.

## Replay-window methodology
- Canonical ordering by `(window_index, window_id, window_checksum)`.
- Stable checksums for window index and output manifests.
- Safe handling for empty, single, and multi-window inputs.

## Propagation persistence methodology
- Compare propagation breadth and concentration deltas across windows.
- Compute persistence, broadening, narrowing, and pathway persistence scores (0–100).

## Pressure evolution methodology
- Compare concentration and dispersion deltas across windows.
- Compute intensification, dispersion, and structural stability scores (0–100).

## Carrier persistence methodology
- Track top carrier continuity across adjacent windows.
- Compute carrier persistence score (0–100).

## Corridor evolution methodology
- Compare mean resilience corridor scores across windows.
- Describe strengthening/weakening with deterministic thresholds.

## Propagation rotation methodology
- Track top propagation leader rotation across windows.
- Compute rotation score (0–100).

## Explainability boundaries
- Fixed deterministic templates only.
- Allowed descriptors include remained elevated, broadened, narrowed, persistent concentration, structural rotation, and corridor resilience weakened descriptively.
- Forbidden predictive/trading language blocked by boundary checks.

## Checksum/replay methodology
Lineage includes input window checksums, P5-B references, canonical manifest checksum, replay metadata, evolution policy checksum, and output checksum.

## Certification gates
Statuses:
- `CERTIFIED_PATH5C_PROPAGATION_PERSISTENCE_EVOLUTION`
- `DEGRADED_PATH5C_PROPAGATION_PERSISTENCE_EVOLUTION`
- `BLOCKED_PATH5C_PROPAGATION_PERSISTENCE_EVOLUTION`

Gates validate replay presence, deterministic ordering, bounded scores, checksum presence, explainability boundaries, immutable input safety, additive-only behavior, and P5-B lineage references.

## Governance boundaries
P5-C remains deterministic, bounded, replay-safe, additive-only, checksum-traceable, and institutionally interpretable.

## Final supervisor interpretation
P5-C provides descriptive replay-based structural evolution intelligence and does not imply what happens next.
