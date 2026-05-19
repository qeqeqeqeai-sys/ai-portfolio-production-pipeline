from __future__ import annotations

from pathlib import Path

from .governance_history_summary import build_phase5c_summary
from .monitoring_history_context import load_phase5b_monitoring_context, stable_json_dumps
from .monitoring_snapshot_store import current_run_id, load_history, persist_append_only_snapshot
from .trend_analytics import analyze_monitoring_trends


def _write(path: str, payload: dict) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(stable_json_dumps(payload), encoding="utf-8")


def run_governance_monitoring_history() -> dict:
    context = load_phase5b_monitoring_context()
    run_id = current_run_id()
    artifacts = context["loaded_artifacts"]
    persist_append_only_snapshot(run_id, artifacts)
    history = load_history()
    trend = analyze_monitoring_trends(history)
    summary = build_phase5c_summary(context, trend, run_id, len(history))

    _write("logs/tier3h5_monitoring_history_context.json", context)
    _write("logs/tier3h5_governance_trend_analytics.json", trend)
    _write("logs/tier3h5_drift_frequency_summary.json", trend["trend_categories"]["drift_frequency"])
    _write("logs/tier3h5_orchestration_trend_summary.json", trend["trend_categories"]["orchestration"])
    _write("logs/tier3h5_artifact_trend_summary.json", trend["trend_categories"]["artifact"])
    _write("logs/tier3h5_readiness_trend_summary.json", trend["trend_categories"]["readiness"])
    _write("logs/tier3h5_phase5c_history_summary.json", summary)
    return summary
