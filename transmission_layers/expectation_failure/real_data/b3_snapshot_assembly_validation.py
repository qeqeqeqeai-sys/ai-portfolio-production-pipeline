"""B3 deterministic validation for B2 candidate -> B1 snapshot assembly."""

from __future__ import annotations

from copy import deepcopy

from .b1_benchmark_registry import FIXED_BENCHMARK_ORDER
from .b1_real_entity_registry import FIXED_ENTITY_ORDER
from .b3_snapshot_input_mapper import METRIC_POLICY


def validate_b3_candidate_for_assembly(candidate: dict) -> dict:
    frozen = deepcopy(candidate)
    accepted = frozen.get("accepted_records")
    known_symbols = set(FIXED_ENTITY_ORDER) | set(FIXED_BENCHMARK_ORDER)
    supported_metrics = set(METRIC_POLICY["required_for_certified"]) | set(METRIC_POLICY["required_for_degraded"])

    symbol_ok = isinstance(accepted, list) and all(r.get("symbol") in known_symbols for r in accepted)
    metrics_ok = isinstance(accepted, list) and all(r.get("metric_name") in supported_metrics for r in accepted)
    checksum_ok = bool(frozen.get("deterministic_checksum"))
    has_accepted = isinstance(accepted, list)
    quarantine_visible = "quarantined_records" in frozen

    gates = {
        "b2_checksum_present": checksum_ok,
        "accepted_records_present": has_accepted,
        "symbols_in_b1_registries": symbol_ok,
        "supported_metrics_only": metrics_ok,
        "required_metric_policy_defined": True,
        "benchmark_coverage_visible": "benchmark_coverage_summary" in frozen,
        "quarantine_visibility_preserved": quarantine_visible,
        "no_live_network_behavior": frozen.get("operating_constraints", {}).get("network_calls") == "none",
        "no_write_behavior": frozen.get("operating_constraints", {}).get("database_writes") == "none",
        "no_trading_prediction_behavior": "trading" in frozen.get("forbidden_capabilities", []) and "prediction" in frozen.get("forbidden_capabilities", []),
    }
    blocked = not all(gates.values())
    degraded = bool(frozen.get("quarantined_records")) or bool(frozen.get("degraded_input_flags"))
    return {
        "validation_stage": "B3_SNAPSHOT_ASSEMBLY_VALIDATION",
        "gates": gates,
        "status": "BLOCKED" if blocked else ("DEGRADED" if degraded else "PASS"),
    }
