from __future__ import annotations

import json
from collections import Counter
from copy import deepcopy
from pathlib import Path
from typing import Any, Sequence

from transmission_layers.expectation_failure.real_data.ops_hist6_regime_morphology_observation import OPS_HIST6_SCHEMA_VERSION

OPS_HIST7_SCHEMA_VERSION = "ops_hist7_v1"
SOURCE_SCHEMA_VERSION = OPS_HIST6_SCHEMA_VERSION


def _governance_flags() -> dict[str, Any]:
    return {
        "observational_only": True,
        "historical_observation_mode": True,
        "continuity_intelligence_mode": True,
        "continuity_compression_mode": True,
        "archetype_observation_mode": True,
        "recurrence_ecology_mode": True,
        "archetype_persistence_observation_mode": True,
        "temporal_regime_observation_mode": True,
        "regime_morphology_observation_mode": True,
        "regime_ecology_saturation_mode": True,
        "no_recursive_replay_operationalization": True,
        "no_autonomous_replay": True,
        "no_topology_activation": True,
        "no_self_modifying_pathways": True,
        "no_prediction_or_trading_execution": True,
        "no_graph_execution_engines": True,
        "no_high_frequency_streaming": True,
        "persistence_mode": "local_json_only",
        "supabase_write_enabled": False,
        "repo_writeback_enabled": False,
        "orchestration_enabled": False,
        "streaming_enabled": False,
    }


def load_ops_hist6_payload(input_json: str) -> dict[str, Any]:
    return json.loads(Path(input_json).read_text(encoding="utf-8"))


def load_ops_hist6_payloads_from_dir(input_dir: str) -> list[dict[str, Any]]:
    return [json.loads(p.read_text(encoding="utf-8")) for p in sorted(Path(input_dir).glob("*.json"), key=lambda p: p.name)]


def _ensure_hist6(payloads: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    if not payloads:
        raise ValueError("OPS-HIST-7 fails closed: no OPS-HIST-6 payload provided")
    valid = [p for p in payloads if p and p.get("schema_version") == SOURCE_SCHEMA_VERSION]
    if not valid:
        raise ValueError("OPS-HIST-7 requires source_schema_version ops_hist6_v1 payload")
    return sorted(valid, key=lambda p: (p.get("snapshot_start_date", ""), p.get("snapshot_end_date", ""), json.dumps(p.get("morphology_scorecard", {}), sort_keys=True)))


def _classify_ratio(r: float, labels: list[str]) -> str:
    if r >= 0.9:
        return labels[3]
    if r >= 0.67:
        return labels[2]
    if r >= 0.34:
        return labels[1]
    return labels[0]


def build_ops_hist7_regime_ecology_saturation(hist6_payloads: Sequence[dict[str, Any]] | dict[str, Any]) -> dict[str, Any]:
    payloads = _ensure_hist6([hist6_payloads] if isinstance(hist6_payloads, dict) else list(hist6_payloads))
    governance = _governance_flags()
    artifact_count = len(payloads)
    saturation_depth = "single_artifact_saturation_observation" if artifact_count == 1 else "multi_artifact_saturation_observation"
    start_date = min(p.get("snapshot_start_date", "") for p in payloads)
    end_date = max(p.get("snapshot_end_date", "") for p in payloads)
    reviewed_total = sum(int(p.get("reviewed_snapshot_count_total", 0)) for p in payloads)

    rows = []
    for i, p in enumerate(payloads):
        s = p.get("morphology_scorecard", {})
        rows.append({
            "source_artifact_index": i,
            "artifact_id": p.get("artifact_id", f"hist6_artifact_{i}"),
            "snapshot_start_date": p.get("snapshot_start_date", ""),
            "snapshot_end_date": p.get("snapshot_end_date", ""),
            "reviewed_snapshot_count_total": int(p.get("reviewed_snapshot_count_total", 0)),
            "morphology_depth": p.get("morphology_depth", ""),
            "regime_morphology_class": s.get("regime_morphology_class", "mixed_regime_morphology"),
            "transition_shape_class": s.get("transition_shape_class", "mixed_transition_shape"),
            "fragmentation_propagation_class": s.get("fragmentation_propagation_class", "moderate_fragmentation_propagation"),
            "stability_deformation_class": s.get("stability_deformation_class", "moderate_stability_deformation"),
        })

    morphology_counts = Counter(r["regime_morphology_class"] for r in rows)
    topology_counts = Counter(r["transition_shape_class"] for r in rows)
    frag_high = sum(1 for r in rows if r["fragmentation_propagation_class"] == "high_fragmentation_propagation")
    stable_low = sum(1 for r in rows if r["stability_deformation_class"] == "low_stability_deformation")
    repeated = sum(v for v in morphology_counts.values() if v > 1)
    dominant = max(morphology_counts.values())
    diversity = len(morphology_counts)

    ecology_saturation_class = _classify_ratio(dominant / artifact_count, ["low_ecology_saturation", "moderate_ecology_saturation", "high_ecology_saturation", "concentrated_ecology_saturation"])
    structural_density_class = _classify_ratio(repeated / artifact_count, ["sparse_structural_density", "moderate_structural_density", "dense_structural_density", "highly_dense_structural_density"])
    continuity_crowding_class = _classify_ratio((artifact_count - diversity) / max(1, artifact_count), ["low_continuity_crowding", "moderate_continuity_crowding", "high_continuity_crowding", "high_continuity_crowding"])
    morphology_diversity_class = (
        "highly_diversified_morphology" if diversity == artifact_count else
        "diversified_morphology" if diversity >= max(2, artifact_count // 2) else
        "moderately_concentrated_morphology" if diversity > 1 else
        "concentrated_morphology"
    )
    topology_concentration_class = (
        "topology_monoculture" if len(topology_counts) == 1 and artifact_count > 1 else
        "concentrated_topology" if max(topology_counts.values()) / artifact_count >= 0.67 else
        "mixed_topology" if len(topology_counts) > 1 else
        "distributed_topology"
    )
    stability_density_class = _classify_ratio((artifact_count - stable_low) / artifact_count, ["low_stability_density", "moderate_stability_density", "high_stability_density", "high_stability_density"])

    scorecard = {
        "artifact_count": artifact_count,
        "saturation_depth": saturation_depth,
        "snapshot_start_date": start_date,
        "snapshot_end_date": end_date,
        "reviewed_snapshot_count_total": reviewed_total,
        "ecology_saturation_class": ecology_saturation_class,
        "structural_density_class": structural_density_class,
        "continuity_crowding_class": continuity_crowding_class,
        "morphology_diversity_class": morphology_diversity_class,
        "topology_concentration_class": topology_concentration_class,
        "stability_density_class": stability_density_class,
    }

    evidence = []
    for r in rows:
        evidence.append({
            "schema_version": OPS_HIST7_SCHEMA_VERSION,
            "source_schema_version": SOURCE_SCHEMA_VERSION,
            "artifact_id": r["artifact_id"],
            "source_artifact_index": r["source_artifact_index"],
            "snapshot_start_date": r["snapshot_start_date"],
            "snapshot_end_date": r["snapshot_end_date"],
            "reviewed_snapshot_count_total": r["reviewed_snapshot_count_total"],
            "morphology_depth": r["morphology_depth"],
            "regime_morphology_class": r["regime_morphology_class"],
            "transition_shape_class": r["transition_shape_class"],
            "fragmentation_propagation_class": r["fragmentation_propagation_class"],
            "stability_deformation_class": r["stability_deformation_class"],
            "ecology_saturation_label": ecology_saturation_class,
            "structural_density_marker": structural_density_class,
            "continuity_crowding_marker": continuity_crowding_class,
            "morphology_diversity_marker": morphology_diversity_class,
            "descriptive_rationale": "Historical period ecology saturation observed from OPS-HIST-6 morphology artifacts only.",
            "governance_metadata": deepcopy(governance),
        })

    density_rows = [{"structural_density_class": structural_density_class, "repeated_structure_count": repeated, "artifact_count": artifact_count}]
    continuity_rows = [{"continuity_crowding_class": continuity_crowding_class, "continuity_crowding_count": artifact_count - diversity}]
    recurrence_rows = [{"recurrence_congestion_class": structural_density_class, "repeated_morphology_count": repeated}]
    topology_rows = [{"topology_concentration_class": topology_concentration_class, "topology_shape_count": len(topology_counts)}]
    diversity_rows = [{"morphology_diversity_class": morphology_diversity_class, "morphology_class_count": diversity}]
    stability_rows = [{"stability_density_class": stability_density_class, "stable_low_density_count": stable_low}]
    collapse_rows = [{"morphology_collapse_marker": "fragmented" if frag_high > 0 else "stable", "high_fragmentation_observed_count": frag_high}]

    observation = {
        "saturation_counts": {
            "regime_morphology_counts": dict(sorted(morphology_counts.items())),
            "transition_shape_counts": dict(sorted(topology_counts.items())),
        },
        "density_rows": density_rows,
        "continuity_crowding_rows": continuity_rows,
        "recurrence_congestion_rows": recurrence_rows,
        "topology_concentration_rows": topology_rows,
        "morphology_diversity_rows": diversity_rows,
        "stability_density_rows": stability_rows,
        "morphology_collapse_rows": collapse_rows,
        "saturation_observation_notes": [
            "Saturation observed from OPS-HIST-6 morphology artifacts only.",
            "Single artifact saturation observation is bounded and does not imply extended historical period saturation.",
            "No prediction, trading execution, replay activation, topology activation, orchestration, or streaming observed.",
        ],
    }

    streamlit = {
        "schema_version": OPS_HIST7_SCHEMA_VERSION,
        "source_schema_version": SOURCE_SCHEMA_VERSION,
        "saturation_scorecard_panel": [scorecard],
        "structural_density_timeline": density_rows,
        "continuity_crowding_table": continuity_rows,
        "recurrence_congestion_panel": recurrence_rows,
        "morphology_diversity_panel": diversity_rows,
        "topology_concentration_panel": topology_rows,
        "stability_density_panel": stability_rows,
        "morphology_collapse_panel": collapse_rows,
        "saturation_evidence_table": evidence,
        "governance_boundary_panel": [{"boundary": k, "value": v} for k, v in sorted(governance.items())],
    }

    canonical = {
        "schema_version": OPS_HIST7_SCHEMA_VERSION,
        "source_schema_version": SOURCE_SCHEMA_VERSION,
        "hist7_saturation_scorecard_rows": [scorecard],
        "hist7_structural_density_rows": density_rows,
        "hist7_continuity_crowding_rows": continuity_rows,
        "hist7_recurrence_congestion_rows": recurrence_rows,
        "hist7_topology_concentration_rows": topology_rows,
        "hist7_morphology_diversity_rows": diversity_rows,
        "hist7_stability_density_rows": stability_rows,
        "hist7_morphology_collapse_rows": collapse_rows,
        "hist7_saturation_evidence_rows": evidence,
        "hist7_governance_rows": [{"key": k, "value": v} for k, v in sorted(governance.items())],
    }

    return {
        "status": "ok",
        "schema_version": OPS_HIST7_SCHEMA_VERSION,
        "source_schema_version": SOURCE_SCHEMA_VERSION,
        "artifact_count": artifact_count,
        "saturation_depth": saturation_depth,
        "snapshot_start_date": start_date,
        "snapshot_end_date": end_date,
        "reviewed_snapshot_count_total": reviewed_total,
        "regime_ecology_saturation_summary": "Regime ecology saturation observed as low, moderate, high, or concentrated across historical period morphology artifacts.",
        "structural_density_summary": "Structural density observed from repeated morphology and transition continuity across artifacts.",
        "continuity_crowding_summary": "Continuity crowding observed from recurring morphology occupancy across historical period sequence.",
        "recurrence_congestion_summary": "Recurrence congestion observed from repeated morphology concentration across bounded artifacts.",
        "morphology_diversity_summary": "Morphology diversity observed from concentrated and diversified morphology class distribution.",
        "topology_concentration_summary": "Topology concentration observed from distributed, mixed, or concentrated transition shape classes.",
        "stability_density_interaction_summary": "Stability density interaction observed from stable and mixed deformation density markers.",
        "ecology_fragmentation_distribution_summary": "Ecology fragmentation distribution observed from low, moderate, and high fragmentation propagation classes.",
        "morphology_collapse_observation_summary": "Morphology collapse observation summary is descriptive and bounded to observed fragmentation markers.",
        "saturation_scorecard": scorecard,
        "saturation_observation_summary": observation,
        "saturation_evidence_records": evidence,
        "governance_metadata": governance,
        "streamlit_saturation_payload": streamlit,
        "canonical_table_payload": canonical,
    }


def render_ops_hist7_regime_ecology_saturation_markdown(review: dict[str, Any]) -> str:
    return "\n".join([
        "# OPS-HIST-7 Regime Ecology Saturation & Structural Density Observation",
        "## Objective",
        "Observe regime ecology saturation, structural density, continuity crowding, recurrence congestion, topology concentration, and morphology diversity across historical period morphology artifacts.",
        "## Source Morphology Coverage",
        f"{review['artifact_count']} artifacts from {review['snapshot_start_date']} to {review['snapshot_end_date']} ({review['reviewed_snapshot_count_total']} reviewed snapshots).",
        "## Saturation Scorecard", json.dumps(review["saturation_scorecard"], sort_keys=True),
        "## Regime Ecology Saturation Summary", review["regime_ecology_saturation_summary"],
        "## Structural Density Summary", review["structural_density_summary"],
        "## Continuity Crowding Summary", review["continuity_crowding_summary"],
        "## Recurrence Congestion Summary", review["recurrence_congestion_summary"],
        "## Morphology Diversity Summary", review["morphology_diversity_summary"],
        "## Topology Concentration Summary", review["topology_concentration_summary"],
        "## Stability Density Interaction Summary", review["stability_density_interaction_summary"],
        "## Morphology Collapse Observation Summary", review["morphology_collapse_observation_summary"],
        "## Saturation Evidence Summary", f"{len(review['saturation_evidence_records'])} saturation evidence records observed.",
        "## Governance Certification", "Observational historical regime ecology saturation observation only.",
        "## Explicit Forbidden Boundaries", "No prediction/trading/replay/topology/graph execution/orchestration/streaming activation observed.",
        "## Future Expansion Recommendation", "Continue bounded deterministic ecology saturation observation using stable schema rows.",
    ])
