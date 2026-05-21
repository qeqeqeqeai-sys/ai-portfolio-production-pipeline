"""Deterministic replay engine dry-run executor (Operationalization O1O)."""

from __future__ import annotations

from pathlib import Path

from .replay_contract import build_replay_plan_skeleton
from .replay_preflight import build_replay_engine_preflight


def _project_step(step: dict) -> dict:
    return {
        "step_name": step.get("step_name"),
        "status": step.get("status"),
        "executes_runtime_logic": step.get("executes_runtime_logic") is True,
    }


def execute_replay_dry_run(export_path: str | Path) -> dict:
    """Execute deterministic replay dry-run simulation without runtime replay execution."""

    path = Path(export_path)
    preflight = build_replay_engine_preflight(path)
    replay_plan = build_replay_plan_skeleton(path)

    replay_steps = replay_plan.get("replay_steps", [])
    projected_steps = [_project_step(step) for step in replay_steps]

    ready = replay_plan.get("plan_status") == "ready"

    deferred_steps = [step for step in projected_steps if step.get("status") == "deferred"]
    non_deferred_steps = [step for step in projected_steps if step.get("status") != "deferred"]

    executed_steps = non_deferred_steps if ready else []
    blocked_steps = [] if ready else non_deferred_steps

    runtime_logic_executed = any(step.get("executes_runtime_logic") is True for step in executed_steps)

    simulated_execution = {
        "simulation_status": "simulated" if ready else "blocked",
        "runtime_logic_executed": runtime_logic_executed,
        "artifacts_restored": False,
        "intelligence_layers_executed": False,
        "executed_steps": executed_steps,
        "deferred_steps": deferred_steps,
        "blocked_steps": blocked_steps,
    }

    execution_summary = {
        "total_replay_steps": len(projected_steps),
        "executed_step_count": len(executed_steps),
        "deferred_step_count": len(deferred_steps),
        "blocked_step_count": len(blocked_steps),
        "plan_status": replay_plan.get("plan_status"),
        "preflight_status": preflight.get("preflight_status"),
        "simulation_status": simulated_execution["simulation_status"],
        "runtime_logic_executed": simulated_execution["runtime_logic_executed"],
        "artifacts_restored": simulated_execution["artifacts_restored"],
        "intelligence_layers_executed": simulated_execution["intelligence_layers_executed"],
    }

    execution_status = "simulated" if ready else "blocked"

    return {
        "execution_status": execution_status,
        "execution_mode": "dry_run",
        "replay_execution_enabled": False,
        "export_path": str(path),
        "export_filename": path.name,
        "preflight": preflight,
        "replay_plan": replay_plan,
        "simulated_execution": simulated_execution,
        "execution_summary": execution_summary,
    }
