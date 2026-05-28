from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

MAX_ENTITY_LIST = 10
MAX_NARRATIVES = 12
MAX_WARNING_COUNT = 8


def _governance_certification() -> dict[str, Any]:
    return {
        "observational_only_semantics": True,
        "no_prediction_or_trading_logic": True,
        "no_replay_activation": True,
        "no_topology_activation": True,
        "no_autonomous_orchestration": True,
        "no_cognition_persistence_introduced": True,
        "persistence_posture": "raw_input_only",
    }


def _safe_ratio(a: float, b: float) -> float:
    return round(a / b, 6) if b else 0.0


def _sorted_counter(counter: Counter[str]) -> dict[str, int]:
    return {k: counter[k] for k in sorted(counter)}


def _top_items(counter: Counter[str], k: int = MAX_ENTITY_LIST) -> list[dict[str, Any]]:
    rows = sorted(counter.items(), key=lambda x: (-x[1], x[0]))[:k]
    return [{"entity": e, "count": c} for e, c in rows]


def _extract_entities(rows: Iterable[dict[str, Any]]) -> list[str]:
    entities: list[str] = []
    for row in rows:
        for key in ("artifact_id", "entity", "symbol", "regime_morphology_class", "transition_shape_class"):
            v = row.get(key)
            if isinstance(v, str) and v:
                entities.append(v)
                break
    return entities


def build_hist_review1_summary(hist7_payload: dict[str, Any], *, execution_id: str = "HIST_REVIEW1_DETERMINISTIC") -> dict[str, Any]:
    evidence = list(hist7_payload.get("saturation_evidence_records", []))
    score = hist7_payload.get("saturation_scorecard", {})
    observations = hist7_payload.get("saturation_observation_summary", {})

    morphology_counter = Counter(r.get("regime_morphology_class", "unknown") for r in evidence)
    topology_counter = Counter(r.get("transition_shape_class", "unknown") for r in evidence)
    frag_counter = Counter(r.get("fragmentation_propagation_class", "unknown") for r in evidence)

    entities = _extract_entities(evidence)
    entity_counter = Counter(entities)

    artifact_count = max(int(score.get("artifact_count", len(evidence) or 1)), 1)
    unique_morph = len(morphology_counter)
    unique_topo = len(topology_counter)
    repeated_count = sum(v for v in morphology_counter.values() if v > 1)

    metrics = {
        "topology_concentration_ratio": _safe_ratio(max(topology_counter.values(), default=0), artifact_count),
        "morphology_diversity_ratio": _safe_ratio(unique_morph, artifact_count),
        "recurrence_density_ratio": _safe_ratio(repeated_count, artifact_count),
        "continuity_density_ratio": _safe_ratio(len([v for v in entity_counter.values() if v > 1]), max(len(entity_counter), 1)),
        "saturation_pressure_ratio": _safe_ratio(artifact_count - unique_morph, artifact_count),
    }

    continuity_review = {
        "persistent_entities": _top_items(Counter({k: v for k, v in entity_counter.items() if v > 1})),
        "recurring_observational_motifs": _top_items(morphology_counter),
        "longitudinal_continuity_density": metrics["continuity_density_ratio"],
        "continuity_crowding_indicator": score.get("continuity_crowding_class", "unknown"),
        "continuity_fragmentation_indicator": "elevated" if frag_counter.get("high_fragmentation_propagation", 0) > 0 else "contained",
    }

    recurrence_review = {
        "recurrence_frequency_distribution": _sorted_counter(morphology_counter),
        "high_recurrence_clusters": [r for r in _top_items(morphology_counter) if r["count"] >= 2],
        "low_recurrence_sparse_regions": [k for k, v in sorted(morphology_counter.items()) if v == 1][:MAX_ENTITY_LIST],
        "recurrence_stability_indicator": score.get("structural_density_class", "unknown"),
        "recurrence_asymmetry_observation": "asymmetric" if len(set(morphology_counter.values())) > 1 else "balanced",
    }

    morphology_review = {
        "topology_concentration": score.get("topology_concentration_class", "unknown"),
        "morphology_diversity": score.get("morphology_diversity_class", "unknown"),
        "monoculture_indicator": unique_topo == 1,
        "structural_clustering_summaries": _top_items(topology_counter),
        "topology_sparsity_indicator": "sparse" if unique_topo <= 2 else "distributed",
    }

    saturation_review = {
        "saturation_density": score.get("ecology_saturation_class", "unknown"),
        "repeated_observational_convergence": repeated_count,
        "over_concentrated_structures": [k for k, v in sorted(topology_counter.items()) if v / artifact_count >= 0.67],
        "saturation_instability_markers": [k for k, v in sorted(frag_counter.items()) if "high" in k and v > 0],
    }

    temporal_review = {
        "early_vs_later_ecology_differences": "bounded artifact-level contrast only",
        "continuity_maturation_observation": "continuity density increased in later windows" if metrics["continuity_density_ratio"] >= 0.5 else "continuity remained sparse across windows",
        "recurrence_stabilization_observation": "recurrence structures remain sparse but stabilizing" if metrics["recurrence_density_ratio"] <= 0.5 else "recurrence concentration remained elevated",
        "topology_broadening_narrowing_trend": "narrowing" if metrics["topology_concentration_ratio"] >= 0.67 else "broadening_or_mixed",
    }

    narratives = [
        temporal_review["recurrence_stabilization_observation"],
        temporal_review["continuity_maturation_observation"],
        "topology concentration remains elevated" if metrics["topology_concentration_ratio"] >= 0.67 else "topology concentration remained mixed",
        "morphology diversity improved modestly" if metrics["morphology_diversity_ratio"] >= 0.5 else "morphology diversity remained constrained",
    ][:MAX_NARRATIVES]

    warnings = []
    if artifact_count <= 1:
        warnings.append("single_artifact_input_limits_temporal_resolution")
    if len(evidence) > 500:
        warnings.append("evidence_truncated_recommended")
    warnings = warnings[:MAX_WARNING_COUNT]

    return {
        "schema_version": "hist_review1_v1",
        "execution_metadata": {
            "execution_id": execution_id,
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "artifact_count": artifact_count,
            "evidence_count": len(evidence),
        },
        "governance_certification": _governance_certification(),
        "review_metrics": metrics,
        "continuity_review": continuity_review,
        "recurrence_ecology_review": recurrence_review,
        "morphology_review": morphology_review,
        "saturation_review": saturation_review,
        "temporal_evolution_review": temporal_review,
        "operator_interpretability_helpers": {
            "top_recurring_entities": _top_items(entity_counter),
            "most_persistent_entities": continuity_review["persistent_entities"],
            "sparse_continuity_entities": [k for k, v in sorted(entity_counter.items()) if v == 1][:MAX_ENTITY_LIST],
            "topology_cluster_summaries": _top_items(topology_counter),
            "recurrence_imbalance_summaries": recurrence_review["high_recurrence_clusters"],
        },
        "bounded_narratives": narratives,
        "observational_findings": list(observations.get("saturation_observation_notes", []))[:MAX_NARRATIVES],
        "review_warnings": warnings,
        "next_phase_recommendations": [
            "Expand longitudinal window count while preserving bounded deterministic review outputs.",
            "Perform operator-led recurrence drift inspection before any new cognition-layer expansion.",
        ],
    }


def render_hist_review1_markdown(summary: dict[str, Any]) -> str:
    sections = [
        ("Execution Metadata", "execution_metadata"),
        ("Governance Certification", "governance_certification"),
        ("Review Metrics", "review_metrics"),
        ("Continuity Review", "continuity_review"),
        ("Recurrence Ecology Review", "recurrence_ecology_review"),
        ("Morphology Review", "morphology_review"),
        ("Saturation Review", "saturation_review"),
        ("Temporal Evolution Review", "temporal_evolution_review"),
    ]
    lines = ["# HIST-REVIEW-1 Longitudinal Ecology Review"]
    for title, key in sections:
        lines += [f"## {title}", json.dumps(summary[key], sort_keys=True)]
    lines += ["## Bounded Narratives", json.dumps(summary["bounded_narratives"], sort_keys=True)]
    lines += ["## Review Warnings", json.dumps(summary["review_warnings"], sort_keys=True)]
    lines += ["## Next-Phase Recommendations", json.dumps(summary["next_phase_recommendations"], sort_keys=True)]
    return "\n".join(lines)


def run_hist_review1(hist7_payload: dict[str, Any], *, output_root: str = "reports/hist_review1", execution_id: str = "HIST_REVIEW1_DETERMINISTIC") -> dict[str, Any]:
    summary = build_hist_review1_summary(hist7_payload, execution_id=execution_id)
    root = Path(output_root)
    root.mkdir(parents=True, exist_ok=True)
    (root / "hist_review1_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    (root / "hist_review1_summary.md").write_text(render_hist_review1_markdown(summary), encoding="utf-8")
    return summary
