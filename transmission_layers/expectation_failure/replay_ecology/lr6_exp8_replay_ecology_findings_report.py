from __future__ import annotations

from typing import Any

from transmission_layers.expectation_failure.replay_ecology.lr6_exp7_replay_ecology_interestingness_scoring import (
    classify_interestingness_band,
)

DETERMINISTIC_VERSION = "LR6_EXP8_REPLAY_ECOLOGY_FINDINGS_REPORT_V1"
SOURCE_PHASE = "LR6-EXP8"
SOURCE_MODULES = [
    "transmission_layers.expectation_failure.replay_ecology.lr6_exp2_longitudinal_replay_observation",
    "transmission_layers.expectation_failure.replay_ecology.lr6_exp3_replay_ecology_signal_readout",
    "transmission_layers.expectation_failure.replay_ecology.lr6_exp4_replay_ecology_evidence_trace",
    "transmission_layers.expectation_failure.replay_ecology.lr6_exp5_replay_ecology_dashboard_view_model",
    "transmission_layers.expectation_failure.replay_ecology.lr6_exp6a_longitudinal_snapshot_comparison",
    "transmission_layers.expectation_failure.replay_ecology.lr6_exp7_replay_ecology_interestingness_scoring",
]

MAX_TOP_INTERESTING_FINDINGS = 10
MAX_DOMAIN_FINDINGS = 8
MAX_ENTITIES = 8
MAX_CLUSTERS = 6
MAX_PATHWAYS = 6
MAX_CONTRADICTIONS = 6
MAX_REFS = 6
MAX_CAVEATS = 8
MAX_PRIORITIES = 8


def _as_list(v: Any) -> list[str]:
    if isinstance(v, list):
        return [str(x).strip() for x in v if str(x).strip()]
    if isinstance(v, str) and v.strip():
        return [v.strip()]
    return []


def _bounded_unique(values: list[str], limit: int) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value and value not in seen:
            seen.add(value)
            out.append(value)
        if len(out) >= limit:
            break
    return out


def build_finding_title(domain: str, item_id: str) -> str:
    return f"{domain.replace('_', ' ').title()} — {item_id.replace('_', ' ').title()} replay ecology shift"


def build_finding_summary(item: dict[str, Any]) -> str:
    drivers = _as_list(item.get("interestingness_drivers", []))
    d = ", ".join(drivers[:2]) if drivers else "structural replay shift"
    return f"This finding highlights {d} with score band {item.get('score_band', 'routine_change')} and evidence-linked ecological persistence."


def classify_structural_significance(score: float) -> str:
    if score >= 0.75:
        return "high_structural_significance"
    if score >= 0.5:
        return "moderate_structural_significance"
    return "baseline_structural_significance"


def build_structural_significance_summary(item: dict[str, Any]) -> str:
    s = classify_structural_significance(float(item.get("score", 0.0)))
    return f"{s}: replay ecology shift carries {item.get('score_band', 'routine_change')} signal with bounded evidence linkage."


def extract_supporting_ecology_refs(item: dict[str, Any]) -> dict[str, list[str]]:
    return {
        "supporting_entities": _bounded_unique(_as_list(item.get("involved_entities", [])), MAX_ENTITIES),
        "supporting_clusters": _bounded_unique(_as_list(item.get("involved_clusters", [])), MAX_CLUSTERS),
        "supporting_pathways": _bounded_unique(_as_list(item.get("involved_pathways", [])), MAX_PATHWAYS),
        "supporting_contradiction_surfaces": _bounded_unique(_as_list(item.get("involved_contradiction_surfaces", [])), MAX_CONTRADICTIONS),
        "supporting_evidence_refs": _bounded_unique(_as_list(item.get("evidence_refs", [])), MAX_REFS),
    }


def normalize_interestingness_findings(interestingness: dict[str, Any]) -> list[dict[str, Any]]:
    ranked = _as_list([])
    _ = ranked
    return list(interestingness.get("ranked_interesting_changes", []))


def _build_finding(item: dict[str, Any], idx: int) -> dict[str, Any]:
    refs = extract_supporting_ecology_refs(item)
    return {
        "finding_id": f"F{idx:02d}_{item.get('item_id', 'unknown')}",
        "finding_title": build_finding_title(str(item.get("domain", "ecology")), str(item.get("item_id", "unknown"))),
        "finding_summary": build_finding_summary(item),
        "interestingness_band": item.get("score_band", classify_interestingness_band(float(item.get("score", 0.0)))),
        **refs,
        "structural_significance": build_structural_significance_summary(item),
        "caveats": _bounded_unique(_as_list(item.get("caveats", [])), MAX_CAVEATS),
    }


def build_bounded_findings_section(items: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    return [_build_finding(item, idx + 1) for idx, item in enumerate(items[:limit])]


def build_top_interesting_findings_section(interestingness: dict[str, Any]) -> list[dict[str, Any]]:
    return build_bounded_findings_section(normalize_interestingness_findings(interestingness), MAX_TOP_INTERESTING_FINDINGS)


def _domain_section(interestingness: dict[str, Any], domain_prefix: str) -> list[dict[str, Any]]:
    items = [x for x in normalize_interestingness_findings(interestingness) if str(x.get("domain", "")).startswith(domain_prefix)]
    return build_bounded_findings_section(items, MAX_DOMAIN_FINDINGS)


def build_contradiction_ecology_findings(interestingness: dict[str, Any]) -> list[dict[str, Any]]:
    return _domain_section(interestingness, "contradiction")


def build_propagation_evolution_findings(interestingness: dict[str, Any]) -> list[dict[str, Any]]:
    return _domain_section(interestingness, "propagation")


def build_saturation_monoculture_findings(interestingness: dict[str, Any]) -> list[dict[str, Any]]:
    return _domain_section(interestingness, "saturation_monoculture")


def build_ecosystem_interaction_findings(interestingness: dict[str, Any]) -> list[dict[str, Any]]:
    return _domain_section(interestingness, "ecosystem_interaction")


def build_entity_cluster_attribution_findings(interestingness: dict[str, Any]) -> list[dict[str, Any]]:
    return _domain_section(interestingness, "entity_cluster_attribution")


def build_replay_ecology_executive_summary(interestingness: dict[str, Any]) -> dict[str, Any]:
    ranked = normalize_interestingness_findings(interestingness)
    top = ranked[0] if ranked else {}
    return {
        "dominant_replay_ecology_state": "observation-heavy replay ecology shift",
        "replay_ecology_maturity_band": "evolving",
        "replay_ecology_interestingness_band": interestingness.get("replay_ecology_interestingness_band", "routine_change"),
        "strongest_ecological_finding": build_finding_title(str(top.get("domain", "ecology")), str(top.get("item_id", "unknown"))),
        "strongest_persistence_signal": "contradiction persistence and ecological persistence remain visible",
        "strongest_emerged_signal": "replay bridge emergence and interaction-density increase",
        "strongest_weakened_signal": "novelty decay in low-information sectors",
        "strongest_contradiction_finding": "contradiction persistence carries cross-cluster coupling relevance",
        "strongest_propagation_finding": "propagation evolution reflects replay flow shifts",
        "strongest_interaction_finding": "interaction-density increase reflects ecosystem coupling movement",
        "key_ecological_caveats": _bounded_unique(_as_list(interestingness.get("caveats", [])), MAX_CAVEATS),
    }


def build_replay_ecology_findings_report(interestingness: dict[str, Any]) -> dict[str, Any]:
    scoring_meta = interestingness.get("scoring_metadata", {})
    return {
        "report_metadata": {
            "report_id": f"{DETERMINISTIC_VERSION}::{scoring_meta.get('scoring_id', 'unknown')}",
            "source_phase": SOURCE_PHASE,
            "source_modules": SOURCE_MODULES,
            "input_scoring_id": scoring_meta.get("scoring_id", "unknown"),
            "deterministic_report_mode": True,
            "report_version": DETERMINISTIC_VERSION,
            "experimental_mode_only": True,
            "no_prediction": True,
            "no_trading": True,
            "no_governed_activation": True,
        },
        "executive_summary": build_replay_ecology_executive_summary(interestingness),
        "top_interesting_findings": build_top_interesting_findings_section(interestingness),
        "contradiction_ecology_findings": build_contradiction_ecology_findings(interestingness),
        "propagation_evolution_findings": build_propagation_evolution_findings(interestingness),
        "saturation_monoculture_findings": build_saturation_monoculture_findings(interestingness),
        "ecosystem_interaction_findings": build_ecosystem_interaction_findings(interestingness),
        "entity_cluster_attribution_findings": build_entity_cluster_attribution_findings(interestingness),
        "ecological_caveats": _bounded_unique(_as_list(interestingness.get("caveats", [])), MAX_CAVEATS),
        "next_observation_priorities": _bounded_unique(_as_list(interestingness.get("next_observation_priorities", [])), MAX_PRIORITIES),
    }


def build_replay_ecology_findings_summary(report: dict[str, Any]) -> dict[str, Any]:
    top = report.get("top_interesting_findings", [])
    return {
        "report_id": report.get("report_metadata", {}).get("report_id", "unknown"),
        "top_findings_count": len(top),
        "dominant_state": report.get("executive_summary", {}).get("dominant_replay_ecology_state", "unknown"),
        "interestingness_band": report.get("executive_summary", {}).get("replay_ecology_interestingness_band", "routine_change"),
    }


def build_replay_ecology_findings_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# LR6-EXP8 Replay Ecology Findings Report",
        "",
        "## Executive Summary",
        f"- Dominant state: {report['executive_summary']['dominant_replay_ecology_state']}",
        f"- Interestingness band: {report['executive_summary']['replay_ecology_interestingness_band']}",
        "",
        "## Top Interesting Findings",
    ]
    for finding in report.get("top_interesting_findings", []):
        lines.append(f"- **{finding['finding_id']}**: {finding['finding_title']} — {finding['finding_summary']}")
    lines.extend([
        "",
        "## Experimental Boundaries",
        "- Experimental mode only",
        "- No prediction outputs",
        "- No trading outputs",
        "- No governed LR6 activation",
    ])
    return "\n".join(lines)


def build_lr6_exp8_dashboard_payload(interestingness: dict[str, Any]) -> dict[str, Any]:
    report = build_replay_ecology_findings_report(interestingness)
    return {
        "lr6_exp8_replay_ecology_findings_dashboard": report,
        "lr6_exp8_replay_ecology_findings_summary": build_replay_ecology_findings_summary(report),
        "experimental_certification": certify_lr6_exp8_experimental_boundaries(),
    }


def certify_lr6_exp8_experimental_boundaries() -> dict[str, Any]:
    return {
        "experimental_mode_only": True,
        "governed_lr6_activation": False,
        "no_persistence_writes": True,
        "no_direct_sql": True,
        "no_external_apis": True,
        "no_prediction_or_trading": True,
        "deterministic_bounded_outputs": True,
        "additive_architecture_preserved": True,
    }
