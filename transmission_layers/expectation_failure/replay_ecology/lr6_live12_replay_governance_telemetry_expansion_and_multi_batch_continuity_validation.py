from __future__ import annotations

from typing import Any

from transmission_layers.expectation_failure.replay_ecology import (
    lr6_live11_governance_monitoring_hardening_and_longitudinal_drift_surveillance as live11,
)

LIVE12_VERSION = "LR6_LIVE12_REPLAY_GOVERNANCE_TELEMETRY_EXPANSION_AND_MULTI_BATCH_CONTINUITY_VALIDATION_V1"
_BATCH_COUNT_BOUND = 3
_PER_BATCH_ENTITY_BOUND = 4


def build_lr6_live12_multi_batch_telemetry_context() -> dict[str, Any]:
    return {
        "telemetry_version": LIVE12_VERSION,
        "governance_lineage_reference": ["LIVE5", "LIVE6", "LIVE7", "LIVE8", "LIVE9", "LIVE10", "LIVE11"],
        "multi_batch_continuity_mode": "deterministic_governance_validation",
        "replay_richness_only_scope": True,
        "append_only_expectation": True,
        "deterministic_shared_wave_expectation": True,
        "duplicate_prevention_continuity_expectation": True,
        "batch_count_bound": _BATCH_COUNT_BOUND,
        "per_batch_entity_bound": _PER_BATCH_ENTITY_BOUND,
        "synthetic_dry_run_certification": True,
        "no_live_write_certification": True,
        "no_expansion_certification": True,
    }


def build_lr6_live12_batch_snapshot(sequence_name: str, batch_index: int, scenario: str = "stable") -> dict[str, Any]:
    telemetry = live11.build_lr6_live11_governance_snapshot(batch_index, scenario=scenario)
    entity_ids = [f"entity_{batch_index}_{i}" for i in range(_PER_BATCH_ENTITY_BOUND)]
    return {
        "batch_id": f"{sequence_name}_batch_{batch_index}",
        "wave_id": f"{sequence_name}_wave_{batch_index}",
        "batch_index": batch_index,
        "rows": _PER_BATCH_ENTITY_BOUND,
        "duplicate_prevention_keys": [f"{sequence_name}:key:{batch_index}:{i}" for i in range(_PER_BATCH_ENTITY_BOUND)],
        "entity_ids": entity_ids,
        "metric_target": "replay_richness",
        "metric_dimension": "replay_richness",
        "evidence_status": "validated",
        "comparison_ready": True,
        "scaffold_only": False,
        "adapter_name": "lr6_replay_governance_adapter",
        "execution_mode": "synthetic_dry_run",
        "append_only_delta": _PER_BATCH_ENTITY_BOUND,
        "prior_cumulative_rows": batch_index * _PER_BATCH_ENTITY_BOUND,
        "cumulative_rows": (batch_index + 1) * _PER_BATCH_ENTITY_BOUND,
        "governance_telemetry": {
            "scenario": scenario,
            "governance_confidence_state": telemetry["governance_confidence_state"],
            "anomaly_frequency": telemetry["anomaly_detection_state"]["anomaly_frequency"],
            "monitoring_coverage_state": telemetry["monitoring_coverage_state"],
            "governance_boundary_state": telemetry["governance_boundary_state"],
        },
    }


def build_lr6_live12_synthetic_multi_batch_sequences() -> dict[str, list[dict[str, Any]]]:
    stable = [build_lr6_live12_batch_snapshot("stable_multi_batch_sequence", i, "stable") for i in range(_BATCH_COUNT_BOUND)]
    wave_fragmented = [dict(batch) for batch in stable]
    wave_fragmented[0]["batch_id"] = "wave_fragmentation_batch_sequence_batch_0"
    wave_fragmented[0]["wave_id"] = ["wf_a", "wf_b"]

    cross_wave = [build_lr6_live12_batch_snapshot("cross_batch_wave_collision_sequence", i, "stable") for i in range(_BATCH_COUNT_BOUND)]
    cross_wave[1]["wave_id"] = cross_wave[0]["wave_id"]

    dup_cross = [build_lr6_live12_batch_snapshot("duplicate_key_cross_batch_sequence", i, "stable") for i in range(_BATCH_COUNT_BOUND)]
    dup_cross[1]["duplicate_prevention_keys"][0] = dup_cross[0]["duplicate_prevention_keys"][0]

    append_violation = [build_lr6_live12_batch_snapshot("append_only_boundary_violation_sequence", i, "stable") for i in range(_BATCH_COUNT_BOUND)]
    append_violation[1]["cumulative_rows"] = append_violation[0]["cumulative_rows"] - 1

    metric_violation = [build_lr6_live12_batch_snapshot("metric_scope_violation_sequence", i, "stable") for i in range(_BATCH_COUNT_BOUND)]
    metric_violation[1]["metric_dimension"] = "replay_density"

    degrading = [build_lr6_live12_batch_snapshot("degrading_governance_sequence", i, "degrading") for i in range(_BATCH_COUNT_BOUND)]
    improving = [build_lr6_live12_batch_snapshot("improving_governance_sequence", i, "improving") for i in range(_BATCH_COUNT_BOUND)]

    return {
        "stable_multi_batch_sequence": stable,
        "wave_fragmentation_batch_sequence": wave_fragmented,
        "cross_batch_wave_collision_sequence": cross_wave,
        "duplicate_key_cross_batch_sequence": dup_cross,
        "append_only_boundary_violation_sequence": append_violation,
        "metric_scope_violation_sequence": metric_violation,
        "degrading_governance_sequence": degrading,
        "improving_governance_sequence": improving,
    }


def build_lr6_live12_multi_batch_continuity_review(sequence_name: str, batches: list[dict[str, Any]]) -> dict[str, Any]:
    wave_ids: list[str] = []
    duplicate_keys: set[str] = set()
    checks = {
        "intra_batch_wave_uniqueness": True,
        "cross_batch_wave_distinction": True,
        "duplicate_key_uniqueness_within_batch": True,
        "duplicate_key_collision_detection_across_batches": True,
        "replay_richness_scope_continuity": True,
        "append_only_continuity": True,
        "entity_completeness_continuity": True,
        "evidence_status_continuity": True,
        "comparison_scaffold_continuity": True,
        "adapter_execution_mode_consistency": True,
        "batch_boundedness": True,
        "governance_telemetry_continuity": True,
    }
    violations: list[str] = []
    affected_batches: set[str] = set()
    prior_cumulative = -1
    for b in batches:
        bid = b["batch_id"]
        w = b["wave_id"]
        if isinstance(w, list):
            checks["intra_batch_wave_uniqueness"] = False
            violations.append("INTRA_BATCH_WAVE_FRAGMENTATION")
            affected_batches.add(bid)
        else:
            if w in wave_ids:
                checks["cross_batch_wave_distinction"] = False
                violations.append("CROSS_BATCH_WAVE_COLLISION")
                affected_batches.add(bid)
            wave_ids.append(w)
        keys = b["duplicate_prevention_keys"]
        if len(keys) != len(set(keys)):
            checks["duplicate_key_uniqueness_within_batch"] = False
            violations.append("INTRA_BATCH_DUPLICATE_KEY_COLLISION")
            affected_batches.add(bid)
        for k in keys:
            if k in duplicate_keys:
                checks["duplicate_key_collision_detection_across_batches"] = False
                violations.append("CROSS_BATCH_DUPLICATE_KEY_COLLISION")
                affected_batches.add(bid)
            duplicate_keys.add(k)
        if b["metric_target"] != "replay_richness" or b["metric_dimension"] != "replay_richness":
            checks["replay_richness_scope_continuity"] = False
            violations.append("MULTI_BATCH_METRIC_SCOPE_VIOLATION")
            affected_batches.add(bid)
        if len(b["entity_ids"]) != b["rows"]:
            checks["entity_completeness_continuity"] = False
            violations.append("ENTITY_COMPLETENESS_VIOLATION")
            affected_batches.add(bid)
        if b["evidence_status"] != "validated":
            checks["evidence_status_continuity"] = False
        if not b["comparison_ready"] or b["scaffold_only"]:
            checks["comparison_scaffold_continuity"] = False
        if b["adapter_name"] != "lr6_replay_governance_adapter" or b["execution_mode"] != "synthetic_dry_run":
            checks["adapter_execution_mode_consistency"] = False
        if b["rows"] > _PER_BATCH_ENTITY_BOUND or len(batches) > _BATCH_COUNT_BOUND:
            checks["batch_boundedness"] = False
            violations.append("MULTI_BATCH_BOUNDEDNESS_VIOLATION")
            affected_batches.add(bid)
        if b["cumulative_rows"] < prior_cumulative:
            checks["append_only_continuity"] = False
            violations.append("MULTI_BATCH_APPEND_ONLY_BOUNDARY_VIOLATION")
            affected_batches.add(bid)
        prior_cumulative = b["cumulative_rows"]

    return {
        "sequence_name": sequence_name,
        "batch_count": len(batches),
        "checks": checks,
        "violations": sorted(set(violations)),
        "affected_batch_ids": sorted(affected_batches),
        "continuity_pass": not any(v is False for v in checks.values()) ,
    }


def build_lr6_live12_multi_batch_anomaly_classification(continuity_review: dict[str, Any]) -> list[dict[str, Any]]:
    mapping = {
        "INTRA_BATCH_WAVE_FRAGMENTATION": ("high", "Split wave_id detected within a single batch.", False),
        "CROSS_BATCH_WAVE_COLLISION": ("high", "Identical wave_id reused across multiple batches.", False),
        "CROSS_BATCH_DUPLICATE_KEY_COLLISION": ("high", "Duplicate prevention keys collided across batches.", False),
        "MULTI_BATCH_METRIC_SCOPE_VIOLATION": ("high", "Non replay_richness metric scope detected.", False),
        "MULTI_BATCH_APPEND_ONLY_BOUNDARY_VIOLATION": ("critical", "Cumulative rows regressed across append-only batches.", False),
        "MULTI_BATCH_BOUNDEDNESS_VIOLATION": ("high", "Batch or entity bounds exceeded.", False),
        "MULTI_BATCH_GOVERNANCE_DRIFT": ("moderate", "Scenario-derived governance drift detected by LIVE11 telemetry bridge.", True),
    }
    violations = continuity_review.get("violations", [])
    if not violations:
        return [{
            "anomaly_class": "NO_MULTI_BATCH_ANOMALY",
            "severity": "none",
            "deterministic_reason": "All deterministic multi-batch continuity checks passed.",
            "affected_batch_ids": [],
            "recommended_operator_action": "Proceed with bounded governance telemetry monitoring cadence.",
            "live13_may_proceed": True,
        }]
    out = []
    for v in violations:
        sev, reason, may = mapping.get(v, ("moderate", "Deterministic continuity anomaly detected.", False))
        out.append({
            "anomaly_class": v,
            "severity": sev,
            "deterministic_reason": reason,
            "affected_batch_ids": continuity_review.get("affected_batch_ids", []),
            "recommended_operator_action": "Run targeted dry-run remediation and re-validate bounded multi-batch continuity.",
            "live13_may_proceed": may,
        })
    return out


def build_lr6_live12_live11_telemetry_bridge_review(sequence_name: str, batches: list[dict[str, Any]]) -> dict[str, Any]:
    scenario = batches[-1]["governance_telemetry"]["scenario"]
    snapshots = live11.build_lr6_live11_snapshot_series(scenario=scenario)
    drift = live11.build_lr6_live11_governance_drift_review(snapshots=snapshots, scenario=scenario)
    c = drift["drift_classification"]["classification"]
    return {
        "sequence_name": sequence_name,
        "scenario": scenario,
        "live11_drift_classification": c,
        "governance_drift_detected": c != "NO_GOVERNANCE_DRIFT",
        "drift_is_scenario_derived": True,
        "continuity_violations_separate_from_drift": True,
    }


def certify_lr6_live12_multi_batch_boundary() -> dict[str, Any]:
    return {
        "governance_telemetry_only": True,
        "multi_batch_validation_only": True,
        "live_persistence_enabled": False,
        "scaling_enabled": False,
        "new_replay_metrics_enabled": False,
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


def build_lr6_live12_supervisor_review() -> dict[str, Any]:
    context = build_lr6_live12_multi_batch_telemetry_context()
    sequences = build_lr6_live12_synthetic_multi_batch_sequences()
    continuity = {n: build_lr6_live12_multi_batch_continuity_review(n, s) for n, s in sequences.items()}
    anomalies = {n: build_lr6_live12_multi_batch_anomaly_classification(r) for n, r in continuity.items()}
    bridges = {n: build_lr6_live12_live11_telemetry_bridge_review(n, s) for n, s in sequences.items()}
    if bridges["degrading_governance_sequence"]["governance_drift_detected"]:
        anomalies["degrading_governance_sequence"].append({
            "anomaly_class": "MULTI_BATCH_GOVERNANCE_DRIFT",
            "severity": "moderate",
            "deterministic_reason": "LIVE11 scenario-derived telemetry indicates degrading governance trend.",
            "affected_batch_ids": [b["batch_id"] for b in sequences["degrading_governance_sequence"]],
            "recommended_operator_action": "Pause progression and run targeted governance hardening dry-runs.",
            "live13_may_proceed": False,
        })
    stable_ok = all(a[0]["anomaly_class"] == "NO_MULTI_BATCH_ANOMALY" for k, a in anomalies.items() if k in {"stable_multi_batch_sequence", "improving_governance_sequence"})
    live13 = "proceed_with_bounded_live13_pilot_readiness_checks" if stable_ok else "defer_live13_pending_multi_batch_governance_remediation"
    return {
        "objective": "Validate deterministic replay-governance continuity across multiple bounded replay batches.",
        "multi_batch_telemetry_context": context,
        "synthetic_multi_batch_sequence_inventory": {k: [b["batch_id"] for b in v] for k, v in sequences.items()},
        "continuity_validation_findings": continuity,
        "cross_batch_anomaly_classifications": anomalies,
        "live11_telemetry_bridge_findings": bridges,
        "governance_boundary_certification": certify_lr6_live12_multi_batch_boundary(),
        "residual_risks": [
            "Synthetic bounded scenarios may not cover every rare operator misconfiguration pathway.",
            "Dry-run continuity validation remains dependent on periodic scenario refresh cadence.",
        ],
        "live13_recommendation": live13,
    }


def build_lr6_live12_markdown_report(review: dict[str, Any]) -> str:
    return "\n".join([
        "# LR6-LIVE12 — Replay Governance Telemetry Expansion & Multi-Batch Continuity Validation",
        "",
        "## objective",
        f"- {review.get('objective')}",
        "",
        "## multi-batch telemetry context",
        f"- {review.get('multi_batch_telemetry_context')}",
        "",
        "## synthetic multi-batch sequence inventory",
        f"- {review.get('synthetic_multi_batch_sequence_inventory')}",
        "",
        "## continuity validation findings",
        f"- {review.get('continuity_validation_findings')}",
        "",
        "## cross-batch anomaly classifications",
        f"- {review.get('cross_batch_anomaly_classifications')}",
        "",
        "## LIVE11 telemetry bridge findings",
        f"- {review.get('live11_telemetry_bridge_findings')}",
        "",
        "## governance boundary certification",
        f"- {review.get('governance_boundary_certification')}",
        "",
        "## residual risks",
        f"- {review.get('residual_risks')}",
        "",
        "## LIVE13 recommendation",
        f"- {review.get('live13_recommendation')}",
        "",
    ])
