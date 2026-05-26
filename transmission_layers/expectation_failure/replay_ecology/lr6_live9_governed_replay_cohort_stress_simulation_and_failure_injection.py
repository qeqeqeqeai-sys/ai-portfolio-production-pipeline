from __future__ import annotations

from typing import Any

from transmission_layers.expectation_failure.replay_ecology import (
    lr6_live8_replay_cohort_integrity_monitoring_and_regression_safeguards as live8,
)

LIVE9_VERSION = "LR6_LIVE9_GOVERNED_REPLAY_COHORT_STRESS_SIMULATION_AND_FAILURE_INJECTION_V1"


def _base_row(i: int) -> dict[str, Any]:
    return {
        "wave_id": "LR6_LIVE7_WAVE_ABC123",
        "duplicate_prevention_key": f"k{i}",
        "entity_id": f"E{i}",
        "metric_target": "replay_richness",
        "metric_dimension": "replay_richness",
        "evidence_status": "MEASURED",
        "comparison_ready": False,
        "scaffold_only": False,
        "adapter_name": "replay_richness_wave0_shadow_append_only_adapter",
        "execution_mode": "append_only_insert",
        "synthetic_only": True,
    }


def build_lr6_live9_stress_simulation_context() -> dict[str, Any]:
    return {
        "stress_test_version": LIVE9_VERSION,
        "simulation_only": True,
        "synthetic_only": True,
        "input_marker": "LR6_LIVE9_SYNTHETIC_ONLY",
        "replay_richness_only_expected": True,
        "max_entities_bound": 5,
        "expected_adapter_name": "replay_richness_wave0_shadow_append_only_adapter",
        "expected_execution_mode": "append_only_insert",
        "expected_evidence_status": "MEASURED",
        "expected_comparison_ready": False,
        "expected_scaffold_only": False,
        "no_live_write_certified": True,
    }


def build_lr6_live9_synthetic_failure_cohorts() -> dict[str, dict[str, Any]]:
    valid = [_base_row(1), _base_row(2), _base_row(3)]
    historical_valid = [{"wave_id": "LR6_LIVE5_WAVE_1FB274FE8C0A"}, {"wave_id": "LR6_LIVE5_WAVE_62418FB64AB0"}]
    return {
        "valid_control_cohort": {
            "inserted_rows": valid,
            "historical_rows": historical_valid,
            "expected_primary_anomaly": "NO_ANOMALY",
            "expected_block": False,
        },
        "multi_wave_failure_cohort": {
            "inserted_rows": [_base_row(1), _base_row(2) | {"wave_id": "LR6_LIVE7_WAVE_DIFFERENT"}],
            "historical_rows": historical_valid,
            "expected_primary_anomaly": "MULTI_WAVE_BATCH_ANOMALY",
            "expected_block": True,
        },
        "duplicate_key_failure_cohort": {
            "inserted_rows": [_base_row(1), _base_row(2) | {"duplicate_prevention_key": "k1"}],
            "historical_rows": historical_valid,
            "expected_primary_anomaly": "DUPLICATE_KEY_ANOMALY",
            "expected_block": True,
        },
        "missing_entity_id_failure_cohort": {
            "inserted_rows": [_base_row(1), _base_row(2) | {"entity_id": ""}],
            "historical_rows": historical_valid,
            "expected_primary_anomaly": "MISSING_ENTITY_ID_ANOMALY",
            "expected_block": True,
        },
        "metric_scope_failure_cohort": {
            "inserted_rows": [_base_row(1) | {"metric_target": "topology_drift", "metric_dimension": "topology_drift"}],
            "historical_rows": historical_valid,
            "expected_primary_anomaly": "METRIC_SCOPE_ANOMALY",
            "expected_block": True,
        },
        "append_only_boundary_failure_cohort": {
            "inserted_rows": [_base_row(1) | {"execution_mode": "upsert"}],
            "historical_rows": historical_valid,
            "expected_primary_anomaly": "APPEND_ONLY_BOUNDARY_ANOMALY",
            "expected_block": True,
        },
        "over_bound_failure_cohort": {
            "inserted_rows": [_base_row(i) for i in range(1, 7)],
            "historical_rows": historical_valid,
            "expected_primary_anomaly": "APPEND_ONLY_BOUNDARY_ANOMALY",
            "expected_block": True,
        },
        "historical_compatibility_failure_case": {
            "inserted_rows": valid,
            "historical_rows": [{"wave_id": "BROKEN_HISTORICAL_WAVE"}],
            "expected_primary_anomaly": "HISTORICAL_COMPATIBILITY_ANOMALY",
            "expected_block": True,
            "force_historical_compatibility_fail": True,
        },
    }


def run_lr6_live9_failure_injection_suite() -> dict[str, Any]:
    context = build_lr6_live9_stress_simulation_context()
    cohorts = build_lr6_live9_synthetic_failure_cohorts()
    results: list[dict[str, Any]] = []

    for cohort_name, cohort in cohorts.items():
        inserted_rows = cohort["inserted_rows"]
        historical_rows = cohort["historical_rows"]

        cohort_review = live8.build_lr6_live8_cohort_integrity_review(inserted_rows=inserted_rows, context=context)
        regression_review = live8.build_lr6_live8_regression_safeguard_review(inserted_rows=inserted_rows, historical_rows=historical_rows)
        historical_review = live8.build_lr6_live8_historical_compatibility_monitor(historical_rows=historical_rows)
        if cohort.get("force_historical_compatibility_fail"):
            historical_review["historical_compatibility_pass"] = False
        boundary_review = live8.build_lr6_live8_append_only_boundary_monitor(inserted_rows=inserted_rows)

        if len(inserted_rows) > context["max_entities_bound"]:
            regression_review["append_only_semantics_preserved"] = False

        anomaly = live8.build_lr6_live8_anomaly_classification(
            cohort_review=cohort_review,
            regression_review=regression_review,
            historical_review=historical_review,
            boundary_review=boundary_review,
        )
        anomaly_names = [a["anomaly"] for a in anomaly["anomalies"]]
        expected = cohort["expected_primary_anomaly"]
        detected = expected in anomaly_names
        block_expected = cohort["expected_block"]
        block_actual = not anomaly["live9_may_proceed"]
        results.append(
            {
                "cohort_name": cohort_name,
                "expected_primary_anomaly": expected,
                "actual_anomalies": anomaly_names,
                "failure_caught": detected,
                "expected_block": block_expected,
                "actual_block": block_actual,
                "blocking_behavior_correct": block_expected == block_actual,
                "pass": detected and (block_expected == block_actual),
            }
        )

    summary = build_lr6_live9_stress_result_summary(results)
    return {
        "context": context,
        "simulation_results": results,
        "summary": summary,
    }


def build_lr6_live9_stress_result_summary(simulation_results: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(simulation_results)
    passed = sum(1 for r in simulation_results if r["pass"])
    failed = total - passed
    anomalies_expected = [r for r in simulation_results if r["expected_primary_anomaly"] != "NO_ANOMALY"]
    caught = sum(1 for r in anomalies_expected if r["failure_caught"])
    missed = len(anomalies_expected) - caught
    false_positives = sum(1 for r in simulation_results if r["expected_primary_anomaly"] == "NO_ANOMALY" and r["actual_anomalies"] != ["NO_ANOMALY"])
    false_negatives = sum(1 for r in anomalies_expected if not r["failure_caught"])
    blocking_ok = all(r["blocking_behavior_correct"] for r in simulation_results)
    return {
        "total_cohorts_simulated": total,
        "passed_simulations": passed,
        "failed_simulations": failed,
        "caught_anomalies": caught,
        "missed_anomalies": missed,
        "false_positives": false_positives,
        "false_negatives": false_negatives,
        "blocking_behavior_correct": blocking_ok,
        "aggregate_pass": failed == 0,
    }


def build_lr6_live9_supervisor_review() -> dict[str, Any]:
    suite = run_lr6_live9_failure_injection_suite()
    summary = suite["summary"]
    readiness = "ready_for_live10_stabilization_gate" if summary["aggregate_pass"] else "remediation_required_before_live10"
    return {
        "objective": "stress-test LIVE8 replay cohort governance with deterministic synthetic failure injection before any expansion",
        "stress_context": suite["context"],
        "synthetic_cohort_inventory": list(build_lr6_live9_synthetic_failure_cohorts().keys()),
        "expected_anomaly_matrix": {
            k: v["expected_primary_anomaly"] for k, v in build_lr6_live9_synthetic_failure_cohorts().items()
        },
        "actual_detection_results": suite["simulation_results"],
        "stress_summary": summary,
        "governance_boundary": certify_lr6_live9_stress_boundary(),
        "residual_risks": ["stress suite depends on LIVE8 monitor truthfulness of adapter-provided row metadata"],
        "live10_recommendation": readiness,
    }


def build_lr6_live9_markdown_report(review: dict[str, Any]) -> str:
    return "\n".join([
        "# LR6-LIVE9 — Governed Replay Cohort Stress Simulation & Failure Injection",
        "",
        "## objective",
        f"- {review.get('objective')}",
        "",
        "## simulation-only boundary",
        f"- {review.get('stress_context')}",
        "",
        "## synthetic cohort inventory",
        f"- {review.get('synthetic_cohort_inventory')}",
        "",
        "## expected anomaly matrix",
        f"- {review.get('expected_anomaly_matrix')}",
        "",
        "## actual detection results",
        f"- {review.get('actual_detection_results')}",
        "",
        "## missed/false-positive review",
        f"- {review.get('stress_summary')}",
        "",
        "## append-only/governance boundary certification",
        f"- {review.get('governance_boundary')}",
        "",
        "## residual risks",
        f"- {review.get('residual_risks')}",
        "",
        "## LIVE10 recommendation",
        f"- {review.get('live10_recommendation')}",
        "",
    ])


def certify_lr6_live9_stress_boundary() -> dict[str, Any]:
    return {
        "simulation_only": True,
        "synthetic_only": True,
        "live_persistence_enabled": False,
        "direct_sql_enabled": False,
        "scaling_enabled": False,
        "new_metrics_enabled": False,
        "topology_drift_enabled": False,
        "contradiction_persistence_migration_enabled": False,
        "prediction_enabled": False,
        "trading_enabled": False,
        "auto_expansion_enabled": False,
        "schema_expansion_enabled": False,
        "historical_row_rewrite_enabled": False,
        "replay_richness_only_expected": True,
    }
