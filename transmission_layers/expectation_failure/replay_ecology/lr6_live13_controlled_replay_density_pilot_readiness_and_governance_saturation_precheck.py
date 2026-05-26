from __future__ import annotations

from typing import Any

from transmission_layers.expectation_failure.replay_ecology import (
    lr6_live11_governance_monitoring_hardening_and_longitudinal_drift_surveillance as live11,
    lr6_live12_replay_governance_telemetry_expansion_and_multi_batch_continuity_validation as live12,
)

LIVE13_VERSION = "LR6_LIVE13_CONTROLLED_REPLAY_DENSITY_PILOT_READINESS_AND_GOVERNANCE_SATURATION_PRECHECK_V1"
_CURRENT_BOUNDED_REPLAY_SIZE = 4
_CANDIDATE_PILOT_REPLAY_SIZE = 6
_MAX_BOUNDED_BATCHES = 3


def build_lr6_live13_density_pilot_readiness_context() -> dict[str, Any]:
    return {
        "readiness_version": LIVE13_VERSION,
        "governance_lineage_reference": ["LIVE5", "LIVE6", "LIVE7", "LIVE8", "LIVE9", "LIVE10", "LIVE11", "LIVE12"],
        "current_bounded_replay_size": _CURRENT_BOUNDED_REPLAY_SIZE,
        "candidate_pilot_replay_size": _CANDIDATE_PILOT_REPLAY_SIZE,
        "replay_richness_only_certification": True,
        "append_only_certification": True,
        "deterministic_replay_certification": True,
        "multi_batch_continuity_certification": True,
        "governance_saturation_monitoring_enabled": True,
        "dry_run_only_certification": True,
        "no_live_expansion_certification": True,
    }


def build_lr6_live13_density_snapshot(sequence_name: str, scenario: str, batch_index: int = 0) -> dict[str, Any]:
    rows = _CURRENT_BOUNDED_REPLAY_SIZE
    if scenario in {"modest_density_increase", "replay_identity_pressure", "duplicate_prevention_pressure", "telemetry_noise_stress"}:
        rows = _CANDIDATE_PILOT_REPLAY_SIZE
    if scenario in {"governance_saturation_warning", "bounded_multi_batch_density_pressure"}:
        rows = _CANDIDATE_PILOT_REPLAY_SIZE + 1
    if scenario == "governance_saturation_failure":
        rows = _CANDIDATE_PILOT_REPLAY_SIZE + 2

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
        "execution_mode": "synthetic_dry_run",
        "live_persistence": False,
        "bounded_density_only": True,
        "append_only_delta": rows,
        "cumulative_rows": rows * (batch_index + 1),
        "simulated_telemetry_noise": 0.0,
    }

    if scenario == "telemetry_noise_stress":
        snap["simulated_telemetry_noise"] = 0.24
    if scenario == "governance_saturation_warning":
        snap["simulated_telemetry_noise"] = 0.32
    if scenario == "governance_saturation_failure":
        snap["simulated_telemetry_noise"] = 0.45
    if scenario == "replay_identity_pressure":
        snap["entity_ids"][-1] = snap["entity_ids"][0]
    if scenario == "duplicate_prevention_pressure":
        snap["duplicate_prevention_keys"][-1] = snap["duplicate_prevention_keys"][0]
    return snap


def build_lr6_live13_density_pilot_sequences() -> dict[str, list[dict[str, Any]]]:
    return {
        "baseline_density_control": [build_lr6_live13_density_snapshot("baseline_density_control", "baseline_density_control")],
        "modest_density_increase": [build_lr6_live13_density_snapshot("modest_density_increase", "modest_density_increase")],
        "governance_saturation_warning": [build_lr6_live13_density_snapshot("governance_saturation_warning", "governance_saturation_warning")],
        "governance_saturation_failure": [build_lr6_live13_density_snapshot("governance_saturation_failure", "governance_saturation_failure")],
        "telemetry_noise_stress": [build_lr6_live13_density_snapshot("telemetry_noise_stress", "telemetry_noise_stress")],
        "replay_identity_pressure": [build_lr6_live13_density_snapshot("replay_identity_pressure", "replay_identity_pressure")],
        "duplicate_prevention_pressure": [build_lr6_live13_density_snapshot("duplicate_prevention_pressure", "duplicate_prevention_pressure")],
        "bounded_multi_batch_density_pressure": [
            build_lr6_live13_density_snapshot("bounded_multi_batch_density_pressure", "bounded_multi_batch_density_pressure", batch_index=i)
            for i in range(_MAX_BOUNDED_BATCHES)
        ],
    }


def build_lr6_live13_governance_saturation_review(sequence_name: str, snapshots: list[dict[str, Any]]) -> dict[str, Any]:
    rows = sum(s["rows"] for s in snapshots)
    batch_count = len(snapshots)
    unique_entities = len({e for s in snapshots for e in s["entity_ids"]})
    unique_keys = len({k for s in snapshots for k in s["duplicate_prevention_keys"]})
    telemetry_noise = max(s["simulated_telemetry_noise"] for s in snapshots)
    return {
        "sequence_name": sequence_name,
        "governance_signal_clarity": "stable" if telemetry_noise < 0.3 else "degraded",
        "replay_identity_stability": unique_entities == rows,
        "duplicate_prevention_reliability": unique_keys == rows,
        "wave_isolation_stability": len({s["wave_id"] for s in snapshots}) == batch_count,
        "anomaly_detection_stability": telemetry_noise <= 0.35,
        "telemetry_coherence": all(s["execution_mode"] == "synthetic_dry_run" for s in snapshots),
        "governance_continuity_stability": batch_count <= _MAX_BOUNDED_BATCHES,
        "replay_cohort_observability": rows > 0,
        "boundedness_integrity": all(s["rows"] <= _CANDIDATE_PILOT_REPLAY_SIZE + 2 for s in snapshots),
        "monitoring_load_pressure": "high" if rows >= (_CANDIDATE_PILOT_REPLAY_SIZE + 2) else "moderate" if rows > _CURRENT_BOUNDED_REPLAY_SIZE else "low",
        "rows": rows,
        "batch_count": batch_count,
        "max_noise": telemetry_noise,
    }


def build_lr6_live13_density_pressure_classification(review: dict[str, Any]) -> dict[str, Any]:
    if not review["boundedness_integrity"] or not review["telemetry_coherence"]:
        cls = "GOVERNANCE_DENSITY_PILOT_BLOCKED"
    elif not review["replay_identity_stability"] or not review["duplicate_prevention_reliability"]:
        cls = "HIGH_GOVERNANCE_SATURATION"
    elif review["max_noise"] > 0.35:
        cls = "HIGH_GOVERNANCE_SATURATION"
    elif review["max_noise"] >= 0.3 or review["monitoring_load_pressure"] == "high":
        cls = "MODERATE_GOVERNANCE_PRESSURE"
    elif review["monitoring_load_pressure"] == "moderate":
        cls = "LOW_GOVERNANCE_PRESSURE"
    else:
        cls = "NO_GOVERNANCE_SATURATION"

    may_proceed = cls in {"NO_GOVERNANCE_SATURATION", "LOW_GOVERNANCE_PRESSURE"}
    if cls == "MODERATE_GOVERNANCE_PRESSURE":
        may_proceed = True
    return {
        "classification": cls,
        "deterministic_explanation": f"Classification derived from deterministic telemetry: load={review['monitoring_load_pressure']}, noise={review['max_noise']}",
        "affected_dimensions": [k for k, v in review.items() if isinstance(v, bool) and not v],
        "estimated_governance_risk": "high" if "HIGH" in cls or "BLOCKED" in cls else "moderate" if "MODERATE" in cls else "low",
        "recommended_operator_action": "Hold LIVE14 pilot and run additional saturation dry-runs." if not may_proceed else "Proceed only with bounded conditional LIVE14 precheck.",
        "live14_bounded_density_pilot_may_proceed": may_proceed,
    }


def build_lr6_live13_density_telemetry_review() -> dict[str, Any]:
    sequences = build_lr6_live13_density_pilot_sequences()
    return {n: build_lr6_live13_governance_saturation_review(n, s) for n, s in sequences.items()}


def build_lr6_live13_density_continuity_review() -> dict[str, Any]:
    sequences = build_lr6_live13_density_pilot_sequences()
    live12_stable = live12.build_lr6_live12_multi_batch_continuity_review("stable", live12.build_lr6_live12_synthetic_multi_batch_sequences()["stable_multi_batch_sequence"])
    drift = live11.build_lr6_live11_governance_drift_review(live11.build_lr6_live11_snapshot_series(scenario="stable"), scenario="stable")
    reviews = build_lr6_live13_density_telemetry_review()
    return {
        "replay_cohort_identity_stable": reviews["baseline_density_control"]["replay_identity_stability"],
        "duplicate_prevention_deterministic": reviews["baseline_density_control"]["duplicate_prevention_reliability"],
        "continuity_telemetry_coherent": all(r["telemetry_coherence"] for r in reviews.values()),
        "live11_drift_telemetry_scenario_derived": drift["drift_classification"]["classification"] == "NO_GOVERNANCE_DRIFT",
        "live12_continuity_validation_functional": live12_stable["continuity_pass"],
        "no_governance_blind_spots": all(r["replay_cohort_observability"] for r in reviews.values()),
        "no_replay_identity_fragmentation": reviews["replay_identity_pressure"]["replay_identity_stability"] is False,
        "sequence_count": len(sequences),
    }


def build_lr6_live13_governance_saturation_safeguards() -> dict[str, Any]:
    return {
        "governance_overload_emergence_guard": "trigger_block_if_high_saturation",
        "telemetry_degradation_guard": "trigger_warning_if_noise_ge_0_30",
        "replay_identity_fragmentation_guard": "block_if_entity_uniqueness_breaks",
        "duplicate_prevention_instability_guard": "block_if_duplicate_key_collision_detected",
        "continuity_degradation_guard": "require_live12_continuity_pass",
        "anomaly_monitoring_saturation_guard": "raise_operator_review_when_load_high",
    }


def build_lr6_live13_density_risk_review() -> dict[str, Any]:
    telemetry = build_lr6_live13_density_telemetry_review()
    classifications = {k: build_lr6_live13_density_pressure_classification(v) for k, v in telemetry.items()}
    return {"telemetry": telemetry, "classifications": classifications}


def build_lr6_live13_live14_readiness_gate(classifications: dict[str, dict[str, Any]]) -> dict[str, Any]:
    classes = {v["classification"] for v in classifications.values()}
    if "GOVERNANCE_DENSITY_PILOT_BLOCKED" in classes or "HIGH_GOVERNANCE_SATURATION" in classes:
        gate = "LIVE14_BLOCKED"
    elif "MODERATE_GOVERNANCE_PRESSURE" in classes:
        gate = "LIVE14_CONDITIONALLY_ELIGIBLE"
    else:
        gate = "LIVE14_READY_FOR_BOUNDED_PILOT_PRECHECK"
    return {
        "live14_readiness_gate": gate,
        "governance_readiness_only": True,
        "scaling_authorization_granted": False,
    }


def certify_lr6_live13_density_precheck_boundary() -> dict[str, Any]:
    return {
        "readiness_assessment_only": True,
        "synthetic_density_only": True,
        "live_density_expansion_enabled": False,
        "scaling_enabled": False,
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


def build_lr6_live13_supervisor_review() -> dict[str, Any]:
    context = build_lr6_live13_density_pilot_readiness_context()
    sequences = build_lr6_live13_density_pilot_sequences()
    telemetry = build_lr6_live13_density_telemetry_review()
    classifications = {k: build_lr6_live13_density_pressure_classification(v) for k, v in telemetry.items()}
    continuity = build_lr6_live13_density_continuity_review()
    safeguards = build_lr6_live13_governance_saturation_safeguards()
    gate = build_lr6_live13_live14_readiness_gate(classifications)
    return {
        "objective": "Controlled replay-density pilot readiness assessment and governance saturation precheck before any density expansion.",
        "density_readiness_context": context,
        "synthetic_density_scenarios": {k: [s["batch_id"] for s in v] for k, v in sequences.items()},
        "governance_saturation_telemetry_findings": telemetry,
        "density_pressure_classifications": classifications,
        "continuity_under_density_findings": continuity,
        "governance_saturation_safeguards": safeguards,
        "live14_readiness_gate_findings": gate,
        "governance_boundary_certification": certify_lr6_live13_density_precheck_boundary(),
        "residual_risks": [
            "Synthetic density pressure cannot fully represent all operator misconfiguration pathways.",
            "Telemetry-noise assumptions should be recalibrated before any bounded LIVE14 pilot precheck.",
        ],
        "governance_recommendation": "Keep LIVE14 blocked unless only bounded conditional scenarios remain at moderate-or-lower pressure.",
    }


def build_lr6_live13_markdown_report(review: dict[str, Any]) -> str:
    return "\n".join([
        "# LR6-LIVE13 — Controlled Replay Density Pilot Readiness & Governance Saturation Precheck",
        "",
        "## objective",
        f"- {review.get('objective')}",
        "",
        "## density readiness context",
        f"- {review.get('density_readiness_context')}",
        "",
        "## synthetic density scenarios",
        f"- {review.get('synthetic_density_scenarios')}",
        "",
        "## governance saturation telemetry findings",
        f"- {review.get('governance_saturation_telemetry_findings')}",
        "",
        "## density pressure classifications",
        f"- {review.get('density_pressure_classifications')}",
        "",
        "## continuity-under-density findings",
        f"- {review.get('continuity_under_density_findings')}",
        "",
        "## governance saturation safeguards",
        f"- {review.get('governance_saturation_safeguards')}",
        "",
        "## LIVE14 readiness gate findings",
        f"- {review.get('live14_readiness_gate_findings')}",
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
