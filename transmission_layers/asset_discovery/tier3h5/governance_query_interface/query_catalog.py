from __future__ import annotations

QUERY_TYPES: tuple[str, ...] = (
    "inspect_advisory_only_preservation",
    "inspect_artifact",
    "inspect_exact_match_only_preservation",
    "inspect_invariant",
    "inspect_phase",
    "inspect_posture",
    "inspect_release_readiness",
    "inspect_tier3h4_freeze_boundary",
    "list_artifacts_by_phase",
    "list_artifacts_verifying_invariant",
    "list_governance_artifacts",
    "list_governance_phases",
    "list_invariants",
    "list_lineage_paths",
    "list_phase_dependencies",
    "list_reachability_records",
)


def build_query_catalog() -> dict[str, object]:
    return {
        "query_catalog_status": "generated",
        "query_types": list(QUERY_TYPES),
        "query_types_registered": len(QUERY_TYPES),
        "exact_query_type_matching_only": True,
        "semantic_querying_absent": True,
        "fuzzy_matching_absent": True,
        "llm_driven_query_answering_absent": True,
    }
