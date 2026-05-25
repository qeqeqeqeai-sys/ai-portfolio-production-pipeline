from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

import json

DETERMINISTIC_VERSION = "LR6_DRY3_FULL_UNIVERSE_CERTIFICATION_V1"
DETERMINISTIC_SEED = "LR6_DRY3_FULL_UNIVERSE_CERTIFICATION_SEED_V1"
READINESS_THRESHOLD = 0.79
DEFAULT_MAX_ENTITIES = 300
TARGET_ECOSYSTEMS = 12
ECOSYSTEM_SHARE_CAP = 0.22


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


def load_lr6_dry3_inputs(
    pruned_universe_path: str = "configs/sde1c_pruned_entity_universe.yaml",
    sde1d_readiness_path: str = "configs/sde1d_semantic_ecosystem_readiness_certification.yaml",
    lr6r_readiness_path: str = "configs/lr6r_replay_ecology_reactivation_readiness.yaml",
    lr6_dry1_path: str = "configs/lr6_dry1_bounded_replay_ecology_diagnostic.yaml",
    lr6_dry2_path: str = "configs/lr6_dry2_expanded_replay_ecology_diagnostic.yaml",
) -> dict[str, Any]:
    return {
        "pruned_universe": _load_yaml(pruned_universe_path),
        "sde1d_readiness": _load_yaml(sde1d_readiness_path),
        "lr6r_readiness": _load_yaml(lr6r_readiness_path),
        "lr6_dry1": _load_yaml(lr6_dry1_path),
        "lr6_dry2": _load_yaml(lr6_dry2_path),
        "input_artifact_references": {
            "pruned_universe": pruned_universe_path,
            "sde1d_readiness": sde1d_readiness_path,
            "lr6r_readiness": lr6r_readiness_path,
            "lr6_dry1": lr6_dry1_path,
            "lr6_dry2": lr6_dry2_path,
        },
    }


def build_lr6_dry3_full_universe_window(inputs: dict[str, Any], max_entities: int = DEFAULT_MAX_ENTITIES) -> dict[str, Any]:
    entities = sorted(inputs["pruned_universe"]["selected_entities"], key=lambda e: (e["primary_ecosystem"], e["entity_id"]))
    selected = entities[:max_entities]
    counts = Counter(e["primary_ecosystem"] for e in selected)
    return {
        "max_entities": max_entities,
        "selected_entities": selected,
        "ecosystem_counts": dict(sorted(counts.items())),
        "full_universe_selected": len(selected) == len(inputs["pruned_universe"]["selected_entities"]),
    }


def build_lr6_dry3_replay_ecology_diagnostics(window: dict[str, Any], inputs: dict[str, Any]) -> dict[str, Any]:
    total_ecosystems = len(inputs["sde1d_readiness"]["diagnostics"]["ecosystem_counts"])
    covered = len(window["ecosystem_counts"])
    return {
        "full_universe_size": len(window["selected_entities"]),
        "ecosystem_coverage_in_window": round(covered / total_ecosystems, 6),
    }


def build_lr6_dry3_semantic_diversity_diagnostics(window: dict[str, Any]) -> dict[str, float]:
    entities = window["selected_entities"]
    unique_secondary = {eco for e in entities for eco in e.get("secondary_ecosystems", [])}
    score = round((len(unique_secondary) / TARGET_ECOSYSTEMS + len(window["ecosystem_counts"]) / TARGET_ECOSYSTEMS) / 2, 6)
    return {"semantic_diversity_score": score}


def build_lr6_dry3_contradiction_richness_diagnostics(window: dict[str, Any]) -> dict[str, float]:
    entities = window["selected_entities"]
    score = round(sum(len(e.get("contradiction_surfaces", [])) for e in entities) / (len(entities) * 3), 6)
    return {"contradiction_richness_score": score}


def build_lr6_dry3_propagation_pathway_diagnostics(window: dict[str, Any]) -> dict[str, float]:
    entities = window["selected_entities"]
    link_score = sum(len(e.get("propagation_links", [])) for e in entities) / (len(entities) * 3)
    roles = len({e.get("propagation_role") for e in entities}) / 5
    return {"propagation_pathway_score": round(min(1.0, (link_score + roles) / 2), 6)}


def build_lr6_dry3_saturation_risk_diagnostics(window: dict[str, Any]) -> dict[str, float]:
    max_share = max(window["ecosystem_counts"].values()) / len(window["selected_entities"])
    return {"saturation_risk_score": round(max_share / ECOSYSTEM_SHARE_CAP, 6)}


def build_lr6_dry3_monoculture_risk_diagnostics(window: dict[str, Any]) -> dict[str, float]:
    max_share = max(window["ecosystem_counts"].values()) / len(window["selected_entities"])
    return {"monoculture_risk_score": round(max(0.0, min(1.0, max_share / ECOSYSTEM_SHARE_CAP)), 6)}


def build_lr6_dry3_dry_sequence_comparison(diagnostics: dict[str, Any], inputs: dict[str, Any], window: dict[str, Any]) -> dict[str, Any]:
    dry1 = inputs["lr6_dry1"]
    dry2 = inputs["lr6_dry2"]
    d1 = dry1["diagnostic_scores"]
    d2 = dry2["diagnostic_scores"]
    d3 = diagnostics
    return {
        "window_size_progression": [int(d1["bounded_window_size"]), int(d2["expanded_window_size"]), int(d3["full_universe_size"])],
        "ecosystem_balance_stability": round(1 - (max(window["ecosystem_counts"].values()) - min(window["ecosystem_counts"].values())) / max(1, len(window["selected_entities"])), 6),
        "semantic_diversity_stability": round(1 - abs(float(d3["semantic_diversity_score"]) - float(d2["semantic_diversity_score"])), 6),
        "contradiction_richness_stability": round(1 - abs(float(d3["contradiction_richness_score"]) - float(d2["contradiction_richness_score"])), 6),
        "propagation_richness_stability": round(1 - abs(float(d3["propagation_pathway_score"]) - float(d2["propagation_pathway_score"])), 6),
        "saturation_risk_trend": round(float(d3["saturation_risk_score"]) - float(d2["saturation_risk_score"]), 6),
        "monoculture_risk_trend": round(float(d3["monoculture_risk_score"]) - float(d2["monoculture_risk_score"]), 6),
        "readiness_score_progression": [float(d1["diagnostic_readiness_score"]), float(d2["diagnostic_readiness_score"]), float(d3["diagnostic_readiness_score"])],
        "stability_interpretation": "stable_progressive_expansion" if d3["dry_sequence_stability_score"] >= 0.85 else "mixed_stability",
    }


def build_lr6_dry3_governance_certification(inputs: dict[str, Any]) -> dict[str, Any]:
    return {**inputs["lr6r_readiness"]["governance_certification_metadata"], "dry_run_only": True, "lr6_production_replay_activated": False}


def certify_lr6_dry3_full_universe_readiness(diagnostics: dict[str, Any], governance: dict[str, Any]) -> dict[str, Any]:
    score = round((
        diagnostics["semantic_diversity_score"] + diagnostics["contradiction_richness_score"] + diagnostics["propagation_pathway_score"] +
        (1 - diagnostics["saturation_risk_score"]) + (1 - diagnostics["monoculture_risk_score"]) + diagnostics["dry_run_governance_score"] +
        diagnostics["dry_sequence_stability_score"]
    ) / 7, 6)
    decision = score >= READINESS_THRESHOLD and governance["dry_run_only"] and not governance["lr6_production_replay_activated"]
    return {
        "diagnostic_readiness_score": score,
        "readiness_threshold": READINESS_THRESHOLD,
        "full_universe_readiness_decision": "ready_for_governed_lr6_activation_proposal" if decision else "additional_dry_run_iteration_required",
        "governed_activation_proposal_readiness_flag": decision,
    }


def build_lr6_dry3_report_payload(max_entities: int = DEFAULT_MAX_ENTITIES) -> dict[str, Any]:
    inputs = load_lr6_dry3_inputs()
    window = build_lr6_dry3_full_universe_window(inputs, max_entities=max_entities)
    governance = build_lr6_dry3_governance_certification(inputs)
    diagnostics = {
        **build_lr6_dry3_replay_ecology_diagnostics(window, inputs),
        **build_lr6_dry3_semantic_diversity_diagnostics(window),
        **build_lr6_dry3_contradiction_richness_diagnostics(window),
        **build_lr6_dry3_propagation_pathway_diagnostics(window),
        **build_lr6_dry3_saturation_risk_diagnostics(window),
        **build_lr6_dry3_monoculture_risk_diagnostics(window),
    }
    diagnostics["dry_run_governance_score"] = 1.0 if all(bool(v) for k, v in governance.items() if k != "lr6_production_replay_activated") else 0.0
    diagnostics["diagnostic_readiness_score"] = 0.0
    diagnostics["dry_sequence_stability_score"] = 0.0
    sequence = build_lr6_dry3_dry_sequence_comparison(diagnostics, inputs, window)
    diagnostics["dry_sequence_stability_score"] = round((sequence["ecosystem_balance_stability"] + sequence["semantic_diversity_stability"] + sequence["contradiction_richness_stability"] + sequence["propagation_richness_stability"]) / 4, 6)
    readiness = certify_lr6_dry3_full_universe_readiness(diagnostics, governance)
    full = {**diagnostics, **readiness}
    sequence = build_lr6_dry3_dry_sequence_comparison(full, inputs, window)
    return {
        "deterministic_version": DETERMINISTIC_VERSION,
        "deterministic_seed": DETERMINISTIC_SEED,
        "objective": "LR6-DRY3 full-universe replay ecology dry-run certification (no replay execution)",
        "input_artifact_references": inputs["input_artifact_references"],
        "full_universe_dry_run_window_parameters": {
            "max_entities": max_entities,
            "expected_max_entities": DEFAULT_MAX_ENTITIES,
            "ecosystem_share_cap": ECOSYSTEM_SHARE_CAP,
            "full_universe_selected": window["full_universe_selected"],
        },
        "selected_full_universe_entities": [e["entity_id"] for e in window["selected_entities"]],
        "ecosystem_counts_in_window": window["ecosystem_counts"],
        "diagnostic_scores": full,
        "dry_sequence_comparison_metrics": sequence,
        "governance_certification_metadata": governance,
        "next_recommended_phase": "Prepare governed LR6 activation proposal (no activation executed)" if readiness["governed_activation_proposal_readiness_flag"] else "Repeat LR6-DRY3 diagnostics",
        "lr6_production_replay_activated": False,
    }
