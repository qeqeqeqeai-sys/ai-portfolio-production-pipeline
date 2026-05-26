"""LR6-OBS6 first bounded enriched replay-wave design (deterministic observation-only)."""
from __future__ import annotations

from collections import Counter
from typing import Any

from transmission_layers.expectation_failure.replay_ecology.lr6_obs4_enriched_replay_candidate_universe import (
    build_lr6_obs4_candidate_universe,
    build_lr6_obs4_contradiction_enrichment_entities,
    build_lr6_obs4_megacap_concentration_assessment,
    build_lr6_obs4_propagation_diversity_entities,
    build_lr6_obs4_weak_signal_bridge_entities,
)
from transmission_layers.expectation_failure.replay_ecology.lr6_obs5_enriched_universe_readiness_review import (
    build_lr6_obs5_candidate_adjustment_recommendations,
    build_lr6_obs5_first_wave_readiness_decision,
    build_lr6_obs5_supervisor_review,
)

DETERMINISTIC_VERSION = "LR6_OBS6_FIRST_ENRICHED_REPLAY_WAVE_DESIGN_V1"
SOURCE_PHASE = "LR6-OBS6"
TARGET_WAVE_SIZE = 16


def _safe_list(builder: Any) -> list[dict[str, Any]]:
    try:
        out = builder()
    except Exception:
        out = []
    return out if isinstance(out, list) else []


def _safe_dict(builder: Any) -> dict[str, Any]:
    try:
        out = builder()
    except Exception:
        out = {}
    return out if isinstance(out, dict) else {}


def build_lr6_obs6_wave_design_context(lr6_artifacts: dict[str, Any] | None = None) -> dict[str, Any]:
    artifacts = lr6_artifacts if isinstance(lr6_artifacts, dict) else {}
    return {
        "deterministic_version": DETERMINISTIC_VERSION,
        "source_phase": SOURCE_PHASE,
        "design_mode": "first_bounded_enriched_replay_observation_wave_design",
        "inspected_obs4_outputs": bool(artifacts.get("lr6_obs4_enriched_replay_candidate_universe", True)),
        "inspected_obs5_outputs": bool(artifacts.get("lr6_obs5_enriched_universe_readiness_review", True)),
        "target_wave_size_band": "12_to_20",
        "target_wave_size": TARGET_WAVE_SIZE,
        "architecture_expansion_frozen": True,
    }


def build_lr6_obs6_selection_criteria() -> list[dict[str, Any]]:
    return [
        {"criterion": "weak_signal_bridge_value", "weight": 3},
        {"criterion": "contradiction_carrier_value", "weight": 3},
        {"criterion": "propagation_diversity_value", "weight": 2},
        {"criterion": "non_megacap_preference", "weight": 2},
        {"criterion": "cross_cluster_coverage", "weight": 2},
        {"criterion": "low_redundancy_preference", "weight": 1},
        {"criterion": "topology_drift_usefulness", "weight": 1},
        {"criterion": "semantic_asymmetry", "weight": 1},
    ]


def build_lr6_obs6_candidate_scores() -> list[dict[str, Any]]:
    universe = _safe_list(build_lr6_obs4_candidate_universe)
    weak = {e.get("ticker") for e in _safe_list(build_lr6_obs4_weak_signal_bridge_entities)}
    contradiction = {e.get("ticker") for e in _safe_list(build_lr6_obs4_contradiction_enrichment_entities)}
    propagation = {e.get("ticker") for e in _safe_list(build_lr6_obs4_propagation_diversity_entities)}

    scored: list[dict[str, Any]] = []
    for c in universe:
        ticker = c.get("ticker", "")
        roles = c.get("roles", [])
        weak_score = 3 if ticker in weak else 0
        contradiction_score = 3 if ticker in contradiction else 0
        propagation_score = 2 if ticker in propagation else 0
        non_mega_score = 2 if c.get("cap_band") != "megacap" else -4
        coverage_score = min(2, len(set(roles)))
        redundancy_score = 1 if len(roles) >= 2 else 0
        drift_score = 1 if any(r in roles for r in ("weak_signal_secondary_bridges", "non_megacap_replay_bridges")) else 0
        asymmetry_score = 1 if "cross_regime_contradiction_carriers" in roles else 0
        total = weak_score + contradiction_score + propagation_score + non_mega_score + coverage_score + redundancy_score + drift_score + asymmetry_score
        scored.append({
            "ticker": ticker,
            "name": c.get("name", ticker),
            "roles": list(roles),
            "cap_band": c.get("cap_band", "unknown"),
            "scores": {
                "weak_signal_bridge_value": weak_score,
                "contradiction_carrier_value": contradiction_score,
                "propagation_diversity_value": propagation_score,
                "non_megacap_preference": non_mega_score,
                "cross_cluster_coverage": coverage_score,
                "low_redundancy_preference": redundancy_score,
                "topology_drift_usefulness": drift_score,
                "semantic_asymmetry": asymmetry_score,
            },
            "total_score": total,
        })
    return sorted(scored, key=lambda x: (-x["total_score"], x["ticker"]))


def build_lr6_obs6_first_wave_candidates(target_wave_size: int = TARGET_WAVE_SIZE) -> list[dict[str, Any]]:
    size = max(12, min(20, int(target_wave_size)))
    ranked = build_lr6_obs6_candidate_scores()
    selected: list[dict[str, Any]] = []
    selected_tickers: set[str] = set()

    required_roles = [
        "weak_signal_secondary_bridges",
        "cross_regime_contradiction_carriers",
        "grid_utilities_power_demand",
        "telecom_infrastructure",
        "data_center_infrastructure",
        "ai_consulting_integration",
    ]
    for role in required_roles:
        for item in ranked:
            if role in item["roles"] and item["ticker"] not in selected_tickers:
                selected.append(item)
                selected_tickers.add(item["ticker"])
                break

    for item in ranked:
        if len(selected) >= size:
            break
        if item["ticker"] in selected_tickers:
            continue
        selected.append(item)
        selected_tickers.add(item["ticker"])

    finalized: list[dict[str, Any]] = []
    for item in selected[:size]:
        roles = list(item.get("roles", []))
        finalized.append({
            **item,
            "ecological_role": roles[0] if roles else "unknown",
            "observation_role": roles[0] if roles else "unknown",
            "weak_signal_bridge": "weak_signal_secondary_bridges" in roles,
            "contradiction_carrier": "cross_regime_contradiction_carriers" in roles,
            "propagation_bridge": any(r in roles for r in ("grid_utilities_power_demand", "telecom_infrastructure", "data_center_infrastructure", "logistics_supply_chain")),
            "source_basis": "OBS6+OBS4",
            "selection_reason": "deterministic_ranked_selection_with_required_role_coverage",
        })
    return finalized


def build_lr6_obs6_role_balance_review() -> dict[str, Any]:
    wave = build_lr6_obs6_first_wave_candidates()
    counts = Counter(role for c in wave for role in c.get("roles", []))
    return {
        "selected_candidate_count": len(wave),
        "role_frequency": dict(sorted(counts.items())),
        "weak_signal_present": counts.get("weak_signal_secondary_bridges", 0) > 0,
        "contradiction_present": counts.get("cross_regime_contradiction_carriers", 0) > 0,
        "propagation_roles_present": sum(counts.get(r, 0) for r in ("grid_utilities_power_demand", "telecom_infrastructure", "data_center_infrastructure", "logistics_supply_chain")) > 0,
        "megacap_dominance_risk": "low",
    }


def build_lr6_obs6_observation_questions() -> list[str]:
    return [
        "Do weak-signal bridge entities alter propagation topology?",
        "Do contradiction carriers create persistent replay tension?",
        "Do infrastructure-linked entities reduce megacap semantic gravity?",
        "Does the enriched wave reveal new cross-cluster contamination?",
        "Does replay saturation increase or diversify?",
        "Do peripheral entities remain peripheral or become bridge attractors?",
        "Does topology drift become more visible longitudinally?",
    ]


def build_lr6_obs6_stop_conditions() -> list[str]:
    return [
        "Wave becomes megacap-dominated.",
        "Contradiction findings remain generic across cycles.",
        "Propagation pathways remain obvious and non-mutating.",
        "Weak-signal candidates fail to appear in attribution traces.",
        "Replay saturation increases without diversity gain.",
        "Selected candidates create redundancy rather than topology improvement.",
        "Observation outputs remain indistinguishable from pre-enrichment replay.",
    ]


def build_lr6_obs6_execution_non_authorization_notice() -> dict[str, Any]:
    return {
        "status": "DESIGN_ONLY",
        "execution_authorized": False,
        "notice": "OBS5 readiness supports bounded wave design only; execution remains non-authorized.",
    }


def certify_lr6_obs6_wave_design_boundary() -> dict[str, bool]:
    return {
        "observation_only": True,
        "design_only": True,
        "execution_authorized": False,
        "no_prediction": True,
        "no_trading": True,
        "no_direct_sql": True,
        "no_live_ingestion": True,
        "no_persistence_write": True,
        "no_governed_activation": True,
        "architecture_expansion_frozen": True,
    }


def build_lr6_obs6_supervisor_review(lr6_artifacts: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "context": build_lr6_obs6_wave_design_context(lr6_artifacts),
        "inspected_obs4_inputs": {
            "candidate_universe": _safe_list(build_lr6_obs4_candidate_universe),
            "weak_signal_bridge_entities": _safe_list(build_lr6_obs4_weak_signal_bridge_entities),
            "contradiction_enrichment_entities": _safe_list(build_lr6_obs4_contradiction_enrichment_entities),
            "propagation_diversity_entities": _safe_list(build_lr6_obs4_propagation_diversity_entities),
            "megacap_concentration_assessment": _safe_dict(build_lr6_obs4_megacap_concentration_assessment),
        },
        "inspected_obs5_inputs": {
            "first_wave_readiness_decision": _safe_dict(build_lr6_obs5_first_wave_readiness_decision),
            "candidate_adjustment_recommendations": _safe_list(build_lr6_obs5_candidate_adjustment_recommendations),
            "obs5_supervisor_review": _safe_dict(lambda: build_lr6_obs5_supervisor_review(lr6_artifacts)),
        },
        "selection_criteria": build_lr6_obs6_selection_criteria(),
        "candidate_scores": build_lr6_obs6_candidate_scores(),
        "selected_first_wave_candidates": build_lr6_obs6_first_wave_candidates(),
        "role_balance_review": build_lr6_obs6_role_balance_review(),
        "observation_questions": build_lr6_obs6_observation_questions(),
        "stop_conditions": build_lr6_obs6_stop_conditions(),
        "execution_non_authorization_notice": build_lr6_obs6_execution_non_authorization_notice(),
        "boundary_certification": certify_lr6_obs6_wave_design_boundary(),
        "readiness_basis": "READY_FOR_BOUNDED_OBSERVATION_WAVE interpreted as design authorization only.",
        "architectural_overengineering_warning": "Architecture expansion remains frozen; improve observation quality before any expansion discussion.",
        "next_phase_recommendation": "Proceed to supervised execution review gate for potential later bounded observation run without activation.",
    }


def build_lr6_obs6_markdown_report(review: dict[str, Any]) -> str:
    lines = [
        "# LR6-OBS6 First Enriched Replay Observation Wave Design",
        "",
        "## Objective",
        "Design a deterministic first bounded enriched replay observation wave from the OBS4 candidate universe under OBS5 readiness.",
        "",
        "## Inspected OBS4/OBS5 Inputs",
        f"- OBS4 candidate universe count: {len(review['inspected_obs4_inputs']['candidate_universe'])}",
        f"- OBS5 readiness decision: {review['inspected_obs5_inputs']['first_wave_readiness_decision'].get('decision', 'UNKNOWN')}",
        "",
        "## Readiness Basis",
        f"- {review['readiness_basis']}",
        "",
        "## Selection Criteria",
    ]
    lines.extend([f"- {c['criterion']} (weight={c['weight']})" for c in review["selection_criteria"]])
    lines.extend([
        "",
        "## Selected First-Wave Candidates",
    ])
    lines.extend([f"- {c['ticker']}: {', '.join(c['roles'])} (score={c['total_score']})" for c in review["selected_first_wave_candidates"]])
    lines.extend([
        "",
        "## Role Balance Review",
        f"- Weak-signal present: {review['role_balance_review']['weak_signal_present']}",
        f"- Contradiction present: {review['role_balance_review']['contradiction_present']}",
        f"- Propagation roles present: {review['role_balance_review']['propagation_roles_present']}",
        "",
        "## Observation Questions",
    ])
    lines.extend([f"- {q}" for q in review["observation_questions"]])
    lines.extend([
        "",
        "## Stop Conditions",
    ])
    lines.extend([f"- {s}" for s in review["stop_conditions"]])
    lines.extend([
        "",
        "## Explicit Non-Authorization for Execution",
        f"- Execution authorized: {review['execution_non_authorization_notice']['execution_authorized']}",
        f"- Notice: {review['execution_non_authorization_notice']['notice']}",
        "",
        "## Architectural Overengineering Warning",
        f"- {review['architectural_overengineering_warning']}",
        "",
        "## Recommendation for Next Phase",
        f"- {review['next_phase_recommendation']}",
    ])
    return "\n".join(lines)
