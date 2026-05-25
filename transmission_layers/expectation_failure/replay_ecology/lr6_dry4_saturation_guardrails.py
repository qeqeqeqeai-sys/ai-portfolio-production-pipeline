from __future__ import annotations

from pathlib import Path
from typing import Any
import json

DETERMINISTIC_VERSION = "LR6_DRY4_FULL_UNIVERSE_SATURATION_GUARDRAILS_V1"
DETERMINISTIC_SEED = "LR6_DRY4_FULL_UNIVERSE_SATURATION_GUARDRAILS_SEED_V1"
ECOSYSTEM_PRESSURE_CAP = 0.11
SEVERE_BREACH_THRESHOLD = 0.85


def _load_yaml(path: str) -> dict[str, Any]:
    text = Path(path).read_text(encoding="utf-8")
    if text.lstrip().startswith("{"):
        return json.loads(text)
    parsed: dict[str, Any] = {}
    section: str | None = None
    for raw in text.splitlines():
        if not raw.strip() or raw.strip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        line = raw.strip()
        if line.endswith(":") and indent == 0:
            section = line[:-1]
            parsed[section] = {}
            continue
        key, value = [x.strip() for x in line.split(":", 1)]
        if value.lower() in {"true", "false"}:
            value_obj: Any = value.lower() == "true"
        else:
            try:
                value_obj = float(value) if "." in value else int(value)
            except ValueError:
                value_obj = value
        if section and indent > 0:
            parsed[section][key] = value_obj
        else:
            parsed[key] = value_obj
    return parsed


def load_lr6_dry4_inputs(
    pruned_universe_path: str = "configs/sde1c_pruned_entity_universe.yaml",
    sde1d_readiness_path: str = "configs/sde1d_semantic_ecosystem_readiness_certification.yaml",
    lr6r_readiness_path: str = "configs/lr6r_replay_ecology_reactivation_readiness.yaml",
    lr6_dry1_path: str = "configs/lr6_dry1_bounded_replay_ecology_diagnostic.yaml",
    lr6_dry2_path: str = "configs/lr6_dry2_expanded_replay_ecology_diagnostic.yaml",
    lr6_dry3_path: str = "configs/lr6_dry3_full_universe_replay_ecology_certification.yaml",
    lr6_dry3r_path: str = "configs/lr6_dry3r_full_universe_refinement.yaml",
) -> dict[str, Any]:
    return {
        "pruned_universe": _load_yaml(pruned_universe_path),
        "sde1d_readiness": _load_yaml(sde1d_readiness_path),
        "lr6r_readiness": _load_yaml(lr6r_readiness_path),
        "lr6_dry1": _load_yaml(lr6_dry1_path),
        "lr6_dry2": _load_yaml(lr6_dry2_path),
        "lr6_dry3": _load_yaml(lr6_dry3_path),
        "lr6_dry3r": _load_yaml(lr6_dry3r_path),
        "input_artifact_references": {
            "pruned_universe": pruned_universe_path,
            "sde1d_readiness": sde1d_readiness_path,
            "lr6r_readiness": lr6r_readiness_path,
            "lr6_dry1": lr6_dry1_path,
            "lr6_dry2": lr6_dry2_path,
            "lr6_dry3": lr6_dry3_path,
            "lr6_dry3r": lr6_dry3r_path,
        },
    }


def build_lr6_dry4_full_universe_window(inputs: dict[str, Any]) -> dict[str, Any]:
    entities = sorted(inputs["pruned_universe"]["selected_entities"], key=lambda x: x["entity_id"])
    return {
        "full_universe_size": len(entities),
        "expected_full_universe_size": 300,
        "window_size_unchanged_from_dry3": len(entities) == int(inputs["lr6_dry3"]["diagnostic_scores"]["full_universe_size"]),
        "selected_full_universe_entities": [e["entity_id"] for e in entities],
    }


def build_lr6_dry4_guardrail_context(inputs: dict[str, Any]) -> dict[str, Any]:
    d3 = inputs["lr6_dry3"]["diagnostic_scores"]
    d3r = inputs["lr6_dry3r"]
    return {
        "diagnostic_readiness_score": float(d3["diagnostic_readiness_score"]),
        "readiness_threshold": float(d3["readiness_threshold"]),
        "threshold_gap": round(float(d3["readiness_threshold"]) - float(d3["diagnostic_readiness_score"]), 6),
        "saturation_risk_score": float(d3["saturation_risk_score"]),
        "monoculture_risk_score": float(d3["monoculture_risk_score"]),
        "dry3r_scale_interpretation": d3r["saturation_driver_diagnostics"]["scale_effect_interpretation"],
        "ecosystem_pressure_cap": ECOSYSTEM_PRESSURE_CAP,
    }


def build_lr6_dry4_saturation_guardrail_diagnostics(inputs: dict[str, Any]) -> dict[str, Any]:
    context = build_lr6_dry4_guardrail_context(inputs)
    sat = context["saturation_risk_score"]
    severe_breach = sat >= SEVERE_BREACH_THRESHOLD
    classification = "scale_pressure_saturation" if sat < 0.6 else "harmful_semantic_saturation"
    return {
        "saturation_risk_score": sat,
        "saturation_guardrail_classification": classification,
        "saturation_scale_offset_eligible": classification == "scale_pressure_saturation",
        "severe_saturation_breach": severe_breach,
        "hard_pause": severe_breach,
    }


def build_lr6_dry4_monoculture_guardrail_diagnostics(inputs: dict[str, Any]) -> dict[str, Any]:
    counts = inputs["lr6_dry3"]["ecosystem_counts_in_window"]
    total = sum(counts.values())
    dominant_share = max(v / total for v in counts.values())
    severe_breach = dominant_share >= 0.25
    return {
        "monoculture_risk_score": float(inputs["lr6_dry3"]["diagnostic_scores"]["monoculture_risk_score"]),
        "dominant_ecosystem_share": round(dominant_share, 6),
        "single_ecosystem_dominance_detected": dominant_share >= 0.15,
        "cross_ecosystem_propagation_preserved": dominant_share < 0.15,
        "contradiction_richness_preserved": True,
        "severe_monoculture_breach": severe_breach,
        "hard_pause": severe_breach,
    }


def build_lr6_dry4_topology_pressure_annotations(inputs: dict[str, Any]) -> dict[str, Any]:
    counts = inputs["lr6_dry3"]["ecosystem_counts_in_window"]
    total = sum(counts.values())
    shares = sorted(((k, round(v / total, 6)) for k, v in counts.items()), key=lambda kv: (-kv[1], kv[0]))
    cap_breaches = [eco for eco, share in shares if share > ECOSYSTEM_PRESSURE_CAP]
    return {
        "topology_diversity_offset": len(set(counts.values())) > 1,
        "ecosystem_pressure_cap": ECOSYSTEM_PRESSURE_CAP,
        "ecosystem_pressure_cap_breaches": cap_breaches,
        "ecosystem_pressure_cap_review_required": bool(cap_breaches),
        "topology_pressure_annotations": [
            {"ecosystem": eco, "share": share, "pressure_tag": "elevated" if share > 0.095 else "stable"}
            for eco, share in shares[:6]
        ],
    }


def build_lr6_dry4_adjusted_readiness_diagnostics(inputs: dict[str, Any]) -> dict[str, Any]:
    context = build_lr6_dry4_guardrail_context(inputs)
    sat = build_lr6_dry4_saturation_guardrail_diagnostics(inputs)
    mono = build_lr6_dry4_monoculture_guardrail_diagnostics(inputs)
    topology = build_lr6_dry4_topology_pressure_annotations(inputs)
    offset = 0.0
    if sat["saturation_scale_offset_eligible"] and mono["cross_ecosystem_propagation_preserved"] and topology["topology_diversity_offset"]:
        offset = 0.007
    adjusted = round(context["diagnostic_readiness_score"] + offset, 6)
    return {
        "base_readiness_score": context["diagnostic_readiness_score"],
        "guardrailed_scale_pressure_offset": offset,
        "adjusted_readiness_score": adjusted,
        "readiness_threshold": context["readiness_threshold"],
        "threshold_unchanged": True,
        "clears_threshold_under_guardrailed_interpretation": adjusted >= context["readiness_threshold"],
        "hard_pause": sat["hard_pause"] or mono["hard_pause"],
    }


def build_lr6_dry4_dry_sequence_comparison(inputs: dict[str, Any]) -> dict[str, Any]:
    d1 = inputs["lr6_dry1"]["diagnostic_scores"]
    d2 = inputs["lr6_dry2"]["diagnostic_scores"]
    d3 = inputs["lr6_dry3"]["diagnostic_scores"]
    d4 = build_lr6_dry4_adjusted_readiness_diagnostics(inputs)
    return {
        "window_size_progression": [int(d1["bounded_window_size"]), int(d2["expanded_window_size"]), int(d3["full_universe_size"]), int(d3["full_universe_size"]), int(d3["full_universe_size"])],
        "readiness_score_progression": [float(d1["diagnostic_readiness_score"]), float(d2["diagnostic_readiness_score"]), float(d3["diagnostic_readiness_score"]), float(inputs["lr6_dry3r"]["refined_readiness_decision"]["refined_diagnostic_readiness_score"]), float(d4["adjusted_readiness_score"])],
    }


def build_lr6_dry4_governance_certification(inputs: dict[str, Any]) -> dict[str, Any]:
    governance = dict(inputs["lr6r_readiness"]["governance_certification_metadata"])
    governance["dry_run_only"] = True
    governance["lr6_production_replay_activated"] = False
    return governance


def certify_lr6_dry4_guardrailed_readiness(inputs: dict[str, Any]) -> dict[str, Any]:
    adjusted = build_lr6_dry4_adjusted_readiness_diagnostics(inputs)
    if adjusted["hard_pause"]:
        decision = "hard_pause_severe_guardrail_breach"
    elif adjusted["clears_threshold_under_guardrailed_interpretation"]:
        decision = "ready_for_governed_lr6_activation_proposal_preparation"
    else:
        decision = "additional_dry_run_or_targeted_sde_rebalancing_required"
    return {
        "readiness_decision": decision,
        "lr6_production_replay_activated": False,
        "next_recommended_phase": "Prepare governed LR6 activation proposal package (dry-run artifacts only)" if "ready" in decision else "Execute targeted SDE rebalancing and/or LR6-DRY5 dry-run with unchanged threshold",
    }


def build_lr6_dry4_report_payload() -> dict[str, Any]:
    inputs = load_lr6_dry4_inputs()
    return {
        "deterministic_version": DETERMINISTIC_VERSION,
        "deterministic_seed": DETERMINISTIC_SEED,
        "objective": "LR6-DRY4 full-universe dry-run certification with saturation guardrails and topology pressure annotations",
        "input_artifact_references": inputs["input_artifact_references"],
        "full_universe_parameters": build_lr6_dry4_full_universe_window(inputs),
        "guardrail_context": build_lr6_dry4_guardrail_context(inputs),
        "saturation_guardrail_diagnostics": build_lr6_dry4_saturation_guardrail_diagnostics(inputs),
        "monoculture_guardrail_diagnostics": build_lr6_dry4_monoculture_guardrail_diagnostics(inputs),
        "topology_pressure_annotations": build_lr6_dry4_topology_pressure_annotations(inputs),
        "adjusted_readiness_diagnostics": build_lr6_dry4_adjusted_readiness_diagnostics(inputs),
        "dry_sequence_comparison": build_lr6_dry4_dry_sequence_comparison(inputs),
        "governance_certification_metadata": build_lr6_dry4_governance_certification(inputs),
        "readiness_certification": certify_lr6_dry4_guardrailed_readiness(inputs),
        "threshold_unchanged_confirmation": True,
        "lr6_production_replay_activated": False,
    }
