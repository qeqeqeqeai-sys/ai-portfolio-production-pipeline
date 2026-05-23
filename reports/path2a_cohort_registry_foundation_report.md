# Path 2-A Cohort Registry Foundation Report

## Objective
Implement a deterministic, replay-safe Cohort Registry Foundation that enables future cross-sectional relative fragility and peer comparison intelligence.

## Scope
Additive-only implementation of cohort contracts, manifest generation, deterministic membership resolution, benchmark mapping registry, integrity validation, explainability metadata, and replay/checksum certification.

## Non-Goals
- Dynamic clustering
- ML peer discovery
- Adaptive weighting
- Trading, forecasting, optimization, or portfolio execution behavior

## Architecture Summary
The module is a static deterministic pipeline:
1. Contract declaration (`build_cohort_registry_contracts`)
2. Canonical membership resolution (`resolve_cohort_membership`)
3. Deterministic benchmark mapping registry (`build_benchmark_mapping_registry`)
4. Cohort manifest construction (`build_cohort_manifest`)
5. Integrity validation gates (`validate_cohort_integrity`)
6. Certification (`certify_cohort_registry`)
7. Supervisor-readable report payload (`build_path2a_cohort_registry_report`)

## Cohort Registry Methodology
- Explicit versioned cohorts
- Static cohort types only
- Canonical member ordering
- Inclusion rationale and exclusion rules required
- Explainability metadata attached at cohort level

## Benchmark Mapping Methodology
Benchmark mapping is represented as a deterministic `cohort_id -> benchmark_id` registry with sorted keys and SHA256 checksum traceability.

## Deterministic Membership Rules
- Input members trimmed to canonical string representation
- Empty values removed
- Membership deduplicated
- Final member list sorted lexicographically

## Validation Gates
- cohort_id present
- cohort_version present
- cohort_type allowed
- members present
- members canonical ordered
- duplicate members rejected or flagged
- benchmark mapping valid
- inclusion rationale present
- exclusion rules present
- explainability metadata present
- checksum stable
- forbidden dynamic capabilities absent
- input immutability preserved

## Replay/Checksum Guarantees
- Stable JSON serialization (`sort_keys=True`, fixed separators)
- SHA256 manifest checksum
- Deterministic ordering of cohort entries

## Forbidden Capabilities
- dynamic_clustering
- ml_peer_discovery
- adaptive_weighting

## Certification Decision Logic
- `BLOCKED_COHORT_REGISTRY` when critical identity/type/checksum gates fail
- `DEGRADED_COHORT_REGISTRY` when non-critical quality gates fail (e.g., mapping/duplicates)
- `CERTIFIED_COHORT_REGISTRY` when all gates pass

## Final Supervisor Interpretation
P2-A provides additive deterministic registry foundations without altering existing Path 1 behavior and is suitable for replay-safe downstream cohort-relative intelligence.
