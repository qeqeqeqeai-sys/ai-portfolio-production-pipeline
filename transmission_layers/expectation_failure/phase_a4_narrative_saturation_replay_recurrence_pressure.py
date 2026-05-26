from __future__ import annotations

from collections import Counter, OrderedDict
from typing import Any

from .phase_a1_curated_observational_expansion import (
    build_phase_a1b_real_curated_structural_universe,
    certify_phase_a_observational_expansion_boundary,
)
from .phase_a3_derived_replay_ecology_measurement import (
    build_phase_a3_hub_concentration_measurement,
    build_phase_a3_monoculture_pressure_measurement,
    build_phase_a3_replay_overlap_risk_measurement,
    build_phase_a3_structural_balance_score,
    build_phase_a3_weak_node_amplification_measurement,
)


def _band(value: float, lo: float = 0.33, hi: float = 0.66) -> str:
    if value < lo:
        return "low"
    if value < hi:
        return "moderate"
    return "high"


def _bounded(v: float) -> float:
    return round(max(0.0, min(1.0, v)), 6)


def _measurement(metric_name: str, inputs: list[str], value: float, interpretation: str, risk: str, mitigation: str) -> OrderedDict[str, Any]:
    return OrderedDict([
        ("metric_name", metric_name),
        ("deterministic_inputs_used", inputs),
        ("measurement_value", _bounded(value)),
        ("measurement_band", _band(_bounded(value))),
        ("interpretation", interpretation),
        ("replay_ecology_risk", risk),
        ("mitigation_guidance", mitigation),
        ("governance_status", "observational_only_boundary_preserved"),
    ])


def _base() -> dict[str, Any]:
    rows = build_phase_a1b_real_curated_structural_universe()
    sectors = Counter(r["sector"] for r in rows)
    domains = Counter(r["sefi_domain"] for r in rows)
    return {
        "rows": rows,
        "sectors": sectors,
        "domains": domains,
        "adj": [r["adjacency_richness_score"] / 10 for r in rows],
        "contra": [r["contradiction_richness_score"] / 10 for r in rows],
        "prop": [r["propagation_richness_score"] / 10 for r in rows],
        "mono": [r["monoculture_risk_score"] / 10 for r in rows],
        "low_info": [r["low_information_growth_risk_score"] / 10 for r in rows],
        "replay": [r["replay_ecology_richness_score"] / 10 for r in rows],
    }


def build_phase_a4_narrative_saturation_configuration() -> OrderedDict[str, Any]:
    return OrderedDict([
        ("phase", "A4"),
        ("mode", "deterministic_observational_pressure_measurement"),
        ("measurement_input_source", "phase_a1b_real_curated_structural_universe_plus_phase_a3_measurements"),
        ("observational_only", True),
        ("bounded", True),
        ("pure_function_oriented", True),
        ("governance_boundary", certify_phase_a_observational_expansion_boundary()),
    ])


def build_phase_a4_narrative_saturation_pressure_measurement() -> OrderedDict[str, Any]:
    b = _base()
    value = _bounded((sum(b["mono"]) / len(b["mono"]) + build_phase_a3_monoculture_pressure_measurement()["measurement_value"] + build_phase_a3_hub_concentration_measurement()["measurement_value"]) / 3)
    return _measurement("narrative_saturation_pressure", ["sector", "sefi_domain", "monoculture_risk_score", "hub_concentration"], value, f"Narrative concentration pressure band={_band(value)}.", "higher_values_raise_story_monotony_risk", "Increase domain/sector heterogeneity in next curated refresh.")


def build_phase_a4_replay_recurrence_pressure_measurement() -> OrderedDict[str, Any]:
    b = _base()
    value = _bounded((sum(1 for i in range(len(b["rows"])) if b["adj"][i] >= 0.8 and b["prop"][i] >= 0.8) / len(b["rows"]) + build_phase_a3_replay_overlap_risk_measurement()["measurement_value"]) / 2)
    return _measurement("replay_recurrence_pressure", ["adjacency_richness_score", "propagation_richness_score", "replay_overlap_risk"], value, f"Recurrence pressure band={_band(value)}.", "higher_values_imply_reused_replay_corridors", "Prefer orthogonal propagation and adjacency mixes.")


def build_phase_a4_contradiction_recurrence_density_measurement() -> OrderedDict[str, Any]:
    b = _base()
    high_contra = sum(1 for x in b["contra"] if x >= 0.8) / len(b["contra"])
    value = _bounded((high_contra + build_phase_a3_weak_node_amplification_measurement()["measurement_value"]) / 2)
    return _measurement("contradiction_recurrence_density", ["contradiction_richness_score", "weak_node_amplification"], value, f"Contradiction recurrence density band={_band(value)}.", "excess_density_can_recycle_identical_tension_frames", "Inject underrepresented contradiction classes in future curation.")


def build_phase_a4_semantic_crowding_measurement() -> OrderedDict[str, Any]:
    b = _base()
    sec_top = max(b["sectors"].values()) / len(b["rows"])
    dom_top = max(b["domains"].values()) / len(b["rows"])
    value = _bounded((sec_top + dom_top + build_phase_a3_hub_concentration_measurement()["measurement_value"]) / 3)
    return _measurement("semantic_crowding", ["sector", "sefi_domain", "hub_concentration"], value, f"Semantic crowding band={_band(value)}.", "crowding_can_reduce_signal_novelty", "Increase coverage of less-dense sectors/domains.")


def build_phase_a4_novelty_decay_risk_measurement() -> OrderedDict[str, Any]:
    b = _base()
    low_novelty = sum(1 for i in range(len(b["rows"])) if b["replay"][i] >= 0.8 and b["low_info"][i] >= 0.4) / len(b["rows"])
    value = _bounded((low_novelty + build_phase_a3_replay_overlap_risk_measurement()["measurement_value"] + build_phase_a3_monoculture_pressure_measurement()["measurement_value"]) / 3)
    return _measurement("novelty_decay_risk", ["replay_ecology_richness_score", "low_information_growth_risk_score", "replay_overlap_risk", "monoculture_pressure"], value, f"Novelty decay risk band={_band(value)}.", "higher_values_indicate_reducing_marginal_information_gain", "Favor high-information nodes with lower overlap structure.")


def build_phase_a4_structural_redundancy_measurement() -> OrderedDict[str, Any]:
    a3_balance = build_phase_a3_structural_balance_score()["score"]
    value = _bounded((build_phase_a3_hub_concentration_measurement()["measurement_value"] + build_phase_a3_replay_overlap_risk_measurement()["measurement_value"] + (1 - a3_balance)) / 3)
    return _measurement("structural_redundancy", ["hub_concentration", "replay_overlap_risk", "structural_balance_score"], value, f"Structural redundancy band={_band(value)}.", "redundancy_can_overweight_repeated_pathways", "Constrain high-centrality repeated structures in future adds.")


def build_phase_a4_replay_path_repetition_measurement() -> OrderedDict[str, Any]:
    b = _base()
    repeated = sum(1 for i in range(len(b["rows"])) if b["adj"][i] >= 0.8 and b["replay"][i] >= 0.8) / len(b["rows"])
    value = _bounded((repeated + build_phase_a3_replay_overlap_risk_measurement()["measurement_value"]) / 2)
    return _measurement("replay_path_repetition", ["adjacency_richness_score", "replay_ecology_richness_score", "replay_overlap_risk"], value, f"Replay path repetition band={_band(value)}.", "repetition_can_accelerate_replay_lock_in", "Diversify path structures before any governed replay scaling.")


def build_phase_a4_contradiction_exhaustion_risk_measurement() -> OrderedDict[str, Any]:
    b = _base()
    same_bucket = Counter(int(x * 10) for x in b["contra"])
    dominant_share = max(same_bucket.values()) / len(b["rows"])
    value = _bounded((dominant_share + build_phase_a3_weak_node_amplification_measurement()["measurement_value"]) / 2)
    return _measurement("contradiction_exhaustion_risk", ["contradiction_richness_score", "weak_node_amplification"], value, f"Contradiction exhaustion risk band={_band(value)}.", "exhaustion_risk_can_flatten_future_contradiction_yield", "Increase contradiction spread across buckets/domains.")


def build_phase_a4_saturation_recurrence_composite_score() -> OrderedDict[str, Any]:
    dims = OrderedDict([
        ("narrative_saturation_pressure", build_phase_a4_narrative_saturation_pressure_measurement()["measurement_value"]),
        ("replay_recurrence_pressure", build_phase_a4_replay_recurrence_pressure_measurement()["measurement_value"]),
        ("contradiction_recurrence_density", build_phase_a4_contradiction_recurrence_density_measurement()["measurement_value"]),
        ("semantic_crowding", build_phase_a4_semantic_crowding_measurement()["measurement_value"]),
        ("novelty_decay_risk", build_phase_a4_novelty_decay_risk_measurement()["measurement_value"]),
        ("structural_redundancy", build_phase_a4_structural_redundancy_measurement()["measurement_value"]),
        ("replay_path_repetition", build_phase_a4_replay_path_repetition_measurement()["measurement_value"]),
        ("contradiction_exhaustion_risk", build_phase_a4_contradiction_exhaustion_risk_measurement()["measurement_value"]),
    ])
    score = _bounded(sum(dims.values()) / len(dims))
    return OrderedDict([
        ("score", score),
        ("band", _band(score)),
        ("strongest_pressure_dimension", max(dims.items(), key=lambda kv: kv[1])[0]),
        ("weakest_pressure_dimension", min(dims.items(), key=lambda kv: kv[1])[0]),
        ("caveats", ["metadata_only_derivation", "no_historical_ingestion", "higher_score_means_higher_pressure"]),
        ("recommended_next_phase_action", "Proceed to Phase A5 with anti-recurrence curation guardrails; keep operational replay disabled."),
        ("subcomponent_scores", dims),
    ])


def build_phase_a4_supervisor_review() -> OrderedDict[str, Any]:
    return OrderedDict([
        ("phase", "A4"),
        ("status", "deterministic_observational_pressure_measurements_complete"),
        ("configuration", build_phase_a4_narrative_saturation_configuration()),
        ("composite_score", build_phase_a4_saturation_recurrence_composite_score()),
        ("governance_boundary", certify_phase_a_observational_expansion_boundary()),
    ])


def build_phase_a4_markdown_report() -> str:
    c = build_phase_a4_saturation_recurrence_composite_score()
    g = certify_phase_a_observational_expansion_boundary()
    return "\n".join([
        "# Phase A4 Narrative Saturation & Replay Recurrence Pressure",
        "## objective",
        "Add deterministic observational pressure metrics for semantic/narrative replay crowding risk before any replay operationalization.",
        "## relationship to A3",
        "A4 extends A3 by converting replay overlap and hub concentration findings into saturation/recurrence pressure measurements.",
        "## observational-only boundary", str(g),
        "## measurement methodology",
        "All metrics are bounded [0,1], deterministic, metadata-only, and derived from curated universe plus A3 measurements.",
        "## narrative saturation pressure", str(build_phase_a4_narrative_saturation_pressure_measurement()),
        "## replay recurrence pressure", str(build_phase_a4_replay_recurrence_pressure_measurement()),
        "## contradiction recurrence density", str(build_phase_a4_contradiction_recurrence_density_measurement()),
        "## semantic crowding", str(build_phase_a4_semantic_crowding_measurement()),
        "## novelty decay risk", str(build_phase_a4_novelty_decay_risk_measurement()),
        "## structural redundancy", str(build_phase_a4_structural_redundancy_measurement()),
        "## replay path repetition", str(build_phase_a4_replay_path_repetition_measurement()),
        "## contradiction exhaustion risk", str(build_phase_a4_contradiction_exhaustion_risk_measurement()),
        "## saturation recurrence composite score", str(c),
        "## governance preservation",
        "All Phase A boundary flags remain unchanged; no writes, schema paths, SQL paths, prediction, trading, or topology activation.",
        "## residual risks",
        "Metadata-only derivation may under-represent latent semantic drift until future governed phases.",
        "## recommendation for Phase A5 or B1", c["recommended_next_phase_action"],
    ])
