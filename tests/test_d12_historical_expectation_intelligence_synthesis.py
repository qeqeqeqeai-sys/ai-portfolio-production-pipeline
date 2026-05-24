from copy import deepcopy

from transmission_layers.expectation_failure.expectation_intelligence import (
    build_d12_cross_window_expectation_patterns,
    build_d12_dashboard_expectation_cards,
    build_d12_expectation_intelligence_synthesis,
    build_d12_historical_expectation_inventory,
    build_d12_report_markdown,
    build_d12_report_payload,
    certify_d12_historical_expectation_synthesis,
    classify_d12_historical_expectation_regime,
    validate_d12_synthesis_eligibility,
)


def _fake_inputs(cert="CERTIFIED_HISTORICAL_BACKFILL", depth="REPLAY_DEPTH_SUFFICIENT", continuity="CONTINUITY_OK"):
    windows = [
        {"replay_window_id": "D11-WINDOW-001", "replay_ids": ["R1", "R2"], "finding_refs": ["F1"], "lineage_refs": ["L1"]},
        {"replay_window_id": "D11-WINDOW-002", "replay_ids": ["R3"], "finding_refs": ["F1", "F2"], "lineage_refs": ["L2"]},
    ]
    return dict(
        d11_backfill_inventory={"manifest_checksums": ["M1"]},
        d11_replay_windows=windows,
        d11_reconstruction={"replay_continuity_status": continuity},
        d11_historical_summary={"replay_depth_assessment": depth, "evidence_history_confidence": "HIGH"},
        d11_certification={"certification_status": cert, "continuity_status": continuity},
    )


def test_api_export_presence():
    assert callable(build_d12_historical_expectation_inventory)


def test_deterministic_ordering_and_ranking():
    inp = _fake_inputs()
    inv = build_d12_historical_expectation_inventory(**inp)
    pats1 = build_d12_cross_window_expectation_patterns(d11_replay_windows=inp["d11_replay_windows"], historical_expectation_inventory=inv)
    pats2 = build_d12_cross_window_expectation_patterns(d11_replay_windows=inp["d11_replay_windows"], historical_expectation_inventory=inv)
    assert [p["pattern_id"] for p in pats1] == [p["pattern_id"] for p in pats2]
    assert [p["deterministic_rank"] for p in pats1] == sorted([p["deterministic_rank"] for p in pats1])


def test_input_immutability():
    inp = _fake_inputs()
    before = deepcopy(inp)
    inv = build_d12_historical_expectation_inventory(**inp)
    _ = validate_d12_synthesis_eligibility(historical_expectation_inventory=inv)
    assert inp == before


def test_blocked_when_d11_blocked_or_no_windows():
    inp = _fake_inputs(cert="BLOCKED_HISTORICAL_BACKFILL")
    inv = build_d12_historical_expectation_inventory(**inp)
    elig = validate_d12_synthesis_eligibility(historical_expectation_inventory=inv)
    assert elig["eligibility_status"] == "SYNTHESIS_BLOCKED"
    inp2 = _fake_inputs(); inp2["d11_replay_windows"] = []
    inv2 = build_d12_historical_expectation_inventory(**inp2)
    elig2 = validate_d12_synthesis_eligibility(historical_expectation_inventory=inv2)
    assert elig2["eligibility_status"] == "SYNTHESIS_BLOCKED"


def test_degraded_and_certified_paths():
    inp = _fake_inputs(cert="DEGRADED_HISTORICAL_BACKFILL", depth="REPLAY_DEPTH_LIMITED", continuity="CONTINUITY_DEGRADED")
    inv = build_d12_historical_expectation_inventory(**inp)
    elig = validate_d12_synthesis_eligibility(historical_expectation_inventory=inv)
    assert elig["eligibility_status"] == "SYNTHESIS_DEGRADED"

    good = _fake_inputs()
    invg = build_d12_historical_expectation_inventory(**good)
    eligg = validate_d12_synthesis_eligibility(historical_expectation_inventory=invg)
    pats = build_d12_cross_window_expectation_patterns(d11_replay_windows=good["d11_replay_windows"], historical_expectation_inventory=invg)
    regime = classify_d12_historical_expectation_regime(historical_expectation_inventory=invg, cross_window_patterns=pats, eligibility_validation=eligg)
    cert = certify_d12_historical_expectation_synthesis(historical_expectation_inventory=invg, eligibility_validation=eligg, cross_window_patterns=pats, regime_classification=regime)
    assert cert["certification_status"] == "CERTIFIED_HISTORICAL_EXPECTATION_SYNTHESIS"


def test_patterns_families_and_refs_and_regimes():
    inp = _fake_inputs()
    inv = build_d12_historical_expectation_inventory(**inp)
    elig = validate_d12_synthesis_eligibility(historical_expectation_inventory=inv)
    pats = build_d12_cross_window_expectation_patterns(d11_replay_windows=inp["d11_replay_windows"], historical_expectation_inventory=inv)
    fams = {p["pattern_family"] for p in pats}
    required = {
        "recurring_expectation_constraint", "persistent_lineage_integrity", "replay_depth_drift", "continuity_degradation", "evidence_confidence_drift", "unresolved_constraint_persistence", "finding_recurrence"
    }
    assert required.issubset(fams)
    assert all(p["supporting_replay_ids"] and p["supporting_window_refs"] for p in pats)

    regimes = set()
    for cert, depth, cont in [
        ("CERTIFIED_HISTORICAL_BACKFILL", "REPLAY_DEPTH_SUFFICIENT", "CONTINUITY_OK"),
        ("CERTIFIED_HISTORICAL_BACKFILL", "REPLAY_DEPTH_SUFFICIENT", "CONTINUITY_FRAGMENTED"),
        ("CERTIFIED_HISTORICAL_BACKFILL", "REPLAY_DEPTH_INSUFFICIENT", "CONTINUITY_OK"),
        ("DEGRADED_HISTORICAL_BACKFILL", "REPLAY_DEPTH_LIMITED", "CONTINUITY_DEGRADED"),
        ("CERTIFIED_HISTORICAL_BACKFILL", "REPLAY_DEPTH_SUFFICIENT", "CONTINUITY_OK"),
    ]:
        x = _fake_inputs(cert=cert, depth=depth, continuity=cont)
        xi = build_d12_historical_expectation_inventory(**x)
        xe = validate_d12_synthesis_eligibility(historical_expectation_inventory=xi)
        xp = build_d12_cross_window_expectation_patterns(d11_replay_windows=x["d11_replay_windows"], historical_expectation_inventory=xi)
        regimes.add(classify_d12_historical_expectation_regime(historical_expectation_inventory=xi, cross_window_patterns=xp, eligibility_validation=xe)["historical_expectation_regime"])
    assert regimes.issuperset({"historically_stable_expectation_base", "fragmented_expectation_history", "insufficient_historical_depth", "mixed_historical_expectation_state"})


def test_dashboard_payload_markdown_and_governance_flags_and_stability():
    inp = _fake_inputs()
    inv = build_d12_historical_expectation_inventory(**inp)
    elig = validate_d12_synthesis_eligibility(historical_expectation_inventory=inv)
    pats = build_d12_cross_window_expectation_patterns(d11_replay_windows=inp["d11_replay_windows"], historical_expectation_inventory=inv)
    regime = classify_d12_historical_expectation_regime(historical_expectation_inventory=inv, cross_window_patterns=pats, eligibility_validation=elig)
    synth = build_d12_expectation_intelligence_synthesis(cross_window_patterns=pats, regime_classification=regime, historical_expectation_inventory=inv)
    cert = certify_d12_historical_expectation_synthesis(historical_expectation_inventory=inv, eligibility_validation=elig, cross_window_patterns=pats, regime_classification=regime)
    cards = build_d12_dashboard_expectation_cards(certification=cert, regime_classification=regime, cross_window_patterns=pats, expectation_intelligence_synthesis=synth)
    required = {"synthesis_status","historical_expectation_regime","regime_confidence_band","pattern_count","strongest_recurring_pattern","strongest_historical_constraint","replay_depth_interpretation","continuity_interpretation","recommendation"}
    assert required.issubset(cards.keys())
    payload1 = build_d12_report_payload(historical_expectation_inventory=inv, eligibility_validation=elig, cross_window_patterns=pats, regime_classification=regime, expectation_intelligence_synthesis=synth, dashboard_cards=cards, certification=cert)
    payload2 = build_d12_report_payload(historical_expectation_inventory=inv, eligibility_validation=elig, cross_window_patterns=pats, regime_classification=regime, expectation_intelligence_synthesis=synth, dashboard_cards=cards, certification=cert)
    assert payload1 == payload2
    assert payload1["no_direct_sql_bypass_used"] and payload1["no_writes_performed"] and payload1["no_live_fetches_performed"]
    md = build_d12_report_markdown(report_payload=payload1)
    low = md.lower()
    assert "select " not in low and "insert " not in low and "update " not in low and "delete " not in low
    assert "api_key" not in low and "secret" not in low and "token" not in low
    assert "predict" not in low and "trade" not in low
