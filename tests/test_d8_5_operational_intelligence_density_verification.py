from transmission_layers.expectation_failure.dashboard_operationalization.d7_streamlit_dashboard_viewer import build_d7_dashboard_view_model


def _payload(rows):
    return {"rows": rows, "row_count": len(rows), "status": "ok" if rows else "empty"}


def _build_vm(*, findings_rows, evidence_rows, replay_rows):
    return build_d7_dashboard_view_model(
        findings_payload=_payload(findings_rows),
        narratives_payload=_payload([]),
        evidence_payload=_payload(evidence_rows),
        integrity_payload={"manifests": _payload([]), "audits": _payload([]), "replay": _payload(replay_rows)},
    )


def test_d8_5_density_operational_and_backfill_not_required():
    vm = _build_vm(
        findings_rows=[
            {"record_id": "F1", "finding_id": "F1", "finding_type": "liq", "finding_title": "Liquidity", "confidence_label": "high", "payload": {"contradiction_or_divergence_notes": "valuation conflict"}},
            {"record_id": "F2", "finding_id": "F2", "finding_type": "val", "finding_title": "Valuation", "confidence_label": "medium"},
        ],
        evidence_rows=[
            {"record_id": "E1", "finding_id": "F1", "payload": {"supporting_evidence_refs": ["EV-1"]}},
            {"record_id": "E2", "finding_id": "F2", "payload": {"supporting_evidence_refs": ["EV-2"]}},
        ],
        replay_rows=[
            {"record_id": "R1", "replay_id": "RUN-1", "created_at": "2026-05-20T00:00:00Z", "payload": {"run_id": "RUN-1", "run_timestamp": "2026-05-20T00:00:00Z", "semantic": {"themes": ["liquidity"]}, "contradictions": {"claims": ["valuation conflict"]}}},
            {"record_id": "R2", "replay_id": "RUN-2", "created_at": "2026-05-21T00:00:00Z", "payload": {"run_id": "RUN-2", "run_timestamp": "2026-05-21T00:00:00Z", "semantic": {"themes": ["liquidity", "valuation"]}, "contradictions": {"claims": ["valuation conflict"]}}},
        ],
    )
    d = vm["d8_5_operational_intelligence_density_verification"]
    b = vm["d8_5_supabase_backfill_readiness"]
    assert d["readiness_status"] == "DENSITY_OPERATIONAL"
    assert d["findings_with_evidence_linkage"] == 2
    assert d["historical_runs_derived"] == 2
    assert d["recurring_semantic_themes_detected"] == 1
    assert d["contradiction_claims_detected"] >= 1
    assert d["strongest_supporting_evidence_available"] is True
    assert b["recommendation"] == "NO_BACKFILL_REQUIRED"


def test_d8_5_sparse_but_valid_and_no_fake_history():
    vm = _build_vm(
        findings_rows=[{"record_id": "F1", "finding_id": "F1", "finding_type": "liq", "finding_title": "Liquidity"}],
        evidence_rows=[{"record_id": "E1", "finding_id": "F1", "payload": {"supporting_evidence_refs": ["EV-1"]}}],
        replay_rows=[{"record_id": "R1", "replay_id": "RUN-1", "created_at": "2026-05-20T00:00:00Z", "payload": {"run_id": "RUN-1", "run_timestamp": "2026-05-20T00:00:00Z", "semantic": {"themes": ["liquidity"]}}}],
    )
    d = vm["d8_5_operational_intelligence_density_verification"]
    assert d["readiness_status"] == "DENSITY_SPARSE_BUT_VALID"
    assert d["historical_runs_derived"] == 1


def test_d8_5_no_history_blocked_and_backfill_required():
    vm = _build_vm(
        findings_rows=[{"record_id": "F1", "finding_id": "F1", "finding_type": "liq", "finding_title": "Liquidity"}],
        evidence_rows=[{"record_id": "E1", "finding_id": "F1", "payload": {"supporting_evidence_refs": ["EV-1"]}}],
        replay_rows=[],
    )
    d = vm["d8_5_operational_intelligence_density_verification"]
    b = vm["d8_5_supabase_backfill_readiness"]
    assert d["readiness_status"] == "DENSITY_BLOCKED_BY_NO_HISTORY"
    assert "no_history_rows" in d["caveat_reasons"]
    assert b["recommendation"] == "BACKFILL_REQUIRED_FOR_HISTORY_CONTINUITY"


def test_d8_5_checksum_deterministic_and_read_only_flags():
    base = _build_vm(findings_rows=[], evidence_rows=[], replay_rows=[])
    again = _build_vm(findings_rows=[], evidence_rows=[], replay_rows=[])
    assert base["d8_5_operational_intelligence_density_verification"]["d8_5_density_checksum"] == again["d8_5_operational_intelligence_density_verification"]["d8_5_density_checksum"]
    assert base["d8_5_supabase_backfill_readiness"]["dry_run_only"] is True
    assert base["d8_5_supabase_backfill_readiness"]["write_path_enabled"] is False
