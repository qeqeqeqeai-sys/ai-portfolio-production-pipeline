# Tier 3H.5 Phase 5H — Deterministic Governance Knowledge Graph

## Scope
- Advisory-only deterministic governance graph surfaces built from explicit Phase 5A–5G artifacts.
- Exact-match-only mapping across phases, artifacts, invariants, posture signals, lineage, and topology references.

## Node and edge semantics
- Nodes are deterministic IDs keyed by exact phase names, artifact paths, and invariant keys.
- Edges are deterministic IDs keyed by `(source, edge_type, destination)`.
- Allowed edge types only: `produced_by_phase`, `consumed_by_phase`, `derived_from_artifact`, `summarizes_artifact`, `verifies_invariant`, `depends_on_invariant`, `continues_state`, `reports_posture`, `traces_lineage`, `covers_phase`.

## Surface semantics
- Traversal surfaces are bounded-depth, deterministic summaries with no mutation and no enforcement.
- Invariant dependency surfaces expose exact supporting artifacts only.
- Reachability surfaces report explicit support coverage for phases, invariants, lineage auditability, and control-plane observability.
- Coverage graph export reports deterministic phase and artifact coverage.

## Guarantees
- Exact-match-only graph construction.
- No semantic reasoning, fuzzy matching, probabilistic scoring, or LLM-driven decisioning.
- Advisory-only outputs; no remediation and no automated release gating.
- Tier 3H.4 freeze boundary preserved.
