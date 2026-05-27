from __future__ import annotations

import json
from collections import Counter
from copy import deepcopy
from pathlib import Path
from typing import Any, Sequence

from transmission_layers.expectation_failure.real_data.ops_hist1_controlled_historical_observation import GOVERNANCE_BOUNDARIES

OPS_HIST2_SCHEMA_VERSION = "ops_hist2_v1"
SOURCE_SCHEMA_VERSION = "ops_hist1_v1"


def _governance_flags() -> dict[str, Any]:
    flags = deepcopy(GOVERNANCE_BOUNDARIES)
    flags.update(
        {
            "observational_only": True,
            "historical_observation_mode": True,
            "continuity_intelligence_mode": True,
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
    )
    return flags


def load_ops_hist1_snapshots_for_hist2(input_dir: str) -> list[dict[str, Any]]:
    rows = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(Path(input_dir).glob("ops_hist1_*.json"), key=lambda p: p.name)]
    return sorted(rows, key=lambda r: (r.get("snapshot_date", ""), r.get("snapshot_id", "")))


def _direction(values: list[float]) -> str:
    if len(values) < 2:
        return "stable"
    delta = values[-1] - values[0]
    if abs(delta) < 1e-9:
        return "stable"
    return "increased" if delta > 0 else "decreased"


def _posture_class(postures: list[str], changed_count: int) -> str:
    if len(set(postures)) == 1:
        return "stable_posture"
    ratio = changed_count / max(1, len(postures) - 1)
    return "transition_heavy_posture" if ratio >= 0.5 else "mixed_posture"


def build_ops_hist2_continuity_intelligence(snapshots: Sequence[dict[str, Any]]) -> dict[str, Any]:
    if not snapshots:
        raise ValueError("OPS-HIST-2 fails closed: no OPS-HIST-1 snapshots provided")
    bad = [s for s in snapshots if s.get("schema_version") != SOURCE_SCHEMA_VERSION]
    if bad:
        raise ValueError("OPS-HIST-2 requires source_schema_version ops_hist1_v1 snapshots")
    ordered = sorted(snapshots, key=lambda s: (s.get("snapshot_date", ""), s.get("snapshot_id", "")))
    rows = []
    prev_posture = None
    for s in ordered:
        d = s.get("operational_diagnostics", {})
        posture = s.get("posture", "unknown")
        rows.append({
            "snapshot_id": s["snapshot_id"], "snapshot_date": s["snapshot_date"], "posture": posture,
            "posture_transition": "initial" if prev_posture is None else ("changed" if prev_posture != posture else "unchanged"),
            "fragmentation_value": float(d.get("fragmentation_avg", 0.0)),
            "resilience_value": float(d.get("resilience_avg", 0.0)),
            "sector_concentration_hhi": float(d.get("sector_hhi", 0.0)),
            "volatility_avg": float(d.get("volatility_avg", 0.0)),
            "valuation_dispersion": float(d.get("valuation_dispersion", 0.0)),
            "normalization_completeness": float(d.get("normalization_completeness", 0.0)),
            "fallback_usage": float(d.get("fallback_usage", 0.0)),
        })
        prev_posture = posture

    postures = [r["posture"] for r in rows]
    transition_changed = sum(1 for r in rows if r["posture_transition"] == "changed")
    frag_dir = _direction([r["fragmentation_value"] for r in rows])
    res_dir = _direction([r["resilience_value"] for r in rows])
    sector_dir = _direction([r["sector_concentration_hhi"] for r in rows])
    vol_dir = _direction([r["volatility_avg"] for r in rows])
    val_dir = _direction([r["valuation_dispersion"] for r in rows])

    norm_values = [r["normalization_completeness"] for r in rows]
    fallback_values = [r["fallback_usage"] for r in rows]
    min_norm = min(norm_values)
    max_norm = max(norm_values)

    posture_class = _posture_class(postures, transition_changed)
    frag_class = "stable_fragmentation" if frag_dir == "stable" else ("widening_fragmentation" if frag_dir == "increased" else "narrowing_fragmentation")
    if len(set([r["fragmentation_value"] for r in rows])) > 2 and frag_dir == "stable":
        frag_class = "mixed_fragmentation"
    res_class = "stable_resilience" if res_dir == "stable" else ("improving_resilience_observed" if res_dir == "increased" else "weakening_resilience_observed")
    if len(set([r["resilience_value"] for r in rows])) > 2 and res_dir == "stable":
        res_class = "mixed_resilience"
    norm_class = "complete_or_high_quality" if min_norm >= 99.0 else ("partial_quality" if min_norm >= 90.0 else "unstable_quality")

    summaries = {
        "posture_transition_summary": f"Posture transitions observed across the historical window; changed={transition_changed} and unchanged={sum(1 for r in rows if r['posture_transition']=='unchanged')}.",
        "posture_persistence_summary": f"Posture persisted in {Counter(postures).most_common(1)[0][1]} of {len(postures)} historical window snapshots.",
        "fragmentation_drift_summary": f"Fragmentation {('widened' if frag_dir=='increased' else 'narrowed' if frag_dir=='decreased' else 'fluctuated')} across the historical window.",
        "resilience_drift_summary": f"Resilience {('increased' if res_dir=='increased' else 'decreased' if res_dir=='decreased' else 'fluctuated')} across the historical window.",
        "sector_concentration_evolution_summary": f"Sector concentration {('increased' if sector_dir=='increased' else 'decreased' if sector_dir=='decreased' else 'persisted')} across the historical window.",
        "volatility_regime_observation_summary": f"Volatility {('increased' if vol_dir=='increased' else 'decreased' if vol_dir=='decreased' else 'stable')} observed across the historical window.",
        "valuation_dispersion_observation_summary": f"Valuation dispersion {('widened' if val_dir=='increased' else 'narrowed' if val_dir=='decreased' else 'stable')} across the historical window.",
        "normalization_quality_summary": f"Normalization quality {('persisted' if min_norm==max_norm else 'fluctuated')} across the historical window.",
        "fallback_usage_summary": f"Fallback usage {('increased' if _direction(fallback_values)=='increased' else 'decreased' if _direction(fallback_values)=='decreased' else 'persisted')} across the historical window.",
    }

    scorecard = {
        "posture_continuity_class": posture_class,
        "fragmentation_continuity_class": frag_class,
        "resilience_continuity_class": res_class,
        "normalization_quality_class": norm_class,
    }
    governance = _governance_flags()
    payload = {
        "status": "ok",
        "schema_version": OPS_HIST2_SCHEMA_VERSION,
        "source_schema_version": SOURCE_SCHEMA_VERSION,
        "snapshot_start_date": rows[0]["snapshot_date"],
        "snapshot_end_date": rows[-1]["snapshot_date"],
        "reviewed_snapshot_count": len(rows),
        **summaries,
        "continuity_stability_scorecard": scorecard,
        "governance_metadata": governance,
        "streamlit_continuity_payload": {
            "schema_version": OPS_HIST2_SCHEMA_VERSION, "source_schema_version": SOURCE_SCHEMA_VERSION,
            "continuity_scorecard_panel": [scorecard], "posture_transition_timeline": rows,
            "posture_persistence_panel": [{"posture": k, "count": v} for k, v in sorted(Counter(postures).items())],
            "fragmentation_drift_panel": [{"snapshot_date": r["snapshot_date"], "fragmentation_value": r["fragmentation_value"]} for r in rows],
            "resilience_drift_panel": [{"snapshot_date": r["snapshot_date"], "resilience_value": r["resilience_value"]} for r in rows],
            "sector_concentration_panel": [{"snapshot_date": r["snapshot_date"], "sector_concentration_hhi": r["sector_concentration_hhi"]} for r in rows],
            "volatility_observation_panel": [{"snapshot_date": r["snapshot_date"], "volatility_avg": r["volatility_avg"]} for r in rows],
            "valuation_dispersion_panel": [{"snapshot_date": r["snapshot_date"], "valuation_dispersion": r["valuation_dispersion"]} for r in rows],
            "normalization_quality_panel": [{"snapshot_date": r["snapshot_date"], "normalization_completeness": r["normalization_completeness"]} for r in rows],
            "fallback_usage_panel": [{"snapshot_date": r["snapshot_date"], "fallback_usage": r["fallback_usage"]} for r in rows],
            "governance_boundary_panel": [{"boundary": k, "value": v} for k, v in sorted(governance.items())],
        },
        "canonical_table_payload": {
            "schema_version": OPS_HIST2_SCHEMA_VERSION, "source_schema_version": SOURCE_SCHEMA_VERSION,
            "hist2_continuity_scorecard_rows": [{"metric": k, "value": v} for k, v in sorted(scorecard.items())],
            "hist2_posture_transition_rows": [{"snapshot_id": r["snapshot_id"], "snapshot_date": r["snapshot_date"], "posture": r["posture"], "posture_transition": r["posture_transition"]} for r in rows],
            "hist2_fragmentation_drift_rows": [{"snapshot_date": r["snapshot_date"], "fragmentation_value": r["fragmentation_value"]} for r in rows],
            "hist2_resilience_drift_rows": [{"snapshot_date": r["snapshot_date"], "resilience_value": r["resilience_value"]} for r in rows],
            "hist2_sector_concentration_rows": [{"snapshot_date": r["snapshot_date"], "sector_concentration_hhi": r["sector_concentration_hhi"]} for r in rows],
            "hist2_volatility_observation_rows": [{"snapshot_date": r["snapshot_date"], "volatility_avg": r["volatility_avg"]} for r in rows],
            "hist2_valuation_dispersion_rows": [{"snapshot_date": r["snapshot_date"], "valuation_dispersion": r["valuation_dispersion"]} for r in rows],
            "hist2_normalization_quality_rows": [{"snapshot_date": r["snapshot_date"], "normalization_completeness": r["normalization_completeness"]} for r in rows],
            "hist2_fallback_usage_rows": [{"snapshot_date": r["snapshot_date"], "fallback_usage": r["fallback_usage"]} for r in rows],
            "hist2_governance_rows": [{"key": k, "value": v} for k, v in sorted(governance.items())],
        },
    }
    return payload


def render_ops_hist2_continuity_markdown(review: dict[str, Any]) -> str:
    return "\n".join([
        "# OPS-HIST-2 Historical Continuity Intelligence",
        "## Objective",
        "Expand historical observation review into bounded descriptive continuity intelligence.",
        "## Source Snapshot Coverage",
        f"{review['snapshot_start_date']} to {review['snapshot_end_date']} ({review['reviewed_snapshot_count']} snapshots)",
        "## Continuity Scorecard",
        json.dumps(review["continuity_stability_scorecard"], sort_keys=True),
        "## Posture Transition Summary", review["posture_transition_summary"],
        "## Fragmentation Drift Summary", review["fragmentation_drift_summary"],
        "## Resilience Drift Summary", review["resilience_drift_summary"],
        "## Sector Concentration Evolution", review["sector_concentration_evolution_summary"],
        "## Volatility Observation", review["volatility_regime_observation_summary"],
        "## Valuation Dispersion Observation", review["valuation_dispersion_observation_summary"],
        "## Normalization Quality", review["normalization_quality_summary"],
        "## Fallback Usage", review["fallback_usage_summary"],
        "## Governance Certification", "Observational historical continuity intelligence only.",
        "## Explicit Forbidden Boundaries", "No prediction/trading/replay/topology/orchestration/streaming activation observed.",
        "## Future Expansion Recommendation", "Continue bounded descriptive historical window reviews with deterministic schemas.",
    ])
