from transmission_layers.expectation_failure.real_data.b1_fragility_payload_builder import build_deterministic_fragility_payload
from transmission_layers.expectation_failure.real_data.b1_market_snapshot_builder import build_deterministic_market_snapshot
from transmission_layers.expectation_failure.real_data.b1_snapshot_certification import certify_b1_snapshot


def _build_payload():
    snapshot = build_deterministic_market_snapshot(
        raw_entity_inputs=[
            {"ticker": "NVDA", "price_momentum_score": 65, "fundamental_health_score": 70, "expectation_pressure_score": 60},
            {"ticker": "AMD", "price_momentum_score": 55, "fundamental_health_score": 50, "expectation_pressure_score": 50},
        ],
        raw_benchmark_inputs=[{"symbol": "SOXX", "benchmark_pressure_score": 66}],
    )
    return build_deterministic_fragility_payload(snapshot)


def test_b1_certification_checksum_stability_and_replay_consistency():
    payload = _build_payload()
    cert1 = certify_b1_snapshot(payload)
    cert2 = certify_b1_snapshot(payload)
    assert cert1["certification"]["checksum"] == cert2["certification"]["checksum"]
    assert cert1["replay_checksum"] == cert2["replay_checksum"]


def test_b1_certification_bounds_and_degraded_visibility():
    payload = _build_payload()
    certified = certify_b1_snapshot(payload)
    assert certified["certification"]["score_bounds_valid"] is True
    assert "QQQ" in certified["certification"]["degraded_visibility"]["benchmark_missing"]


def test_b1_additive_only_export_integrity():
    payload = _build_payload()
    certified = certify_b1_snapshot(payload)
    assert set(certified.keys()) == {"payload", "certification", "replay_checksum"}
    assert certified["certification"]["replay_contract"]["network_calls"] == "none"
