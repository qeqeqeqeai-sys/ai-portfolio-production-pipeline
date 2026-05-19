from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .monitoring_history_context import stable_json_dumps


HISTORY_ROOT = Path("logs/history/tier3h5_monitoring")


def current_run_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d")


def persist_append_only_snapshot(run_id: str, artifacts: dict[str, Any]) -> Path:
    run_dir = HISTORY_ROOT / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    for name, payload in artifacts.items():
        target = run_dir / name
        if target.exists():
            continue
        target.write_text(stable_json_dumps(payload), encoding="utf-8")
    return run_dir


def load_history(limit: int = 20) -> list[dict[str, Any]]:
    if not HISTORY_ROOT.exists():
        return []
    runs: list[dict[str, Any]] = []
    for run_dir in sorted((p for p in HISTORY_ROOT.iterdir() if p.is_dir()), key=lambda p: p.name):
        summary = run_dir / "monitoring_summary.json"
        if not summary.exists():
            continue
        runs.append({"run_id": run_dir.name, "monitoring_summary": summary.read_text(encoding="utf-8")})
    return runs[-limit:]
