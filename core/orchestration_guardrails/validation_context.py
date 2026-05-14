from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict


@dataclass
class ValidationSummary:
    workflow_name: str | None
    github_run_id: str | None
    theme_name: str | None
    run_date_sgt: str | None
    validation_status: str
    warnings_count: int
    errors_count: int
    hard_fail_count: int
    source: str | None
    created_at_utc: str
    metadata: Dict[str, Any]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: str | Path) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: str | Path, payload: Dict[str, Any]) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


def build_validation_summary(
    context: Dict[str, Any],
    source: str,
    validation_status: str,
    warnings_count: int,
    errors_count: int,
    hard_fail_count: int,
) -> ValidationSummary:

    return ValidationSummary(
        workflow_name=context.get("workflow_name"),
        github_run_id=context.get("github_run_id"),
        theme_name=context.get("theme_name"),
        run_date_sgt=context.get("resolved_run_date_sgt"),
        validation_status=validation_status,
        warnings_count=warnings_count,
        errors_count=errors_count,
        hard_fail_count=hard_fail_count,
        source=source,
        created_at_utc=utc_now_iso(),
        metadata=context.get("metadata", {}),
    )


def summarize_validation(
    context_file: str,
    source: str,
    validation_status: str,
    warnings_count: int,
    errors_count: int,
    hard_fail_count: int,
    output_file: str,
) -> None:

    context = load_json(context_file)

    summary = build_validation_summary(
        context=context,
        source=source,
        validation_status=validation_status,
        warnings_count=warnings_count,
        errors_count=errors_count,
        hard_fail_count=hard_fail_count,
    )

    write_json(output_file, asdict(summary))
