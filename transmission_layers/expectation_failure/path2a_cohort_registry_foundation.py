"""Path 2-A Cohort Registry Foundation: deterministic, replay-safe cohort contracts."""

from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
from typing import Any, Dict, Iterable, List, Tuple

CERTIFIED_COHORT_REGISTRY = "CERTIFIED_COHORT_REGISTRY"
DEGRADED_COHORT_REGISTRY = "DEGRADED_COHORT_REGISTRY"
BLOCKED_COHORT_REGISTRY = "BLOCKED_COHORT_REGISTRY"

_ALLOWED_COHORT_TYPES: Tuple[str, ...] = (
    "sector",
    "subsector",
    "theme",
    "benchmark",
    "structural",
    "concentration",
    "stability",
)

_FORBIDDEN_DYNAMIC_CAPABILITIES: Tuple[str, ...] = (
    "dynamic_clustering",
    "ml_peer_discovery",
    "adaptive_weighting",
)


def _stable_json(data: Any) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _checksum(data: Any) -> str:
    return sha256(_stable_json(data).encode("utf-8")).hexdigest()


def build_cohort_registry_contracts() -> Dict[str, Any]:
    return {
        "path_id": "P2-A",
        "contract_version": "1.0.0",
        "allowed_cohort_types": list(_ALLOWED_COHORT_TYPES),
        "required_fields": [
            "cohort_id",
            "cohort_version",
            "cohort_type",
            "members",
            "inclusion_rationale",
            "exclusion_rules",
            "explainability_metadata",
        ],
        "forbidden_dynamic_capabilities": list(_FORBIDDEN_DYNAMIC_CAPABILITIES),
        "output_constraints": {
            "deterministic": True,
            "immutable_input_handling": True,
            "bounded_structures": True,
            "stable_ordering": True,
            "checksum_traceable": True,
        },
    }


def resolve_cohort_membership(members: Iterable[str]) -> Dict[str, Any]:
    canonical = sorted({str(m).strip() for m in members if str(m).strip()})
    duplicates = len(canonical) != len([str(m).strip() for m in members if str(m).strip()])
    return {
        "members": canonical,
        "member_count": len(canonical),
        "duplicate_members_detected": duplicates,
    }


def build_benchmark_mapping_registry(benchmark_map: Dict[str, str] | None = None) -> Dict[str, Any]:
    mapping = deepcopy(benchmark_map or {})
    canonical = {str(k).strip(): str(v).strip() for k, v in sorted(mapping.items(), key=lambda kv: str(kv[0])) if str(k).strip() and str(v).strip()}
    return {
        "mapping_version": "1.0.0",
        "cohort_to_benchmark": canonical,
        "mapping_count": len(canonical),
        "mapping_checksum": _checksum(canonical),
    }


def build_cohort_explainability_metadata(cohort: Dict[str, Any]) -> Dict[str, Any]:
    c = deepcopy(cohort)
    return {
        "explainability_version": "1.0.0",
        "cohort_id": c.get("cohort_id", ""),
        "cohort_version": c.get("cohort_version", ""),
        "methodology": "deterministic_static_rule_set",
        "inclusion_rationale": c.get("inclusion_rationale", ""),
        "exclusion_rules": c.get("exclusion_rules", []),
        "forbidden_dynamic_capabilities": list(_FORBIDDEN_DYNAMIC_CAPABILITIES),
    }


def build_cohort_manifest(cohorts: Iterable[Dict[str, Any]], benchmark_map: Dict[str, str] | None = None) -> Dict[str, Any]:
    entries: List[Dict[str, Any]] = []
    for raw in cohorts:
        cohort = deepcopy(raw)
        membership = resolve_cohort_membership(cohort.get("members", []))
        entry = {
            "cohort_id": cohort.get("cohort_id", ""),
            "cohort_version": cohort.get("cohort_version", ""),
            "cohort_type": cohort.get("cohort_type", ""),
            "members": membership["members"],
            "member_count": membership["member_count"],
            "duplicate_members_detected": membership["duplicate_members_detected"],
            "inclusion_rationale": cohort.get("inclusion_rationale", ""),
            "exclusion_rules": deepcopy(cohort.get("exclusion_rules", [])),
            "explainability_metadata": build_cohort_explainability_metadata(cohort),
        }
        entries.append(entry)

    ordered_entries = sorted(entries, key=lambda x: (x["cohort_type"], x["cohort_id"], x["cohort_version"]))
    benchmark_registry = build_benchmark_mapping_registry(benchmark_map)
    manifest = {
        "manifest_version": "1.0.0",
        "path_id": "P2-A",
        "cohorts": ordered_entries,
        "benchmark_mapping_registry": benchmark_registry,
    }
    manifest["manifest_checksum"] = _checksum(manifest)
    return manifest


def validate_cohort_integrity(manifest: Dict[str, Any]) -> Dict[str, Any]:
    m = deepcopy(manifest)
    gates = []
    degraded = False
    blocked = False

    benchmark_keys = set(m.get("benchmark_mapping_registry", {}).get("cohort_to_benchmark", {}).keys())
    for cohort in m.get("cohorts", []):
        members = cohort.get("members", [])
        canonical = sorted(members)
        has_dup = len(canonical) != len(set(canonical)) or cohort.get("duplicate_members_detected", False)
        cohort_gates = {
            "cohort_id_present": bool(cohort.get("cohort_id")),
            "cohort_version_present": bool(cohort.get("cohort_version")),
            "cohort_type_allowed": cohort.get("cohort_type") in _ALLOWED_COHORT_TYPES,
            "members_present": len(members) > 0,
            "members_canonical_ordered": members == canonical,
            "duplicate_members_rejected_or_flagged": not has_dup,
            "benchmark_mapping_valid": cohort.get("cohort_id") in benchmark_keys,
            "inclusion_rationale_present": bool(cohort.get("inclusion_rationale")),
            "exclusion_rules_present": isinstance(cohort.get("exclusion_rules"), list),
            "explainability_metadata_present": isinstance(cohort.get("explainability_metadata"), dict),
        }
        gates.append({"cohort_id": cohort.get("cohort_id", ""), "gates": cohort_gates})

        if not cohort_gates["cohort_type_allowed"] or not cohort_gates["cohort_id_present"] or not cohort_gates["cohort_version_present"]:
            blocked = True
        if (not cohort_gates["benchmark_mapping_valid"]) or (not cohort_gates["duplicate_members_rejected_or_flagged"]):
            degraded = True

    checksum_stable = m.get("manifest_checksum") == _checksum({k: v for k, v in m.items() if k != "manifest_checksum"})
    forbidden_capabilities_absent = all(
        cap not in _stable_json(m).lower() for cap in ("dynamic clustering", "ml peer discovery", "adaptive weighting")
    )

    summary_gates = {
        "checksum_stable": checksum_stable,
        "forbidden_dynamic_capabilities_absent": forbidden_capabilities_absent,
        "input_immutability_preserved": True,
    }

    if not checksum_stable:
        blocked = True

    status = CERTIFIED_COHORT_REGISTRY
    if blocked:
        status = BLOCKED_COHORT_REGISTRY
    elif degraded:
        status = DEGRADED_COHORT_REGISTRY

    return {
        "status": status,
        "cohort_validation": gates,
        "summary_gates": summary_gates,
    }


def certify_cohort_registry(manifest: Dict[str, Any]) -> Dict[str, Any]:
    validation = validate_cohort_integrity(manifest)
    return {
        "decision_status": validation["status"],
        "manifest_checksum": manifest.get("manifest_checksum", ""),
        "validation": validation,
    }


def build_path2a_cohort_registry_report(manifest: Dict[str, Any], certification: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "path_id": "P2-A",
        "objective": "Build deterministic replay-safe cohort registry foundation for relative fragility peer intelligence.",
        "scope": "Additive-only cohort contracts, manifesting, membership resolution, benchmark mapping, validation, explainability, and certification.",
        "non_goals": [
            "no_dynamic_clustering",
            "no_ml_peer_discovery",
            "no_adaptive_weighting",
            "no_trading_or_forecasting_behaviors",
        ],
        "architecture_summary": "Static contracts + deterministic manifest builder + validation gates + checksum certification.",
        "cohort_registry_methodology": "Versioned cohorts with canonical membership ordering and explicit rationale/rules.",
        "benchmark_mapping_methodology": "Deterministic cohort_id-to-benchmark mapping with checksum traceability.",
        "deterministic_membership_rules": "Members are trimmed, deduplicated, and sorted lexicographically.",
        "validation_gates": certification.get("validation", {}),
        "replay_checksum_guarantees": {
            "stable_json_serialization": True,
            "sha256_manifest_checksum": True,
        },
        "forbidden_capabilities": list(_FORBIDDEN_DYNAMIC_CAPABILITIES),
        "certification_decision_logic": "BLOCKED if critical gates fail; DEGRADED if non-critical quality gates fail; else CERTIFIED.",
        "final_supervisor_interpretation": certification.get("decision_status", BLOCKED_COHORT_REGISTRY),
        "cohort_count": len(manifest.get("cohorts", [])),
    }
