from transmission_layers.expectation_failure.replay_ecology.lr6_exp3_replay_ecology_signal_readout import (
    build_lr6_exp3_dashboard_payload,
    build_replay_ecology_signal_readout,
    certify_lr6_exp3_experimental_boundaries,
)


def test_deterministic_readout_outputs() -> None:
    assert build_replay_ecology_signal_readout() == build_replay_ecology_signal_readout()


def test_all_six_domains_present() -> None:
    payload = build_replay_ecology_signal_readout()
    domains = payload["domain_readouts"]
    assert sorted(domains.keys()) == sorted(
        [
            "replay_drift",
            "propagation_evolution",
            "contradiction_ecology",
            "saturation_novelty",
            "monoculture_diversity",
            "ecosystem_interaction",
        ]
    )


def test_composite_interpretation_and_evidence_linked_findings() -> None:
    summary = build_replay_ecology_signal_readout()["interpretation_summary"]
    assert "dominant_replay_ecology_state" in summary
    assert "replay_ecology_maturity_band" in summary
    assert "observation_confidence_band" in summary
    assert summary["key_ecological_findings"]
    for finding in summary["key_ecological_findings"]:
        assert "evidence" in finding
        assert finding["evidence"]


def test_no_prediction_or_trading_vocabulary() -> None:
    serialized = str(build_replay_ecology_signal_readout()).lower()
    blocked = ["buy", "sell", "outperform", "underperform", "alpha", "expected return", "price target", "signal to trade", "portfolio allocation"]
    for token in blocked:
        assert token not in serialized


def test_boundary_and_bounded_output_controls() -> None:
    cert = certify_lr6_exp3_experimental_boundaries()
    assert cert["no_persistence_writes"] is True
    assert cert["no_direct_sql"] is True
    assert cert["no_external_apis"] is True
    assert cert["governed_lr6_activation"] is False

    summary = build_replay_ecology_signal_readout()["interpretation_summary"]
    assert len(summary["key_ecological_findings"]) <= 8
    assert len(summary["caveats"]) <= 6
    assert len(summary["next_observation_priorities"]) <= 6
    assert summary["replay_ecology_maturity_band"] in {"low", "moderate", "high"}
    assert summary["observation_confidence_band"] in {"low", "moderate", "high"}


def test_dashboard_payload_structure() -> None:
    payload = build_lr6_exp3_dashboard_payload(max_entities=90, slice_count=4)
    assert payload["phase"] == "LR6-EXP3"
    assert "readout_payload" in payload
    assert "dashboard_sections" in payload
    assert "composite_interpretation" in payload["dashboard_sections"]
