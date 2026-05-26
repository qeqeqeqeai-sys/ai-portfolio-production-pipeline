from __future__ import annotations

from typing import Any

from transmission_layers.expectation_failure.replay_ecology import (
    lr6_live11_governance_monitoring_hardening_and_longitudinal_drift_surveillance as live11,
    lr6_live12_replay_governance_telemetry_expansion_and_multi_batch_continuity_validation as live12,
    lr6_live13_controlled_replay_density_pilot_readiness_and_governance_saturation_precheck as live13,
)

LIVE14_VERSION = "LR6_LIVE14_ULTRA_BOUNDED_REPLAY_DENSITY_PILOT_SYNTHETIC_TO_OPERATIONAL_TRANSITION_GATE_V1"
_CURRENT_BOUNDED_REPLAY_SIZE = 6
_ULTRA_BOUNDED_PILOT_REPLAY_SIZE = 7
_MAX_PILOT_BATCH_COUNT = 3


def build_lr6_live14_ultra_bounded_transition_context() -> dict[str, Any]:
    return {
        "transition_version": LIVE14_VERSION,
        "governance_lineage_reference": ["LIVE5", "LIVE6", "LIVE7", "LIVE8", "LIVE9", "LIVE10", "LIVE11", "LIVE12", "LIVE13"],
        "current_bounded_replay_size": _CURRENT_BOUNDED_REPLAY_SIZE,
        "ultra_bounded_pilot_replay_size": _ULTRA_BOUNDED_PILOT_REPLAY_SIZE,
        "max_pilot_batch_count": _MAX_PILOT_BATCH_COUNT,
        "replay_richness_only_certification": True,
        "append_only_certification": True,
        "governance_continuity_certification": True,
        "multi_batch_continuity_certification": True,
        "operational_transition_mode_certification": True,
        "ultra_bounded_certification": True,
        "no_broad_scaling_certification": True,
    }


def build_lr6_live14_transition_snapshot(sequence_name: str, scenario: str, batch_index: int = 0) -> dict[str, Any]:
    rows = _CURRENT_BOUNDED_REPLAY_SIZE
    if scenario in {"ultra_bounded_control", "telemetry_transition_noise"}:
        rows = _ULTRA_BOUNDED_PILOT_REPLAY_SIZE - 1
    if scenario in {"operational_transition_pressure", "replay_identity_transition_pressure", "duplicate_prevention_transition_pressure", "bounded_multi_batch_transition", "governance_transition_warning"}:
        rows = _ULTRA_BOUNDED_PILOT_REPLAY_SIZE
    if scenario == "governance_transition_failure":
        rows = _ULTRA_BOUNDED_PILOT_REPLAY_SIZE + 1

    snap = {
        "sequence_name": sequence_name,
        "scenario": scenario,
        "batch_index": batch_index,
        "batch_id": f"{sequence_name}_batch_{batch_index}",
        "wave_id": f"{sequence_name}_wave_{batch_index}",
        "rows": rows,
        "entity_ids": [f"entity_{sequence_name}_{batch_index}_{i}" for i in range(rows)],
        "duplicate_prevention_keys": [f"key:{sequence_name}:{batch_index}:{i}" for i in range(rows)],
        "metric_dimension": "replay_richness",
        "execution_mode": "synthetic_operational_transition_dry_run",
        "live_persistence": False,
        "append_only_delta": rows,
        "cumulative_rows": rows * (batch_index + 1),
        "simulated_transition_noise": 0.0,
        "ultra_bounded_only": True,
    }
    if scenario == "telemetry_transition_noise":
        snap["simulated_transition_noise"] = 0.28
    if scenario == "governance_transition_warning":
        snap["simulated_transition_noise"] = 0.34
    if scenario == "governance_transition_failure":
        snap["simulated_transition_noise"] = 0.46
    if scenario == "replay_identity_transition_pressure":
        snap["entity_ids"][-1] = snap["entity_ids"][0]
    if scenario == "duplicate_prevention_transition_pressure":
        snap["duplicate_prevention_keys"][-1] = snap["duplicate_prevention_keys"][0]
    return snap


def build_lr6_live14_ultra_bounded_sequences() -> dict[str, list[dict[str, Any]]]:
    return {
        "ultra_bounded_control": [build_lr6_live14_transition_snapshot("ultra_bounded_control", "ultra_bounded_control")],
        "operational_transition_pressure": [build_lr6_live14_transition_snapshot("operational_transition_pressure", "operational_transition_pressure")],
        "replay_identity_transition_pressure": [build_lr6_live14_transition_snapshot("replay_identity_transition_pressure", "replay_identity_transition_pressure")],
        "duplicate_prevention_transition_pressure": [build_lr6_live14_transition_snapshot("duplicate_prevention_transition_pressure", "duplicate_prevention_transition_pressure")],
        "telemetry_transition_noise": [build_lr6_live14_transition_snapshot("telemetry_transition_noise", "telemetry_transition_noise")],
        "bounded_multi_batch_transition": [build_lr6_live14_transition_snapshot("bounded_multi_batch_transition", "bounded_multi_batch_transition", i) for i in range(_MAX_PILOT_BATCH_COUNT)],
        "governance_transition_warning": [build_lr6_live14_transition_snapshot("governance_transition_warning", "governance_transition_warning")],
        "governance_transition_failure": [build_lr6_live14_transition_snapshot("governance_transition_failure", "governance_transition_failure")],
    }


def build_lr6_live14_transition_telemetry_review(sequence_name: str, snapshots: list[dict[str, Any]]) -> dict[str, Any]:
    rows = sum(s["rows"] for s in snapshots)
    max_noise = max(s["simulated_transition_noise"] for s in snapshots)
    expected_rows = rows
    return {
        "sequence_name": sequence_name,
        "operational_replay_continuity": all(s["rows"] <= _ULTRA_BOUNDED_PILOT_REPLAY_SIZE + 1 for s in snapshots),
        "replay_identity_continuity": len({e for s in snapshots for e in s["entity_ids"]}) == expected_rows,
        "duplicate_prevention_continuity": len({k for s in snapshots for k in s["duplicate_prevention_keys"]}) == expected_rows,
        "governance_telemetry_clarity": "stable" if max_noise < 0.30 else "degraded" if max_noise < 0.40 else "saturated",
        "anomaly_monitoring_continuity": max_noise <= 0.40,
        "append_only_continuity": all(s["append_only_delta"] >= 0 for s in snapshots),
        "multi_batch_continuity": len(snapshots) <= _MAX_PILOT_BATCH_COUNT,
        "governance_signal_saturation": "high" if max_noise >= 0.40 else "moderate" if max_noise >= 0.30 else "low",
        "replay_cohort_observability": rows > 0,
        "operational_transition_pressure": "high" if rows >= _ULTRA_BOUNDED_PILOT_REPLAY_SIZE + 1 else "moderate" if rows >= _ULTRA_BOUNDED_PILOT_REPLAY_SIZE else "low",
        "governance_auditability_continuity": all(s["execution_mode"] == "synthetic_operational_transition_dry_run" and not s["live_persistence"] for s in snapshots),
        "rows": rows,
        "max_noise": max_noise,
    }


def build_lr6_live14_transition_pressure_classification(review: dict[str, Any]) -> dict[str, Any]:
    if not review["governance_auditability_continuity"] or not review["operational_replay_continuity"]:
        classification = "OPERATIONAL_TRANSITION_BLOCKED"
    elif not review["replay_identity_continuity"] or not review["duplicate_prevention_continuity"] or review["max_noise"] >= 0.40:
        classification = "HIGH_TRANSITION_PRESSURE"
    elif review["max_noise"] >= 0.30 or review["operational_transition_pressure"] == "high":
        classification = "MODERATE_TRANSITION_PRESSURE"
    elif review["operational_transition_pressure"] == "moderate":
        classification = "LOW_TRANSITION_PRESSURE"
    else:
        classification = "NO_TRANSITION_PRESSURE"
    may_proceed = classification in {"NO_TRANSITION_PRESSURE", "LOW_TRANSITION_PRESSURE", "MODERATE_TRANSITION_PRESSURE"}
    return {
        "classification": classification,
        "deterministic_explanation": f"Deterministic classification from pressure={review['operational_transition_pressure']} noise={review['max_noise']}",
        "affected_dimensions": [k for k, v in review.items() if isinstance(v, bool) and not v],
        "governance_risk_estimate": "high" if classification in {"HIGH_TRANSITION_PRESSURE", "OPERATIONAL_TRANSITION_BLOCKED"} else "moderate" if classification == "MODERATE_TRANSITION_PRESSURE" else "low",
        "recommended_operator_action": "Hold LIVE15 and run transition hardening dry-runs." if not may_proceed else "Proceed with bounded governance re-certification precheck only.",
        "live15_governance_recertification_may_proceed": may_proceed,
    }


def build_lr6_live14_operational_transition_review() -> dict[str, Any]:
    sequences = build_lr6_live14_ultra_bounded_sequences()
    return {k: build_lr6_live14_transition_telemetry_review(k, v) for k, v in sequences.items()}


def build_lr6_live14_transition_continuity_review() -> dict[str, Any]:
    live11_stable = live11.build_lr6_live11_governance_drift_review(scenario="stable")
    live12_stable = live12.build_lr6_live12_multi_batch_continuity_review("stable", live12.build_lr6_live12_synthetic_multi_batch_sequences()["stable_multi_batch_sequence"])
    live13_telemetry = live13.build_lr6_live13_density_telemetry_review()
    reviews = build_lr6_live14_operational_transition_review()
    return {
        "replay_identity_continuity_stable": reviews["ultra_bounded_control"]["replay_identity_continuity"],
        "duplicate_prevention_continuity_deterministic": reviews["ultra_bounded_control"]["duplicate_prevention_continuity"],
        "append_only_continuity_preserved": all(r["append_only_continuity"] for r in reviews.values()),
        "live11_telemetry_scenario_derived": live11_stable["drift_classification"]["classification"] == "NO_GOVERNANCE_DRIFT",
        "live12_multi_batch_continuity_functional": live12_stable["continuity_pass"],
        "live13_saturation_telemetry_coherent": all(r["telemetry_coherence"] for r in live13_telemetry.values()),
        "no_replay_identity_fragmentation": reviews["replay_identity_transition_pressure"]["replay_identity_continuity"] is False,
        "no_governance_blind_spots": all(r["replay_cohort_observability"] for r in reviews.values()),
        "no_governance_auditability_gaps": all(r["governance_auditability_continuity"] for r in reviews.values()),
    }


def build_lr6_live14_transition_safeguards() -> dict[str, Any]:
    return {
        "operational_transition_overload_guard": "block_if_transition_pressure_high_or_blocked",
        "replay_identity_instability_guard": "block_if_replay_identity_continuity_false",
        "duplicate_prevention_degradation_guard": "block_if_duplicate_prevention_continuity_false",
        "telemetry_coherence_degradation_guard": "warn_if_governance_telemetry_clarity_degraded",
        "anomaly_monitoring_overload_guard": "block_if_governance_signal_saturation_high",
        "auditability_continuity_degradation_guard": "block_if_governance_auditability_continuity_false",
        "governance_saturation_escalation_guard": "escalate_if_consecutive_moderate_or_any_high",
    }


def build_lr6_live14_transition_risk_review() -> dict[str, Any]:
    telemetry = build_lr6_live14_operational_transition_review()
    classifications = {k: build_lr6_live14_transition_pressure_classification(v) for k, v in telemetry.items()}
    return {"transition_telemetry": telemetry, "transition_classifications": classifications}


def build_lr6_live14_live15_eligibility_gate(classifications: dict[str, dict[str, Any]]) -> dict[str, Any]:
    classes = {v["classification"] for v in classifications.values()}
    if "OPERATIONAL_TRANSITION_BLOCKED" in classes or "HIGH_TRANSITION_PRESSURE" in classes:
        gate = "LIVE15_BLOCKED"
    elif "MODERATE_TRANSITION_PRESSURE" in classes:
        gate = "LIVE15_CONDITIONALLY_ELIGIBLE"
    else:
        gate = "LIVE15_READY_FOR_RECERTIFICATION_PRECHECK"
    return {"live15_eligibility_gate": gate, "recertification_only": True, "scaling_authorized": False}


def certify_lr6_live14_transition_boundary() -> dict[str, Any]:
    return {
        "ultra_bounded_transition_only": True,
        "synthetic_operational_transition_only": True,
        "live_density_scaling_enabled": False,
        "broad_scaling_enabled": False,
        "topology_drift_enabled": False,
        "contradiction_persistence_migration_enabled": False,
        "prediction_enabled": False,
        "trading_enabled": False,
        "auto_expansion_enabled": False,
        "schema_expansion_enabled": False,
        "historical_row_rewrite_enabled": False,
        "replay_richness_only": True,
        "append_only_required": True,
        "deterministic_governance_required": True,
    }


def build_lr6_live14_supervisor_review() -> dict[str, Any]:
    context = build_lr6_live14_ultra_bounded_transition_context()
    sequences = build_lr6_live14_ultra_bounded_sequences()
    telemetry = build_lr6_live14_operational_transition_review()
    classifications = {k: build_lr6_live14_transition_pressure_classification(v) for k, v in telemetry.items()}
    continuity = build_lr6_live14_transition_continuity_review()
    safeguards = build_lr6_live14_transition_safeguards()
    gate = build_lr6_live14_live15_eligibility_gate(classifications)
    return {
        "objective": "Ultra-bounded replay-density pilot transition gate from synthetic readiness to operationally-adjacent governance eligibility.",
        "transition_context": context,
        "ultra_bounded_pilot_scenarios": {k: [s["batch_id"] for s in v] for k, v in sequences.items()},
        "operational_transition_telemetry_findings": telemetry,
        "transition_pressure_classifications": classifications,
        "continuity_findings": continuity,
        "governance_transition_safeguards": safeguards,
        "live15_eligibility_findings": gate,
        "governance_boundary_certification": certify_lr6_live14_transition_boundary(),
        "residual_risks": [
            "Synthetic transition-noise model may not represent all real-world operator timing jitter.",
            "Moderate transition pressure requires additional bounded runs before LIVE15 precheck.",
        ],
        "governance_recommendation": "Permit only governance re-certification precheck pathways when pressure remains moderate-or-lower and no blocked/high classes remain.",
    }


def build_lr6_live14_markdown_report(review: dict[str, Any]) -> str:
    return "\n".join([
        "# LR6-LIVE14 — Ultra-Bounded Replay Density Pilot (Synthetic-to-Operational Transition Gate)",
        "",
        "## objective",
        f"- {review.get('objective')}",
        "",
        "## transition context",
        f"- {review.get('transition_context')}",
        "",
        "## ultra-bounded pilot scenarios",
        f"- {review.get('ultra_bounded_pilot_scenarios')}",
        "",
        "## operational-transition telemetry findings",
        f"- {review.get('operational_transition_telemetry_findings')}",
        "",
        "## transition pressure classifications",
        f"- {review.get('transition_pressure_classifications')}",
        "",
        "## continuity findings",
        f"- {review.get('continuity_findings')}",
        "",
        "## governance transition safeguards",
        f"- {review.get('governance_transition_safeguards')}",
        "",
        "## LIVE15 eligibility findings",
        f"- {review.get('live15_eligibility_findings')}",
        "",
        "## governance boundary certification",
        f"- {review.get('governance_boundary_certification')}",
        "",
        "## residual risks",
        f"- {review.get('residual_risks')}",
        "",
        "## recommendation",
        f"- {review.get('governance_recommendation')}",
        "",
    ])
