from transmission_layers.expectation_failure.expectation_intelligence.d8_6_evidence_graph_enrichment_linkage_density import build_d8_6_evidence_graph_enrichment_linkage_density


def _base(recurring=None):
    return {
        "d8_2_payload": {"semantic_persistence_summary": {"recurring_themes": recurring or []}, "replay_density_inventory": {"semantic_memory_ref": {}}},
        "e2_payload": {"evidence_finding_linkages": [], "contradiction_evidence_map": []},
        "historical_runs_payloads": [],
    }


def test_rich_graph_enriched_status():
    b = _base()
    out = build_d8_6_evidence_graph_enrichment_linkage_density(
        findings=[{"finding_id": "F1"}, {"finding_id": "F2"}, {"finding_id": "F3"}],
        evidence_maps=[
            {"finding_id": "F1", "payload": {"supporting_evidence_refs": ["E1", "E2"]}},
            {"finding_id": "F2", "payload": {"supporting_evidence_refs": ["E1", "E3"]}},
            {"finding_id": "F3", "payload": {"supporting_evidence_refs": ["E1", "E4"]}},
        ],
        historical_runs_payloads=[], e2_payload=b["e2_payload"], d8_2_payload=b["d8_2_payload"],
    )
    assert out["enrichment_status"] == "EVIDENCE_GRAPH_ENRICHED"
    assert out["strongest_supporting_evidence"]["evidence_ref"] == "E1"


def test_sparse_valid_and_no_evidence_and_shape_gap():
    b = _base()
    sparse = build_d8_6_evidence_graph_enrichment_linkage_density(findings=[{"finding_id": "F1"}], evidence_maps=[{"finding_id": "F1", "payload": {"supporting_evidence_refs": ["E1"]}}], historical_runs_payloads=[], e2_payload=b["e2_payload"], d8_2_payload=b["d8_2_payload"])
    assert sparse["enrichment_status"] == "EVIDENCE_GRAPH_SPARSE_BUT_VALID"
    noev = build_d8_6_evidence_graph_enrichment_linkage_density(findings=[{"finding_id": "F1"}], evidence_maps=[], historical_runs_payloads=[], e2_payload=b["e2_payload"], d8_2_payload=b["d8_2_payload"])
    assert noev["enrichment_status"] == "EVIDENCE_GRAPH_BLOCKED_NO_EVIDENCE"
    shapegap = build_d8_6_evidence_graph_enrichment_linkage_density(findings=[{"finding_id": "F1"}], evidence_maps=[{"finding_id": "F1", "payload": {"x": 1}}], historical_runs_payloads=[], e2_payload=b["e2_payload"], d8_2_payload=b["d8_2_payload"])
    assert shapegap["enrichment_status"] == "EVIDENCE_GRAPH_BLOCKED_SHAPE_GAP"


def test_ranking_contradiction_theme_and_tiebreakers_and_weak_linkage():
    b = _base(recurring=["valuation_pressure"])
    b["e2_payload"]["contradiction_evidence_map"] = [{"supporting_evidence_refs": ["EA"]}]
    b["d8_2_payload"]["replay_density_inventory"]["semantic_memory_ref"]["theme_evidence_support_profile"] = [{"supporting_evidence_refs": ["EB"]}]
    out = build_d8_6_evidence_graph_enrichment_linkage_density(
        findings=[{"finding_id": "F1"}, {"finding_id": "F2"}],
        evidence_maps=[
            {"finding_id": "F1", "payload": {"supporting_evidence_refs": ["EA", "EB", "EC"]}},
            {"finding_id": "F2", "payload": {"supporting_evidence_refs": ["EA", "EB", "ED"]}},
        ],
        historical_runs_payloads=[{"evidence_highlights": [{"evidence_ref": "EB"}]}],
        e2_payload=b["e2_payload"],
        d8_2_payload=b["d8_2_payload"],
    )
    cands = out["strongest_evidence_candidates"]
    assert cands[0]["evidence_ref"] == "EA"  # contradiction bonus over EB
    # lexical tie-breaker for equal-score singleton refs EC and ED
    tail = [c["evidence_ref"] for c in cands if c["finding_multiplicity"] == 1]
    assert tail == sorted(tail)
    assert "low_multiplicity_graph" not in out["weakest_linkage_areas"]


def test_no_fabricated_content_and_governance_flags_present():
    b = _base()
    out = build_d8_6_evidence_graph_enrichment_linkage_density(findings=[], evidence_maps=[], historical_runs_payloads=[], e2_payload=b["e2_payload"], d8_2_payload=b["d8_2_payload"])
    assert out["strongest_supporting_evidence"]["status"] == "Unavailable"
    assert "summary" not in out["strongest_supporting_evidence"]
    assert out["forbidden_capability_inventory"]["writes"] is False
    assert out["forbidden_capability_inventory"]["network_calls"] is False
