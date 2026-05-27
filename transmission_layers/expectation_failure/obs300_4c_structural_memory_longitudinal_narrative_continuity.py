"""OBS300-4C deterministic structural memory & longitudinal narrative continuity intelligence."""

from __future__ import annotations

from copy import deepcopy
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, List, Mapping

_MAX_LINEAGE_ROWS = 6
_MAX_PANEL_ROWS = 5
_MAX_SUMMARY_CHARS = 320


STRUCTURE_KEYS = {
    "contradiction_structures": "contradiction",
    "resilience_structures": "resilience",
    "fragmentation_structures": "fragmentation",
    "transition_pathways": "transition",
    "recovery_bridges": "recovery",
    "pressure_bridges": "pressure",
}


def _clamp(v: float, lo: int = 0, hi: int = 100) -> int:
    return max(lo, min(hi, int(Decimal(str(v)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))))


def _f(payload: Mapping[str, object], key: str, default: float = 50.0) -> float:
    value = payload.get(key)
    if isinstance(value, bool) or value is None:
        return default
    if isinstance(value, (int, float)):
        return max(0.0, min(100.0, float(value)))
    return default


def _bounded_summary(value: str) -> str:
    return value[:_MAX_SUMMARY_CHARS]


def _classification(continuity: int, persistence: int, frag: int, norm: int) -> str:
    if frag >= 70 and continuity >= 55:
        return "fragmentation_persistent"
    if continuity >= 82 and persistence >= 80:
        return "entrenched"
    if continuity >= 72 and persistence >= 68:
        return "persistent"
    if norm >= 70 and continuity >= 58:
        return "stabilizing"
    if norm >= 62 and frag <= 50:
        return "re-cohering"
    if frag >= 60 and norm <= 45:
        return "decompression_continuing"
    if continuity >= 52:
        return "recurring"
    return "transient"


def _build_structure_row(payload: Mapping[str, object], structure_key: str, family: str) -> Dict[str, Any]:
    continuity = _clamp((_f(payload, f"{family}_recurrence", 50.0) * 0.40) + (_f(payload, f"{family}_lineage_depth", 50.0) * 0.35) + (_f(payload, f"{family}_pathway_stability", 50.0) * 0.25))
    narrative = _clamp((_f(payload, f"{family}_narrative_alignment", 50.0) * 0.50) + (_f(payload, f"{family}_normalization_continuity", 50.0) * 0.30) + (_f(payload, f"{family}_topology_continuity", 50.0) * 0.20))
    persistence = _clamp((_f(payload, f"{family}_persistence", 50.0) * 0.65) + (_f(payload, f"{family}_bridge_reuse", 50.0) * 0.35))
    frag = _clamp(_f(payload, f"{family}_fragmentation_pressure", 50.0))
    norm = _clamp(_f(payload, f"{family}_normalization_continuity", 50.0))
    return {
        "structure": structure_key,
        "family": family,
        "continuity_score": continuity,
        "narrative_continuity_score": narrative,
        "topology_continuity_score": _clamp(_f(payload, f"{family}_topology_continuity", 50.0)),
        "contradiction_recurrence_continuity": _clamp(_f(payload, f"{family}_contradiction_recurrence", 50.0)),
        "normalization_continuity": norm,
        "fragmentation_persistence_continuity": frag,
        "persistence_score": persistence,
        "continuity_classification": _classification(continuity, persistence, frag, norm),
    }


def build_obs300_4c_structural_memory_longitudinal_narrative_continuity(input_payload: Dict[str, object]) -> Dict[str, object]:
    payload = deepcopy(input_payload)

    rows = [_build_structure_row(payload, structure, family) for structure, family in STRUCTURE_KEYS.items()]
    ranked = sorted(rows, key=lambda r: (-r["continuity_score"], -r["persistence_score"], r["structure"]))

    compressed_lineage = [
        {
            "structure": row["structure"],
            "classification": row["continuity_classification"],
            "continuity_score": row["continuity_score"],
            "lineage_signature": f"{row['family']}:{row['continuity_score']}:{row['narrative_continuity_score']}",
        }
        for row in ranked[:_MAX_LINEAGE_ROWS]
    ]

    dominant = ranked[:_MAX_PANEL_ROWS]
    longest = max(ranked, key=lambda r: (r["continuity_score"] + r["persistence_score"], r["structure"]))

    governance = {
        "observational_only": True,
        "no_recursive_replay_operationalization": True,
        "no_autonomous_replay": True,
        "no_topology_activation": True,
        "no_self_modifying_pathways": True,
        "no_prediction_or_trading_execution": True,
        "no_sql_write_introduction": True,
    }

    return {
        "module": "OBS300-4C",
        "status": "deterministic_structural_memory_longitudinal_narrative_continuity_complete",
        "structural_memory_layer": {
            "tracked_structures": rows,
            "bounded_structure_count": len(rows),
            "structural_continuity_observation": "persistent_ecosystem_structural_continuity_observed",
        },
        "ecosystem_lineage_observation": {
            "ecosystem_lineage_summaries": compressed_lineage,
            "recurring_topology_patterns": [r["structure"] for r in ranked if r["continuity_classification"] in {"recurring", "persistent", "entrenched"}][:_MAX_LINEAGE_ROWS],
            "persistent_propagation_lineage": [r["structure"] for r in ranked if r["persistence_score"] >= 68][:_MAX_LINEAGE_ROWS],
            "stabilization_lineage_continuity": [r["structure"] for r in ranked if r["normalization_continuity"] >= 62][:_MAX_LINEAGE_ROWS],
        },
        "narrative_continuity_observation": {
            "narrative_continuity_scoring": {r["structure"]: r["narrative_continuity_score"] for r in rows},
            "topology_continuity_scoring": {r["structure"]: r["topology_continuity_score"] for r in rows},
            "continuity_evolution_summary": _bounded_summary(
                f"dominant={ranked[0]['structure']};longest_pathway={longest['structure']};avg_continuity={_clamp(sum(r['continuity_score'] for r in rows)/max(1, len(rows)))}"
            ),
        },
        "structural_memory_compression": {
            "bounded_continuity_compression": True,
            "compressed_lineage_summaries": compressed_lineage,
            "recurrence_abstraction": [f"{r['structure']}::{r['continuity_classification']}" for r in ranked[:_MAX_LINEAGE_ROWS]],
            "topology_memory_suppression_controls": {
                "max_tracked_structures": len(STRUCTURE_KEYS),
                "max_lineage_entries": _MAX_LINEAGE_ROWS,
                "max_panel_rows": _MAX_PANEL_ROWS,
            },
        },
        "ecosystem_continuity_classification": {r["structure"]: r["continuity_classification"] for r in rows},
        "operator_continuity_intelligence": {
            "dominant_recurring_structures": [r["structure"] for r in dominant if r["continuity_score"] >= 52],
            "strongest_persistent_contradictions": [r["structure"] for r in ranked if r["contradiction_recurrence_continuity"] >= 65][:_MAX_PANEL_ROWS],
            "longest_continuity_pathways": [longest["structure"]],
            "recurring_resilience_bridges": [r["structure"] for r in ranked if "resilience" in r["structure"] or "recovery" in r["structure"]][:_MAX_PANEL_ROWS],
            "persistent_fragmentation_clusters": [r["structure"] for r in ranked if r["fragmentation_persistence_continuity"] >= 62][:_MAX_PANEL_ROWS],
            "normalization_continuity_structures": [r["structure"] for r in ranked if r["normalization_continuity"] >= 60][:_MAX_PANEL_ROWS],
        },
        "operator_facing_visualization_payloads": {
            "continuity_dashboards": {"top_structures": dominant, "summary": "bounded_continuity_dashboard"},
            "ecosystem_lineage_panels": {"lineage": compressed_lineage},
            "recurrence_topology_summaries": {"recurrence_classes": {k: v for k, v in sorted((r['structure'], r['continuity_classification']) for r in rows)}},
            "continuity_pathway_views": {"longest": longest, "topology_memory_bounds": {"max": _MAX_LINEAGE_ROWS}},
            "structural_memory_summaries": {"tracked": len(rows), "compressed": len(compressed_lineage)},
        },
        "structural_memory_architecture_summary": {
            "observational_only_contracts": True,
            "bounded_historical_ecosystem_cognition": True,
            "live_ingestion_ready_payload_surfaces": True,
            "deterministic_where_practical": True,
            "graph_execution_engine_required": False,
            "sql_write_required": False,
        },
        "governance_certification": governance,
        "ecosystem_continuity_summary": {
            "top_classification": ranked[0]["continuity_classification"],
            "tracked_structures": len(rows),
            "bounded": True,
            "deterministic": True,
        },
    }
