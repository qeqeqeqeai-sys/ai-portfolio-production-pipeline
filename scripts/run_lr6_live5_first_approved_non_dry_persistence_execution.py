"""GitHub Actions runner for LR6-LIVE5 first approved non-dry persistence execution."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from transmission_layers.expectation_failure.replay_ecology.lr6_live3_first_tiny_governed_replay_ingestion_non_dry_execution import (
    ISOLATED_PERSISTENCE_TARGET,
    MAX_ENTITIES,
    REQUIRED_APPROVAL_PHRASE,
    REQUIRED_EXECUTION_TOKEN,
    TARGET_METRIC,
)
from transmission_layers.expectation_failure.replay_ecology.lr6_live5_first_approved_non_dry_persistence_execution_attempt import (
    build_lr6_live5_post_write_verification,
    execute_lr6_live5_approved_non_dry_attempt,
)
from transmission_layers.expectation_failure.replay_ecology.persistence.adapters import replay_richness_wave0_shadow_append_only_adapter as approved_adapter

RESULT_PATH = Path("outputs/lr6_live5_first_approved_non_dry_persistence_execution_result.json")
REPORT_PATH = Path("reports/lr6_live5_first_approved_non_dry_persistence_execution.md")
STATUS_BLOCKED_NO_ADAPTER = "APPROVED_EXECUTION_BLOCKED_NO_APPROVED_ADAPTER"
STATUS_GOVERNANCE_FAILURE = "APPROVED_EXECUTION_GOVERNANCE_FAILURE"
STATUS_MISSING_CREDENTIALS = "APPROVED_EXECUTION_BLOCKED_MISSING_CREDENTIALS"
STATUS_ADAPTER_SAFETY_FAILURE = "APPROVED_EXECUTION_BLOCKED_ADAPTER_SAFETY_FAILURE"


def _as_bool(value: str | bool | None) -> bool:
    return str(value).strip().lower() == "true"


def _build_entities(max_entities: int) -> list[dict[str, Any]]:
    return [{"entity_id": f"LIVE5_E{i}", "metric_dimension": TARGET_METRIC} for i in range(1, max_entities + 1)]


def _gate_inputs() -> dict[str, Any]:
    max_entities = int(os.getenv("LIVE5_MAX_ENTITIES", "0"))
    checks = {
        "approval_phrase_match": os.getenv("LIVE5_APPROVAL_PHRASE") == REQUIRED_APPROVAL_PHRASE,
        "execution_token_match": os.getenv("LIVE5_NON_DRY_EXECUTION_TOKEN") == REQUIRED_EXECUTION_TOKEN,
        "max_entities_leq_5": 0 < max_entities <= MAX_ENTITIES,
        "metric_target_replay_richness": os.getenv("LIVE5_METRIC_TARGET") == TARGET_METRIC,
        "persistence_target_isolated_shadow": os.getenv("LIVE5_PERSISTENCE_TARGET") == ISOLATED_PERSISTENCE_TARGET,
        "append_only_confirmation": _as_bool(os.getenv("LIVE5_APPEND_ONLY_CONFIRMATION")),
        "rollback_confirmation": _as_bool(os.getenv("LIVE5_ROLLBACK_CONFIRMATION")),
        "lineage_confirmation": _as_bool(os.getenv("LIVE5_LINEAGE_CONFIRMATION")),
    }
    return {"max_entities": max_entities, "checks": checks, "passed": all(checks.values())}


def _has_supabase_credentials() -> bool:
    return bool(os.getenv("SUPABASE_URL")) and bool(os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY"))


def _approved_append_only_adapter_available() -> bool:
    return approved_adapter.approved_adapter_available()


def _schema_confirmed() -> bool:
    return _as_bool(os.getenv("LIVE5_SCHEMA_CONFIRMED", "false"))


def _write_artifacts(payload: dict[str, Any]) -> None:
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report = ["# LR6-LIVE5 First Approved Non-Dry Persistence Execution", "", f"- status: {payload['status']}"]
    REPORT_PATH.write_text("\n".join(report) + "\n", encoding="utf-8")


def _build_adapter(client: Any):
    def _adapter(insert_intents: list[dict[str, Any]], meta: dict[str, Any]) -> dict[str, Any]:
        return approved_adapter.execute_append_only_insert(
            insert_intents=insert_intents,
            metadata={**meta, "metric_target": TARGET_METRIC, "append_only": True, "mode": "append_only_insert", "schema_confirmed": _schema_confirmed()},
            client=client,
        )
    return _adapter


def _default_client():
    from supabase import create_client  # type: ignore
    return create_client(os.environ["SUPABASE_URL"], os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.environ["SUPABASE_KEY"])


def main(*, supabase_client: Any = None) -> int:
    governance = _gate_inputs()
    base = {"attempted": False, "inserted_rows": 0, "simulated_sample_rows": 0, "governance": governance, "approved_adapter_available": _approved_append_only_adapter_available(), "post_write_verification": {}, "direct_sql_used": False}

    if not _has_supabase_credentials():
        _write_artifacts({**base, "status": STATUS_MISSING_CREDENTIALS})
        return 1
    if not governance["passed"]:
        _write_artifacts({**base, "status": STATUS_GOVERNANCE_FAILURE})
        return 1
    if not base["approved_adapter_available"]:
        _write_artifacts({**base, "status": STATUS_BLOCKED_NO_ADAPTER})
        return 1
    if not _schema_confirmed():
        _write_artifacts({**base, "status": STATUS_ADAPTER_SAFETY_FAILURE, "halt_reason": "schema_not_confirmed"})
        return 1

    client = supabase_client or _default_client()
    execution = execute_lr6_live5_approved_non_dry_attempt(entities=_build_entities(governance["max_entities"]), approval_phrase=os.environ["LIVE5_APPROVAL_PHRASE"], execution_token=os.environ["LIVE5_NON_DRY_EXECUTION_TOKEN"], persistence_adapter=_build_adapter(client))
    status = "APPROVED_EXECUTION_COMPLETED"
    if execution.get("adapter_result", {}).get("halt_triggered"):
        status = STATUS_ADAPTER_SAFETY_FAILURE
    payload = {**base, "status": status, "attempted": bool(execution.get("persistence_attempted", False)), "inserted_rows": int(execution.get("inserted_rows", 0)), "simulated_sample_rows": len(execution.get("payload_preparation", {}).get("prepared_payloads", [])), "post_write_verification": build_lr6_live5_post_write_verification(execution)}
    _write_artifacts(payload)
    return 0 if status == "APPROVED_EXECUTION_COMPLETED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
