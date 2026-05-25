from __future__ import annotations

from pathlib import Path
from typing import Any
import json

DETERMINISTIC_VERSION = "LR6_DRY3R_FULL_UNIVERSE_REFINEMENT_V1"
DETERMINISTIC_SEED = "LR6_DRY3R_FULL_UNIVERSE_REFINEMENT_SEED_V1"
LOW_CONNECTIVITY_THRESHOLD = 2.0


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


def load_lr6_dry3r_inputs(
    pruned_universe_path: str = "configs/sde1c_pruned_entity_universe.yaml",
    sde1d_readiness_path: str = "configs/sde1d_semantic_ecosystem_readiness_certification.yaml",
    lr6r_readiness_path: str = "configs/lr6r_replay_ecology_reactivation_readiness.yaml",
    lr6_dry1_path: str = "configs/lr6_dry1_bounded_replay_ecology_diagnostic.yaml",
    lr6_dry2_path: str = "configs/lr6_dry2_expanded_replay_ecology_diagnostic.yaml",
    lr6_dry3_path: str = "configs/lr6_dry3_full_universe_replay_ecology_certification.yaml",
) -> dict[str, Any]:
    return {
        "pruned_universe": _load_yaml(pruned_universe_path),
        "sde1d_readiness": _load_yaml(sde1d_readiness_path),
        "lr6r_readiness": _load_yaml(lr6r_readiness_path),
        "lr6_dry1": _load_yaml(lr6_dry1_path),
        "lr6_dry2": _load_yaml(lr6_dry2_path),
        "lr6_dry3": _load_yaml(lr6_dry3_path),
        "input_artifact_references": {
            "pruned_universe": pruned_universe_path,
            "sde1d_readiness": sde1d_readiness_path,
            "lr6r_readiness": lr6r_readiness_path,
            "lr6_dry1": lr6_dry1_path,
            "lr6_dry2": lr6_dry2_path,
            "lr6_dry3": lr6_dry3_path,
        },
    }


def build_lr6_dry3r_threshold_gap_analysis(inputs: dict[str, Any]) -> dict[str, Any]:
    d3 = inputs["lr6_dry3"]["diagnostic_scores"]
    gap = round(float(d3["readiness_threshold"]) - float(d3["diagnostic_readiness_score"]), 6)
    return {
        "diagnostic_readiness_score": float(d3["diagnostic_readiness_score"]),
        "readiness_threshold": float(d3["readiness_threshold"]),
        "threshold_gap": gap,
        "gap_bps": int(round(gap * 10000)),
        "miss_type": "near_threshold_shortfall" if gap <= 0.01 else "material_shortfall",
    }


def build_lr6_dry3r_saturation_driver_diagnostics(inputs: dict[str, Any]) -> dict[str, Any]:
    counts = inputs["lr6_dry3"]["ecosystem_counts_in_window"]
    total = sum(counts.values())
    shares = {k: round(v / total, 6) for k, v in sorted(counts.items())}
    ranked = sorted(shares.items(), key=lambda kv: (-kv[1], kv[0]))
    d2 = float(inputs["lr6_dry2"]["diagnostic_scores"]["saturation_risk_score"])
    d3 = float(inputs["lr6_dry3"]["diagnostic_scores"]["saturation_risk_score"])
    return {
        "saturation_risk_score": d3,
        "saturation_risk_delta_vs_dry2": round(d3 - d2, 6),
        "top_concentration_ecosystems": [
            {"ecosystem": eco, "share": share} for eco, share in ranked[:4]
        ],
        "ecosystem_share_spread": round(max(shares.values()) - min(shares.values()), 6),
        "scale_effect_interpretation": "acceptable_expansion_pressure" if (d3 - d2) <= 0.08 else "elevated_expansion_pressure",
    }


def build_lr6_dry3r_monoculture_driver_diagnostics(inputs: dict[str, Any]) -> dict[str, Any]:
    sat = build_lr6_dry3r_saturation_driver_diagnostics(inputs)
    return {
        "monoculture_risk_score": float(inputs["lr6_dry3"]["diagnostic_scores"]["monoculture_risk_score"]),
        "monoculture_risk_delta_vs_dry2": round(
            float(inputs["lr6_dry3"]["diagnostic_scores"]["monoculture_risk_score"]) - float(inputs["lr6_dry2"]["diagnostic_scores"]["monoculture_risk_score"]),
            6,
        ),
        "dominant_ecosystem_share": sat["top_concentration_ecosystems"][0]["share"],
        "dominance_interpretation": "no_single_ecosystem_monoculture" if sat["top_concentration_ecosystems"][0]["share"] < 0.15 else "emergent_monoculture_pressure",
    }


def build_lr6_dry3r_ecosystem_pressure_diagnostics(inputs: dict[str, Any]) -> dict[str, Any]:
    entities = inputs["pruned_universe"]["selected_entities"]
    low = []
    for e in sorted(entities, key=lambda x: x["entity_id"]):
        links = len(e.get("propagation_links", []))
        contradictions = len(e.get("contradiction_surfaces", []))
        pressure = round((links + contradictions) / 2, 6)
        if pressure <= LOW_CONNECTIVITY_THRESHOLD:
            low.append({"entity_id": e["entity_id"], "pressure_score": pressure, "primary_ecosystem": e["primary_ecosystem"]})
    return {
        "low_connectivity_threshold": LOW_CONNECTIVITY_THRESHOLD,
        "low_information_entity_count": len(low),
        "low_information_entities_preview": low[:12],
        "low_connectivity_cluster_signal": "present" if low else "not_present",
    }


def build_lr6_dry3r_refinement_actions(inputs: dict[str, Any]) -> dict[str, Any]:
    gap = build_lr6_dry3r_threshold_gap_analysis(inputs)
    sat = build_lr6_dry3r_saturation_driver_diagnostics(inputs)
    return {
        "preserve_full_universe_300": True,
        "entity_exclusion_recommended": False,
        "actions": [
            "Apply stricter saturation interpretation in next dry-run certification review.",
            "Annotate topology pressure for top concentration ecosystems before DRY4 scoring.",
            "Enforce ecosystem pressure cap review gate when dominant ecosystem share exceeds 0.10.",
            "Add dry-run escalation guardrail: require non-increasing saturation trend before activation proposal.",
            "Recommend targeted SDE-1C rebalancing only if saturation delta remains above +0.05 in next full-universe dry-run.",
            "Execute another full-universe dry-run iteration with unchanged readiness threshold.",
        ],
        "calibration_adjustment_required": gap["threshold_gap"] < 0.01 and sat["scale_effect_interpretation"] == "acceptable_expansion_pressure",
    }


def build_lr6_dry3r_refined_certification(inputs: dict[str, Any]) -> dict[str, Any]:
    d3 = inputs["lr6_dry3"]["diagnostic_scores"]
    threshold = float(d3["readiness_threshold"])
    score = float(d3["diagnostic_readiness_score"])
    return {
        "refined_diagnostic_readiness_score": score,
        "readiness_threshold": threshold,
        "threshold_unchanged": True,
        "refined_readiness_decision": "additional_dry_run_iteration_required" if score < threshold else "ready_for_governed_lr6_activation_proposal",
        "lr6_production_replay_activated": False,
    }


def build_lr6_dry3r_dry_sequence_comparison(inputs: dict[str, Any]) -> dict[str, Any]:
    d1 = inputs["lr6_dry1"]["diagnostic_scores"]
    d2 = inputs["lr6_dry2"]["diagnostic_scores"]
    d3 = inputs["lr6_dry3"]["diagnostic_scores"]
    return {
        "window_size_progression": [int(d1["bounded_window_size"]), int(d2["expanded_window_size"]), int(d3["full_universe_size"]), int(d3["full_universe_size"])],
        "readiness_score_progression": [float(d1["diagnostic_readiness_score"]), float(d2["diagnostic_readiness_score"]), float(d3["diagnostic_readiness_score"]), float(d3["diagnostic_readiness_score"])],
        "saturation_progression": [float(d1["saturation_risk_score"]), float(d2["saturation_risk_score"]), float(d3["saturation_risk_score"])],
        "monoculture_progression": [float(d1["monoculture_risk_score"]), float(d2["monoculture_risk_score"]), float(d3["monoculture_risk_score"])],
        "interpretation": "full_universe_scale_effect_with_stable_topology",
    }


def build_lr6_dry3r_governance_certification(inputs: dict[str, Any]) -> dict[str, Any]:
    governance = dict(inputs["lr6r_readiness"]["governance_certification_metadata"])
    governance["dry_run_only"] = True
    governance["lr6_production_replay_activated"] = False
    return governance


def build_lr6_dry3r_report_payload() -> dict[str, Any]:
    inputs = load_lr6_dry3r_inputs()
    return {
        "deterministic_version": DETERMINISTIC_VERSION,
        "deterministic_seed": DETERMINISTIC_SEED,
        "objective": "LR6-DRY3R deterministic refinement and saturation-risk diagnostics (dry-run only)",
        "input_artifact_references": inputs["input_artifact_references"],
        "threshold_gap_analysis": build_lr6_dry3r_threshold_gap_analysis(inputs),
        "saturation_driver_diagnostics": build_lr6_dry3r_saturation_driver_diagnostics(inputs),
        "monoculture_driver_diagnostics": build_lr6_dry3r_monoculture_driver_diagnostics(inputs),
        "ecosystem_pressure_diagnostics": build_lr6_dry3r_ecosystem_pressure_diagnostics(inputs),
        "recommended_refinement_actions": build_lr6_dry3r_refinement_actions(inputs),
        "refined_readiness_decision": build_lr6_dry3r_refined_certification(inputs),
        "dry_sequence_comparison": build_lr6_dry3r_dry_sequence_comparison(inputs),
        "governance_certification_metadata": build_lr6_dry3r_governance_certification(inputs),
        "next_recommended_phase": "LR6-DRY4 full-universe replay ecology dry-run with saturation guardrails",
        "lr6_production_replay_activated": False,
    }
