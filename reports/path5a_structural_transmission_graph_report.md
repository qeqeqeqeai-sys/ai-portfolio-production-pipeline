# P5-A Structural Transmission Graph Layer Report

## Objective
Build a deterministic, replay-safe, descriptive-only structural topology layer answering: *what is connected to what, and why*.

## Scope
- Node taxonomy, edge taxonomy, relationship registry.
- Deterministic node/edge construction and normalization.
- Deterministic topology metrics.
- Lineage and checksum manifests.
- Certification statuses and supervisor/dashboard summaries.

## Non-goals
- Prediction, propagation forecasting, expected-return inference.
- Trading/recommendation/optimization outputs.
- Graph ML, stochastic generation, LLM orchestration.

## Relationship to Paths 1–3
P5-A consumes already-certified deterministic structural artifacts from Paths 1–3 as upstream structural context and preserves additive governance semantics.

## Why Path 5 before Path 4
Path 5 establishes the deterministic topology substrate required for institutionally interpretable transmission surfaces. This foundational topology can be certified independently before additional path sequencing work.

## Node Taxonomy
`entity`, `subsector`, `sector`, `benchmark`, `theme`, `regime`, `structural_condition`, `certified_interpretation`.

## Edge Taxonomy
`entity_to_subsector`, `subsector_to_sector`, `entity_to_benchmark`, `entity_to_theme`, `subsector_to_theme`, `benchmark_relative_link`, `regime_membership_link`, `fragility_condition_link`, `resilience_condition_link`, `asymmetry_condition_link`, `concentration_condition_link`, `interpretation_lineage_link`.

## Relationship Registry
Each relationship declares deterministic fields:
- `relationship_id`
- `source_node_type`
- `target_node_type`
- `directionality`
- `allowed_weight_range`
- `deterministic_weight_policy`
- `governance_tags`
- `description`

## Deterministic Graph Construction Methodology
- Defensive deep-copy input handling.
- Deterministic normalization of nodes/edges.
- Stable node/edge IDs from SHA-256 of canonical payload signatures.
- Deterministic duplicate elimination.
- Stable ordering for nodes and edges.
- Canonical sorted JSON and SHA-256 checksums.

## Topology Metrics Methodology
Bounded descriptive metrics only:
- counts: nodes/edges/types
- degree: max/average
- connectivity: connected components, isolated nodes
- bounded scores: density and concentration constrained to `[0,100]`

## Lineage and Checksum Methodology
- Node and edge lineage include source metadata and input checksums.
- Graph checksum is canonical SHA-256 of graph payload.
- Manifest includes graph, metrics, and lineage checksums, plus manifest checksum.

## Certification Logic
Statuses:
- `CERTIFIED_TRANSMISSION_GRAPH`
- `DEGRADED_TRANSMISSION_GRAPH`
- `BLOCKED_TRANSMISSION_GRAPH`

Blocking conditions include invalid edge references, checksum mismatch, forbidden semantics, or structural invalidity. Partial safe graphs with missing optional structure are degraded.

## Governance Boundaries
- Deterministic, replay-safe, additive-only, checksum-traceable.
- Supervisor-readable and institutionally interpretable.
- No runtime side effects inside public APIs.

## Forbidden Capabilities
Explicit exclusion of prediction/trading/recommendation/optimization semantics and related language signatures.

## Test Coverage
Dedicated suite validates public APIs/exports, taxonomies, registries, determinism, checksums, immutability, certification transitions, invalid-edge hardening, metrics bounds, lineage/manifest/report structures, and non-regression import surfaces.

## Final Certification Interpretation
P5-A is merge-ready when certified inputs produce `CERTIFIED_TRANSMISSION_GRAPH`, partial safe inputs produce `DEGRADED_TRANSMISSION_GRAPH`, and invalid/forbidden inputs deterministically produce `BLOCKED_TRANSMISSION_GRAPH`.
