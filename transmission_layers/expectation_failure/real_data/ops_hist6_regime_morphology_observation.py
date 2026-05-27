from __future__ import annotations

import json
from collections import Counter
from copy import deepcopy
from pathlib import Path
from typing import Any, Sequence

from transmission_layers.expectation_failure.real_data.ops_hist5_temporal_continuity_regimes import OPS_HIST5_SCHEMA_VERSION

OPS_HIST6_SCHEMA_VERSION = "ops_hist6_v1"
SOURCE_SCHEMA_VERSION = OPS_HIST5_SCHEMA_VERSION


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


def load_ops_hist5_payload(input_json: str) -> dict[str, Any]:
    return json.loads(Path(input_json).read_text(encoding="utf-8"))


def load_ops_hist5_payloads_from_dir(input_dir: str) -> list[dict[str, Any]]:
    return [json.loads(p.read_text(encoding="utf-8")) for p in sorted(Path(input_dir).glob("*.json"), key=lambda p: p.name)]


def _ensure_hist5(payloads: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    if not payloads:
        raise ValueError("OPS-HIST-6 fails closed: no OPS-HIST-5 payload provided")
    valid = [p for p in payloads if p and p.get("schema_version") == SOURCE_SCHEMA_VERSION]
    if not valid:
        raise ValueError("OPS-HIST-6 requires source_schema_version ops_hist5_v1 payload")
    return sorted(valid, key=lambda p: (p.get("snapshot_start_date", ""), p.get("snapshot_end_date", ""), json.dumps(p.get("temporal_regime_scorecard", {}), sort_keys=True)))


def _to_numeric(label: str) -> int:
    return {"stable_temporal_regime": 0, "mixed_temporal_regime": 1, "fragmented_temporal_regime": 2, "transition_heavy_temporal_regime": 3}.get(label, 1)


def _transition_shape_class(changes: int, artifact_count: int) -> str:
    if artifact_count < 2:
        return "insufficient_transition_shape"
    density = changes / max(1, artifact_count - 1)
    return "abrupt_transition_shape" if density >= 0.67 else ("mixed_transition_shape" if density >= 0.34 else "smooth_transition_shape")


def build_ops_hist6_regime_morphology_observation(hist5_payloads: Sequence[dict[str, Any]] | dict[str, Any]) -> dict[str, Any]:
    payloads = _ensure_hist5([hist5_payloads] if isinstance(hist5_payloads, dict) else list(hist5_payloads))
    governance = _governance_flags()
    artifact_count = len(payloads)
    morphology_depth = "single_artifact_morphology_observation" if artifact_count == 1 else "multi_artifact_morphology_observation"
    start_date = min(p.get("snapshot_start_date", "") for p in payloads)
    end_date = max(p.get("snapshot_end_date", "") for p in payloads)
    reviewed_total = sum(int(p.get("reviewed_snapshot_count_total", 0)) for p in payloads)

    rows = []
    for i, p in enumerate(payloads):
        s = p.get("temporal_regime_scorecard", {})
        rows.append({
            "source_artifact_index": i,
            "artifact_id": p.get("artifact_id", f"hist5_artifact_{i}"),
            "snapshot_start_date": p.get("snapshot_start_date", ""),
            "snapshot_end_date": p.get("snapshot_end_date", ""),
            "reviewed_snapshot_count_total": int(p.get("reviewed_snapshot_count_total", 0)),
            "regime_depth": p.get("regime_depth", ""),
            "temporal_regime_class": s.get("temporal_regime_class", "mixed_temporal_regime"),
            "regime_transition_class": s.get("regime_transition_class", "moderate_transition_density"),
            "regime_stability_class": s.get("regime_stability_class", "mixed_window_stability"),
            "regime_fragmentation_class": s.get("regime_fragmentation_class", "moderate_regime_fragmentation"),
        })

    classes = [r["temporal_regime_class"] for r in rows]
    numeric = [_to_numeric(c) for c in classes]
    class_counts = Counter(classes)
    changes = sum(1 for i in range(1, len(classes)) if classes[i] != classes[i - 1])
    avg_abs_delta = round(sum(abs(numeric[i] - numeric[i - 1]) for i in range(1, len(numeric))) / max(1, len(numeric) - 1), 6)
    frag_high = sum(1 for r in rows if r["regime_fragmentation_class"] == "high_regime_fragmentation")
    unstable = sum(1 for r in rows if r["regime_stability_class"] == "unstable_window_dominant")
    discont = sum(1 for i in range(1, len(numeric)) if abs(numeric[i] - numeric[i - 1]) >= 2)

    transition_shape_class = _transition_shape_class(changes, artifact_count)
    regime_morphology_class = "stable_regime_morphology" if changes == 0 else ("gradual_regime_morphology" if discont == 0 else ("discontinuous_regime_morphology" if discont >= max(1, artifact_count // 2) else "mixed_regime_morphology"))
    fragmentation_propagation_class = "high_fragmentation_propagation" if frag_high >= max(1, artifact_count // 2) else ("moderate_fragmentation_propagation" if frag_high > 0 else "low_fragmentation_propagation")
    stability_deformation_class = "high_stability_deformation" if unstable >= max(1, artifact_count // 2) else ("moderate_stability_deformation" if unstable > 0 else "low_stability_deformation")
    persistence_morphology_class = "insufficient_persistence_structure" if artifact_count == 1 else ("persistent_structure_stable" if changes == 0 else ("persistent_structure_fragmented" if transition_shape_class == "abrupt_transition_shape" else "persistent_structure_shifted"))

    evidence = []
    seq_rows = []
    for i, r in enumerate(rows):
        prev = rows[i - 1]["temporal_regime_class"] if i > 0 else None
        marker = "smoothed" if prev == r["temporal_regime_class"] else ("clustered" if i == 0 else "transformed")
        transition_marker = "stable" if marker == "smoothed" else ("mixed" if marker == "clustered" else "discontinuous")
        deformation_marker = "stable" if r["regime_stability_class"] == "stable_window_dominant" else ("mixed" if r["regime_stability_class"] == "mixed_window_stability" else "fragmented")
        discontinuity_marker = "discontinuous" if i > 0 and abs(numeric[i] - numeric[i - 1]) >= 2 else "stable"
        seq_rows.append({"sequence_index": i, "artifact_id": r["artifact_id"], "temporal_regime_class": r["temporal_regime_class"], "morphology_label": marker})
        evidence.append({
            "schema_version": OPS_HIST6_SCHEMA_VERSION, "source_schema_version": SOURCE_SCHEMA_VERSION,
            "artifact_id": r["artifact_id"], "source_artifact_index": i,
            "snapshot_start_date": r["snapshot_start_date"], "snapshot_end_date": r["snapshot_end_date"],
            "reviewed_snapshot_count_total": r["reviewed_snapshot_count_total"], "regime_depth": r["regime_depth"],
            "temporal_regime_class": r["temporal_regime_class"], "regime_transition_class": r["regime_transition_class"],
            "regime_stability_class": r["regime_stability_class"], "regime_fragmentation_class": r["regime_fragmentation_class"],
            "morphology_label": marker, "transition_shape_marker": transition_marker,
            "deformation_marker": deformation_marker, "discontinuity_marker": discontinuity_marker,
            "descriptive_rationale": "Historical period regime morphology observed from OPS-HIST-5 regime artifacts only.",
            "governance_metadata": deepcopy(governance),
        })

    scorecard = {
        "artifact_count": artifact_count, "morphology_depth": morphology_depth,
        "snapshot_start_date": start_date, "snapshot_end_date": end_date,
        "reviewed_snapshot_count_total": reviewed_total,
        "regime_morphology_class": regime_morphology_class,
        "transition_shape_class": transition_shape_class,
        "fragmentation_propagation_class": fragmentation_propagation_class,
        "stability_deformation_class": stability_deformation_class,
        "persistence_morphology_class": persistence_morphology_class,
    }

    transition_shape_rows = [{"transition_shape_class": transition_shape_class, "transition_count_observed": changes, "artifact_count": artifact_count}]
    deformation_rows = [{"regime_morphology_class": regime_morphology_class, "average_morphology_drift_observed": avg_abs_delta}]
    fragmentation_rows = [{"fragmentation_propagation_class": fragmentation_propagation_class, "high_fragmentation_observed_count": frag_high}]
    stability_rows = [{"stability_deformation_class": stability_deformation_class, "unstable_window_observed_count": unstable}]
    discontinuity_rows = [{"discontinuity_observed_count": discont, "discontinuity_marker": "discontinuous" if discont > 0 else "stable"}]
    persistence_rows = [{"persistence_morphology_class": persistence_morphology_class, "observed_transition_shape": transition_shape_class}]

    streamlit = {"schema_version": OPS_HIST6_SCHEMA_VERSION, "source_schema_version": SOURCE_SCHEMA_VERSION,
        "morphology_scorecard_panel": [scorecard], "morphology_sequence_timeline": seq_rows, "transition_shape_table": transition_shape_rows,
        "deformation_table": deformation_rows, "fragmentation_propagation_panel": fragmentation_rows, "stability_deformation_panel": stability_rows,
        "discontinuity_observation_panel": discontinuity_rows, "persistence_morphology_panel": persistence_rows,
        "morphology_evidence_table": evidence, "governance_boundary_panel": [{"boundary": k, "value": v} for k, v in sorted(governance.items())]}

    canonical = {"schema_version": OPS_HIST6_SCHEMA_VERSION, "source_schema_version": SOURCE_SCHEMA_VERSION,
        "hist6_morphology_scorecard_rows": [scorecard], "hist6_morphology_sequence_rows": seq_rows,
        "hist6_transition_shape_rows": transition_shape_rows, "hist6_deformation_rows": deformation_rows,
        "hist6_fragmentation_propagation_rows": fragmentation_rows, "hist6_stability_deformation_rows": stability_rows,
        "hist6_discontinuity_observation_rows": discontinuity_rows, "hist6_persistence_morphology_rows": persistence_rows,
        "hist6_morphology_evidence_rows": evidence, "hist6_governance_rows": [{"key": k, "value": v} for k, v in sorted(governance.items())]}

    return {
        "status": "ok", "schema_version": OPS_HIST6_SCHEMA_VERSION, "source_schema_version": SOURCE_SCHEMA_VERSION,
        "artifact_count": artifact_count, "morphology_depth": morphology_depth, "snapshot_start_date": start_date, "snapshot_end_date": end_date,
        "reviewed_snapshot_count_total": reviewed_total,
        "regime_morphology_summary": "Regime morphology observed as stable, shifted, mixed, or discontinuous across historical period artifacts.",
        "structural_transition_shape_summary": "Structural transition shape observed from sequential regime class changes.",
        "regime_deformation_summary": "Regime deformation observed through morphology drift across historical period sequence.",
        "fragmentation_propagation_summary": "Fragmentation propagation observed through repeated high-fragmented regime states.",
        "stability_deformation_summary": "Stability deformation observed from mixed and unstable window classifications.",
        "discontinuity_observation_summary": "Discontinuity markers observed from widened regime class jumps.",
        "persistence_structure_morphology_summary": "Persistence structure morphology observed from transition smoothness and repeated structure.",
        "transition_smoothness_summary": "Transition smoothness observed from transition shape classification.",
        "morphology_scorecard": scorecard,
        "morphology_observation_summary": {"morphology_counts": dict(sorted(class_counts.items())), "transition_shape_rows": transition_shape_rows,
            "deformation_rows": deformation_rows, "fragmentation_propagation_rows": fragmentation_rows,
            "stability_deformation_rows": stability_rows, "discontinuity_observation_rows": discontinuity_rows,
            "persistence_morphology_rows": persistence_rows,
            "morphology_observation_notes": ["Morphology observed from OPS-HIST-5 temporal regime artifacts only.", "No prediction, trading execution, replay activation, topology activation, orchestration, or streaming observed."]},
        "morphology_evidence_records": evidence, "governance_metadata": governance,
        "streamlit_morphology_payload": streamlit, "canonical_table_payload": canonical,
    }


def render_ops_hist6_regime_morphology_markdown(review: dict[str, Any]) -> str:
    return "\n".join([
        "# OPS-HIST-6 Regime Morphology & Structural Transition Observation", "## Objective", "Observe how temporal continuity regimes structurally morph across bounded historical period artifacts.",
        "## Source Temporal Regime Coverage", f"{review['artifact_count']} artifacts from {review['snapshot_start_date']} to {review['snapshot_end_date']} ({review['reviewed_snapshot_count_total']} reviewed snapshots).",
        "## Morphology Scorecard", json.dumps(review["morphology_scorecard"], sort_keys=True),
        "## Regime Morphology Summary", review["regime_morphology_summary"], "## Structural Transition Shape Summary", review["structural_transition_shape_summary"],
        "## Regime Deformation Summary", review["regime_deformation_summary"], "## Fragmentation Propagation Summary", review["fragmentation_propagation_summary"],
        "## Stability Deformation Summary", review["stability_deformation_summary"], "## Discontinuity Observation Summary", review["discontinuity_observation_summary"],
        "## Persistence Morphology Summary", review["persistence_structure_morphology_summary"],
        "## Morphology Evidence Summary", f"{len(review['morphology_evidence_records'])} morphology evidence records observed.",
        "## Governance Certification", "Observational historical regime morphology observation only.",
        "## Explicit Forbidden Boundaries", "No prediction/trading/replay/topology/graph execution/orchestration/streaming activation observed.",
        "## Future Expansion Recommendation", "Continue bounded deterministic morphology observation using stable schema rows.",
    ])
