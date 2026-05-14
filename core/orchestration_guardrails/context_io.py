from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from core.orchestration_guardrails.execution_context import ExecutionContext


def ensure_parent_dir(path: str | Path) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)


def write_json(path: str | Path, payload: dict[str, Any]) -> None:
    ensure_parent_dir(path)

    with Path(path).open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, sort_keys=True)


def read_json(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as f:
        return json.load(f)


def write_context(path: str | Path, context: ExecutionContext) -> None:
    write_json(path, context.to_dict())


def read_context(path: str | Path) -> ExecutionContext:
    payload = read_json(path)
    return ExecutionContext.from_dict(payload)


def extract_field_from_json(path: str | Path, field: str) -> Any:
    payload = read_json(path)

    if field not in payload:
        raise KeyError(f"Field '{field}' not found in JSON file: {path}")

    return payload[field]


def append_github_env(env_file: str | Path, values: dict[str, str]) -> None:
    """
    Append key/value pairs to GitHub Actions env file.

    This is intentionally simple and conservative.
    """
    ensure_parent_dir(env_file)

    with Path(env_file).open("a", encoding="utf-8") as f:
        for key, value in values.items():
            safe_value = "" if value is None else str(value)
            f.write(f"{key}={safe_value}\n")
