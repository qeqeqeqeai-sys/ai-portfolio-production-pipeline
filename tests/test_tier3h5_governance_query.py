import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from transmission_layers.asset_discovery.tier3h5.governance_history.hashing import stable_hash
from transmission_layers.asset_discovery.tier3h5.governance_query import (
    build_dashboard_views,
    query_governance_explainability,
    query_governance_incidents,
    query_governance_trends,
    query_lineage_instability_history,
    query_replay_instability_history,
    write_dashboard_artifacts,
)
from transmission_layers.asset_discovery.tier3h5.governance_query.dashboard_views import dashboard_history_status
from transmission_layers.asset_discovery.tier3h5.governance_query.serialization import stable_json_dumps


def _write(path: str, payload: dict) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")


def _read(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _seed_history() -> None:
    _write("logs/tier3h5_governance_incident_history.json", {
        "history": [
            {"incident_key": "b", "category": "lineage_integrity_incident", "severity": "governance_risk", "entity": "issuer-2", "registry_source": "xnys", "run_date_sgt": "2026-05-18", "replay_mode": "advisory_only", "enforcement_enabled": False},
            {"incident_key": "a", "category": "replay_governance_incident", "severity": "advisory_attention", "entity": "issuer-1", "registry_source": "xnas", "run_date_sgt": "2026-05-17", "replay_mode": "advisory_only", "enforcement_enabled": False},
            {"incident_key": "c", "category": "normalization_governance_incident", "severity": "critical_governance_instability", "entity": "issuer-3", "registry_source": "xnas", "run_date_sgt": "2026-05-19", "replay_mode": "advisory_only", "enforcement_enabled": False},
        ],
        "replay_mode": "advisory_only",
        "enforcement_enabled": False,
    })
    _write("logs/tier3h5_governance_escalation_history.json", {"history": [{"escalation_status": "advisory_review", "governance_review_recommended": True}], "replay_mode": "advisory_only", "enforcement_enabled": False})
    _write("logs/tier3h5_governance_watchlist_history.json", {"history": [{"watchlist_name": "persistent_governance", "watchlist_count": 2}], "replay_mode": "advisory_only", "enforcement_enabled": False})
    _write("logs/tier3h5_governance_trend_history.json", {"history": [{"governance_trend_status": "degrading", "escalation_trend_status": "stable", "replay_stability_trend": "degrading", "lineage_stability_trend": "stable", "normalization_drift_trend": "degrading", "provenance_quality_trend": "insufficient_history", "run_date_sgt": "2026-05-19", "replay_mode": "advisory_only", "enforcement_enabled": False}], "replay_mode": "advisory_only", "enforcement_enabled": False})
    _write("logs/tier3h5_governance_continuity_history.json", {"history": [{"historical_continuity_status": "unresolved_governance_risk", "persistent_incident_count": 1, "recurring_incident_count": 0, "transient_incident_count": 1, "run_date_sgt": "2026-05-19", "replay_mode": "advisory_only", "enforcement_enabled": False}], "replay_mode": "advisory_only", "enforcement_enabled": False})
    _write("logs/tier3h5_governance_history_explainability.json", {
        "persistence_explanation": {"source": "persisted_governance_history_only"},
        "trend_explanation": {"governance_trend_status": "degrading"},
        "continuity_explanation": {"historical_continuity_status": "unresolved_governance_risk"},
        "lifecycle_explanation": {"mutation_performed": False},
        "replay_mode": "advisory_only",
        "enforcement_enabled": False,
    })


def test_query_filters_are_exact_stably_sorted_and_paginated(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    _seed_history()

    first = query_governance_incidents(registry_source="xnas", start_date="2026-05-17", end_date="2026-05-19", page_size=1)
    second = query_governance_incidents(registry_source="xnas", start_date="2026-05-17", end_date="2026-05-19", page_size=1)

    assert first == second
    assert first["total_rows"] == 2
    assert first["rows"][0]["incident_key"] == "a"
    assert query_governance_incidents(entity_id="issuer")["total_rows"] == 0
    assert query_governance_incidents(entity_id="issuer-1")["total_rows"] == 1
    assert query_replay_instability_history()["rows"][0]["category"] == "replay_governance_incident"
    assert query_lineage_instability_history()["rows"][0]["category"] == "lineage_integrity_incident"
    assert first["replay_mode"] == "advisory_only"
    assert first["enforcement_enabled"] is False


def test_dashboard_views_are_deterministic_advisory_only_and_export_ready(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    _seed_history()

    first = build_dashboard_views(window=10)
    second = build_dashboard_views(window=10)
    artifacts = write_dashboard_artifacts(window=10)

    assert first == second == artifacts
    operational = artifacts["operational_summary"]
    assert operational["replay_mode"] == "advisory_only"
    assert operational["enforcement_enabled"] is False
    assert operational["canonical_override_enabled"] is False
    assert operational["scoring_mutation_enabled"] is False
    assert operational["propagation_mutation_enabled"] is False
    assert operational["governance_history_depth"] == 3
    assert operational["unresolved_governance_totals"] == 2
    assert operational["replay_instability_totals"] == 1
    assert operational["lineage_instability_totals"] == 1
    assert operational["dashboard_view_hash"] == stable_hash(operational)
    assert stable_json_dumps(operational) == stable_json_dumps(operational)
    for path in [
        "logs/tier3h5_dashboard_governance_summary.json",
        "logs/tier3h5_dashboard_governance_trends.json",
        "logs/tier3h5_dashboard_watchlist_summary.json",
        "logs/tier3h5_dashboard_continuity_summary.json",
        "logs/tier3h5_dashboard_escalation_summary.json",
        "logs/tier3h5_dashboard_operational_summary.json",
    ]:
        assert _read(path)["replay_mode"] == "advisory_only"


def test_explainability_query_reads_persisted_history_without_mutation(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    _seed_history()
    before = _read("logs/tier3h5_governance_history_explainability.json")

    first = query_governance_explainability()
    trend = query_governance_explainability("trend_explanation")
    unknown = query_governance_explainability("semantic_explanation")

    assert first["explanations"]["persistence_explanation"]["source"] == "persisted_governance_history_only"
    assert trend["explanations"]["trend_explanation"]["governance_trend_status"] == "degrading"
    assert unknown["explanations"] == {}
    assert _read("logs/tier3h5_governance_history_explainability.json") == before


def test_sparse_dashboard_history_gracefully_degrades(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)

    empty = build_dashboard_views()
    assert empty["governance_summary"]["dashboard_history_status"] == "insufficient_dashboard_history"
    assert query_governance_trends()["total_rows"] == 0
    assert dashboard_history_status(1) == "dashboard_history_initializing"
    assert dashboard_history_status(2) == "partial_dashboard_history_available"
    assert dashboard_history_status(3) == "stable_dashboard_history_available"
