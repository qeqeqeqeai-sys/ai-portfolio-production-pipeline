"""Deterministic design guardrails for a future replay engine phase."""

from __future__ import annotations


_REQUIRED_GUARDRAILS = {
    "replay_must_be_explicitly_invoked": True,
    "replay_must_require_verified_export": True,
    "replay_must_require_replay_ready_contract": True,
    "replay_must_not_modify_source_export": True,
    "replay_must_not_mutate_manifest": True,
    "replay_must_not_call_scheduler": True,
    "replay_must_not_write_database": True,
    "replay_must_not_use_runtime_ids": True,
    "replay_must_not_use_timestamps": True,
    "replay_must_not_use_randomness": True,
    "replay_must_not_restore_artifacts_without_future_contract": True,
    "replay_must_preserve_tier4_tier5_isolation": True,
    "replay_must_emit_deterministic_report": True,
    "replay_must_have_no_hidden_external_state": True,
    "replay_engine_not_implemented_in_o1m": "confirmed",
}


def build_replay_engine_guardrails() -> dict:
    """Return deterministic replay design guardrails for O1M.

    This function is intentionally pure and side-effect free; it does not execute
    any replay behavior and serves as a static design-control checkpoint.
    """

    guardrails = dict(_REQUIRED_GUARDRAILS)

    failed_guardrails = sorted(
        guardrail_name
        for guardrail_name, guardrail_result in guardrails.items()
        if guardrail_result is False or guardrail_result == "failed"
    )
    warning_guardrails = sorted(
        guardrail_name
        for guardrail_name, guardrail_result in guardrails.items()
        if guardrail_result == "warning"
    )
    passed_guardrails = sorted(
        guardrail_name
        for guardrail_name in guardrails
        if guardrail_name not in failed_guardrails and guardrail_name not in warning_guardrails
    )

    guardrail_status = "passed" if not failed_guardrails else "failed"

    return {
        "guardrail_status": guardrail_status,
        "guardrail_scope": "future_replay_engine_design",
        "guardrails": guardrails,
        "passed_guardrails": passed_guardrails,
        "failed_guardrails": failed_guardrails,
        "warning_guardrails": warning_guardrails,
        "design_summary": {
            "total_guardrails": len(guardrails),
            "passed_guardrail_count": len(passed_guardrails),
            "failed_guardrail_count": len(failed_guardrails),
            "warning_guardrail_count": len(warning_guardrails),
            "replay_engine_allowed_to_execute_now": False,
            "future_replay_engine_requires_new_phase": True,
            "next_recommended_phase": "O1N — Deterministic Replay Engine Contract Preflight",
        },
    }
