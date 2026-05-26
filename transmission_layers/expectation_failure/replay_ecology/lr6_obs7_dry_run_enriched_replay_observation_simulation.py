"""LR6-OBS7 governed dry-run enriched replay observation simulation (deterministic, non-executing)."""
from __future__ import annotations

from collections import Counter
from typing import Any

from transmission_layers.expectation_failure.replay_ecology.lr6_obs6_first_enriched_replay_wave_design import (
    build_lr6_obs6_execution_non_authorization_notice,
    build_lr6_obs6_first_wave_candidates,
    build_lr6_obs6_observation_questions,
    build_lr6_obs6_role_balance_review,
    build_lr6_obs6_selection_criteria,
    build_lr6_obs6_stop_conditions,
    build_lr6_obs6_supervisor_review,
)

DETERMINISTIC_VERSION = "LR6_OBS7_DRY_RUN_ENRICHED_REPLAY_OBSERVATION_SIMULATION_V1"
SOURCE_PHASE = "LR6-OBS7"

ALLOWED_DRY_RUN_DECISIONS = {
    "DRY_RUN_READY_FOR_GOVERNED_OBSERVATION_PROPOSAL",
    "DRY_RUN_CONDITIONALLY_READY_NEEDS_REBALANCE",
    "DRY_RUN_NOT_READY_REQUIRES_REDESIGN",
}


def _safe_list(builder: Any) -> list[Any]:
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


def build_lr6_obs7_dry_run_context(lr6_artifacts: dict[str, Any] | None = None) -> dict[str, Any]:
    artifacts = lr6_artifacts if isinstance(lr6_artifacts, dict) else {}
    return {
        "deterministic_version": DETERMINISTIC_VERSION,
        "source_phase": SOURCE_PHASE,
        "simulation_mode": "governed_dry_run_enriched_replay_observation_simulation",
        "inspected_obs6_outputs": bool(artifacts.get("lr6_obs6_first_enriched_replay_wave_design", True)),
        "observation_only": True,
        "dry_run_only": True,
        "architecture_expansion_frozen": True,
    }


def build_lr6_obs7_simulated_wave_manifest() -> dict[str, Any]:
    candidates = _safe_list(build_lr6_obs6_first_wave_candidates)
    role_counts = Counter(role for c in candidates for role in c.get("roles", []))
    return {
        "selected_candidates": candidates,
        "selected_count": len(candidates),
        "roles_represented": sorted(role_counts.keys()),
        "role_frequency": dict(sorted(role_counts.items())),
        "source_basis": "OBS6 first-wave design",
        "dry_run": True,
        "execution_authorized": False,
        "no_persistence": True,
    }


def build_lr6_obs7_simulated_observation_routes() -> list[dict[str, Any]]:
    candidates = _safe_list(build_lr6_obs6_first_wave_candidates)
    routes: list[dict[str, Any]] = []
    for item in candidates:
        ticker = item.get("ticker", "UNKNOWN")
        roles = item.get("roles", [])
        routes.append(
            {
                "ticker": ticker,
                "roles": roles,
                "contradiction_migration_route": f"{ticker}: peripheral contradiction -> cross-cluster contention tracking",
                "propagation_mutation_route": f"{ticker}: role-to-role spillover tracking across infra/logistics/compute",
                "weak_signal_attribution_route": f"{ticker}: weak-signal mention frequency and bridge emergence review",
                "semantic_gravity_route": f"{ticker}: megacap gravity deflection and local-attractor pressure",
                "saturation_route": f"{ticker}: replay novelty vs repeated narrative density",
                "topology_drift_route": f"{ticker}: edge rewiring likelihood under enriched replay cycle",
            }
        )
    return routes


def build_lr6_obs7_contradiction_stress_review() -> dict[str, Any]:
    questions = _safe_list(build_lr6_obs6_observation_questions)
    return {
        "persistent_replay_tension": "likely_detectable",
        "cross_cluster_contradiction": "likely_detectable",
        "infrastructure_vs_ai_demand_tensions": "likely_detectable",
        "cybersecurity_regulatory_contradictions": "monitor_closely",
        "peripheral_to_core_contradiction_movement": "likely_detectable",
        "basis": questions,
    }


def build_lr6_obs7_propagation_stress_review() -> dict[str, Any]:
    role_balance = _safe_dict(build_lr6_obs6_role_balance_review)
    return {
        "indirect_bridge_propagation": "moderate_to_high",
        "non_megacap_pathway_expansion": "moderate",
        "cross_role_contamination": "likely",
        "telecom_grid_logistics_data_center_route_diversity": "present",
        "topology_mutation": "likely_observable",
        "basis": role_balance,
    }


def build_lr6_obs7_weak_signal_stress_review() -> dict[str, Any]:
    manifest = build_lr6_obs7_simulated_wave_manifest()
    weak_signal_count = manifest["role_frequency"].get("weak_signal_secondary_bridges", 0)
    return {
        "weak_signal_representation": "sufficient" if weak_signal_count > 0 else "insufficient",
        "weak_signal_likely_in_attribution": weak_signal_count > 0,
        "megacap_gravity_reduction_potential": "moderate" if weak_signal_count > 0 else "low",
        "interpretable_topology_drift_potential": "moderate_to_high" if weak_signal_count > 0 else "low",
        "weak_signal_count": weak_signal_count,
    }


def build_lr6_obs7_stop_condition_simulation() -> list[dict[str, str]]:
    stops = _safe_list(build_lr6_obs6_stop_conditions)
    status_cycle = ["monitored", "warning_only", "fail_closed_trigger", "not_applicable_in_dry_run"]
    return [
        {"stop_condition": condition, "dry_run_status": status_cycle[i % len(status_cycle)]}
        for i, condition in enumerate(stops)
    ]


def build_lr6_obs7_expected_review_artifacts() -> list[dict[str, str]]:
    return [
        {"artifact": "enriched_replay_observation_report", "purpose": "first-wave governed observation synthesis"},
        {"artifact": "pre_post_topology_delta_summary", "purpose": "topology drift and bridge rewiring readout"},
        {"artifact": "contradiction_migration_summary", "purpose": "peripheral-to-core contradiction migration review"},
        {"artifact": "weak_signal_attribution_review", "purpose": "weak-signal role attribution coverage check"},
        {"artifact": "saturation_monoculture_review", "purpose": "narrative concentration vs diversity balance"},
        {"artifact": "first_wave_stop_condition_review", "purpose": "stop-condition outcomes and governance interpretation"},
    ]


def build_lr6_obs7_dry_run_readiness_decision() -> dict[str, Any]:
    manifest = build_lr6_obs7_simulated_wave_manifest()
    weak = build_lr6_obs7_weak_signal_stress_review()
    has_roles = len(manifest["roles_represented"]) >= 5
    if manifest["selected_count"] >= 12 and has_roles and weak["weak_signal_likely_in_attribution"]:
        decision = "DRY_RUN_READY_FOR_GOVERNED_OBSERVATION_PROPOSAL"
    elif manifest["selected_count"] >= 8:
        decision = "DRY_RUN_CONDITIONALLY_READY_NEEDS_REBALANCE"
    else:
        decision = "DRY_RUN_NOT_READY_REQUIRES_REDESIGN"
    return {
        "decision": decision,
        "decision_allowed": decision in ALLOWED_DRY_RUN_DECISIONS,
        "execution_authorized": False,
        "note": "Readiness decision is simulation-only and does not authorize non-dry governed execution.",
    }


def certify_lr6_obs7_dry_run_boundary() -> dict[str, bool]:
    return {
        "observation_only": True,
        "dry_run_only": True,
        "execution_authorized": False,
        "no_prediction": True,
        "no_trading": True,
        "no_direct_sql": True,
        "no_live_ingestion": True,
        "no_persistence_write": True,
        "no_governed_activation": True,
        "architecture_expansion_frozen": True,
    }


def build_lr6_obs7_supervisor_review(lr6_artifacts: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "context": build_lr6_obs7_dry_run_context(lr6_artifacts),
        "inspected_obs6_inputs": {
            "first_wave_candidates": _safe_list(build_lr6_obs6_first_wave_candidates),
            "selection_criteria": _safe_list(build_lr6_obs6_selection_criteria),
            "role_balance_review": _safe_dict(build_lr6_obs6_role_balance_review),
            "observation_questions": _safe_list(build_lr6_obs6_observation_questions),
            "stop_conditions": _safe_list(build_lr6_obs6_stop_conditions),
            "execution_non_authorization_notice": _safe_dict(build_lr6_obs6_execution_non_authorization_notice),
            "obs6_supervisor_review": _safe_dict(lambda: build_lr6_obs6_supervisor_review(lr6_artifacts)),
        },
        "dry_run_boundary": certify_lr6_obs7_dry_run_boundary(),
        "simulated_wave_manifest": build_lr6_obs7_simulated_wave_manifest(),
        "simulated_observation_routes": build_lr6_obs7_simulated_observation_routes(),
        "contradiction_stress_review": build_lr6_obs7_contradiction_stress_review(),
        "propagation_stress_review": build_lr6_obs7_propagation_stress_review(),
        "weak_signal_stress_review": build_lr6_obs7_weak_signal_stress_review(),
        "stop_condition_simulation": build_lr6_obs7_stop_condition_simulation(),
        "expected_review_artifacts": build_lr6_obs7_expected_review_artifacts(),
        "dry_run_readiness_decision": build_lr6_obs7_dry_run_readiness_decision(),
        "explicit_non_authorization_for_execution": "Dry-run simulation only; execution remains explicitly unauthorized.",
        "architectural_overengineering_warning": "Architecture expansion remains frozen; prioritize governed observation quality over structural expansion.",
        "recommendation_for_next_phase": "Submit governed observation proposal package with this dry-run evidence; keep non-dry activation gated.",
    }


def build_lr6_obs7_markdown_report(review: dict[str, Any]) -> str:
    lines = [
        "# LR6-OBS7 Dry-Run Enriched Replay Observation Simulation",
        "",
        "## Objective",
        "Implement a deterministic bounded dry-run simulation to assess OBS6 first-wave procedural and ecological readiness.",
        "",
        "## Inspected OBS6 Inputs",
        f"- Candidate count from OBS6: {len(review['inspected_obs6_inputs']['first_wave_candidates'])}",
        f"- Selection criteria count: {len(review['inspected_obs6_inputs']['selection_criteria'])}",
        "",
        "## Dry-Run Boundary",
    ]
    lines.extend([f"- {k}: {v}" for k, v in review["dry_run_boundary"].items()])
    lines.extend([
        "",
        "## Simulated Wave Manifest",
        f"- Selected count: {review['simulated_wave_manifest']['selected_count']}",
        f"- Dry run: {review['simulated_wave_manifest']['dry_run']}",
        f"- Execution authorized: {review['simulated_wave_manifest']['execution_authorized']}",
        "",
        "## Simulated Observation Routes",
    ])
    lines.extend([f"- {r['ticker']}: contradiction / propagation / weak-signal / semantic-gravity / saturation / topology-drift routes defined" for r in review["simulated_observation_routes"]])
    lines.extend([
        "",
        "## Contradiction Stress Review",
    ])
    lines.extend([f"- {k}: {v}" for k, v in review["contradiction_stress_review"].items() if k != "basis"])
    lines.extend([
        "",
        "## Propagation Stress Review",
    ])
    lines.extend([f"- {k}: {v}" for k, v in review["propagation_stress_review"].items() if k != "basis"])
    lines.extend([
        "",
        "## Weak-Signal Stress Review",
    ])
    lines.extend([f"- {k}: {v}" for k, v in review["weak_signal_stress_review"].items()])
    lines.extend([
        "",
        "## Stop-Condition Simulation",
    ])
    lines.extend([f"- {x['stop_condition']} => {x['dry_run_status']}" for x in review["stop_condition_simulation"]])
    lines.extend([
        "",
        "## Expected Review Artifacts",
    ])
    lines.extend([f"- {a['artifact']}: {a['purpose']}" for a in review["expected_review_artifacts"]])
    lines.extend([
        "",
        "## Dry-Run Readiness Decision",
        f"- Decision: {review['dry_run_readiness_decision']['decision']}",
        f"- Note: {review['dry_run_readiness_decision']['note']}",
        "",
        "## Explicit Non-Authorization for Execution",
        f"- {review['explicit_non_authorization_for_execution']}",
        "",
        "## Architectural Overengineering Warning",
        f"- {review['architectural_overengineering_warning']}",
        "",
        "## Recommendation for Next Phase",
        f"- {review['recommendation_for_next_phase']}",
    ])
    return "\n".join(lines)
