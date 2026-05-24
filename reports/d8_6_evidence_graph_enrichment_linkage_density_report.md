# D8.6 Evidence Graph Enrichment & Linkage Density Intelligence

## Objective
Improve deterministic evidence graph richness, linkage-density diagnostics, and strongest-evidence ranking without fabricating evidence/history/themes.

## Current Live Dashboard Bottleneck
After D8.5, replay continuity and semantic persistence are operational; remaining bottlenecks are weak linkage and strongest supporting evidence availability.

## Audited Evidence Path
- D7 view model loader/assembly consumes findings, narratives, evidence maps, and replay metadata.
- D8 produces evidence rankings from E2 linkage/quality maps.
- D8.2 produces replay density inventory, contradiction persistence, and relationship graph.
- D8.5 verifies operational density/readiness and caveats.

## Root Causes
- Findings may exist without evidence refs.
- Evidence rows may include refs but no resolvable finding linkage.
- Contradiction and persistent theme layers may not carry evidence refs.
- Low multiplicity (1:1 only) lowers graph density.
- Shape gaps where evidence rows exist but expected fields are absent.

## Methodology
Added D8.6 deterministic module to compute graph nodes/edges, multiplicity maps, contradiction/theme linkage counts, multi-hop linkage, density score, caveats, and enrichment status.

## Strongest Evidence Ranking Rules
Ranking uses real, present signals only:
1. finding multiplicity per evidence ref
2. contradiction linkage bonus
3. persistent-theme linkage bonus
4. replay/history appearance bonus
5. deterministic lexical tie-breaker

## Weak Linkage Diagnosis Logic
D8.6 flags:
- findings_without_evidence_refs
- evidence_refs_without_finding_refs
- contradiction_clusters_without_evidence_refs
- persistent_themes_without_evidence_refs
- evidence_maps_present_but_disconnected
- low_multiplicity_graph
- schema_shape_gaps

## Exact Changes Made
- Added D8.6 module and dashboard view helper.
- Wired D8.6 into D7 view model and debug surface.
- D7 can consume D8.6 strongest evidence when rankable evidence exists.
- Added dedicated D8.6 tests plus D7 integration assertion.

## Deterministic Guarantees
- Stable checksum
- No randomness
- Lexical tie-breakers
- Read-only payload composition

## Governance Boundaries
- No writes
- No network calls
- No prediction/trading/execution logic
- No black-box ML

## Limitations
- Theme-evidence linkage depends on persisted theme-evidence profile availability.
- Sparse source payloads still degrade to sparse/blocked statuses by design.

## Before/After Dashboard Expectation
- Before: weak_linkage caveat with unavailable strongest evidence in sparse graph cases.
- After: explicit linkage diagnostics + rankable strongest evidence when real linkage exists; otherwise deterministic "Unavailable" with caveat.

## Tests Run / Results
See pytest command output in task verification.

## Final Supervisor Recommendation
Proceed with D8.6 rollout; prioritize upstream evidence-map shape consistency to reduce persistent weak_linkage caveats.
