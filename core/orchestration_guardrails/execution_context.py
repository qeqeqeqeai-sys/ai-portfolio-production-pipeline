from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any

from core.orchestration_guardrails.run_date import (
    SGT_TIMEZONE,
    resolve_run_date_sgt,
)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class ExecutionContext:
    workflow_name: str
    github_run_id: str
    run_mode: str
    theme_name: str = "ai"
    requested_run_date_sgt: str = ""
    resolved_run_date_sgt: str = ""
    timezone: str = SGT_TIMEZONE
    created_at_utc: str = field(default_factory=utc_now_iso)
    updated_at_utc: str = field(default_factory=utc_now_iso)
    status: str = "resolved"
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def resolve(
        cls,
        workflow_name: str,
        github_run_id: str,
        run_mode: str,
        theme_name: str = "ai",
        requested_run_date_sgt: str | None = "",
        metadata: dict[str, Any] | None = None,
    ) -> "ExecutionContext":
        resolved = resolve_run_date_sgt(requested_run_date_sgt)

        return cls(
            workflow_name=workflow_name,
            github_run_id=str(github_run_id or ""),
            run_mode=str(run_mode or ""),
            theme_name=str(theme_name or "ai"),
            requested_run_date_sgt=str(requested_run_date_sgt or ""),
            resolved_run_date_sgt=resolved,
            metadata=metadata or {},
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ExecutionContext":
        return cls(
            workflow_name=str(payload.get("workflow_name", "")),
            github_run_id=str(payload.get("github_run_id", "")),
            run_mode=str(payload.get("run_mode", "")),
            theme_name=str(payload.get("theme_name", "ai")),
            requested_run_date_sgt=str(payload.get("requested_run_date_sgt", "")),
            resolved_run_date_sgt=str(payload.get("resolved_run_date_sgt", "")),
            timezone=str(payload.get("timezone", SGT_TIMEZONE)),
            created_at_utc=str(payload.get("created_at_utc", utc_now_iso())),
            updated_at_utc=str(payload.get("updated_at_utc", utc_now_iso())),
            status=str(payload.get("status", "resolved")),
            metadata=dict(payload.get("metadata", {}) or {}),
        )

    def update_field(self, target_field: str, value: Any) -> None:
        """
        Update a supported top-level field safely.
        """
        if not hasattr(self, target_field):
            raise ValueError(f"Unsupported execution context field: {target_field}")

        setattr(self, target_field, value)
        self.updated_at_utc = utc_now_iso()

    def update_metadata(self, key: str, value: Any) -> None:
        self.metadata[key] = value
        self.updated_at_utc = utc_now_iso()

    def github_env_vars(self, context_file: str) -> dict[str, str]:
        """
        Safe GitHub environment variables.
        """
        return {
            "EXECUTION_CONTEXT_FILE": context_file,
            "RUN_DATE_SGT": self.resolved_run_date_sgt,
            "THEME_NAME": self.theme_name,
            "GITHUB_RUN_ID": self.github_run_id,
        }
