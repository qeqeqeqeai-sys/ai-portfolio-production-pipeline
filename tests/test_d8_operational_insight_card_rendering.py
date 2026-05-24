from transmission_layers.expectation_failure.expectation_intelligence.d8_evidence_prioritization_operational_insight import (
    build_d8_1_operational_card_render_model,
    build_d8_evidence_priority_inventory,
)


def _payload():
    findings = [{"finding_id": "F1", "confidence": "high"}, {"finding_id": "F2", "confidence": "weak"}]
    evidence = [{"evidence_ref": "EV1", "evidence_metadata": {"metric": "spread"}}, {"evidence_ref": "EV2", "evidence_metadata": {"metric": "macro"}}]
    e2 = {
        "evidence_quality_profiles": [
            {"evidence_ref": "EV1", "evidence_quality_score": 90, "evidence_quality_band": "strong"},
            {"evidence_ref": "EV2", "evidence_quality_score": 60, "evidence_quality_band": "moderate"},
        ],
        "evidence_finding_linkages": [
            {"evidence_ref": "EV1", "finding_id": "F1", "linkage_strength_score": 85},
            {"evidence_ref": "EV2", "finding_id": "F2", "linkage_strength_score": 55},
        ],
        "evidence_support_buckets": {"contradiction_evidence": ["EV2"]},
        "contradiction_evidence_map": [{"contradiction_claim": "macro conflicts", "contradiction_strength": 60, "affected_findings": ["F2"], "persistence_context": "persistent", "supporting_evidence_refs": ["EV2"]}],
    }
    e3 = {"contradiction_drift": {"direction": "rising"}, "expectation_pressure_drift": {"direction": "weakening"}, "history_sufficiency": "sufficient_history"}
    e4 = {"narrative_drift_profile": {"narrative_drift_direction": "widening"}}
    e5 = {"composite_regime_synthesis": {"dominant_expectation_regime": "valuation_persistence", "supporting_signal_refs": ["E1", "E2"]}, "caveat_inventory": {"consolidated_caveats": ["low_specificity"]}}
    return build_d8_evidence_priority_inventory(findings, evidence, e2, e3, e4, e5)


def test_d8_1_card_model_readability_and_ordering_and_primary_fields():
    model = build_d8_1_operational_card_render_model(_payload())
    assert model["available"] is True
    assert [c["section"] for c in model["cards"]] == [
        "What matters most",
        "Why this regime was selected",
        "Main contradiction",
        "Confidence weakener",
        "Temporal/semantic drift",
        "What to monitor next",
        "Evidence lineage",
    ]
    assert model["supporting_evidence"]["strongest_supporting_evidence_ref"] == "EV1"
    assert model["contradiction"]["severity"] in {"high", "moderate", "low"}
    assert "checksum" not in " ".join(card["content"].lower() for card in model["cards"])


def test_d8_1_graceful_fallback_when_missing_payload():
    model = build_d8_1_operational_card_render_model({})
    assert model["available"] is False
    assert model["degraded"] is True
    assert "unavailable" in model["message"].lower() or "degraded" in model["message"].lower()
    assert isinstance(model["debug"]["raw_d8_payload"], dict)
