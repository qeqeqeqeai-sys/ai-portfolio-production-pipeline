from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from .drift_diagnostics import run_drift_diagnostics, write_diagnostics_files
from .monitoring_context import load_monitoring_context, stable_json_dumps, write_monitoring_context
from .monitoring_summary import build_monitoring_summary, write_monitoring_summary


def run_governance_production_monitoring() -> dict[str, object]:
    context = load_monitoring_context()
    diagnostics = run_drift_diagnostics(context)
    summary = build_monitoring_summary(context, diagnostics)
    write_monitoring_context(context)
    write_diagnostics_files(diagnostics)
    write_monitoring_summary(summary)

    run_id = datetime.now(timezone.utc).strftime("%Y%m%d")
    history_dir = Path("logs/history/tier3h5_monitoring") / run_id
    history_dir.mkdir(parents=True, exist_ok=True)
    (history_dir / "tier3h5_phase5b_monitoring_summary.json").write_text(stable_json_dumps(summary), encoding="utf-8")
    return summary
