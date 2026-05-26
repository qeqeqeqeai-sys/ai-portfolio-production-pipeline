from __future__ import annotations

import math
from collections import Counter, OrderedDict
from typing import Any

from .phase_a1_curated_observational_expansion import (
    build_phase_a1b_real_curated_structural_universe,
    certify_phase_a_observational_expansion_boundary,
)


def _band(value: float, lo: float = 0.33, hi: float = 0.66) -> str:
    if value < lo:
        return "low"
    if value < hi:
        return "moderate"
    return "high"


def _entropy_norm(counts: list[int]) -> float:
    total = sum(counts)
    if total <= 0 or len(counts) <= 1:
        return 0.0
    probs = [c / total for c in counts if c > 0]
    h = -sum(p * math.log(p, 2) for p in probs)
    return round(h / math.log(len(counts), 2), 6)


def build_phase_a3_replay_ecology_measurement_configuration() -> OrderedDict[str, Any]:
    return OrderedDict([
        ("phase", "A3"),
        ("mode", "deterministic_derived_measurement"),
        ("measurement_input_source", "phase_a1b_real_curated_structural_universe"),
        ("observational_only", True),
        ("bounded", True),
        ("pure_function_oriented", True),
        ("governance_boundary", certify_phase_a_observational_expansion_boundary()),
    ])


def _base_stats() -> dict[str, Any]:
    rows = build_phase_a1b_real_curated_structural_universe()
    sectors = Counter(r["sector"] for r in rows)
    domains = Counter(r["sefi_domain"] for r in rows)
    return {
        "rows": rows,
        "sectors": sectors,
        "domains": domains,
        "adjacency_scores": [r["adjacency_richness_score"] for r in rows],
        "contradiction_scores": [r["contradiction_richness_score"] for r in rows],
        "propagation_scores": [r["propagation_richness_score"] for r in rows],
        "monoculture_scores": [r["monoculture_risk_score"] for r in rows],
        "low_info_scores": [r["low_information_growth_risk_score"] for r in rows],
        "replay_scores": [r["replay_ecology_richness_score"] for r in rows],
    }


def _measurement(metric_name: str, inputs: list[str], value: Any, interpretation: str, risk: str, mitigation: str) -> OrderedDict[str, Any]:
    return OrderedDict([
        ("metric_name", metric_name),
        ("deterministic_inputs_used", inputs),
        ("measurement_value", value),
        ("interpretation", interpretation),
        ("replay_ecology_risk", risk),
        ("mitigation_guidance", mitigation),
        ("governance_status", "observational_only_boundary_preserved"),
    ])


def build_phase_a3_topology_entropy_measurement() -> OrderedDict[str, Any]:
    s = _base_stats()
    val = _entropy_norm(list(s["domains"].values()))
    return _measurement("topology_entropy", ["sefi_domain", "adjacency_richness_score"], val, f"Topology diversity band={_band(val)}", "lower_entropy_increases_hub_fragility", "Increase cross-domain connector representation in next curated refresh.")


def build_phase_a3_contradiction_entropy_measurement() -> OrderedDict[str, Any]:
    s = _base_stats()
    bucket = Counter(min(10, max(1, x)) for x in s["contradiction_scores"])
    val = _entropy_norm(list(bucket.values()))
    return _measurement("contradiction_entropy", ["contradiction_richness_score"], val, f"Contradiction diversity band={_band(val)}", "low_diversity_can_hide_structural_tension_modes", "Favor additions from underrepresented contradiction-rich domains.")


def build_phase_a3_propagation_diversity_measurement() -> OrderedDict[str, Any]:
    s = _base_stats()
    bucket = Counter(min(10, max(1, x)) for x in s["propagation_scores"])
    val = _entropy_norm(list(bucket.values()))
    return _measurement("propagation_diversity", ["propagation_richness_score"], val, f"Propagation diversity band={_band(val)}", "narrow_propagation_paths_raise_replay_correlation", "Preserve multi-role upstream/downstream exposure.")


def build_phase_a3_hub_concentration_measurement() -> OrderedDict[str, Any]:
    s = _base_stats()
    max_share = max(s["sectors"].values()) / len(s["rows"])
    val = round(max_share, 6)
    return _measurement("hub_concentration", ["sector", "topology_richness_score"], val, f"Largest sector share={val}", "high_concentration_reduces_ecology_resilience", "Constrain overrepresented sectors in future observational curation.")


def build_phase_a3_replay_overlap_risk_measurement() -> OrderedDict[str, Any]:
    s = _base_stats()
    overlap = sum(1 for r in s["rows"] if r["adjacency_richness_score"] >= 8 and r["propagation_richness_score"] >= 8) / len(s["rows"])
    val = round(overlap, 6)
    return _measurement("replay_overlap_risk", ["adjacency_richness_score", "propagation_richness_score"], val, f"Overlap pressure band={_band(val,0.25,0.5)}", "higher_overlap_can_create_monotonic_replay_paths", "Prefer nodes with orthogonal propagation structure.")


def build_phase_a3_monoculture_pressure_measurement() -> OrderedDict[str, Any]:
    s = _base_stats()
    mean_mono = sum(s["monoculture_scores"]) / len(s["monoculture_scores"])
    pressure = round(mean_mono / 10.0, 6)
    return _measurement("monoculture_pressure", ["monoculture_risk_score", "sector"], pressure, f"Monoculture pressure band={_band(pressure,0.4,0.7)}", "higher_pressure_signals_sector-domain crowding", "Rotate candidates toward non-dominant sectors/domains.")


def build_phase_a3_weak_node_amplification_measurement() -> OrderedDict[str, Any]:
    s = _base_stats()
    weak_ratio = sum(1 for x in s["low_info_scores"] if x >= 4) / len(s["low_info_scores"])
    val = round(weak_ratio, 6)
    return _measurement("weak_node_amplification", ["low_information_growth_risk_score", "replay_ecology_richness_score"], val, f"Weak-node amplification band={_band(val,0.25,0.5)}", "weak_nodes_can_amplify_noisy_replay_signals", "Prioritize high-information replacements for weak nodes.")


def build_phase_a3_structural_balance_score() -> OrderedDict[str, Any]:
    topo = build_phase_a3_topology_entropy_measurement()["measurement_value"]
    contra = build_phase_a3_contradiction_entropy_measurement()["measurement_value"]
    prop = build_phase_a3_propagation_diversity_measurement()["measurement_value"]
    mono_res = 1.0 - build_phase_a3_monoculture_pressure_measurement()["measurement_value"]
    weak_sup = 1.0 - build_phase_a3_weak_node_amplification_measurement()["measurement_value"]
    overlap_ctl = 1.0 - build_phase_a3_replay_overlap_risk_measurement()["measurement_value"]
    dims = OrderedDict([
        ("topology_diversity", topo),
        ("contradiction_diversity", contra),
        ("propagation_diversity", prop),
        ("monoculture_resistance", mono_res),
        ("weak_node_suppression", weak_sup),
        ("replay_overlap_control", overlap_ctl),
    ])
    score = round(sum(dims.values()) / len(dims), 6)
    strongest = max(dims.items(), key=lambda kv: kv[1])[0]
    weakest = min(dims.items(), key=lambda kv: kv[1])[0]
    return OrderedDict([
        ("score", score),
        ("band", _band(score, 0.45, 0.75)),
        ("strongest_supporting_dimension", strongest),
        ("weakest_dimension", weakest),
        ("caveats", ["derived_from_curated_metadata_only", "no_historical_ingestion", "no_operational_replay_execution"]),
        ("recommended_next_phase_action", "Proceed to Phase A4 narrative saturation under unchanged governance boundary."),
        ("subcomponent_scores", dims),
    ])


def build_phase_a3_replay_ecology_measurement_summary() -> OrderedDict[str, Any]:
    measurements = OrderedDict([
        ("topology_entropy", build_phase_a3_topology_entropy_measurement()),
        ("contradiction_entropy", build_phase_a3_contradiction_entropy_measurement()),
        ("propagation_diversity", build_phase_a3_propagation_diversity_measurement()),
        ("hub_concentration", build_phase_a3_hub_concentration_measurement()),
        ("replay_overlap_risk", build_phase_a3_replay_overlap_risk_measurement()),
        ("monoculture_pressure", build_phase_a3_monoculture_pressure_measurement()),
        ("weak_node_amplification", build_phase_a3_weak_node_amplification_measurement()),
    ])
    return OrderedDict([
        ("configuration", build_phase_a3_replay_ecology_measurement_configuration()),
        ("measurements", measurements),
        ("structural_balance_score", build_phase_a3_structural_balance_score()),
        ("governance_boundary", certify_phase_a_observational_expansion_boundary()),
    ])


def build_phase_a3_supervisor_review() -> OrderedDict[str, Any]:
    summary = build_phase_a3_replay_ecology_measurement_summary()
    return OrderedDict([
        ("phase", "A3"),
        ("status", "deterministic_derived_measurements_complete"),
        ("measurement_count", len(summary["measurements"])),
        ("structural_balance_score", summary["structural_balance_score"]),
        ("governance_boundary", summary["governance_boundary"]),
    ])


def build_phase_a3_markdown_report() -> str:
    m = build_phase_a3_replay_ecology_measurement_summary()
    b = m["governance_boundary"]
    s = m["structural_balance_score"]
    return "\n".join([
        "# Phase A3 Derived Replay Ecology Measurement",
        "## objective",
        "Convert A2 static replay-ecology labels into deterministic derived measurements.",
        "## relationship to A2",
        "A3 retains A2 observational planning scope while replacing static judgements with bounded pure-function metrics.",
        "## observational-only boundary",
        str(b),
        "## measurement methodology",
        "Entropy, concentration, overlap, and weak-node pressure are derived from curated deterministic metadata fields only.",
        "## topology entropy measurement",
        str(m["measurements"]["topology_entropy"]),
        "## contradiction entropy measurement",
        str(m["measurements"]["contradiction_entropy"]),
        "## propagation diversity measurement",
        str(m["measurements"]["propagation_diversity"]),
        "## hub concentration measurement",
        str(m["measurements"]["hub_concentration"]),
        "## replay overlap risk measurement",
        str(m["measurements"]["replay_overlap_risk"]),
        "## monoculture pressure measurement",
        str(m["measurements"]["monoculture_pressure"]),
        "## weak-node amplification measurement",
        str(m["measurements"]["weak_node_amplification"]),
        "## structural balance score",
        str(s),
        "## governance preservation",
        "All Phase A/A2 boundary flags remain unchanged and false-path preserving.",
        "## residual risks",
        "Metadata-only derivation may miss latent live-market topology shifts until future governed phases.",
        "## recommendation for Phase A4 or B1",
        s["recommended_next_phase_action"],
    ])
