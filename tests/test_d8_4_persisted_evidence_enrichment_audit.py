from transmission_layers.expectation_failure.dashboard_operationalization.d7_streamlit_dashboard_viewer import build_d7_dashboard_view_model


def _payload(rows):
    return {"rows": rows, "row_count": len(rows), "status": "ok" if rows else "empty"}


def test_d8_4_evidence_linkage_and_replay_continuity_and_contradictions():
    findings = _payload([
        {"record_id": "F1", "finding_id": "F1", "finding_title": "Liquidity stress", "finding_type": "liquidity", "finding_severity": "high", "finding_direction": "worsening", "confidence_label": "high", "created_at": "2026-05-20T00:00:00Z", "payload": {"finding_summary": "stress"}},
        {"record_id": "F2", "finding_id": "F2", "finding_title": "Valuation conflict", "finding_type": "valuation", "finding_severity": "medium", "finding_direction": "mixed", "confidence_label": "medium", "created_at": "2026-05-21T00:00:00Z", "payload": {"finding_summary": "conflict", "contradiction_or_divergence_notes": "valuation conflict"}},
    ])
    narratives = _payload([])
    evidence = _payload([
        {"record_id": "E1", "finding_id": "F1", "created_at": "2026-05-20T01:00:00Z", "payload": {"supporting_evidence_refs": ["EV-1"], "evidence_summary": "spread widening"}},
        {"record_id": "E2", "finding_id": "F2", "created_at": "2026-05-21T01:00:00Z", "payload": {"supporting_evidence_refs": ["EV-2"], "evidence_summary": "multiple divergence contradiction"}},
    ])
    integrity = {
        "manifests": _payload([]),
        "audits": _payload([]),
        "replay": _payload([
            {"record_id": "R1", "replay_id": "RUN-1", "created_at": "2026-05-20T02:00:00Z", "payload": {"run_id": "RUN-1", "run_timestamp": "2026-05-20T02:00:00Z", "semantic": {"themes": ["liquidity"]}, "contradictions": {"claims": ["valuation conflict"]}}},
            {"record_id": "R2", "replay_id": "RUN-2", "created_at": "2026-05-21T02:00:00Z", "payload": {"run_id": "RUN-2", "run_timestamp": "2026-05-21T02:00:00Z", "semantic": {"themes": ["liquidity", "valuation"]}, "contradictions": {"claims": ["valuation conflict"]}}},
        ]),
    }

    vm = build_d7_dashboard_view_model(findings_payload=findings, narratives_payload=narratives, evidence_payload=evidence, integrity_payload=integrity)
    d82 = vm["d8_2_replay_density_expansion"]
    inv = d82["replay_density_inventory"]
    assert inv["runs_observed"] == 2
    assert inv["evidence_count"] == 2
    assert any(x["evidence_ref"] == "EV-1" and x["linkage_density"] >= 1 for x in inv["evidence_lineage"])
    assert d82["semantic_persistence_summary"]["recurring_themes"] == ["liquidity"]
    assert d82["contradiction_persistence_summary"]["tracked_contradiction_themes"]
    edges = d82["evidence_relationship_graph"]["edges"]
    assert any(e["from"] == "EV-1" and e["to"] == "F1" for e in edges)


def test_d8_4_sparse_history_degrades_honestly_no_fabrication():
    vm = build_d7_dashboard_view_model(
        findings_payload=_payload([]),
        narratives_payload=_payload([]),
        evidence_payload=_payload([]),
        integrity_payload={"manifests": _payload([]), "audits": _payload([]), "replay": _payload([])},
    )
    d82 = vm["d8_2_replay_density_expansion"]
    assert d82["replay_density_inventory"]["runs_observed"] == 0
    assert d82["semantic_persistence_summary"]["themes_observed"] == []
    assert d82["contradiction_persistence_summary"]["persistence_count"] == 0
    assert d82["forbidden_capability_inventory"]["writes"] is False
