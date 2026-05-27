import json
from pathlib import Path

from transmission_layers.expectation_failure.real_data.ops_live1b_snapshot_observation_review import (
    build_ops_live1b_snapshot_observation_review,
    load_ops_live1b_snapshots,
)


def _snapshot(snapshot_id: str, ts: str, checksum: str = "u1", status: str = "ok", norm: float = 100.0, failed: int = 0, posture: str = "calm", canonical_keys=None):
    canonical_keys = canonical_keys or [
        "snapshot_metadata_rows","symbol_snapshot_rows","sector_summary_rows","pressure_rows","resilience_rows","fragmentation_rows","continuity_rows","integrity_rows","governance_rows","compression_rows"
    ]
    canonical = {k: [] for k in canonical_keys}
    canonical["snapshot_metadata_rows"] = [{"snapshot_id": snapshot_id, "snapshot_ts": ts, "universe_checksum": checksum, "universe_size": 50}]
    canonical.setdefault("pressure_rows", []).append({"symbol": "AAPL", "structural_pressure_score": 80})
    canonical.setdefault("resilience_rows", []).append({"symbol": "MSFT", "profitability_structure": 90})
    canonical.setdefault("fragmentation_rows", []).append({"symbol": "NVDA", "breadth_dispersion_structure": 70})
    return {
        "status": status,
        "ops_live1b_payload": {
            "snapshot_id": snapshot_id,
            "snapshot_ts": ts,
            "observation_mode": "controlled_operational_observation",
            "governance_boundaries": {"safe": True},
            "canonical_tables": canonical,
            "streamlit_payloads": {
                "streamlit_summary_cards": [{"label": "posture", "value": posture}],
                "streamlit_sector_summary": [],
                "streamlit_pressure_table": [],
                "streamlit_resilience_table": [],
                "streamlit_fragmentation_table": [],
                "streamlit_continuity_panel": [],
                "streamlit_integrity_panel": [],
                "streamlit_governance_panel": [],
                "streamlit_snapshot_metadata": [],
            },
            "diagnostics": {
                "normalization_completeness_percentage": norm,
                "data_completeness_summary": norm,
                "symbols_successfully_normalized": 50 - failed,
                "symbols_failed_closed": failed,
                "invalid_values": 0,
                "missing_fields": 0,
                "null_fields": 0,
                "fallback_usage_percentage": 0,
                "compression_ratio": 1.0,
                "sector_distribution": [{"sector": "Tech", "count": 30}],
            },
        },
    }


def test_loading_is_deterministic_and_bounded(tmp_path):
    for i in range(35):
        p = tmp_path / f"snap_{i:02d}.json"
        p.write_text(json.dumps(_snapshot(f"s{i}", f"2026-05-{(i%30)+1:02d}T00:00:00Z")), encoding="utf-8")
    snaps = load_ops_live1b_snapshots(str(tmp_path), max_snapshots=30)
    assert len(snaps) == 30
    assert snaps == sorted(snaps, key=lambda r: (r["snapshot_ts"], r["source_file"]))


def test_stable_and_unstable_checksum_detection():
    stable = [
        {"snapshot_id": "a", "snapshot_ts": "2026-05-01", "status": "ok", "universe_checksum": "x", "universe_size": 50, "observation_mode": "controlled_operational_observation", "governance_boundaries": {"safe": True}, "canonical_keys": ["a"], "streamlit_keys": ["b"], "symbol_rows": 50, "compression_ratio": 1.0, "summary_items": 1, "normalization_completeness_percentage": 100, "data_completeness_summary": 100, "symbols_successfully_normalized": 50, "symbols_failed_closed": 0, "invalid_values": 0, "missing_fields": 0, "null_fields": 0, "fallback_usage_percentage": 0, "sector_distribution": (), "posture": "calm", "pressure": (), "resilience": (), "fragmentation": ()},
        {"snapshot_id": "b", "snapshot_ts": "2026-05-02", "status": "ok", "universe_checksum": "x", "universe_size": 50, "observation_mode": "controlled_operational_observation", "governance_boundaries": {"safe": True}, "canonical_keys": ["a"], "streamlit_keys": ["b"], "symbol_rows": 50, "compression_ratio": 1.0, "summary_items": 1, "normalization_completeness_percentage": 100, "data_completeness_summary": 100, "symbols_successfully_normalized": 50, "symbols_failed_closed": 0, "invalid_values": 0, "missing_fields": 0, "null_fields": 0, "fallback_usage_percentage": 0, "sector_distribution": (), "posture": "risk", "pressure": (), "resilience": (), "fragmentation": ()},
    ]
    r1 = build_ops_live1b_snapshot_observation_review(stable)
    assert any(x["check"] == "universe_checksum_stable" and x["value"] is True for x in r1["stability_check_rows"])
    stable[1]["universe_checksum"] = "y"
    r2 = build_ops_live1b_snapshot_observation_review(stable)
    assert any(x["check"] == "universe_checksum_stable" and x["value"] is False for x in r2["stability_check_rows"])


def test_readiness_ready_and_blocked_cases(tmp_path):
    p1 = tmp_path / "a.json"
    p2 = tmp_path / "b.json"
    p1.write_text(json.dumps(_snapshot("s1", "2026-05-01T00:00:00Z")), encoding="utf-8")
    p2.write_text(json.dumps(_snapshot("s2", "2026-05-02T00:00:00Z")), encoding="utf-8")
    review = build_ops_live1b_snapshot_observation_review(load_ops_live1b_snapshots(str(tmp_path)))
    assert review["readiness_classification"] == "ready_for_controlled_300_symbol_probe"

    p2.write_text(json.dumps(_snapshot("s2", "2026-05-02T00:00:00Z", failed=2, norm=90.0)), encoding="utf-8")
    blocked = build_ops_live1b_snapshot_observation_review(load_ops_live1b_snapshots(str(tmp_path)))
    assert blocked["readiness_classification"] in {"blocked_by_data_quality", "needs_more_50_symbol_observation"}
    assert blocked["governance_panel"]["observational_only"] is True


def test_payload_schema_instability_and_posture_transition(tmp_path):
    (tmp_path / "a.json").write_text(json.dumps(_snapshot("s1", "2026-05-01T00:00:00Z", posture="calm", canonical_keys=["x"])), encoding="utf-8")
    (tmp_path / "b.json").write_text(json.dumps(_snapshot("s2", "2026-05-02T00:00:00Z", posture="stress", canonical_keys=["y"])), encoding="utf-8")
    review = build_ops_live1b_snapshot_observation_review(load_ops_live1b_snapshots(str(tmp_path)))
    assert any(x["check"] == "payload_schema_stable" and x["value"] is False for x in review["stability_check_rows"])
    assert review["posture_transition_rows"][0]["changed"] is True
