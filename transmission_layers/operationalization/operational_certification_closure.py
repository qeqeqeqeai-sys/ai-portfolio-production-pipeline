"""Deterministic unified operational certification closure (Operationalization O3)."""

from __future__ import annotations

from pathlib import Path

from .recovery_historical_closure import run_recovery_historical_closure
from .replay_observability_closure import run_replay_observability_closure
from .serialization import stable_checksum

_ALLOWED_STATUSES = {"certified", "certified_with_findings", "degraded", "blocked", "invalid_input"}
_ALLOWED_TRUST_STATUSES = {"operationally_trusted", "trusted_with_findings", "not_trusted", "invalid_input"}


_STATUS_RANK = {
    "invalid_input": 0,
    "blocked": 1,
    "degraded": 2,
    "certified_with_findings": 3,
    "certified": 4,
}

_GATE_ORDER = [
    "replay_determinism",
    "checksum_stability",
    "immutable_input_safety",
    "observability_completeness",
    "recovery_safety",
    "historical_reconstruction_sufficiency",
    "no_runtime_replay_execution",
    "no_artifact_restore",
    "no_external_mutation",
    "no_prediction",
    "no_optimization",
    "no_adaptive_control",
    "additive_only_operational_architecture",
]


def _passes(status: str, accepted: set[str]) -> bool:
    return status in accepted


def _gate(name: str, passed: bool, reason: str) -> dict:
    return {"gate": name, "result": "PASS" if passed else "FAIL", "reason": reason}


def build_operational_certification_gates(export_path: str | Path) -> dict:
    """Build deterministic O3 certification gates from O1/O2 closure outputs."""

    path = Path(export_path)
    o1 = run_replay_observability_closure(path)
    o2 = run_recovery_historical_closure(path)

    o1_status = o1.get("status", "invalid_input")
    o2_status = o2.get("status", "invalid_input")

    replay_determinism = o1.get("replay_integrity", {}).get("deterministic_repeated_output") is True
    checksum_stability = o1.get("replay_integrity", {}).get("replay_plan_checksum_stable") is True
    immutable_input_safety = (
        o1.get("invariants", {}).get("mutates_external_state") is False
        and o2.get("invariants", {}).get("mutates_external_state") is False
    )
    observability_completeness = _passes(o1_status, {"ready", "degraded"})
    recovery_safety = _passes(o2.get("recovery_safety", {}).get("status", "invalid_input"), {"ready", "degraded"})
    historical_reconstruction_sufficiency = _passes(
        o2.get("historical_reconstruction", {}).get("status", "invalid_input"), {"ready", "degraded"}
    )

    invariant_passes = {
        "no_runtime_replay_execution": (
            o1.get("invariants", {}).get("executes_runtime_logic") is False
            and o2.get("invariants", {}).get("executes_runtime_logic") is False
        ),
        "no_artifact_restore": (
            o1.get("invariants", {}).get("restores_artifacts") is False
            and o2.get("invariants", {}).get("restores_artifacts") is False
        ),
        "no_external_mutation": immutable_input_safety,
        "no_prediction": (
            o1.get("invariants", {}).get("uses_prediction") is False
            and o2.get("invariants", {}).get("uses_prediction") is False
        ),
        "no_optimization": (
            o1.get("invariants", {}).get("uses_optimization") is False
            and o2.get("invariants", {}).get("uses_optimization") is False
        ),
        "no_adaptive_control": (
            o1.get("invariants", {}).get("uses_adaptive_control") is False
            and o2.get("invariants", {}).get("uses_adaptive_control") is False
        ),
        "additive_only_operational_architecture": True,
    }

    gate_map = {
        "replay_determinism": _gate("replay_determinism", replay_determinism, "O1 deterministic repeated output."),
        "checksum_stability": _gate("checksum_stability", checksum_stability, "O1 replay-plan checksum stability."),
        "immutable_input_safety": _gate(
            "immutable_input_safety", immutable_input_safety, "O1/O2 read-only invariants require no external mutation."
        ),
        "observability_completeness": _gate(
            "observability_completeness", observability_completeness, "O1 observability closure status in ready/degraded band."
        ),
        "recovery_safety": _gate(
            "recovery_safety", recovery_safety, "O2 recovery safety status in ready/degraded band."
        ),
        "historical_reconstruction_sufficiency": _gate(
            "historical_reconstruction_sufficiency",
            historical_reconstruction_sufficiency,
            "O2 historical reconstruction status in ready/degraded band.",
        ),
    }
    for name, passed in invariant_passes.items():
        gate_map[name] = _gate(name, passed, "Deterministic bounded operational invariant.")

    gates = [gate_map[name] for name in _GATE_ORDER]
    passed_count = len([gate for gate in gates if gate["result"] == "PASS"])
    failed_count = len(gates) - passed_count

    return {
        "status": "ready" if failed_count == 0 else "blocked",
        "gate_order": list(_GATE_ORDER),
        "gates": gates,
        "passed_gate_count": passed_count,
        "failed_gate_count": failed_count,
        "o1_status": o1_status,
        "o2_status": o2_status,
        "allowed_statuses": sorted(_ALLOWED_STATUSES),
        "allowed_trust_statuses": sorted(_ALLOWED_TRUST_STATUSES),
    }


def run_operational_certification_closure(export_path: str | Path) -> dict:
    """Run deterministic O3 certification closure by aggregating O1 and O2 outputs."""

    path = Path(export_path)
    try:
        o1 = run_replay_observability_closure(path)
        o2 = run_recovery_historical_closure(path)
        gates_report = build_operational_certification_gates(path)

        statuses = [o1.get("status", "invalid_input"), o2.get("status", "invalid_input")]
        has_invalid_input = "invalid_input" in statuses
        has_blocked = "blocked" in statuses
        has_degraded = "degraded" in statuses

        all_gates_pass = gates_report.get("failed_gate_count", 1) == 0

        if has_invalid_input:
            status = "invalid_input"
            trust_status = "invalid_input"
        elif has_blocked:
            status = "blocked"
            trust_status = "not_trusted"
        elif has_degraded:
            status = "certified_with_findings" if all_gates_pass else "degraded"
            trust_status = "trusted_with_findings" if all_gates_pass else "not_trusted"
        else:
            status = "certified" if all_gates_pass else "degraded"
            trust_status = "operationally_trusted" if all_gates_pass else "not_trusted"

        if status not in _ALLOWED_STATUSES:
            status = "invalid_input"
            trust_status = "invalid_input"

        diagnostics = sorted(
            set(o1.get("diagnostics", []))
            | set(o2.get("diagnostics", []))
            | set([gate["gate"] for gate in gates_report.get("gates", []) if gate.get("result") == "FAIL"])
        )

    except Exception:
        o1 = {
            "closure_phase": "O1_replay_observability_closure",
            "status": "invalid_input",
            "diagnostics": ["invalid_export_input"],
        }
        o2 = {
            "closure_phase": "O2_recovery_historical_closure",
            "status": "invalid_input",
            "diagnostics": ["invalid_export_input"],
        }
        gates_report = {
            "status": "blocked",
            "gate_order": list(_GATE_ORDER),
            "gates": [_gate(name, False, "Invalid input prevents deterministic certification.") for name in _GATE_ORDER],
            "passed_gate_count": 0,
            "failed_gate_count": len(_GATE_ORDER),
        }
        status = "invalid_input"
        trust_status = "invalid_input"
        diagnostics = ["invalid_export_input"]

    invariants = {
        "executes_runtime_logic": False,
        "restores_artifacts": False,
        "mutates_external_state": False,
        "uses_prediction": False,
        "uses_optimization": False,
        "uses_adaptive_control": False,
    }

    operational_closure_complete = status in {"certified", "certified_with_findings"}

    result = {
        "closure_phase": "O3_operational_certification_closure",
        "status": status,
        "certification": {
            "trust_status": trust_status,
            "operational_closure_complete": operational_closure_complete,
            "gates": gates_report.get("gates", []),
        },
        "o1_replay_observability": o1,
        "o2_recovery_historical": o2,
        "closure_boundary": {
            "further_operationalization_allowed": not operational_closure_complete,
            "allowed_only_for_intelligence_risk_gap": True,
            "prevents_infrastructure_sprawl": True,
        },
        "diagnostics": sorted(diagnostics),
        "invariants": invariants,
    }
    result["checksum"] = stable_checksum(result, prefix="o3_closure")
    return result
