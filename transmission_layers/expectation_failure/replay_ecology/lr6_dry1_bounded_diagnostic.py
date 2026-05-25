from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

import json

DETERMINISTIC_VERSION = "LR6_DRY1_BOUNDED_DIAGNOSTIC_V1"
DETERMINISTIC_SEED = "LR6_DRY1_BOUNDED_DIAGNOSTIC_SEED_V1"
READINESS_THRESHOLD = 0.74
DEFAULT_MAX_ENTITIES = 60



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
        value_obj: Any
        if value.lower() in {"true", "false"}:
            value_obj = value.lower() == "true"
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



def load_lr6_dry1_inputs(
    pruned_universe_path: str = "configs/sde1c_pruned_entity_universe.yaml",
    sde1d_readiness_path: str = "configs/sde1d_semantic_ecosystem_readiness_certification.yaml",
    lr6r_readiness_path: str = "configs/lr6r_replay_ecology_reactivation_readiness.yaml",
) -> dict[str, Any]:
    return {
        "pruned_universe": _load_yaml(pruned_universe_path),
        "sde1d_readiness": _load_yaml(sde1d_readiness_path),
        "lr6r_readiness": _load_yaml(lr6r_readiness_path),
        "input_artifact_references": {
            "pruned_universe": pruned_universe_path,
            "sde1d_readiness": sde1d_readiness_path,
            "lr6r_readiness": lr6r_readiness_path,
        },
    }



def build_lr6_dry1_bounded_window(inputs: dict[str, Any], max_entities: int = DEFAULT_MAX_ENTITIES) -> dict[str, Any]:
    entities = inputs["pruned_universe"]["selected_entities"]
    ecosystem_cap = max(1, int(max_entities * 0.22))

    by_ecosystem: dict[str, list[dict[str, Any]]] = {}
    for e in entities:
        by_ecosystem.setdefault(e["primary_ecosystem"], []).append(e)

    ranked_by_ecosystem: dict[str, list[dict[str, Any]]] = {}
    for ecosystem in sorted(by_ecosystem):
        ranked_by_ecosystem[ecosystem] = sorted(
            by_ecosystem[ecosystem], key=lambda e: (-float(e["information_quality_score"]), e["entity_id"])
        )[: min(ecosystem_cap, len(by_ecosystem[ecosystem]))]

    selected: list[dict[str, Any]] = []
    step = 0
    ecosystems = sorted(ranked_by_ecosystem)
    while len(selected) < max_entities:
        progressed = False
        for ecosystem in ecosystems:
            bucket = ranked_by_ecosystem[ecosystem]
            if step < len(bucket) and len(selected) < max_entities:
                selected.append(bucket[step])
                progressed = True
        if not progressed:
            break
        step += 1

    selected = sorted(selected, key=lambda e: (e["primary_ecosystem"], e["entity_id"]))
    counts = Counter(e["primary_ecosystem"] for e in selected)
    return {
        "max_entities": max_entities,
        "ecosystem_cap": ecosystem_cap,
        "selected_entities": selected,
        "ecosystem_counts": dict(sorted(counts.items())),
    }



def build_lr6_dry1_replay_ecology_diagnostics(window: dict[str, Any], inputs: dict[str, Any]) -> dict[str, Any]:
    size = len(window["selected_entities"])
    total_ecosystems = len(inputs["sde1d_readiness"]["diagnostics"]["ecosystem_counts"])
    covered = len(window["ecosystem_counts"])
    return {
        "bounded_window_size": size,
        "ecosystem_coverage_in_window": round(covered / total_ecosystems, 6),
    }



def build_lr6_dry1_semantic_diversity_diagnostics(window: dict[str, Any]) -> dict[str, float]:
    entities = window["selected_entities"]
    unique_secondary = {eco for e in entities for eco in e.get("secondary_ecosystems", [])}
    score = round((len(unique_secondary) / 12 + len(window["ecosystem_counts"]) / 12) / 2, 6)
    return {"semantic_diversity_score": score}



def build_lr6_dry1_contradiction_richness_diagnostics(window: dict[str, Any]) -> dict[str, float]:
    entities = window["selected_entities"]
    surfaces = [len(e.get("contradiction_surfaces", [])) for e in entities]
    score = round(sum(surfaces) / (len(entities) * 3), 6)
    return {"contradiction_richness_score": score}



def build_lr6_dry1_propagation_pathway_diagnostics(window: dict[str, Any]) -> dict[str, float]:
    entities = window["selected_entities"]
    links = [len(e.get("propagation_links", [])) for e in entities]
    roles = {e.get("propagation_role") for e in entities}
    score = round(min(1.0, (sum(links) / (len(entities) * 3) + len(roles) / 5) / 2), 6)
    return {"propagation_pathway_score": score}



def build_lr6_dry1_saturation_risk_diagnostics(window: dict[str, Any]) -> dict[str, float]:
    counts = list(window["ecosystem_counts"].values())
    max_share = max(counts) / len(window["selected_entities"])
    score = round(max_share / 0.22, 6)
    return {"saturation_risk_score": score}



def build_lr6_dry1_monoculture_risk_diagnostics(window: dict[str, Any]) -> dict[str, float]:
    counts = list(window["ecosystem_counts"].values())
    max_share = max(counts) / len(window["selected_entities"])
    score = round(max(0.0, min(1.0, max_share / 0.22)), 6)
    return {"monoculture_risk_score": score}



def build_lr6_dry1_governance_certification(inputs: dict[str, Any]) -> dict[str, Any]:
    metadata = inputs["lr6r_readiness"]["governance_certification_metadata"]
    return {
        **metadata,
        "dry_run_only": True,
        "lr6_production_replay_activated": False,
    }



def certify_lr6_dry1_diagnostic_readiness(diagnostics: dict[str, Any], governance: dict[str, Any]) -> dict[str, Any]:
    readiness_score = round(
        (
            diagnostics["semantic_diversity_score"]
            + diagnostics["contradiction_richness_score"]
            + diagnostics["propagation_pathway_score"]
            + (1 - diagnostics["saturation_risk_score"])
            + (1 - diagnostics["monoculture_risk_score"])
            + diagnostics["dry_run_governance_score"]
        )
        / 6,
        6,
    )
    decision = readiness_score >= READINESS_THRESHOLD and governance["dry_run_only"] and not governance["lr6_production_replay_activated"]
    return {
        "diagnostic_readiness_score": readiness_score,
        "readiness_threshold": READINESS_THRESHOLD,
        "diagnostic_readiness_decision": "ready_for_lr6_dry2" if decision else "additional_diagnostic_iteration_required",
        "proceed_to_next_dry_run_flag": decision,
    }



def build_lr6_dry1_report_payload(max_entities: int = DEFAULT_MAX_ENTITIES) -> dict[str, Any]:
    inputs = load_lr6_dry1_inputs()
    window = build_lr6_dry1_bounded_window(inputs=inputs, max_entities=max_entities)
    replay = build_lr6_dry1_replay_ecology_diagnostics(window, inputs)
    semantic = build_lr6_dry1_semantic_diversity_diagnostics(window)
    contradiction = build_lr6_dry1_contradiction_richness_diagnostics(window)
    propagation = build_lr6_dry1_propagation_pathway_diagnostics(window)
    saturation = build_lr6_dry1_saturation_risk_diagnostics(window)
    monoculture = build_lr6_dry1_monoculture_risk_diagnostics(window)
    governance = build_lr6_dry1_governance_certification(inputs)
    dry_run_governance_score = 1.0 if all(bool(v) for k, v in governance.items() if k != "lr6_production_replay_activated") and not governance["lr6_production_replay_activated"] else 0.0

    diagnostics = {
        **replay,
        **semantic,
        **contradiction,
        **propagation,
        **saturation,
        **monoculture,
        "dry_run_governance_score": dry_run_governance_score,
    }
    readiness = certify_lr6_dry1_diagnostic_readiness(diagnostics, governance)
    return {
        "deterministic_version": DETERMINISTIC_VERSION,
        "deterministic_seed": DETERMINISTIC_SEED,
        "objective": "LR6-DRY1 bounded replay ecology diagnostic (dry-run only, no replay execution)",
        "input_artifact_references": inputs["input_artifact_references"],
        "dry_run_window_parameters": {"max_entities": max_entities, "ecosystem_share_cap": 0.22},
        "selected_dry_run_window_entities": [e["entity_id"] for e in window["selected_entities"]],
        "ecosystem_counts_in_window": window["ecosystem_counts"],
        "diagnostic_scores": {**diagnostics, **readiness},
        "governance_certification_metadata": governance,
        "next_recommended_phase": "LR6-DRY2 conditional on operator governance approval" if readiness["proceed_to_next_dry_run_flag"] else "Repeat LR6-DRY1 diagnostics",
        "lr6_production_replay_activated": False,
    }
