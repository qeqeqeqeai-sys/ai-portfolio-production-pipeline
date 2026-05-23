from copy import deepcopy

from transmission_layers.expectation_failure.real_data import (
    build_temporal_checksum_chain,
    build_temporal_replay_window,
    build_temporal_snapshot_sequence,
    certify_temporal_snapshot_sequence,
    validate_temporal_snapshot_inputs,
)


def _snapshot(snapshot_id: str, as_of_date: str, checksum: str, certification_status: str = "CERTIFIED") -> dict:
    return {
        "snapshot_id": snapshot_id,
        "as_of_date": as_of_date,
        "checksum": checksum,
        "certification_status": certification_status,
        "replay_metadata": {"source": "b3"},
        "persistence_eligibility": True,
        "payload_summary": {"entities": 3},
    }


def test_public_api_exports_exist():
    assert callable(build_temporal_snapshot_sequence)
    assert callable(validate_temporal_snapshot_inputs)
    assert callable(build_temporal_replay_window)
    assert callable(build_temporal_checksum_chain)
    assert callable(certify_temporal_snapshot_sequence)


def test_valid_snapshots_certify():
    snaps = [_snapshot("r1", "2026-01-01", "a"), _snapshot("r2", "2026-01-02", "b")]
    result = certify_temporal_snapshot_sequence(snaps)
    assert result["t1_status"] == "TEMPORAL_SEQUENCE_CERTIFIED"


def test_ordering_date_id_checksum_deterministic():
    snaps = [_snapshot("b", "2026-01-01", "z"), _snapshot("a", "2026-01-01", "a"), _snapshot("c", "2025-12-31", "m")]
    seq = build_temporal_snapshot_sequence(snaps)["ordered_sequence"]
    assert [r["snapshot_identifier"] for r in seq] == ["c", "a", "b"]


def test_repeated_calls_identical_output_checksum():
    snaps = [_snapshot("r1", "2026-01-01", "a"), _snapshot("r2", "2026-01-02", "b")]
    one = certify_temporal_snapshot_sequence(snaps)
    two = certify_temporal_snapshot_sequence(snaps)
    assert one == two
    assert one["result_checksum"] == two["result_checksum"]


def test_inputs_not_mutated():
    snaps = [_snapshot("r1", "2026-01-01", "a")]
    before = deepcopy(snaps)
    certify_temporal_snapshot_sequence(snaps)
    assert snaps == before


def test_missing_checksum_degraded():
    snaps = [_snapshot("r1", "2026-01-01", ""), _snapshot("r2", "2026-01-02", "b")]
    result = certify_temporal_snapshot_sequence(snaps)
    assert result["t1_status"] == "TEMPORAL_SEQUENCE_DEGRADED"


def test_missing_date_blocked():
    snaps = [_snapshot("r1", "", "a")]
    result = certify_temporal_snapshot_sequence(snaps)
    assert result["t1_status"] == "TEMPORAL_SEQUENCE_BLOCKED"


def test_duplicate_dates_diagnostic_visible():
    snaps = [_snapshot("r1", "2026-01-01", "a"), _snapshot("r2", "2026-01-01", "b")]
    result = certify_temporal_snapshot_sequence(snaps)
    assert result["gap_diagnostics"]["duplicate_dates_present"] is True


def test_window_policy_approved_only_and_full_sequence():
    snaps = [_snapshot("r1", "2026-01-01", "a"), _snapshot("r2", "2026-02-01", "b"), _snapshot("r3", "2026-03-01", "c")]
    result = certify_temporal_snapshot_sequence(snaps, window_policy=["30D", "FULL_SEQUENCE"])
    assert set(result["replay_windows"].keys()) == {"30D", "FULL_SEQUENCE"}
    assert result["replay_windows"]["FULL_SEQUENCE"]["included_snapshot_count"] == 3


def test_90d_and_30d_windows_deterministic_behavior():
    snaps = [_snapshot("r1", "2026-01-01", "a"), _snapshot("r2", "2026-03-15", "b"), _snapshot("r3", "2026-03-31", "c")]
    seq = build_temporal_snapshot_sequence(snaps)["ordered_sequence"]
    w30 = build_temporal_replay_window(seq, window_type="30D")
    w90 = build_temporal_replay_window(seq, window_type="90D")
    assert w30["included_snapshot_count"] <= w90["included_snapshot_count"]


def test_checksum_chain_stable_and_forbidden_capabilities_false():
    snaps = [_snapshot("r1", "2026-01-01", "a"), _snapshot("r2", "2026-01-03", "b")]
    seq = build_temporal_snapshot_sequence(snaps)["ordered_sequence"]
    one = build_temporal_checksum_chain(seq)
    two = build_temporal_checksum_chain(seq)
    assert one == two
    cert = certify_temporal_snapshot_sequence(snaps)
    assert all(value is False for value in cert["forbidden_capabilities"].values())
