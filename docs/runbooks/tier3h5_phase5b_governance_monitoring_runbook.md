# Tier 3H.5 Phase 5B Governance Monitoring Runbook

Phase 5B adds **advisory-only**, **read-only** governance production run monitoring on top of Phase 5A artifacts.

## What Phase 5B monitors
- Orchestration drift (stage count and required-stage execution).
- Optional artifact skip drift.
- Artifact inventory drift.
- Validation status drift.
- Readiness drift (dashboard, semantic layer, smoke test, operational readiness).
- Governance invariants: advisory-only, exact-match-only, Tier 3H.4 freeze boundary.

## Sparse-history behavior
If monitoring history is missing/insufficient, Phase 5B emits `insufficient_monitoring_history` and still emits current run health artifacts.

## Severity definitions
- `no_drift_detected`: baseline and current normalized outputs match.
- `informational_drift`: limited drift findings.
- `warning_drift`: multi-category drift findings.
- `insufficient_monitoring_history`: not enough prior monitoring context.

## Guarantees
- Advisory-only diagnostics (no enforcement).
- Non-remediation behavior (no automatic correction).
- No canonical/scoring/propagation mutation.
- Exact-match-only preserved (no fuzzy/semantic matching).
- Tier 3H.4 freeze boundary preserved.
