from __future__ import annotations

from pathlib import Path

from .dashboard_export_reporting import build_dashboard_export_readiness
from .drift_reporting import build_drift_report
from .executive_summary_builder import build_executive_summary
from .governance_reporting_summary import build_reporting_summary
from .operational_health_reporting import classify_operational_health
from .readiness_reporting import build_readiness_report
from .release_confidence_reporting import classify_release_readiness
from .reporting_context import load_reporting_context, stable_json_dumps


def _write(path: str, payload: dict) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(stable_json_dumps(payload), encoding="utf-8")


def run_governance_operational_reporting() -> dict:
    context = load_reporting_context()
    health = classify_operational_health(context)
    readiness = build_readiness_report(context)
    drift = build_drift_report(context)
    dashboard = build_dashboard_export_readiness(context)
    release = classify_release_readiness(health, readiness, dashboard, context)
    executive = build_executive_summary(health, release)
    summary = build_reporting_summary(context, health, readiness, drift, dashboard, release)

    _write("logs/tier3h5_governance_reporting_context.json", context)
    _write("logs/tier3h5_operational_health_report.json", health)
    _write("logs/tier3h5_executive_readiness_summary.json", executive)
    _write("logs/tier3h5_drift_operational_report.json", drift)
    _write("logs/tier3h5_release_confidence_summary.json", release)
    _write("logs/tier3h5_dashboard_export_readiness.json", dashboard)
    _write("logs/tier3h5_phase5d_reporting_summary.json", summary)
    return summary
