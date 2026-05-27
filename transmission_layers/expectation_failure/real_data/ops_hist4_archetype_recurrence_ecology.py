from __future__ import annotations

import json
from collections import Counter
from copy import deepcopy
from pathlib import Path
from typing import Any, Sequence

from transmission_layers.expectation_failure.real_data.ops_hist3_historical_continuity_archetypes import (
    OPS_HIST3_SCHEMA_VERSION,
)

OPS_HIST4_SCHEMA_VERSION = "ops_hist4_v1"
SOURCE_SCHEMA_VERSION = OPS_HIST3_SCHEMA_VERSION


def _governance_flags() -> dict[str, Any]:
    return {
        "observational_only": True,
        "historical_observation_mode": True,
        "continuity_intelligence_mode": True,
        "continuity_compression_mode": True,
        "archetype_observation_mode": True,
        "recurrence_ecology_mode": True,
        "archetype_persistence_observation_mode": True,
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


def load_ops_hist3_payload(input_json: str) -> dict[str, Any]:
    return json.loads(Path(input_json).read_text(encoding="utf-8"))


def load_ops_hist3_payloads_from_dir(input_dir: str) -> list[dict[str, Any]]:
    return [json.loads(p.read_text(encoding="utf-8")) for p in sorted(Path(input_dir).glob("*.json"), key=lambda p: p.name)]


def _ensure_hist3(payloads: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    if not payloads:
        raise ValueError("OPS-HIST-4 fails closed: no OPS-HIST-3 payload provided")
    valid = [p for p in payloads if p and p.get("schema_version") == SOURCE_SCHEMA_VERSION]
    if not valid:
        raise ValueError("OPS-HIST-4 requires source_schema_version ops_hist3_v1 payload")
    return sorted(valid, key=lambda p: (p.get("snapshot_start_date", ""), p.get("snapshot_end_date", ""), json.dumps(p.get("dimension_archetypes", {}), sort_keys=True)))


def _classify_density(share: float) -> str:
    return "high_recurrence_density" if share >= 0.67 else ("moderate_recurrence_density" if share >= 0.34 else "low_recurrence_density")


def _classify_persistence(share: float) -> str:
    return "high_persistence" if share >= 0.67 else ("moderate_persistence" if share >= 0.34 else "low_persistence")


def build_ops_hist4_archetype_recurrence_ecology(hist3_payloads: Sequence[dict[str, Any]] | dict[str, Any]) -> dict[str, Any]:
    payloads = _ensure_hist3([hist3_payloads] if isinstance(hist3_payloads, dict) else list(hist3_payloads))
    governance = _governance_flags()
    artifact_count = len(payloads)
    recurrence_depth = "single_artifact_observation" if artifact_count == 1 else "multi_artifact_observation"

    start_date = min(p.get("snapshot_start_date", "") for p in payloads)
    end_date = max(p.get("snapshot_end_date", "") for p in payloads)
    reviewed_total = sum(int(p.get("reviewed_snapshot_count", 0)) for p in payloads)

    dim_records: list[dict[str, Any]] = []
    comp_records: list[str] = []
    evidence: list[dict[str, Any]] = []

    for idx, p in enumerate(payloads):
        dim_map = p.get("dimension_archetypes", {})
        comp = p.get("composite_continuity_archetype", "")
        comp_records.append(comp)
        for dim, name in sorted(dim_map.items()):
            dim_records.append({"dimension": dim, "archetype": name, "artifact_index": idx})
            evidence.append({
                "schema_version": OPS_HIST4_SCHEMA_VERSION,
                "source_schema_version": SOURCE_SCHEMA_VERSION,
                "artifact_id": p.get("artifact_id", f"hist3_artifact_{idx}"),
                "source_artifact_index": idx,
                "snapshot_start_date": p.get("snapshot_start_date", ""),
                "snapshot_end_date": p.get("snapshot_end_date", ""),
                "reviewed_snapshot_count": int(p.get("reviewed_snapshot_count", 0)),
                "archetype_dimension": dim,
                "archetype_name": name,
                "composite_archetype": comp,
            })

    dim_pairs = [(r["dimension"], r["archetype"]) for r in dim_records]
    pair_counts = Counter(dim_pairs)
    dim_counts = Counter(r["dimension"] for r in dim_records)
    comp_counts = Counter(comp_records)

    recurrence_rows = []
    persistence_rows = []
    for dim, name in sorted(pair_counts.keys()):
        c = pair_counts[(dim, name)]
        recurrence_share = c / artifact_count
        persistence_count = max(0, c - 1)
        persistence_share = persistence_count / max(1, artifact_count - 1) if artifact_count > 1 else 0.0
        recurrence_rows.append({"archetype_dimension": dim, "archetype_name": name, "recurrence_count": c, "recurrence_share": round(recurrence_share, 6), "archetype_recurrence_class": _classify_density(recurrence_share)})
        persistence_rows.append({"archetype_dimension": dim, "archetype_name": name, "persistence_count": persistence_count, "persistence_share": round(persistence_share, 6), "archetype_persistence_class": _classify_persistence(persistence_share)})

    if len(dim_counts) <= 1:
        div_class = "monoculture_archetype_ecology"
    else:
        uniq = len(pair_counts) / len(dim_counts)
        div_class = "diversified_archetype_ecology" if uniq >= 2.0 else ("balanced_archetype_ecology" if uniq >= 1.5 else "concentrated_archetype_ecology")

    top_share = max(dim_counts.values()) / sum(dim_counts.values()) if dim_counts else 1.0
    mono_summary = {"archetype_monoculture_observation_summary": "Archetype ecology remained concentrated in the historical window." if top_share >= 0.5 else "Archetype ecology appeared diversified in the historical window."}

    comp_top_share = max(comp_counts.values()) / artifact_count
    comp_class = "stable_composite_recurrence" if comp_top_share >= 0.75 else ("mixed_composite_recurrence" if comp_top_share >= 0.5 else "fragile_composite_recurrence")
    if comp_counts.get("transition_heavy_continuity_composite", 0) >= max(1, artifact_count // 2):
        comp_class = "transition_heavy_composite_recurrence"

    recurrence_map = {(r["archetype_dimension"], r["archetype_name"]): r for r in recurrence_rows}
    persistence_map = {(r["archetype_dimension"], r["archetype_name"]): r for r in persistence_rows}
    for e in evidence:
        k = (e["archetype_dimension"], e["archetype_name"])
        e["recurrence_count"] = recurrence_map[k]["recurrence_count"]
        e["persistence_count"] = persistence_map[k]["persistence_count"]
        e["recurrence_share"] = recurrence_map[k]["recurrence_share"]
        e["persistence_share"] = persistence_map[k]["persistence_share"]
        e["descriptive_rationale"] = "Archetype persisted or transitioned based on repeated historical window appearances only."
        e["governance_metadata"] = deepcopy(governance)

    scorecard = {
        "artifact_count": artifact_count,
        "recurrence_depth": recurrence_depth,
        "snapshot_start_date": start_date,
        "snapshot_end_date": end_date,
        "reviewed_snapshot_count_total": reviewed_total,
        "archetype_recurrence_class": _classify_density(sum(r["recurrence_share"] for r in recurrence_rows) / max(1, len(recurrence_rows))),
        "archetype_persistence_class": _classify_persistence(sum(r["persistence_share"] for r in persistence_rows) / max(1, len(persistence_rows))),
        "archetype_diversity_class": div_class,
        "composite_recurrence_class": comp_class,
    }

    streamlit = {
        "schema_version": OPS_HIST4_SCHEMA_VERSION, "source_schema_version": SOURCE_SCHEMA_VERSION,
        "recurrence_ecology_scorecard_panel": [scorecard], "archetype_recurrence_table": recurrence_rows,
        "archetype_persistence_table": persistence_rows,
        "composite_recurrence_panel": [{"composite_archetype": k, "recurrence_count": v} for k, v in sorted(comp_counts.items())],
        "archetype_diversity_panel": [{"archetype_diversity_class": div_class}], "monoculture_observation_panel": [mono_summary],
        "recurring_dimension_panel": [{"archetype_dimension": d} for d, c in sorted(dim_counts.items()) if c >= 2],
        "persistent_dimension_panel": [{"archetype_dimension": d} for d, c in sorted(dim_counts.items()) if c == artifact_count],
        "recurrence_evidence_table": evidence,
        "governance_boundary_panel": [{"boundary": k, "value": v} for k, v in sorted(governance.items())],
    }

    canonical = {
        "schema_version": OPS_HIST4_SCHEMA_VERSION, "source_schema_version": SOURCE_SCHEMA_VERSION,
        "hist4_recurrence_scorecard_rows": [scorecard], "hist4_archetype_recurrence_rows": recurrence_rows,
        "hist4_archetype_persistence_rows": persistence_rows,
        "hist4_composite_recurrence_rows": [{"composite_archetype": k, "recurrence_count": v} for k, v in sorted(comp_counts.items())],
        "hist4_archetype_diversity_rows": [{"archetype_diversity_class": div_class, "artifact_count": artifact_count}],
        "hist4_monoculture_observation_rows": [mono_summary], "hist4_recurrence_evidence_rows": evidence,
        "hist4_governance_rows": [{"key": k, "value": v} for k, v in sorted(governance.items())],
    }

    return {
        "status": "ok", "schema_version": OPS_HIST4_SCHEMA_VERSION, "source_schema_version": SOURCE_SCHEMA_VERSION,
        "artifact_count": artifact_count, "recurrence_depth": recurrence_depth, "snapshot_start_date": start_date, "snapshot_end_date": end_date,
        "reviewed_snapshot_count_total": reviewed_total, "archetype_persistence_summary": "Archetype persistence observed across bounded historical artifacts.",
        "archetype_recurrence_density_summary": "Archetype recurrence density observed from repeated artifact appearances.",
        "composite_archetype_recurrence_summary": "Composite archetype recurrence observed across historical window artifacts.",
        "archetype_transition_summary": "Archetype transition behavior observed via historical artifact-to-artifact changes.",
        "archetype_diversity_summary": f"Archetype ecology observed as {div_class}.",
        "archetype_monoculture_observation_summary": mono_summary["archetype_monoculture_observation_summary"],
        "stable_archetype_persistence_summary": "Stable archetype dimensions persisted in observed historical window.",
        "mixed_archetype_persistence_summary": "Mixed archetype dimensions repeated in observed historical window.",
        "fragile_archetype_persistence_summary": "Fragile archetype dimensions appeared or disappeared in observed historical window.",
        "recurrence_ecology_scorecard": scorecard,
        "recurrence_ecology_summary": {
            "archetype_counts": dict(sorted(Counter(r["archetype"] for r in dim_records).items())),
            "archetype_dimension_counts": dict(sorted(dim_counts.items())),
            "composite_archetype_counts": dict(sorted(comp_counts.items())),
            "recurring_archetype_dimensions": sorted([d for d, c in dim_counts.items() if c >= 2]),
            "persistent_archetype_dimensions": sorted([d for d, c in dim_counts.items() if c == artifact_count]),
            "concentrated_archetype_dimensions": sorted([d for d, c in dim_counts.items() if c / artifact_count >= 0.75]),
            "diversified_archetype_dimensions": sorted([d for d, c in dim_counts.items() if c / artifact_count < 0.75]),
            "recurrence_observation_notes": ["Recurrence ecology observed from OPS-HIST-3 artifacts only.", "No prediction, trading execution, replay activation, topology activation, or orchestration observed."],
        },
        "archetype_recurrence_evidence_records": evidence,
        "governance_metadata": governance,
        "streamlit_recurrence_payload": streamlit,
        "canonical_table_payload": canonical,
    }


def render_ops_hist4_recurrence_markdown(review: dict[str, Any]) -> str:
    return "\n".join([
        "# OPS-HIST-4 Archetype Persistence & Recurrence Ecology Observation",
        "## Objective",
        "Observe archetype persistence, recurrence density, transition behavior, and recurrence ecology across bounded historical continuity archetype artifacts.",
        "## Source Archetype Artifact Coverage",
        f"{review['artifact_count']} artifacts from {review['snapshot_start_date']} to {review['snapshot_end_date']} ({review['reviewed_snapshot_count_total']} reviewed snapshots).",
        "## Recurrence Ecology Scorecard",
        json.dumps(review["recurrence_ecology_scorecard"], sort_keys=True),
        "## Archetype Persistence Summary", review["archetype_persistence_summary"],
        "## Archetype Recurrence Density Summary", review["archetype_recurrence_density_summary"],
        "## Composite Archetype Recurrence Summary", review["composite_archetype_recurrence_summary"],
        "## Archetype Transition Summary", review["archetype_transition_summary"],
        "## Archetype Diversity Summary", review["archetype_diversity_summary"],
        "## Monoculture Observation Summary", review["archetype_monoculture_observation_summary"],
        "## Recurrence Evidence Summary", f"{len(review['archetype_recurrence_evidence_records'])} recurrence evidence records observed.",
        "## Governance Certification", "Observational historical recurrence ecology only.",
        "## Explicit Forbidden Boundaries", "No prediction/trading/replay/topology/graph execution/orchestration/streaming activation observed.",
        "## Future Expansion Recommendation", "Continue bounded descriptive recurrence ecology observation with deterministic schema checks.",
    ])
