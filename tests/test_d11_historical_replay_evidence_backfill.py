from copy import deepcopy

from transmission_layers.expectation_failure.expectation_intelligence import (
    build_d11_backfill_inventory,
    validate_d11_backfill_eligibility,
    build_d11_historical_replay_windows,
    build_d11_backfill_reconstruction,
    build_d11_historical_evidence_summary,
    certify_d11_backfill,
    build_d11_dashboard_backfill_cards,
    build_d11_report_payload,
    build_d11_report_markdown,
)


def _replay(i, ts, m="M1", append_only=True):
    return {"replay_id": f"R{i}", "replay_timestamp": ts, "manifest_checksum": m, "append_only": append_only, "evidence_category": "STRUCTURAL"}


def _manifest(chk="M1", lineage="L1"):
    return {"manifest_checksum": chk, "lineage_ref": lineage}


def test_api_export_presence():
    assert callable(build_d11_backfill_inventory)


def test_deterministic_window_ordering_and_chronology_and_input_immutability():
    replay_rows = [_replay(2, "2026-01-02T00:00:00Z"), _replay(1, "2026-01-01T00:00:00Z")]
    c = deepcopy(replay_rows)
    windows = build_d11_historical_replay_windows(replay_rows=replay_rows, manifest_rows=[_manifest()], window_size=1)
    assert [w["replay_ids"][0] for w in windows] == ["R1", "R2"]
    assert replay_rows == c


def test_blocked_eligibility_missing_rows():
    b1 = validate_d11_backfill_eligibility(replay_rows=[], manifest_rows=[_manifest()])
    b2 = validate_d11_backfill_eligibility(replay_rows=[_replay(1, "2026-01-01T00:00:00Z")], manifest_rows=[])
    assert b1["eligibility_status"] == "BACKFILL_BLOCKED" and "REPLAY_ROWS_MISSING" in b1["blocking_reasons"]
    assert b2["eligibility_status"] == "BACKFILL_BLOCKED" and "MANIFEST_ROWS_MISSING" in b2["blocking_reasons"]


def test_reconstruction_deterministic_and_continuity_states_and_bounded():
    replays = [_replay(1, "2026-01-01T00:00:00Z", "M1"), _replay(2, "2026-01-02T00:00:00Z", "M2")]
    manifests = [_manifest("M1", "L1"), _manifest("M2", "L2")]
    r1 = build_d11_backfill_reconstruction(replay_rows=replays, manifest_rows=manifests)
    r2 = build_d11_backfill_reconstruction(replay_rows=replays, manifest_rows=manifests)
    assert r1 == r2 and r1["replay_continuity_status"] == "CONTINUITY_OK"
    assert len(r1["reconstructed_replay_sequences"]) <= len(replays)

    degraded = build_d11_backfill_reconstruction(replay_rows=[_replay(1, "2026-01-01T00:00:00Z", "M9")], manifest_rows=[_manifest("M9", "")])
    assert degraded["replay_continuity_status"] in {"CONTINUITY_DEGRADED", "CONTINUITY_FRAGMENTED"}
    fragmented = build_d11_backfill_reconstruction(replay_rows=[], manifest_rows=[])
    assert fragmented["replay_continuity_status"] == "CONTINUITY_FRAGMENTED"


def test_dashboard_summary_payload_checksum_and_certification_paths_and_governance_flags():
    replays = [_replay(1, "2026-01-01T00:00:00Z", "M1"), _replay(2, "2026-01-02T00:00:00Z", "M2")]
    manifests = [_manifest("M1", "L1"), _manifest("M2", "L2")]
    inv = build_d11_backfill_inventory(replay_rows=replays, manifest_rows=manifests)
    inv2 = build_d11_backfill_inventory(replay_rows=replays, manifest_rows=manifests)
    assert inv["inventory_checksum"] == inv2["inventory_checksum"]
    elig = validate_d11_backfill_eligibility(replay_rows=replays, manifest_rows=manifests)
    windows = build_d11_historical_replay_windows(replay_rows=replays, manifest_rows=manifests, window_size=1)
    recon = build_d11_backfill_reconstruction(replay_rows=replays, manifest_rows=manifests)
    summary = build_d11_historical_evidence_summary(backfill_inventory=inv, replay_windows=windows, reconstruction=recon)
    cards = build_d11_dashboard_backfill_cards(historical_summary=summary, certification={"certification_status": "CERTIFIED_HISTORICAL_BACKFILL"}, inventory=inv, reconstruction=recon)
    cert = certify_d11_backfill(inventory=inv, eligibility_validation=elig, replay_windows=windows, reconstruction=recon, historical_summary=summary)
    assert cert["certification_status"] in {"CERTIFIED_HISTORICAL_BACKFILL", "DEGRADED_HISTORICAL_BACKFILL"}

    required_cards = {"historical_backfill_status", "replay_depth_assessment", "historical_window_count", "replay_time_coverage", "strongest_recurring_integrity_signal", "strongest_recurrent_constraint", "continuity_status", "evidence_history_confidence", "recommendation"}
    required_summary = {"dominant_historical_operational_state", "strongest_recurring_integrity_signal", "strongest_recurrent_constraint", "replay_depth_assessment", "evidence_history_confidence", "historical_window_count", "unresolved_historical_constraints", "historical_interpretation"}
    assert required_cards.issubset(cards.keys()) and required_summary.issubset(summary.keys())

    payload = build_d11_report_payload(backfill_inventory=inv, eligibility_validation=elig, replay_windows=windows, reconstruction=recon, historical_summary=summary, dashboard_cards=cards, certification=cert)
    assert payload["no_direct_sql_bypass_used"] is True and payload["no_writes_performed"] is True
    assert "secret" not in str(payload).lower() and "insert into" not in str(payload).lower()
    md = build_d11_report_markdown(report_payload=payload)
    for sec in ["Objective", "Scope", "Non-goals", "Historical Backfill Inventory", "Eligibility Validation", "Replay Window Construction", "Replay Reconstruction", "Historical Evidence Summary", "Dashboard Cards", "Certification", "Governance Boundaries", "Final Recommendation"]:
        assert f"## {sec}" in md

    blocked = certify_d11_backfill(inventory=build_d11_backfill_inventory(replay_rows=[], manifest_rows=[]), eligibility_validation={"eligibility_status": "BACKFILL_BLOCKED"}, replay_windows=[], reconstruction={"replay_continuity_status": "CONTINUITY_FRAGMENTED"}, historical_summary={"replay_depth_assessment": "REPLAY_DEPTH_INSUFFICIENT"})
    assert blocked["certification_status"] == "BLOCKED_HISTORICAL_BACKFILL"
