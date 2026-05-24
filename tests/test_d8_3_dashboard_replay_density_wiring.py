from transmission_layers.expectation_failure.dashboard_operationalization.d7_streamlit_dashboard_viewer import build_d7_dashboard_view_model


def _payload(rows):
    return {"status": "ok", "row_count": len(rows), "rows": rows, "error": None}


def test_d8_2_payload_is_included_and_graceful_without_history():
    vm = build_d7_dashboard_view_model(
        findings_payload=_payload([{"record_id": "F1", "created_at": "2026-05-24T00:00:00Z", "finding_id": "F1", "finding_title": "Title", "finding_type": "risk", "finding_severity": "high", "payload": {"finding_summary": "summary"}, "evidence_refs": ["EV1"]}]),
        narratives_payload=_payload([{"record_id": "N1", "created_at": "2026-05-24T00:00:00Z", "payload": {"narrative_text": "n"}}]),
        evidence_payload=_payload([{"record_id": "E1", "created_at": "2026-05-24T00:00:00Z", "evidence_ref": "EV1", "payload": {"evidence_metadata": {"k": "v"}}}]),
        integrity_payload={"manifests": _payload([]), "audits": _payload([]), "replay": _payload([])},
        historical_runs_payloads=[],
    )
    assert "d8_2_replay_density_expansion" in vm
    assert "d8_2_dashboard" in vm
    assert vm["d8_2_dashboard"]["semantic_persistence_summary"].get("themes_observed") == []
    assert vm["d8_2_dashboard"]["replay_continuity_summary"].get("runs_observed") == 0
    assert "raw_d8_2_payload" in vm["debug_payload_sections"]
