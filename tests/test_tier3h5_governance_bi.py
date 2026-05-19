import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from transmission_layers.asset_discovery.tier3h5.governance_bi import build_bi_export_artifacts, write_bi_export_artifacts
from transmission_layers.asset_discovery.tier3h5.governance_bi.contracts import DIMENSION_MEMBERS, FACT_TABLES
from transmission_layers.asset_discovery.tier3h5.governance_bi.validation import validate_bi_exports
from transmission_layers.asset_discovery.tier3h5.governance_history import run_phase4c_governance_history
from transmission_layers.asset_discovery.tier3h5.governance_risk_intelligence import run_governance_risk_intelligence


def _write(path: str, payload: dict) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")


def _read(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _seed_governance_inputs(replay_ratio: float = 0.5) -> None:
    _write(
        "logs/tier3h5_phase3a_cross_registry_summary.json",
        {
            "deterministic_alias_count": 4,
            "unresolved_cross_registry_count": 2,
            "conflicting_cross_registry_count": 1,
            "dual_listing_count": 1,
            "linkage_mode": "deterministic_exact_match_only",
            "enforcement_enabled": False,
            "canonical_override_enabled": False,
        },
    )
    _write("logs/tier3h5_lineage_dedup_summary.json", {"duplicate_lineage_edges_collapsed": 2, "linkage_mode": "deterministic_exact_match_only"})
    _write(
        "logs/tier3h5_registry_replay_metrics.json",
        {
            "replay_consistency_ratio": replay_ratio,
            "replay_difference_count": 3,
            "replay_normalization_difference_count": 1,
            "replay_provenance_difference_count": 1,
            "replay_metadata_difference_count": 1,
            "governance_replay_stable": replay_ratio >= 0.9,
        },
    )
    _write(
        "logs/tier3h5_registry_replay_governance_summary.json",
        {
            "replay_governance_status": "normalization_drift",
            "replay_status_tags": ["normalization_drift"],
            "replay_mode": "advisory_only",
            "enforcement_enabled": False,
            "canonical_override_enabled": False,
        },
    )
    _write("logs/tier3h5_registry_replay_continuity_lineage.json", {"replay_governance_status": "normalization_drift", "replay_lineage_depth": 3})
    _write("logs/tier3h5_registry_replay_baseline_history.json", {"history": [{"replay_consistency_ratio": 1.0}, {"replay_consistency_ratio": 0.8}]})
    _write("logs/tier3h5_snapshot_archive_manifest.json", {"snapshot_hash_verified": False})
    _write("logs/tier3h5_governance_operational_intelligence.json", {"governance_health_status": "advisory_attention", "replay_health_status": "replay_instability_detected"})
    _write("logs/tier3h5_governance_anomaly_summary.json", {"anomalies": [{"category": "normalization_drift_spike", "status": "elevated_attention"}]})
    run_governance_risk_intelligence()


def test_phase4e_bi_export_artifacts_are_power_bi_ready_and_validated(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    _seed_governance_inputs()
    out = run_phase4c_governance_history()
    artifacts = out["bi_exports"]

    for contract in FACT_TABLES:
        payload = artifacts[contract.table_name]
        assert payload["table_name"] == contract.table_name
        assert payload["primary_key"] == contract.primary_key
        assert payload["fields"] == list(contract.fields)
        assert payload["replay_mode"] == "advisory_only"
        assert payload["enforcement_enabled"] is False
        assert payload["append_history_compatible"] is True
        pks = [row[contract.primary_key] for row in payload["rows"]]
        assert pks == sorted(pks)
        assert len(pks) == len(set(pks))
        assert all(set(contract.fields) <= set(row) for row in payload["rows"])

    validation = validate_bi_exports(
        {contract.table_name: artifacts[contract.table_name] for contract in FACT_TABLES},
        artifacts["governance_dimensions"],
        artifacts["semantic_layer"],
        artifacts["measure_catalog"],
    )
    assert validation == {"validation_status": "valid", "validation_error_count": 0, "validation_errors": []}
    assert artifacts["summary"]["bi_export_status"] == "bi_exports_available"
    assert artifacts["summary"]["dashboard_ready"] is True
    assert artifacts["summary"]["exported_measure_count"] == 14

    for path in [
        "logs/tier3h5_bi_governance_incident_fact.json",
        "logs/tier3h5_bi_governance_escalation_fact.json",
        "logs/tier3h5_bi_governance_watchlist_fact.json",
        "logs/tier3h5_bi_governance_trend_fact.json",
        "logs/tier3h5_bi_governance_continuity_fact.json",
        "logs/tier3h5_bi_governance_summary_snapshot.json",
        "logs/tier3h5_bi_governance_dimensions.json",
        "logs/tier3h5_bi_semantic_layer.json",
        "logs/tier3h5_bi_measure_catalog.json",
        "logs/tier3h5_phase4e_bi_export_summary.json",
    ]:
        assert Path(path).exists()


def test_phase4e_semantic_layer_dimensions_and_measure_catalog_reference_valid_fields(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    _seed_governance_inputs()
    artifacts = run_phase4c_governance_history()["bi_exports"]
    exported_fields = {contract.table_name: set(artifacts[contract.table_name]["fields"]) for contract in FACT_TABLES}

    dimensions = artifacts["governance_dimensions"]["dimensions"]
    for dimension_name, expected_members in DIMENSION_MEMBERS.items():
        assert {row["member_key"] for row in dimensions[dimension_name]} == set(expected_members)

    for table in artifacts["semantic_layer"]["tables"]:
        assert set(table["fields"]) <= exported_fields[table["table_name"]]
        assert table["dashboard_description"].startswith("Power BI-ready advisory-only")

    for measure in artifacts["measure_catalog"]["measures"]:
        assert measure["table_name"] in exported_fields
        assert measure["column_name"] in exported_fields[measure["table_name"]]
        assert measure["metadata_only"] is True
        assert measure["runtime_scoring"] is False


def test_phase4e_sparse_history_degrades_without_failing_ci(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    artifacts = write_bi_export_artifacts()
    summary = _read("logs/tier3h5_phase4e_bi_export_summary.json")

    assert summary["bi_history_status"] == "insufficient_bi_history"
    assert summary["dashboard_ready"] is True
    assert artifacts["governance_incident_fact"]["row_count"] == 0
    assert artifacts["governance_incident_fact"]["bi_history_status"] == "insufficient_bi_history"
    assert artifacts["governance_summary_snapshot"]["row_count"] == 1
    assert artifacts["validation"]["validation_status"] == "valid"


def test_phase4e_regression_boundaries_preserve_advisory_read_only_exact_match_and_tier3h4_freeze(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    _seed_governance_inputs(replay_ratio=0.82)
    canonical_before = _read("logs/tier3h5_phase3a_cross_registry_summary.json")
    risk_before = run_governance_risk_intelligence()

    first = build_bi_export_artifacts()
    second = build_bi_export_artifacts()

    assert first == second
    assert _read("logs/tier3h5_phase3a_cross_registry_summary.json") == canonical_before
    assert run_governance_risk_intelligence() == risk_before
    summary = first["summary"]
    assert summary["replay_mode"] == "advisory_only"
    assert summary["enforcement_enabled"] is False
    assert summary["exact_match_only_preserved"] is True
    assert summary["tier3h4_freeze_boundary_preserved"] is True
    assert summary["read_only_export_behavior_preserved"] is True
    assert summary["fuzzy_matching_enabled"] is False
    assert summary["semantic_matching_enabled"] is False
    assert summary["canonical_override_enabled"] is False
    assert summary["scoring_mutation_enabled"] is False
    assert summary["propagation_mutation_enabled"] is False
    assert summary["confidence_mutation_enabled"] is False
    assert summary["reconciliation_mutation_enabled"] is False
