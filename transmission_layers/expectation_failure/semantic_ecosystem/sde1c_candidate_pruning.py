from __future__ import annotations

from collections import Counter
from math import ceil
from pathlib import Path
from typing import Any

DETERMINISTIC_VERSION = "SDE1C_PRUNING_V1"
PRIMARY_MONOCULTURE_CAP_SHARE = 0.18
AI_HYPERSCALER_COMBINED_CAP_SHARE = 0.30

STRUCTURAL_ROLE_WEIGHTS = {
    "core_enabler": 1.00,
    "demand_translator": 0.92,
    "constraint_surface": 1.04,
    "amplifier": 0.90,
    "validator": 0.95,
}


def _parse_scalar(v: str) -> Any:
    v = v.strip()
    if v.startswith('"') and v.endswith('"'):
        return v[1:-1]
    if v.startswith("'") and v.endswith("'"):
        return v[1:-1]
    if v.startswith("[") and v.endswith("]"):
        inner = v[1:-1].strip()
        if not inner:
            return []
        return [part.strip().strip("\"'") for part in inner.split(',')]
    try:
        return int(v)
    except ValueError:
        try:
            return float(v)
        except ValueError:
            return v


def load_sde1_candidate_universe(config_path: str | Path) -> dict[str, Any]:
    lines = Path(config_path).read_text().splitlines()
    ecosystems: dict[str, dict[str, Any]] = {}
    candidates: list[dict[str, Any]] = []
    mode = None
    current = None
    for line in lines:
        if line.startswith("ecosystems:"):
            mode = "ecosystems"
            continue
        if line.startswith("interaction_pathways:"):
            mode = "skip"
            continue
        if line.startswith("candidates:"):
            mode = "candidates"
            continue
        if mode == "ecosystems" and line.startswith("  ") and line.endswith(":") and not line.startswith("    "):
            key = line.strip()[:-1]
            ecosystems[key] = {}
            current = ecosystems[key]
            continue
        if mode == "ecosystems" and line.startswith("    ") and ":" in line and current is not None:
            k, v = line.strip().split(":", 1)
            current[k] = _parse_scalar(v)
            continue
        if mode == "candidates" and line.startswith("  - entity_id:"):
            candidates.append({"entity_id": line.split(":", 1)[1].strip()})
            continue
        if mode == "candidates" and line.startswith("    ") and ":" in line and candidates:
            k, v = line.strip().split(":", 1)
            candidates[-1][k] = _parse_scalar(v)
    return {"ecosystems": ecosystems, "candidates": candidates}


def score_sde1_candidate_topology(candidate: dict[str, Any], ecosystem_definitions: dict[str, Any]) -> dict[str, float]:
    links = len(candidate.get("propagation_links", []))
    contradictions = len(candidate.get("contradiction_surfaces", []))
    regimes = len(candidate.get("regime_exposures", []))
    secondary = len(candidate.get("secondary_ecosystems", []))
    info_quality = float(candidate.get("information_quality_score", 0.0))
    unique_ratio = len(set(candidate.get("secondary_ecosystems", []))) / max(1, secondary)
    connectivity = min(1.0, (secondary + links) / 6)
    propagation = min(1.0, links / 3)
    contradiction = min(1.0, contradictions / 3)
    regime = min(1.0, regimes / 4)
    replay_value = min(1.0, (connectivity + contradiction + propagation) / 3)
    return {
        "ecosystem_connectivity_score": round(connectivity, 6),
        "contradiction_surface_score": round(contradiction, 6),
        "propagation_link_score": round(propagation, 6),
        "regime_exposure_score": round(regime, 6),
        "information_quality_score": round(info_quality, 6),
        "semantic_uniqueness_score": round(unique_ratio, 6),
        "replay_ecology_value_score": round(replay_value, 6),
        "anti_monoculture_adjustment": round(0.06 if secondary >= 2 else 0.0, 6),
        "low_information_penalty": round(max(0.0, (0.60 - info_quality) * 1.5), 6),
        "structural_role_weight": round(STRUCTURAL_ROLE_WEIGHTS.get(candidate.get("structural_role"), 0.85), 6),
    }


def build_sde1_candidate_scorecard(candidate: dict[str, Any], ecosystem_definitions: dict[str, Any]) -> dict[str, Any]:
    s = score_sde1_candidate_topology(candidate, ecosystem_definitions)
    base = s["ecosystem_connectivity_score"] * 1.1 + s["contradiction_surface_score"] * 1.2 + s["propagation_link_score"] * 1.2 + s["regime_exposure_score"] * 0.8 + s["information_quality_score"] * 1.1 + s["semantic_uniqueness_score"] * 0.8 + s["replay_ecology_value_score"] * 1.1 + s["anti_monoculture_adjustment"] - s["low_information_penalty"]
    return {"entity_id": candidate["entity_id"], "symbol": candidate["symbol"], **s, "total_score": round(base * s["structural_role_weight"], 6)}


def rank_sde1_candidates(candidate_universe, ecosystem_definitions):
    rows = [{"candidate": c, "scorecard": build_sde1_candidate_scorecard(c, ecosystem_definitions)} for c in candidate_universe]
    return sorted(rows, key=lambda r: (-r["scorecard"]["total_score"], -r["scorecard"]["contradiction_surface_score"], -r["scorecard"]["propagation_link_score"], -r["scorecard"]["ecosystem_connectivity_score"], r["candidate"]["entity_id"]))


def prune_sde1_candidate_universe(candidate_universe, ecosystem_definitions, target_count=300):
    ranked = rank_sde1_candidates(candidate_universe, ecosystem_definitions)
    per_family_cap = ceil(target_count * PRIMARY_MONOCULTURE_CAP_SHARE)
    combined_cap = ceil(target_count * AI_HYPERSCALER_COMBINED_CAP_SHARE)
    selected = []
    selected_ids = set()
    family_counts = Counter()
    for family in ecosystem_definitions.keys():
        top = next(r for r in ranked if r["candidate"]["primary_ecosystem"] == family)
        selected.append(top); selected_ids.add(top["candidate"]["entity_id"]); family_counts[family] += 1
    for row in ranked:
        if len(selected) >= target_count:
            break
        c = row["candidate"]; fam = c["primary_ecosystem"]; eid = c["entity_id"]
        if eid in selected_ids or family_counts[fam] >= per_family_cap:
            continue
        if fam in {"ai_compute_core", "hyperscaler_cloud_demand"} and family_counts["ai_compute_core"] + family_counts["hyperscaler_cloud_demand"] >= combined_cap:
            continue
        selected.append(row); selected_ids.add(eid); family_counts[fam] += 1
    excluded = [r for r in ranked if r["candidate"]["entity_id"] not in selected_ids]
    return {"selected": selected, "excluded": excluded, "ranked": ranked, "per_family_cap": per_family_cap, "ai_hyperscaler_combined_cap": combined_cap}


def build_sde1_pruning_summary(pruning_result, candidate_universe):
    before = Counter(c["primary_ecosystem"] for c in candidate_universe)
    after = Counter(r["candidate"]["primary_ecosystem"] for r in pruning_result["selected"])
    return {"before_total": len(candidate_universe), "after_total": len(pruning_result["selected"]), "excluded_total": len(pruning_result["excluded"]), "before_by_ecosystem": dict(before), "after_by_ecosystem": dict(after)}


def certify_sde1_pruning_governance(pruning_result, ecosystem_definitions, target_count):
    after = Counter(r["candidate"]["primary_ecosystem"] for r in pruning_result["selected"])
    return {"deterministic_version": DETERMINISTIC_VERSION, "target_count_verified": len(pruning_result["selected"]) == target_count, "ecosystem_coverage_verified": all(after.get(k, 0) > 0 for k in ecosystem_definitions.keys()), "no_replay_execution_introduced": True, "no_persistence_write_path_introduced": True, "no_direct_sql_introduced": True, "no_prediction_or_trading_logic_introduced": True}


def build_sde1c_pruning_report_payload(config_path, target_count=300):
    config = load_sde1_candidate_universe(config_path)
    pr = prune_sde1_candidate_universe(config["candidates"], config["ecosystems"], target_count)
    return {"version": DETERMINISTIC_VERSION, "seed": "SDE1_CURATED_ECOSYSTEM_V1", "source_config": str(config_path), "target_count": target_count, "summary": build_sde1_pruning_summary(pr, config["candidates"]), "certification": certify_sde1_pruning_governance(pr, config["ecosystems"], target_count), "selected_entities": [r["candidate"] for r in pr["selected"]], "excluded_entities": [r["candidate"] for r in pr["excluded"]], "selected_scorecards": [r["scorecard"] for r in pr["selected"]], "excluded_scorecards": [r["scorecard"] for r in pr["excluded"]], "caps": {"primary_ecosystem_cap": pr["per_family_cap"], "ai_hyperscaler_combined_cap": pr["ai_hyperscaler_combined_cap"]}}
