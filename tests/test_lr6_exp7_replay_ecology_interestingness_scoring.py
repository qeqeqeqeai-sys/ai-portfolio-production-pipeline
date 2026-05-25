from transmission_layers.expectation_failure.replay_ecology.lr6_exp6_replay_ecology_snapshot_export import build_replay_ecology_snapshot_export
from transmission_layers.expectation_failure.replay_ecology.lr6_exp6a_longitudinal_snapshot_comparison import build_replay_ecology_snapshot_comparison
from transmission_layers.expectation_failure.replay_ecology.lr6_exp7_replay_ecology_interestingness_scoring import (
    MAX_CAVEATS,
    MAX_LOW_INFORMATION,
    MAX_RANKED_CHANGES,
    build_interestingness_summary,
    build_lr6_exp7_dashboard_payload,
    build_ranked_interesting_ecological_changes,
    build_replay_ecology_interestingness_scores,
    certify_lr6_exp7_experimental_boundaries,
)

BANNED_TERMS = {"buy", "sell", "outperform", "underperform", "alpha", "expected return", "price target", "trade signal", "portfolio allocation", "investment recommendation"}


def _walk(value):
    if isinstance(value, dict):
        for v in value.values():
            yield from _walk(v)
    elif isinstance(value, list):
        for v in value:
            yield from _walk(v)
    elif isinstance(value, str):
        yield value


def _build_comparison():
    prior = build_replay_ecology_snapshot_export(max_entities=120, slice_count=4)
    current = build_replay_ecology_snapshot_export(max_entities=300, slice_count=5)
    return build_replay_ecology_snapshot_comparison(prior, current)


def test_exp7_deterministic_domain_scoring_and_presence():
    comparison = _build_comparison()
    first = build_replay_ecology_interestingness_scores(comparison)
    second = build_replay_ecology_interestingness_scores(comparison)
    assert first == second
    assert len(first["domain_scores"]) == 7


def test_exp7_score_ranges_bands_ordering_and_bounds():
    summary = build_interestingness_summary(build_replay_ecology_interestingness_scores(_build_comparison()))
    assert len(summary["ranked_interesting_changes"]) <= MAX_RANKED_CHANGES
    assert len(summary["low_information_changes"]) <= MAX_LOW_INFORMATION
    assert len(summary["caveats"]) <= MAX_CAVEATS

    scores = [d["score"] for d in summary["domain_scores"]]
    assert all(0.0 <= s <= 1.0 for s in scores)
    ranked = summary["ranked_interesting_changes"]
    assert ranked == sorted(ranked, key=lambda x: (-x["score"], x["item_id"]))
    assert all(x["score_band"] in {"low_information", "routine_change", "notable_ecological_change", "high_interestingness_ecological_shift"} for x in summary["domain_scores"])


def test_exp7_evidence_caveats_penalties_and_payload_structure():
    scores = build_replay_ecology_interestingness_scores(_build_comparison())
    ranked = build_ranked_interesting_ecological_changes(scores)
    payload = build_lr6_exp7_dashboard_payload(_build_comparison())

    assert "ranked_interesting_changes" in ranked and "low_information_changes" in ranked
    assert "lr6_exp7_interestingness_dashboard" in payload
    dash = payload["lr6_exp7_interestingness_dashboard"]
    required = {
        "scoring_metadata", "domain_scores", "ranked_interesting_changes", "top_interestingness_drivers", "low_information_changes",
        "saturation_penalty_notes", "monoculture_penalty_notes", "evidence_quality_band", "replay_ecology_interestingness_band", "caveats", "next_observation_priorities",
    }
    assert required.issubset(dash.keys())
    assert all("evidence_refs" in item for item in dash["domain_scores"])
    assert any(item["caveats"] for item in dash["domain_scores"])


def test_exp7_boundary_and_vocabulary_constraints():
    cert = certify_lr6_exp7_experimental_boundaries()
    assert cert["experimental_mode_only"] is True
    assert cert["governed_lr6_activation"] is False
    assert cert["no_persistence_writes"] is True
    assert cert["no_direct_sql"] is True
    assert cert["no_external_apis"] is True

    text = " ".join(s.lower() for s in _walk(build_lr6_exp7_dashboard_payload(_build_comparison())))
    for banned in BANNED_TERMS:
        assert banned not in text
    assert "select " not in text and "insert " not in text and "update " not in text
