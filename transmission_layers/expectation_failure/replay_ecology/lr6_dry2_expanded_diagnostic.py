from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

import json

DETERMINISTIC_VERSION = "LR6_DRY2_EXPANDED_DIAGNOSTIC_V1"
DETERMINISTIC_SEED = "LR6_DRY2_EXPANDED_DIAGNOSTIC_SEED_V1"
READINESS_THRESHOLD = 0.76
DEFAULT_MAX_ENTITIES = 120
TARGET_ECOSYSTEMS = 12
TARGET_ENTITIES_PER_ECOSYSTEM = 10
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


def load_lr6_dry2_inputs(
    pruned_universe_path: str = "configs/sde1c_pruned_entity_universe.yaml",
    sde1d_readiness_path: str = "configs/sde1d_semantic_ecosystem_readiness_certification.yaml",
    lr6r_readiness_path: str = "configs/lr6r_replay_ecology_reactivation_readiness.yaml",
    lr6_dry1_path: str = "configs/lr6_dry1_bounded_replay_ecology_diagnostic.yaml",
) -> dict[str, Any]:
    return {
        "pruned_universe": _load_yaml(pruned_universe_path),
        "sde1d_readiness": _load_yaml(sde1d_readiness_path),
        "lr6r_readiness": _load_yaml(lr6r_readiness_path),
        "lr6_dry1": _load_yaml(lr6_dry1_path),
        "input_artifact_references": {
            "pruned_universe": pruned_universe_path,
            "sde1d_readiness": sde1d_readiness_path,
            "lr6r_readiness": lr6r_readiness_path,
            "lr6_dry1": lr6_dry1_path,
        },
    }


def build_lr6_dry2_expanded_window(inputs: dict[str, Any], max_entities: int = DEFAULT_MAX_ENTITIES) -> dict[str, Any]:
    entities = inputs["pruned_universe"]["selected_entities"]
    ecosystem_cap = max(1, int(max_entities * ECOSYSTEM_SHARE_CAP))
    target_per_ecosystem = min(TARGET_ENTITIES_PER_ECOSYSTEM, ecosystem_cap)

    by_ecosystem: dict[str, list[dict[str, Any]]] = {}
    for e in entities:
        by_ecosystem.setdefault(e["primary_ecosystem"], []).append(e)

    ranked: dict[str, list[dict[str, Any]]] = {}
    for ecosystem in sorted(by_ecosystem):
        ranked[ecosystem] = sorted(by_ecosystem[ecosystem], key=lambda e: (-float(e["information_quality_score"]), e["entity_id"]))

    selected: list[dict[str, Any]] = []
    ecosystems = sorted(ranked)
    for i in range(target_per_ecosystem):
        for ecosystem in ecosystems:
            if len(selected) >= max_entities:
                break
            bucket = ranked[ecosystem]
            if i < len(bucket):
                selected.append(bucket[i])

    if len(selected) < max_entities:
        counts = Counter(e["primary_ecosystem"] for e in selected)
        leftovers: list[dict[str, Any]] = []
        for ecosystem in ecosystems:
            leftovers.extend(ranked[ecosystem][target_per_ecosystem:])
        leftovers = sorted(leftovers, key=lambda e: (-float(e["information_quality_score"]), e["entity_id"]))
        for entity in leftovers:
            if len(selected) >= max_entities:
                break
            eco = entity["primary_ecosystem"]
            if counts.get(eco, 0) < ecosystem_cap:
                selected.append(entity)
                counts[eco] += 1

    selected = sorted(selected, key=lambda e: (e["primary_ecosystem"], e["entity_id"]))
    counts = Counter(e["primary_ecosystem"] for e in selected)
    return {
        "max_entities": max_entities,
        "ecosystem_cap": ecosystem_cap,
        "target_entities_per_ecosystem": target_per_ecosystem,
        "selected_entities": selected,
        "ecosystem_counts": dict(sorted(counts.items())),
    }


def build_lr6_dry2_replay_ecology_diagnostics(window: dict[str, Any], inputs: dict[str, Any]) -> dict[str, Any]:
    total_ecosystems = len(inputs["sde1d_readiness"]["diagnostics"]["ecosystem_counts"])
    covered = len(window["ecosystem_counts"])
    return {
        "expanded_window_size": len(window["selected_entities"]),
        "ecosystem_coverage_in_window": round(covered / total_ecosystems, 6),
    }


def build_lr6_dry2_semantic_diversity_diagnostics(window: dict[str, Any]) -> dict[str, float]:
    entities = window["selected_entities"]
    unique_secondary = {eco for e in entities for eco in e.get("secondary_ecosystems", [])}
    score = round((len(unique_secondary) / TARGET_ECOSYSTEMS + len(window["ecosystem_counts"]) / TARGET_ECOSYSTEMS) / 2, 6)
    return {"semantic_diversity_score": score}


def build_lr6_dry2_contradiction_richness_diagnostics(window: dict[str, Any]) -> dict[str, float]:
    entities = window["selected_entities"]
    score = round(sum(len(e.get("contradiction_surfaces", [])) for e in entities) / (len(entities) * 3), 6)
    return {"contradiction_richness_score": score}


def build_lr6_dry2_propagation_pathway_diagnostics(window: dict[str, Any]) -> dict[str, float]:
    entities = window["selected_entities"]
    link_score = sum(len(e.get("propagation_links", [])) for e in entities) / (len(entities) * 3)
    roles = len({e.get("propagation_role") for e in entities}) / 5
    return {"propagation_pathway_score": round(min(1.0, (link_score + roles) / 2), 6)}


def build_lr6_dry2_saturation_risk_diagnostics(window: dict[str, Any]) -> dict[str, float]:
    max_share = max(window["ecosystem_counts"].values()) / len(window["selected_entities"])
    return {"saturation_risk_score": round(max_share / ECOSYSTEM_SHARE_CAP, 6)}


def build_lr6_dry2_monoculture_risk_diagnostics(window: dict[str, Any]) -> dict[str, float]:
    max_share = max(window["ecosystem_counts"].values()) / len(window["selected_entities"])
    return {"monoculture_risk_score": round(max(0.0, min(1.0, max_share / ECOSYSTEM_SHARE_CAP)), 6)}


def build_lr6_dry2_dry1_comparison(diagnostics: dict[str, Any], inputs: dict[str, Any], window: dict[str, Any]) -> dict[str, float]:
    dry1 = inputs["lr6_dry1"]
    dry1_scores = dry1["diagnostic_scores"]
    dry1_counts = list(dry1["ecosystem_counts_in_window"].values())
    dry2_counts = list(window["ecosystem_counts"].values())
    balance_stability = 1 - (sum(abs(a - b) for a, b in zip(sorted(dry1_counts), sorted(dry2_counts))) / max(1, len(dry2_counts) * TARGET_ENTITIES_PER_ECOSYSTEM))
    return {
        "window_size_increase": diagnostics["expanded_window_size"] - int(dry1_scores["bounded_window_size"]),
        "ecosystem_balance_stability": round(max(0.0, balance_stability), 6),
        "semantic_diversity_stability": round(1 - abs(diagnostics["semantic_diversity_score"] - float(dry1_scores["semantic_diversity_score"])), 6),
        "contradiction_richness_stability": round(1 - abs(diagnostics["contradiction_richness_score"] - float(dry1_scores["contradiction_richness_score"])), 6),
        "propagation_richness_stability": round(1 - abs(diagnostics["propagation_pathway_score"] - float(dry1_scores["propagation_pathway_score"])), 6),
        "saturation_risk_change": round(diagnostics["saturation_risk_score"] - float(dry1_scores["saturation_risk_score"]), 6),
        "monoculture_risk_change": round(diagnostics["monoculture_risk_score"] - float(dry1_scores["monoculture_risk_score"]), 6),
        "diagnostic_readiness_delta": round(diagnostics["diagnostic_readiness_score"] - float(dry1_scores["diagnostic_readiness_score"]), 6),
    }


def build_lr6_dry2_governance_certification(inputs: dict[str, Any]) -> dict[str, Any]:
    return {**inputs["lr6r_readiness"]["governance_certification_metadata"], "dry_run_only": True, "lr6_production_replay_activated": False}


def certify_lr6_dry2_diagnostic_readiness(diagnostics: dict[str, Any], governance: dict[str, Any]) -> dict[str, Any]:
    score = round((
        diagnostics["semantic_diversity_score"] + diagnostics["contradiction_richness_score"] + diagnostics["propagation_pathway_score"] +
        (1 - diagnostics["saturation_risk_score"]) + (1 - diagnostics["monoculture_risk_score"]) + diagnostics["dry_run_governance_score"] +
        diagnostics["dry1_to_dry2_stability_score"]
    ) / 7, 6)
    decision = score >= READINESS_THRESHOLD and governance["dry_run_only"] and not governance["lr6_production_replay_activated"]
    return {
        "diagnostic_readiness_score": score,
        "readiness_threshold": READINESS_THRESHOLD,
        "diagnostic_readiness_decision": "ready_for_lr6_dry3" if decision else "additional_diagnostic_iteration_required",
        "proceed_to_next_dry_run_flag": decision,
    }


def build_lr6_dry2_report_payload(max_entities: int = DEFAULT_MAX_ENTITIES) -> dict[str, Any]:
    inputs = load_lr6_dry2_inputs()
    window = build_lr6_dry2_expanded_window(inputs, max_entities=max_entities)
    governance = build_lr6_dry2_governance_certification(inputs)

    diagnostics = {
        **build_lr6_dry2_replay_ecology_diagnostics(window, inputs),
        **build_lr6_dry2_semantic_diversity_diagnostics(window),
        **build_lr6_dry2_contradiction_richness_diagnostics(window),
        **build_lr6_dry2_propagation_pathway_diagnostics(window),
        **build_lr6_dry2_saturation_risk_diagnostics(window),
        **build_lr6_dry2_monoculture_risk_diagnostics(window),
    }
    diagnostics["dry_run_governance_score"] = 1.0 if all(bool(v) for k, v in governance.items() if k != "lr6_production_replay_activated") else 0.0
    prelim = {**diagnostics, "diagnostic_readiness_score": 0.0}
    comparison = build_lr6_dry2_dry1_comparison(prelim, inputs, window)
    diagnostics["dry1_to_dry2_stability_score"] = round((comparison["ecosystem_balance_stability"] + comparison["semantic_diversity_stability"] + comparison["contradiction_richness_stability"] + comparison["propagation_richness_stability"]) / 4, 6)
    readiness = certify_lr6_dry2_diagnostic_readiness(diagnostics, governance)
    full = {**diagnostics, **readiness}
    comparison = build_lr6_dry2_dry1_comparison(full, inputs, window)

    return {
        "deterministic_version": DETERMINISTIC_VERSION,
        "deterministic_seed": DETERMINISTIC_SEED,
        "objective": "LR6-DRY2 expanded bounded replay ecology diagnostic (dry-run only, no replay execution)",
        "input_artifact_references": inputs["input_artifact_references"],
        "expanded_dry_run_window_parameters": {
            "max_entities": max_entities,
            "target_balanced_window": f"{TARGET_ECOSYSTEMS}x{TARGET_ENTITIES_PER_ECOSYSTEM}",
            "ecosystem_share_cap": ECOSYSTEM_SHARE_CAP,
        },
        "selected_dry_run_window_entities": [e["entity_id"] for e in window["selected_entities"]],
        "ecosystem_counts_in_window": window["ecosystem_counts"],
        "diagnostic_scores": full,
        "dry1_comparison_metrics": comparison,
        "governance_certification_metadata": governance,
        "next_recommended_phase": "LR6-DRY3 conditional on operator governance approval" if readiness["proceed_to_next_dry_run_flag"] else "Repeat LR6-DRY2 diagnostics",
        "lr6_production_replay_activated": False,
    }
