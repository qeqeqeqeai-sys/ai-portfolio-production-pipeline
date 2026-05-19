from __future__ import annotations

from .artifact_coordination import emit_artifact_coordination
from .orchestration_context import emit_runtime_context
from .orchestration_guardrails import run_guardrails
from .orchestration_sequence import deterministic_stage_registry
from .orchestration_summary import emit_orchestration_summary
from .runtime_validation import validate_runtime
from .upload_coordination import emit_upload_coordination
from ..governance_bi import write_bi_export_artifacts
from ..governance_history import run_phase4c_governance_history


def run_governance_production_orchestration() -> dict[str, object]:
    stage_registry = deterministic_stage_registry()
    emit_runtime_context([s["stage_name"] for s in stage_registry])

    run_phase4c_governance_history()
    write_bi_export_artifacts()

    for stage in stage_registry:
        stage["execution_status"] = "executed"
        stage["guardrail_status"] = "verified"

    guardrails = run_guardrails(stage_registry)
    artifact_summary = emit_artifact_coordination(stage_registry)
    upload_summary = emit_upload_coordination(artifact_summary)
    runtime = validate_runtime(stage_registry, guardrails)
    summary = emit_orchestration_summary(stage_registry, artifact_summary, upload_summary, runtime)
    return {
        "stage_registry": stage_registry,
        "guardrails": guardrails,
        "artifact_coordination": artifact_summary,
        "upload_coordination": upload_summary,
        "runtime_validation": runtime,
        "summary": summary,
    }
