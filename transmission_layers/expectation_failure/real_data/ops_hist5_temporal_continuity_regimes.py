from __future__ import annotations

import json
from collections import Counter
from copy import deepcopy
from pathlib import Path
from typing import Any, Sequence

from transmission_layers.expectation_failure.real_data.ops_hist4_archetype_recurrence_ecology import OPS_HIST4_SCHEMA_VERSION

OPS_HIST5_SCHEMA_VERSION = "ops_hist5_v1"
SOURCE_SCHEMA_VERSION = OPS_HIST4_SCHEMA_VERSION


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


def load_ops_hist4_payload(input_json: str) -> dict[str, Any]:
    return json.loads(Path(input_json).read_text(encoding="utf-8"))


def load_ops_hist4_payloads_from_dir(input_dir: str) -> list[dict[str, Any]]:
    return [json.loads(p.read_text(encoding="utf-8")) for p in sorted(Path(input_dir).glob("*.json"), key=lambda p: p.name)]


def _ensure_hist4(payloads: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    if not payloads:
        raise ValueError("OPS-HIST-5 fails closed: no OPS-HIST-4 payload provided")
    valid = [p for p in payloads if p and p.get("schema_version") == SOURCE_SCHEMA_VERSION]
    if not valid:
        raise ValueError("OPS-HIST-5 requires source_schema_version ops_hist4_v1 payload")
    return sorted(valid, key=lambda p: (p.get("snapshot_start_date", ""), p.get("snapshot_end_date", ""), json.dumps(p.get("recurrence_ecology_scorecard", {}), sort_keys=True)))


def _transition_class(transitions: int, artifacts: int) -> str:
    density = transitions / max(1, artifacts - 1)
    return "high_transition_density" if density >= 0.67 else ("moderate_transition_density" if density >= 0.34 else "low_transition_density")


def _duration_class(avg_duration: float) -> str:
    return "long_duration_regime" if avg_duration >= 3 else ("moderate_duration_regime" if avg_duration >= 2 else "short_duration_regime")


def build_ops_hist5_temporal_continuity_regimes(hist4_payloads: Sequence[dict[str, Any]] | dict[str, Any]) -> dict[str, Any]:
    payloads = _ensure_hist4([hist4_payloads] if isinstance(hist4_payloads, dict) else list(hist4_payloads))
    governance = _governance_flags()
    artifact_count = len(payloads)
    regime_depth = "single_artifact_regime_observation" if artifact_count == 1 else "multi_artifact_regime_observation"
    start_date = min(p.get("snapshot_start_date", "") for p in payloads)
    end_date = max(p.get("snapshot_end_date", "") for p in payloads)
    reviewed_total = sum(int(p.get("reviewed_snapshot_count_total", p.get("reviewed_snapshot_count", 0))) for p in payloads)

    records = []
    for i, p in enumerate(payloads):
        s = p.get("recurrence_ecology_scorecard", {})
        label = "stable" if s.get("archetype_persistence_class") == "high_persistence" else ("mixed" if s.get("archetype_persistence_class") == "moderate_persistence" else "fragmented")
        records.append({
            "idx": i,
            "artifact_id": p.get("artifact_id", f"hist4_artifact_{i}"),
            "snapshot_start_date": p.get("snapshot_start_date", ""),
            "snapshot_end_date": p.get("snapshot_end_date", ""),
            "reviewed_snapshot_count_total": int(p.get("reviewed_snapshot_count_total", p.get("reviewed_snapshot_count", 0))),
            "recurrence_depth": p.get("recurrence_depth", ""),
            "composite_recurrence_class": s.get("composite_recurrence_class", ""),
            "archetype_recurrence_class": s.get("archetype_recurrence_class", ""),
            "archetype_persistence_class": s.get("archetype_persistence_class", ""),
            "archetype_diversity_class": s.get("archetype_diversity_class", ""),
            "temporal_regime_label": label,
        })

    labels = [r["temporal_regime_label"] for r in records]
    transitions = sum(1 for i in range(1, len(labels)) if labels[i] != labels[i - 1])
    counts = Counter(labels)
    longest = max((sum(1 for _ in g) for _, g in __import__('itertools').groupby(labels)), default=1)
    avg_duration = round(artifact_count / max(1, len(counts)), 6)
    duration_class = "mixed_duration_regime" if len(set(counts.values())) > 1 and artifact_count > 2 else _duration_class(avg_duration)
    transition_class = _transition_class(transitions, artifact_count)
    frag_ratio = transitions / max(1, artifact_count - 1)
    frag_class = "high_regime_fragmentation" if frag_ratio >= 0.67 else ("moderate_regime_fragmentation" if frag_ratio >= 0.34 else "low_regime_fragmentation")
    stability_class = "stable_window_dominant" if longest >= max(2, artifact_count - 1) else ("mixed_window_stability" if longest >= 2 else "unstable_window_dominant")

    temporal_class = "stable_temporal_regime"
    if transition_class == "high_transition_density":
        temporal_class = "transition_heavy_temporal_regime"
    elif frag_class == "high_regime_fragmentation":
        temporal_class = "fragmented_temporal_regime"
    elif len(counts) > 1:
        temporal_class = "mixed_temporal_regime"

    evidence = []
    sequence_rows = []
    transition_rows = []
    duration_rows = []
    window_rows = []
    for i, r in enumerate(records):
        prev = labels[i - 1] if i > 0 else None
        marker = "transitioned" if prev and prev != r["temporal_regime_label"] else "repeated"
        sequence_rows.append({"sequence_index": i, "artifact_id": r["artifact_id"], "temporal_regime_label": r["temporal_regime_label"], "regime_transition_marker": marker})
        duration_rows.append({"artifact_id": r["artifact_id"], "temporal_regime_label": r["temporal_regime_label"], "regime_duration_index": counts[r["temporal_regime_label"]], "regime_duration_class": duration_class})
        window_rows.append({"artifact_id": r["artifact_id"], "stability_window_marker": "stable_window" if marker == "repeated" else "mixed_window", "regime_stability_class": stability_class})
        if i > 0:
            transition_rows.append({"from_regime": prev, "to_regime": r["temporal_regime_label"], "transition_marker": marker})
        evidence.append({
            "schema_version": OPS_HIST5_SCHEMA_VERSION, "source_schema_version": SOURCE_SCHEMA_VERSION,
            "artifact_id": r["artifact_id"], "source_artifact_index": i, "snapshot_start_date": r["snapshot_start_date"], "snapshot_end_date": r["snapshot_end_date"],
            "reviewed_snapshot_count_total": r["reviewed_snapshot_count_total"], "recurrence_depth": r["recurrence_depth"],
            "composite_recurrence_class": r["composite_recurrence_class"], "archetype_recurrence_class": r["archetype_recurrence_class"],
            "archetype_persistence_class": r["archetype_persistence_class"], "archetype_diversity_class": r["archetype_diversity_class"],
            "temporal_regime_label": r["temporal_regime_label"], "regime_transition_marker": marker, "regime_duration_index": counts[r["temporal_regime_label"]],
            "stability_window_marker": window_rows[-1]["stability_window_marker"], "descriptive_rationale": "Temporal regime observed from historical recurrence ecology records only.",
            "governance_metadata": deepcopy(governance),
        })

    scorecard = {"artifact_count": artifact_count, "regime_depth": regime_depth, "snapshot_start_date": start_date, "snapshot_end_date": end_date, "reviewed_snapshot_count_total": reviewed_total,
        "temporal_regime_class": temporal_class, "regime_duration_class": duration_class, "regime_transition_class": transition_class, "regime_stability_class": stability_class, "regime_fragmentation_class": frag_class}

    streamlit = {"schema_version": OPS_HIST5_SCHEMA_VERSION, "source_schema_version": SOURCE_SCHEMA_VERSION,
        "temporal_regime_scorecard_panel": [scorecard], "regime_sequence_timeline": sequence_rows, "regime_duration_table": duration_rows,
        "regime_transition_table": transition_rows, "regime_stability_window_panel": window_rows,
        "regime_fragmentation_panel": [{"regime_fragmentation_class": frag_class, "fragmentation_ratio": round(frag_ratio, 6)}],
        "regime_volatility_cluster_panel": [{"regime_transition_class": transition_class, "transition_count": transitions}],
        "persistence_topology_panel": [{"regime_stability_class": stability_class, "longest_stable_window": longest}],
        "regime_evidence_table": evidence, "governance_boundary_panel": [{"boundary": k, "value": v} for k, v in sorted(governance.items())]}

    canonical = {"schema_version": OPS_HIST5_SCHEMA_VERSION, "source_schema_version": SOURCE_SCHEMA_VERSION,
        "hist5_temporal_regime_scorecard_rows": [scorecard], "hist5_regime_sequence_rows": sequence_rows, "hist5_regime_duration_rows": duration_rows,
        "hist5_regime_transition_rows": transition_rows, "hist5_regime_stability_window_rows": window_rows,
        "hist5_regime_fragmentation_rows": [{"regime_fragmentation_class": frag_class, "fragmentation_ratio": round(frag_ratio, 6)}],
        "hist5_regime_volatility_cluster_rows": [{"regime_transition_class": transition_class, "transition_count": transitions}],
        "hist5_regime_persistence_topology_rows": [{"regime_stability_class": stability_class, "longest_stable_window": longest}],
        "hist5_regime_evidence_rows": evidence, "hist5_governance_rows": [{"key": k, "value": v} for k, v in sorted(governance.items())]}

    return {"status": "ok", "schema_version": OPS_HIST5_SCHEMA_VERSION, "source_schema_version": SOURCE_SCHEMA_VERSION,
        "artifact_count": artifact_count, "regime_depth": regime_depth, "snapshot_start_date": start_date, "snapshot_end_date": end_date, "reviewed_snapshot_count_total": reviewed_total,
        "temporal_regime_summary": "Temporal regime patterns observed across historical recurrence ecology artifacts.",
        "regime_duration_summary": "Regime duration observed as bounded historical period windows.",
        "regime_sequence_summary": "Regime sequence observed as sequential historical labels.",
        "regime_transition_summary": "Regime transitions observed from artifact-to-artifact label changes.",
        "regime_stability_window_summary": "Stability windows observed through repeated adjacent regime labels.",
        "regime_fragmentation_summary": "Regime fragmentation observed through transition density across historical periods.",
        "regime_volatility_cluster_summary": "Regime volatility clustering observed through grouped transitions.",
        "regime_persistence_topology_summary": "Regime persistence topology observed from stable and mixed windows.",
        "regime_transition_density_summary": "Transition density observed from bounded historical sequence transitions.",
        "temporal_regime_scorecard": scorecard,
        "temporal_regime_observation_summary": {"regime_counts": dict(sorted(counts.items())), "regime_sequence_rows": sequence_rows, "regime_transition_rows": transition_rows,
            "regime_duration_rows": duration_rows, "regime_stability_window_rows": window_rows,
            "clustered_regime_observation_rows": [{"temporal_regime_label": k, "observed_count": v} for k, v in sorted(counts.items(), key=lambda kv: kv[0]) if v >= 2],
            "fragmented_regime_observation_rows": [row for row in sequence_rows if row["regime_transition_marker"] == "transitioned"],
            "regime_observation_notes": ["Temporal regimes observed from OPS-HIST-4 recurrence ecology artifacts only.", "No prediction, trading execution, replay activation, topology activation, orchestration, or streaming observed."]},
        "temporal_regime_evidence_records": evidence, "governance_metadata": governance,
        "streamlit_temporal_regime_payload": streamlit, "canonical_table_payload": canonical}


def render_ops_hist5_temporal_regime_markdown(review: dict[str, Any]) -> str:
    return "\n".join([
        "# OPS-HIST-5 Temporal Continuity Regime Observation", "## Objective", "Observe temporal continuity regimes, duration, sequencing, transition clustering, and persistence windows across bounded historical recurrence ecology artifacts.",
        "## Source Recurrence Artifact Coverage", f"{review['artifact_count']} artifacts from {review['snapshot_start_date']} to {review['snapshot_end_date']} ({review['reviewed_snapshot_count_total']} reviewed snapshots).",
        "## Temporal Regime Scorecard", json.dumps(review["temporal_regime_scorecard"], sort_keys=True), "## Regime Duration Summary", review["regime_duration_summary"],
        "## Regime Sequence Summary", review["regime_sequence_summary"], "## Regime Transition Summary", review["regime_transition_summary"],
        "## Regime Stability Window Summary", review["regime_stability_window_summary"], "## Regime Fragmentation Summary", review["regime_fragmentation_summary"],
        "## Regime Volatility Cluster Summary", review["regime_volatility_cluster_summary"], "## Persistence Topology Summary", review["regime_persistence_topology_summary"],
        "## Regime Evidence Summary", f"{len(review['temporal_regime_evidence_records'])} temporal regime evidence records observed.", "## Governance Certification", "Observational historical temporal regime observation only.",
        "## Explicit Forbidden Boundaries", "No prediction/trading/replay/topology/graph execution/orchestration/streaming activation observed.", "## Future Expansion Recommendation", "Continue bounded descriptive temporal regime observation with deterministic schema checks.",
    ])
