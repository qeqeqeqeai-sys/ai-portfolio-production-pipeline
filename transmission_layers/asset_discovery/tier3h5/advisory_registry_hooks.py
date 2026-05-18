from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass
from typing import Any

from transmission_layers.asset_discovery.tier3h5.canonical_registry_resolution import resolve_security_from_registry


@dataclass(frozen=True)
class AdvisoryRegistryLookupResult:
    advisory_registry_enabled: bool
    registry_lookup_attempts: int
    registry_exact_matches: int
    registry_no_match: int
    registry_conflicts: int
    registry_invalid_input: int
    advisory_registry_failures: int
    support_candidates: list[dict[str, Any]]


def _support_strength_for_status(status: str) -> float:
    if status == "accepted":
        return 1.0
    if status == "conflict":
        return 0.5
    return 0.0


def _canonical_propagation_id(security_id: str | None, issuer_id: str | None) -> tuple[str | None, str]:
    if security_id:
        return f"CANONICAL_SECURITY::{security_id}", "canonical_registry_security"
    if issuer_id:
        return f"CANONICAL_ISSUER::{issuer_id}", "canonical_registry_issuer"
    return None, "legacy_candidate_asset_id"


def run_advisory_registry_lookup(
    candidates: list[dict[str, Any]] | None,
    security_registry: list[dict[str, Any]] | None,
    enabled: bool = False,
) -> dict[str, Any]:
    if not enabled:
        return asdict(
            AdvisoryRegistryLookupResult(
                advisory_registry_enabled=False,
                registry_lookup_attempts=0,
                registry_exact_matches=0,
                registry_no_match=0,
                registry_conflicts=0,
                registry_invalid_input=0,
                advisory_registry_failures=0,
                support_candidates=[],
            )
        )

    attempts = 0
    exact = 0
    no_match = 0
    conflicts = 0
    invalid = 0
    failures = 0
    support_candidates: list[dict[str, Any]] = []
    safe_candidates = deepcopy(candidates or [])

    for idx, candidate in enumerate(safe_candidates):
        attempts += 1
        try:
            result = resolve_security_from_registry(
                ticker=str(candidate.get("ticker", "")),
                exchange=str(candidate.get("exchange", "")),
                security_type=candidate.get("security_type"),
                security_registry=security_registry or [],
            )
            if result.resolution_status == "accepted":
                exact += 1
            elif result.resolution_status == "no_match":
                no_match += 1
            elif result.resolution_status == "conflict":
                conflicts += 1
            else:
                invalid += 1
            support_candidates.append(
                {
                    "candidate_index": idx,
                    "ticker": candidate.get("ticker"),
                    "exchange": candidate.get("exchange"),
                    "security_type": candidate.get("security_type"),
                    "support_status": result.resolution_status,
                    "support_strength": _support_strength_for_status(result.resolution_status),
                    "match_rule": result.match_rule,
                    "conflict_count": result.conflict_count,
                    "candidate_count": result.candidate_count,
                    "resolved_security_id": result.resolved_security_id,
                    "resolved_issuer_id": result.resolved_issuer_id,
                }
            )
        except Exception:
            failures += 1

    return asdict(
        AdvisoryRegistryLookupResult(
            advisory_registry_enabled=True,
            registry_lookup_attempts=attempts,
            registry_exact_matches=exact,
            registry_no_match=no_match,
            registry_conflicts=conflicts,
            registry_invalid_input=invalid,
            advisory_registry_failures=failures,
            support_candidates=support_candidates,
        )
    )


def enrich_propagation_identities(
    candidates: list[dict[str, Any]] | None,
    security_registry: list[dict[str, Any]] | None,
    enabled: bool = True,
) -> dict[str, Any]:
    safe_candidates = deepcopy(candidates or [])
    diagnostics = {
        "registry_propagation_candidates_seen": len(safe_candidates),
        "registry_propagation_resolution_attempts": 0,
        "registry_propagation_accepted": 0,
        "registry_propagation_no_match": 0,
        "registry_propagation_conflicts": 0,
        "registry_propagation_invalid_input": 0,
        "canonical_security_identity_used": 0,
        "canonical_issuer_identity_used": 0,
        "legacy_candidate_identity_preserved": 0,
        "propagation_identity_mode_counts": {},
        "duplicate_legacy_candidates_collapsed_by_canonical_id": 0,
        "canonical_identity_conflict_preventions": 0,
    }
    if not enabled:
        for row in safe_candidates:
            row["propagation_identity_mode"] = "legacy_candidate_asset_id"
        diagnostics["legacy_candidate_identity_preserved"] = len(safe_candidates)
        diagnostics["propagation_identity_mode_counts"] = {"legacy_candidate_asset_id": len(safe_candidates)}
        return {"enriched_candidates": safe_candidates, "diagnostics": diagnostics}

    seen_canonical_ids: set[str] = set()
    enriched: list[dict[str, Any]] = []
    mode_counts: dict[str, int] = {}

    for row in safe_candidates:
        diagnostics["registry_propagation_resolution_attempts"] += 1
        result = resolve_security_from_registry(
            ticker=str(row.get("ticker", "")),
            exchange=str(row.get("exchange", "")),
            security_type=row.get("security_type"),
            security_registry=security_registry or [],
        )
        row["registry_resolution_status"] = result.resolution_status
        row["registry_resolution_reason"] = result.explanation
        row["canonical_issuer_id"] = result.resolved_issuer_id
        row["canonical_security_id"] = result.resolved_security_id
        row["canonical_registry_source"] = result.matched_source_registry

        mode = "legacy_candidate_asset_id"
        canonical_id = None
        if result.resolution_status == "accepted":
            diagnostics["registry_propagation_accepted"] += 1
            canonical_id, mode = _canonical_propagation_id(result.resolved_security_id, result.resolved_issuer_id)
            if canonical_id:
                if canonical_id in seen_canonical_ids:
                    diagnostics["duplicate_legacy_candidates_collapsed_by_canonical_id"] += 1
                    diagnostics["canonical_identity_conflict_preventions"] += 1
                    continue
                seen_canonical_ids.add(canonical_id)
                row["canonical_propagation_asset_id"] = canonical_id
                if mode == "canonical_registry_security":
                    diagnostics["canonical_security_identity_used"] += 1
                elif mode == "canonical_registry_issuer":
                    diagnostics["canonical_issuer_identity_used"] += 1
            else:
                diagnostics["legacy_candidate_identity_preserved"] += 1
        elif result.resolution_status == "no_match":
            diagnostics["registry_propagation_no_match"] += 1
            mode = "unresolved"
            diagnostics["legacy_candidate_identity_preserved"] += 1
        elif result.resolution_status == "conflict":
            diagnostics["registry_propagation_conflicts"] += 1
            mode = "conflict_preserved_legacy"
            diagnostics["legacy_candidate_identity_preserved"] += 1
        else:
            diagnostics["registry_propagation_invalid_input"] += 1
            mode = "invalid_input_preserved_legacy"
            diagnostics["legacy_candidate_identity_preserved"] += 1

        row["propagation_identity_mode"] = mode
        mode_counts[mode] = mode_counts.get(mode, 0) + 1
        enriched.append(row)

    diagnostics["propagation_identity_mode_counts"] = dict(sorted(mode_counts.items()))
    return {"enriched_candidates": enriched, "diagnostics": diagnostics}
