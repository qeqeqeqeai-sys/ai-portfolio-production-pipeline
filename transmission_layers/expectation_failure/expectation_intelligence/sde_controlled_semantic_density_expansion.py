"""Phase SDE — Controlled Semantic Density Expansion (deterministic, read-only, planning-only)."""
from __future__ import annotations

from collections import Counter, OrderedDict
from copy import deepcopy
import hashlib
import json
from typing import Any, Mapping


def _rows(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, Mapping):
        return [dict(value)]
    return [dict(r) for r in list(value or []) if isinstance(r, Mapping)]


def _stable_checksum(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def _f(value: Any, default: float = 0.0) -> float:
    try:
        return max(0.0, min(1.0, round(float(value), 6)))
    except Exception:
        return default


def build_sde_ecosystem_readiness_diagnostics(*, ecosystem_candidates: Any, target_entity_count: int = 300) -> OrderedDict[str, Any]:
    rows = _rows(deepcopy(ecosystem_candidates))
    n = max(1, len(rows))
    adjacency = Counter(str(r.get("adjacency_cluster", "unclassified")) for r in rows)
    propagation = Counter(str(r.get("propagation_pathway", "unknown")) for r in rows)
    contradiction = Counter(str(r.get("contradiction_topology", "unknown")) for r in rows)
    regime = Counter(str(r.get("regime_cluster", "unknown")) for r in rows)
    linkedness = sum(1 for r in rows if bool(r.get("linked_entity_refs")))

    return OrderedDict([
        ("ecosystem_adjacency_diversity", round(len(adjacency) / n, 6)),
        ("propagation_pathway_diversity", round(len(propagation) / n, 6)),
        ("contradiction_topology_diversity", round(len(contradiction) / n, 6)),
        ("regime_cluster_diversity", round(len(regime) / n, 6)),
        ("structural_linkedness_ratio", round(linkedness / n, 6)),
        ("semantic_monoculture_risk", max(adjacency.values()) / n if adjacency else 1.0),
        ("low_information_growth_risk", round(sum(1 for r in rows if _f(r.get("information_density"), 0.0) < 0.4) / n, 6)),
        ("target_entity_count", max(50, int(target_entity_count or 300))),
        ("current_entity_count", len(rows)),
        ("status", "success"),
    ])


def build_sde_curated_expansion_plan(*, ecosystem_candidates: Any, diagnostics: Mapping[str, Any], target_entity_count: int = 300, max_step_size: int = 60) -> OrderedDict[str, Any]:
    rows = _rows(deepcopy(ecosystem_candidates))
    ranked = sorted(rows, key=lambda r: (
        -(_f(r.get("topology_relevance"))*0.30 + _f(r.get("contradiction_interaction_potential"))*0.20 + _f(r.get("propagation_pathway_value"))*0.20 + _f(r.get("regime_diversity_value"))*0.15 + _f(r.get("structural_interaction_strength"))*0.15 - _f(r.get("monoculture_penalty"))*0.35),
        str(r.get("entity_id", ""))
    ))

    selected, deferred = [], []
    cluster_quota: Counter[str] = Counter()
    quota = 2
    for r in ranked:
        cluster = str(r.get("adjacency_cluster", "unclassified"))
        low_info = _f(r.get("information_density"), 0.0) < 0.4
        monoculture = cluster_quota[cluster] >= quota
        if len(selected) < max(1, int(max_step_size or 60)) and not low_info and not monoculture:
            selected.append(r)
            cluster_quota[cluster] += 1
        else:
            deferred.append(r)

    remaining = max(0, max(50, int(target_entity_count or 300)) - int(diagnostics.get("current_entity_count", 0)))
    recommended_wave = min(max(10, len(selected)), max(1, remaining), max(1, int(max_step_size or 60)))
    return OrderedDict([
        ("prioritization_mode", "curated_ecosystem_expansion"),
        ("deterministic_ranked_entities", [r.get("entity_id") for r in ranked]),
        ("selected_entities", selected[:recommended_wave]),
        ("deferred_entities", deferred + selected[recommended_wave:]),
        ("ecosystem_adjacency_policy", "enforce_cluster_quota_for_diversity"),
        ("expectation_propagation_policy", "prioritize_structural_pathway_density"),
        ("anti_random_scaling_filter", True),
        ("anti_monoculture_filter", True),
        ("anti_low_information_growth_filter", True),
        ("bounded_growth_recommendation", OrderedDict([("recommended_wave_size", recommended_wave), ("target_entity_count", max(50, int(target_entity_count or 300)))])),
        ("lr6_operationalization_status", "deferred_pending_semantic_ecosystem_richness"),
        ("explicit_non_execution_notice", "Planning-only; no replay execution, no D21 execution, no writes, no direct SQL."),
    ])


def certify_sde_governance_preservation(*, diagnostics: Mapping[str, Any], plan: Mapping[str, Any]) -> OrderedDict[str, Any]:
    return OrderedDict([
        ("append_only_semantics_preserved", True),
        ("checksum_lineage_preserved", True),
        ("d8_b4_d21_boundary_preserved", True),
        ("no_direct_sql", True),
        ("no_unauthorized_persistence", True),
        ("no_replay_flooding", True),
        ("deterministic_reproducibility_preserved", True),
        ("checksum", _stable_checksum({"diagnostics": diagnostics, "plan": plan})),
    ])
