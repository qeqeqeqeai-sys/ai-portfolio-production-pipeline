# P5-D Propagation Regime Classification & Structural State Labelling

## Objective
Implement deterministic, replay-safe, descriptive structural regime classification after P5-C.

## Scope
- Structural regime input extraction from P5-B and P5-C payloads.
- Bounded deterministic score construction (0-100).
- Fixed rule-based regime classification with fixed precedence and tie-breakers.
- Structural state label output.
- Replay transition summary using current/prior observed classifications.
- Deterministic explainability templates.
- Certification and checksum lineage.

## Non-goals
No forecasting, prediction, recommendation, probabilistic inference, ML, optimization, or autonomous decisioning.

## Placement after P5-C
P5-D consumes P5-B propagation structure and P5-C persistence/evolution outputs to classify present/replayed structural state only.

## Regime input methodology
Inputs are additive deterministic extracts: concentration, breadth, carrier load, corridor weakness, rotation, stabilization, amplification, persistence, and evidence count.

## Deterministic scoring methodology
All regime scores are clamped to 0-100 and computed from fixed formulas; mixed-state and evidence sufficiency are deterministic derived scores.

## Classification precedence
1. INSUFFICIENT_PROPAGATION_EVIDENCE
2. CARRIER_DOMINATED_PROPAGATION
3. CORRIDOR_WEAKENED_PROPAGATION
4. AMPLIFYING_PRESSURE_STRUCTURE
5. CONCENTRATED_PRESSURE
6. BROAD_DISTRIBUTED_FRAGILITY
7. ROTATING_PROPAGATION
8. STABILIZING_PROPAGATION
9. ISOLATED_FRAGILITY
10. MIXED_PROPAGATION_STATE

## Structural state labelling methodology
Deterministic labels include propagation_state, pressure_distribution_state, carrier_state, corridor_state, pathway_state, replay_evolution_state, and supervisor_state_label.

## Transition summary methodology
Compares current and prior replay-window structural classifications; outputs unchanged, broadened, narrowed, rotated, intensified, stabilized, or insufficient prior evidence.

## Explainability boundaries
Templates use descriptive language only and explicitly block forbidden predictive/trading terms.

## Checksum/replay methodology
Lineage includes input checksums, P5-B/P5-C references, regime policy checksum, canonical manifest checksum, output checksum, and replay metadata.

## Certification gates
Checks include lineage presence, deterministic input construction, bounded score compliance, policy checksum presence, explainability boundary compliance, checksum stability, immutable input safety, additive-only behavior, and non-predictive behavior.

## Governance boundaries
Descriptive structural state classifier only; no external calls, runtime fetches, or stochastic behavior.

## Final supervisor interpretation
P5-D classifies the observed/replayed propagation structure as a bounded deterministic structural state and does not infer future behavior.
