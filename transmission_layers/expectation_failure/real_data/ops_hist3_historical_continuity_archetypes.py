from __future__ import annotations

import json
from collections import Counter
from copy import deepcopy
from pathlib import Path
from statistics import mean
from typing import Any

from transmission_layers.expectation_failure.real_data.ops_hist2_historical_continuity_intelligence import (
    OPS_HIST2_SCHEMA_VERSION,
)

OPS_HIST3_SCHEMA_VERSION = "ops_hist3_v1"
SOURCE_SCHEMA_VERSION = OPS_HIST2_SCHEMA_VERSION


def _governance_flags() -> dict[str, Any]:
    return {
        "observational_only": True,
        "historical_observation_mode": True,
        "continuity_intelligence_mode": True,
        "continuity_compression_mode": True,
        "archetype_observation_mode": True,
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


def load_ops_hist2_continuity_payload(input_json: str) -> dict[str, Any]:
    return json.loads(Path(input_json).read_text(encoding="utf-8"))


def _sign(first: float, last: float) -> str:
    d = last - first
    if abs(d) < 1e-9:
        return "stable"
    return "increasing" if d > 0 else "decreasing"


def _ensure_hist2(payload: dict[str, Any]) -> list[dict[str, Any]]:
    if not payload:
        raise ValueError("OPS-HIST-3 fails closed: no OPS-HIST-2 payload provided")
    if payload.get("schema_version") != SOURCE_SCHEMA_VERSION:
        raise ValueError("OPS-HIST-3 requires source_schema_version ops_hist2_v1 payload")
    rows = payload.get("streamlit_continuity_payload", {}).get("posture_transition_timeline", [])
    if not rows:
        raise ValueError("OPS-HIST-3 fails closed: no OPS-HIST-2 timeline rows provided")
    return sorted(rows, key=lambda r: (r.get("snapshot_date", ""), r.get("snapshot_id", "")))


def _build_evidence(name: str, dim: str, rows: list[dict[str, Any]], fields: list[str], summary: str, rationale: str, governance: dict[str, Any]) -> dict[str, Any]:
    return {
        "archetype_name": name,
        "archetype_dimension": dim,
        "source_schema_version": SOURCE_SCHEMA_VERSION,
        "schema_version": OPS_HIST3_SCHEMA_VERSION,
        "reviewed_snapshot_count": len(rows),
        "snapshot_start_date": rows[0]["snapshot_date"],
        "snapshot_end_date": rows[-1]["snapshot_date"],
        "evidence_fields_used": fields,
        "observed_values_summary": summary,
        "descriptive_rationale": rationale,
        "governance_metadata": deepcopy(governance),
    }


def build_ops_hist3_historical_continuity_archetypes(hist2_payload: dict[str, Any]) -> dict[str, Any]:
    rows = _ensure_hist2(hist2_payload)
    governance = _governance_flags()
    postures = [r["posture"] for r in rows]
    posture_changes = sum(1 for r in rows if r.get("posture_transition") == "changed")
    posture_arch = "posture_stable_continuity" if len(set(postures)) == 1 else ("posture_transition_heavy_continuity" if posture_changes >= max(1, len(rows)-1)/2 else "posture_mixed_continuity")

    def metric_arch(key: str, stable: str, inc: str, dec: str, mixed: str) -> str:
        vals = [float(r[key]) for r in rows]
        s = _sign(vals[0], vals[-1])
        if s == "stable" and len(set(vals)) > 2:
            return mixed
        return stable if s == "stable" else (inc if s == "increasing" else dec)

    frag_arch = metric_arch("fragmentation_value", "fragmentation_stable_band", "fragmentation_widening_band", "fragmentation_narrowing_band", "fragmentation_mixed_band")
    res_arch = metric_arch("resilience_value", "resilience_stable_band", "resilience_strengthening_observed", "resilience_weakening_observed", "resilience_mixed_band")
    sector_arch = metric_arch("sector_concentration_hhi", "sector_concentration_stable", "sector_concentration_increasing", "sector_concentration_decreasing", "sector_concentration_mixed")
    vol_arch = metric_arch("volatility_avg", "volatility_stable_observed", "volatility_increasing_observed", "volatility_decreasing_observed", "volatility_mixed_observed")
    val_arch = metric_arch("valuation_dispersion", "valuation_dispersion_stable", "valuation_dispersion_widening", "valuation_dispersion_narrowing", "valuation_dispersion_mixed")

    norm_vals = [float(r["normalization_completeness"]) for r in rows]
    normalization_arch = "normalization_high_stability" if min(norm_vals) >= 99.0 else ("normalization_partial_stability" if min(norm_vals) >= 90.0 else "normalization_unstable")

    fb_vals = [float(r["fallback_usage"]) for r in rows]
    fb_sign = _sign(fb_vals[0], fb_vals[-1])
    if max(fb_vals) <= 0.0:
        fallback_arch = "fallback_absent_or_low"
    elif fb_sign == "stable":
        fallback_arch = "fallback_present_stable" if len(set(fb_vals)) <= 2 else "fallback_mixed"
    elif fb_sign == "increasing":
        fallback_arch = "fallback_increasing"
    else:
        fallback_arch = "fallback_mixed"

    by_dim = {
        "posture": posture_arch, "fragmentation": frag_arch, "resilience": res_arch,
        "sector_concentration": sector_arch, "volatility": vol_arch,
        "valuation_dispersion": val_arch, "normalization_quality": normalization_arch, "fallback_usage": fallback_arch,
    }
    labels = list(by_dim.values())
    stable_dims = sorted([k for k, v in by_dim.items() if any(x in v for x in ["stable", "high_stability", "absent_or_low", "present_stable"])])
    mixed_dims = sorted([k for k, v in by_dim.items() if "mixed" in v or "partial" in v])
    fragile_dims = sorted([k for k, v in by_dim.items() if any(x in v for x in ["weakening", "unstable", "increasing"]) and k in {"fragmentation", "volatility", "fallback_usage", "normalization_quality", "resilience"}])

    if posture_arch == "posture_transition_heavy_continuity":
        composite = "transition_heavy_continuity_composite"
    elif len(fragile_dims) >= 3:
        composite = "fragile_continuity_composite"
    elif len(mixed_dims) >= 3:
        composite = "mixed_continuity_composite"
    else:
        composite = "stable_continuity_composite"

    evidence = [_build_evidence(v, k, rows, [k], f"Observed {k} values across {len(rows)} snapshots.", f"{k} mapped deterministically into {v} from OPS-HIST-2 historical continuity fields.", governance) for k, v in sorted(by_dim.items())]
    evidence.append(_build_evidence(composite, "composite_continuity", rows, sorted(by_dim.keys()), "Composite continuity archetype synthesized from dimension archetypes.", "Composite label is deterministic from posture, mixed, and fragile dimension counts.", governance))

    archetype_counts = dict(sorted(Counter(labels + [composite]).items()))
    archetype_summary = {
        "archetype_counts": archetype_counts,
        "dominant_archetype_dimensions": sorted([k for k, _ in sorted(by_dim.items(), key=lambda kv: kv[0])]),
        "mixed_archetype_dimensions": mixed_dims,
        "fragile_archetype_dimensions": fragile_dims,
        "stable_archetype_dimensions": stable_dims,
        "archetype_observation_notes": [
            "OPS-HIST-3 archetypes are descriptive compression of OPS-HIST-2 continuity structures.",
            "No prediction, trading execution, replay activation, or topology activation is included.",
        ],
    }

    streamlit = {
        "schema_version": OPS_HIST3_SCHEMA_VERSION,
        "source_schema_version": SOURCE_SCHEMA_VERSION,
        "archetype_scorecard_panel": [{"dimension": k, "archetype_name": by_dim[k]} for k in sorted(by_dim.keys())],
        "archetype_dimension_table": [{"archetype_dimension": k, "archetype_name": by_dim[k]} for k in sorted(by_dim.keys())],
        "composite_archetype_panel": [{"composite_continuity_archetype": composite}],
        "stable_archetype_panel": [{"archetype_dimension": k} for k in stable_dims],
        "mixed_archetype_panel": [{"archetype_dimension": k} for k in mixed_dims],
        "fragile_archetype_panel": [{"archetype_dimension": k} for k in fragile_dims],
        "archetype_evidence_table": evidence,
        "governance_boundary_panel": [{"boundary": k, "value": v} for k, v in sorted(governance.items())],
    }

    canonical = {
        "schema_version": OPS_HIST3_SCHEMA_VERSION,
        "source_schema_version": SOURCE_SCHEMA_VERSION,
        "hist3_archetype_rows": [{"archetype_dimension": k, "archetype_name": by_dim[k], "snapshot_start_date": rows[0]["snapshot_date"], "snapshot_end_date": rows[-1]["snapshot_date"], "reviewed_snapshot_count": len(rows)} for k in sorted(by_dim.keys())],
        "hist3_archetype_evidence_rows": evidence,
        "hist3_composite_archetype_rows": [{"composite_continuity_archetype": composite, "snapshot_start_date": rows[0]["snapshot_date"], "snapshot_end_date": rows[-1]["snapshot_date"], "reviewed_snapshot_count": len(rows)}],
        "hist3_archetype_count_rows": [{"archetype_name": k, "count": v} for k, v in sorted(archetype_counts.items())],
        "hist3_archetype_dimension_rows": [{"dimension": k, "archetype_name": by_dim[k]} for k in sorted(by_dim.keys())],
        "hist3_governance_rows": [{"key": k, "value": v} for k, v in sorted(governance.items())],
    }

    return {
        "status": "ok",
        "schema_version": OPS_HIST3_SCHEMA_VERSION,
        "source_schema_version": SOURCE_SCHEMA_VERSION,
        "snapshot_start_date": rows[0]["snapshot_date"],
        "snapshot_end_date": rows[-1]["snapshot_date"],
        "reviewed_snapshot_count": len(rows),
        "archetype_summary": archetype_summary,
        "dimension_archetypes": by_dim,
        "composite_continuity_archetype": composite,
        "archetype_evidence_records": evidence,
        "governance_metadata": governance,
        "streamlit_archetype_payload": streamlit,
        "canonical_table_payload": canonical,
    }


def render_ops_hist3_archetype_markdown(review: dict[str, Any]) -> str:
    s = review["archetype_summary"]
    return "\n".join([
        "# OPS-HIST-3 Historical Continuity Compression & Archetype Observation",
        "## Objective",
        "Compress repeated OPS-HIST-2 historical continuity structures into bounded descriptive archetypes.",
        "## Source Continuity Coverage",
        f"{review['snapshot_start_date']} to {review['snapshot_end_date']} ({review['reviewed_snapshot_count']} snapshots)",
        "## Composite Continuity Archetype",
        review["composite_continuity_archetype"],
        "## Dimension Archetypes",
        json.dumps(review["dimension_archetypes"], sort_keys=True),
        "## Archetype Evidence Summary",
        f"{len(review['archetype_evidence_records'])} evidence records generated deterministically.",
        "## Stable Archetype Dimensions",
        json.dumps(s["stable_archetype_dimensions"], sort_keys=True),
        "## Mixed Archetype Dimensions",
        json.dumps(s["mixed_archetype_dimensions"], sort_keys=True),
        "## Fragile Archetype Dimensions",
        json.dumps(s["fragile_archetype_dimensions"], sort_keys=True),
        "## Governance Certification",
        "Observational historical continuity compression and archetype observation only.",
        "## Explicit Forbidden Boundaries",
        "No prediction/trading/replay/topology/graph-orchestration/streaming activation observed.",
        "## Future Expansion Recommendation",
        "Continue bounded descriptive archetype observation with deterministic schema stability checks.",
    ])
