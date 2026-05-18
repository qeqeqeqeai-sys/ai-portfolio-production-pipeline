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
