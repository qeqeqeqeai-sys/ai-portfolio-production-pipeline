from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class ValidationSummary:
    workflow_name: Optional[str]
    github_run_id: Optional[str]
    theme_name: Optional[str]
    run_date_sgt: Optional[str]
    validation_status: str
    warnings_count: int
    errors_count: int
    hard_fail_count: int
    source: Optional[str]
    created_at_utc: str
    metadata: Dict[str, Any]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: str | Path) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def maybe_load_json(path: str | Path | None) -> Optional[Dict[str, Any]]:
    if not path:
        return None

    candidate = Path(path)
    if not candidate.exists():
        return None

    return load_json(candidate)


def write_json(path: str | Path, payload: Dict[str, Any]) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


def _blank_to_none(value: Any) -> Any:
    if isinstance(value, str) and value.strip() == "":
        return None
    return value


def _stringify(value: Any) -> Optional[str]:
    value = _blank_to_none(value)
    if value is None:
        return None
    return str(value)


def _first_non_empty(*values: Any) -> Optional[str]:
    for value in values:
        value = _stringify(value)
        if value:
            return value
    return None


def build_validation_summary(
    context: Dict[str, Any],
    source: str,
    validation_status: str,
    warnings_count: int,
    errors_count: int,
    hard_fail_count: int,
) -> ValidationSummary:
    return ValidationSummary(
        workflow_name=_stringify(context.get("workflow_name")),
        github_run_id=_stringify(context.get("github_run_id")),
        theme_name=_stringify(context.get("theme_name")),
        run_date_sgt=_stringify(context.get("resolved_run_date_sgt")),
        validation_status=validation_status,
        warnings_count=warnings_count,
        errors_count=errors_count,
        hard_fail_count=hard_fail_count,
        source=source,
        created_at_utc=utc_now_iso(),
        metadata=context.get("metadata", {}) or {},
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


def check_env_consistency(
    context_file: str,
    run_date_sgt: str = "",
    github_run_id: str = "",
    theme_name: str = "",
    workflow_name: str = "",
    validation_summary_file: str = "",
    telemetry_snapshot_file: str = "",
    artifact_manifest_file: str = "",
) -> List[str]:
    """
    Advisory-only consistency checks for Tier 3D.1.

    This function intentionally returns warnings instead of raising errors for
    data mismatches. A missing or unreadable context file is still a true runtime
    error and should be allowed to fail the CLI command.
    """
    warnings: List[str] = []

    context = load_json(context_file)
    validation_summary = maybe_load_json(validation_summary_file)
    telemetry_snapshot = maybe_load_json(telemetry_snapshot_file)
    artifact_manifest = maybe_load_json(artifact_manifest_file)

    env_run_date_sgt = _first_non_empty(run_date_sgt, os.getenv("RUN_DATE_SGT"))
    env_github_run_id = _first_non_empty(github_run_id, os.getenv("GITHUB_RUN_ID"))
    env_theme_name = _first_non_empty(theme_name, os.getenv("THEME_NAME"))
    env_workflow_name = _first_non_empty(workflow_name, os.getenv("GITHUB_WORKFLOW"))

    context_run_date = _stringify(context.get("resolved_run_date_sgt"))
    context_requested_run_date = _stringify(context.get("requested_run_date_sgt"))
    context_github_run_id = _stringify(context.get("github_run_id"))
    context_theme_name = _stringify(context.get("theme_name"))
    context_workflow_name = _stringify(context.get("workflow_name"))
    context_status = _stringify(context.get("status"))

    if not context_run_date:
        warnings.append("execution_context.resolved_run_date_sgt is missing")

    if not context_github_run_id:
        warnings.append("execution_context.github_run_id is missing")

    if not context_theme_name:
        warnings.append("execution_context.theme_name is missing")

    if not context_workflow_name:
        warnings.append("execution_context.workflow_name is missing")

    if not context_status:
        warnings.append("execution_context.status is missing")

    if env_run_date_sgt and context_run_date and env_run_date_sgt != context_run_date:
        warnings.append(
            "RUN_DATE_SGT differs from execution_context.resolved_run_date_sgt "
            f"env={env_run_date_sgt} context={context_run_date}"
        )

    if env_github_run_id and context_github_run_id and env_github_run_id != context_github_run_id:
        warnings.append(
            "GITHUB_RUN_ID differs from execution_context.github_run_id "
            f"env={env_github_run_id} context={context_github_run_id}"
        )

    if env_theme_name and context_theme_name and env_theme_name != context_theme_name:
        warnings.append(
            "THEME_NAME differs from execution_context.theme_name "
            f"env={env_theme_name} context={context_theme_name}"
        )

    if env_workflow_name and context_workflow_name and env_workflow_name != context_workflow_name:
        warnings.append(
            "GITHUB_WORKFLOW differs from execution_context.workflow_name "
            f"env={env_workflow_name} context={context_workflow_name}"
        )

    if context_requested_run_date and context_run_date and context_requested_run_date != context_run_date:
        warnings.append(
            "requested_run_date_sgt differs from resolved_run_date_sgt "
            f"requested={context_requested_run_date} resolved={context_run_date}"
        )

    if validation_summary is not None:
        validation_run_date = _stringify(validation_summary.get("run_date_sgt"))
        validation_github_run_id = _stringify(validation_summary.get("github_run_id"))
        validation_theme_name = _stringify(validation_summary.get("theme_name"))
        validation_workflow_name = _stringify(validation_summary.get("workflow_name"))
        validation_status = _stringify(validation_summary.get("validation_status"))

        if not validation_status:
            warnings.append("validation_summary.validation_status is missing")

        if context_run_date and validation_run_date and validation_run_date != context_run_date:
            warnings.append(
                "validation_summary.run_date_sgt differs from execution_context.resolved_run_date_sgt "
                f"validation={validation_run_date} context={context_run_date}"
            )

        if context_github_run_id and validation_github_run_id and validation_github_run_id != context_github_run_id:
            warnings.append(
                "validation_summary.github_run_id differs from execution_context.github_run_id "
                f"validation={validation_github_run_id} context={context_github_run_id}"
            )

        if context_theme_name and validation_theme_name and validation_theme_name != context_theme_name:
            warnings.append(
                "validation_summary.theme_name differs from execution_context.theme_name "
                f"validation={validation_theme_name} context={context_theme_name}"
            )

        if context_workflow_name and validation_workflow_name and validation_workflow_name != context_workflow_name:
            warnings.append(
                "validation_summary.workflow_name differs from execution_context.workflow_name "
                f"validation={validation_workflow_name} context={context_workflow_name}"
            )

    if telemetry_snapshot is not None:
        telemetry_run_date = _stringify(telemetry_snapshot.get("resolved_run_date_sgt"))
        telemetry_github_run_id = _stringify(telemetry_snapshot.get("github_run_id"))
        telemetry_theme_name = _stringify(telemetry_snapshot.get("theme_name"))
        telemetry_workflow_name = _stringify(telemetry_snapshot.get("workflow_name"))
        pipeline_status = _stringify(telemetry_snapshot.get("pipeline_status"))

        if not pipeline_status:
            warnings.append("telemetry_snapshot.pipeline_status is missing")

        if context_run_date and telemetry_run_date and telemetry_run_date != context_run_date:
            warnings.append(
                "telemetry_snapshot.resolved_run_date_sgt differs from execution_context.resolved_run_date_sgt "
                f"telemetry={telemetry_run_date} context={context_run_date}"
            )

        if context_github_run_id and telemetry_github_run_id and telemetry_github_run_id != context_github_run_id:
            warnings.append(
                "telemetry_snapshot.github_run_id differs from execution_context.github_run_id "
                f"telemetry={telemetry_github_run_id} context={context_github_run_id}"
            )

        if context_theme_name and telemetry_theme_name and telemetry_theme_name != context_theme_name:
            warnings.append(
                "telemetry_snapshot.theme_name differs from execution_context.theme_name "
                f"telemetry={telemetry_theme_name} context={context_theme_name}"
            )

        if context_workflow_name and telemetry_workflow_name and telemetry_workflow_name != context_workflow_name:
            warnings.append(
                "telemetry_snapshot.workflow_name differs from execution_context.workflow_name "
                f"telemetry={telemetry_workflow_name} context={context_workflow_name}"
            )

    if artifact_manifest is not None:
        manifest_run_date = _stringify(artifact_manifest.get("run_date_sgt"))
        manifest_github_run_id = _stringify(artifact_manifest.get("github_run_id"))
        manifest_theme_name = _stringify(artifact_manifest.get("theme_name"))
        manifest_workflow_name = _stringify(artifact_manifest.get("workflow_name"))

        if context_run_date and manifest_run_date and manifest_run_date != context_run_date:
            warnings.append(
                "artifact_manifest.run_date_sgt differs from execution_context.resolved_run_date_sgt "
                f"manifest={manifest_run_date} context={context_run_date}"
            )

        if context_github_run_id and manifest_github_run_id and manifest_github_run_id != context_github_run_id:
            warnings.append(
                "artifact_manifest.github_run_id differs from execution_context.github_run_id "
                f"manifest={manifest_github_run_id} context={context_github_run_id}"
            )

        if context_theme_name and manifest_theme_name and manifest_theme_name != context_theme_name:
            warnings.append(
                "artifact_manifest.theme_name differs from execution_context.theme_name "
                f"manifest={manifest_theme_name} context={context_theme_name}"
            )

        if context_workflow_name and manifest_workflow_name and manifest_workflow_name != context_workflow_name:
            warnings.append(
                "artifact_manifest.workflow_name differs from execution_context.workflow_name "
                f"manifest={manifest_workflow_name} context={context_workflow_name}"
            )

    return warnings
