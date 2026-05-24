# D8.4 Persisted Evidence & Finding Enrichment Audit Report

## Root causes found
- D8.2 evidence extraction assumed `evidence_ref` per row, but persisted O6/O7 evidence map rows primarily store `supporting_evidence_refs` in payload, causing evidence lineage undercount and weak linkage.
- D8.2 graph linkage assumed `finding_refs`, while persisted rows commonly expose singular `finding_id`, leaving evidence→finding edges sparse.
- D7→D8.2 history input frequently omitted historical payloads in runtime wiring; without derived history from replay records, semantic persistence and contradiction persistence default to insufficient-history outcomes.

## Persistence-path audit
- Reviewed O6 export contract, O7 persistence serialization, D7 loaders, and D8.2 consumers.
- Verified no new write paths added; changes are read/transform-only.

## Replay/history audit
- Added deterministic history derivation from replay metadata payload fields (`run_id`, `run_timestamp`, semantic themes, contradiction claims) when explicit historical input is absent.
- Maintains honest degradation (no replay rows => zero runs observed).

## Evidence-linkage audit
- Expanded evidence reference extraction to include:
  - `evidence_ref`
  - `supporting_evidence_refs` at row level
  - `payload.supporting_evidence_refs`
- Expanded finding linkage extraction to include:
  - `finding_refs`
  - `payload.finding_refs`
  - `finding_id`
  - `payload.linked_finding_ids`

## Contradiction persistence audit
- Contradiction persistence remains derived from real historical contradiction claims and current contradiction map; no synthetic claims introduced.

## Exact fixes made
- Updated D8.2 replay density inventory evidence extraction and relationship graph linkage normalization.
- Updated D7 view-model builder to derive historical runs from persisted replay metadata when explicit historical payloads are not supplied.
- Added D8.4 regression tests covering continuity, linkage, contradiction persistence, and sparse-history honest degradation.

## Remaining limitations
- Persistence breadth still bounded by loader limits and stored replay richness.
- If upstream replay payload lacks semantic/contradiction fields, persistence summaries remain conservative.

## Deterministic guarantees
- Deterministic sorting and checksum behavior preserved.
- No stochastic logic, no LLM calls, no black-box ML.

## Governance confirmation
- Read-only dashboard behavior preserved.
- No hidden writes/network calls introduced.
- No prediction/trading/execution logic introduced.

## Before/after dashboard intelligence density summary
- Before: evidence lineage often empty/underlinked, replay continuity frequently zero without injected history.
- After: persisted evidence refs and finding linkages are recovered from real stored shapes; replay continuity, recurring themes, and contradiction persistence populate when replay metadata contains real history.

## Test results
- Added and executed D8.4 test coverage plus D8.3/D8.2/D8.1/D7 non-regression suite.
