from transmission_layers.expectation_failure.expectation_intelligence import (
    build_d9_persisted_evidence_inventory,
    validate_d9_finding_generation_eligibility,
    build_d9_operational_findings,
    build_d9_expectation_intelligence_summary,
    certify_d9_finding_generation,
    build_d9_dashboard_operational_cards,
    build_d9_report_payload,
    build_d9_report_markdown,
)


def _d8c_seed(cert="CERTIFIED_DASHBOARD_CONSUMABLE", lineage="LINEAGE_OK", replay_count=2, manifest_count=1):
    return {
        "replay_row_count": replay_count,
        "manifest_row_count": manifest_count,
        "replay_ids": ["R2", "R1"],
        "manifest_checksums": ["M1"],
        "latest_replay_ids": ["R2"],
        "latest_manifest_checksums": ["M1"],
    }, {"lineage_status": lineage}, {"replay_candidate_readiness": "READY" if replay_count and manifest_count else "NOT_READY"}, {"certification_status": cert}


def test_api_export_presence():
    assert callable(build_d9_persisted_evidence_inventory)
    assert callable(build_d9_report_markdown)


def test_deterministic_ordering_and_immutability():
    inv_in, lin, model, cert = _d8c_seed()
    snap = dict(inv_in)
    d9inv = build_d9_persisted_evidence_inventory(d8c_readback_inventory=inv_in, d8c_lineage_validation=lin, d8c_dashboard_consumption_model=model, d8c_certification=cert)
    assert d9inv["replay_ids"] == ["R1", "R2"]
    assert inv_in == snap


def test_blocked_when_d8c_blocked():
    inv_in, lin, model, cert = _d8c_seed(cert="BLOCKED_DASHBOARD_CONSUMPTION")
    d9inv = build_d9_persisted_evidence_inventory(d8c_readback_inventory=inv_in, d8c_lineage_validation=lin, d8c_dashboard_consumption_model=model, d8c_certification=cert)
    elig = validate_d9_finding_generation_eligibility(persisted_evidence_inventory=d9inv)
    findings = build_d9_operational_findings(persisted_evidence_inventory=d9inv, eligibility_validation=elig)
    assert elig["eligibility_status"] == "FINDING_GENERATION_BLOCKED"
    assert findings == []


def test_degraded_eligibility_behavior():
    inv_in, lin, model, cert = _d8c_seed(lineage="LINEAGE_DEGRADED")
    d9inv = build_d9_persisted_evidence_inventory(d8c_readback_inventory=inv_in, d8c_lineage_validation=lin, d8c_dashboard_consumption_model=model, d8c_certification=cert)
    elig = validate_d9_finding_generation_eligibility(persisted_evidence_inventory=d9inv)
    assert elig["eligibility_status"] == "FINDING_GENERATION_DEGRADED"


def test_certified_finding_generation_path_and_required_fields_and_ranking():
    inv_in, lin, model, cert = _d8c_seed()
    d9inv = build_d9_persisted_evidence_inventory(d8c_readback_inventory=inv_in, d8c_lineage_validation=lin, d8c_dashboard_consumption_model=model, d8c_certification=cert)
    elig = validate_d9_finding_generation_eligibility(persisted_evidence_inventory=d9inv)
    findings = build_d9_operational_findings(persisted_evidence_inventory=d9inv, eligibility_validation=elig)
    summary = build_d9_expectation_intelligence_summary(eligibility_validation=elig, operational_findings=findings)
    c9 = certify_d9_finding_generation(persisted_evidence_inventory=d9inv, eligibility_validation=elig, operational_findings=findings)
    assert c9["certification_status"] == "CERTIFIED_FINDING_GENERATION"
    req = {"finding_id", "category", "finding_title", "finding_summary", "supporting_evidence_refs", "replay_ids", "manifest_checksums", "confidence_band", "operational_interpretation", "caveats", "severity", "deterministic_rank"}
    assert all(req.issubset(set(f.keys())) for f in findings)
    assert [f["deterministic_rank"] for f in findings] == sorted([f["deterministic_rank"] for f in findings])
    assert summary["finding_count"] >= 1


def test_no_secret_leakage_no_sql_usage_and_bounded_non_predictive():
    inv_in, lin, model, cert = _d8c_seed()
    d9inv = build_d9_persisted_evidence_inventory(d8c_readback_inventory=inv_in, d8c_lineage_validation=lin, d8c_dashboard_consumption_model=model, d8c_certification=cert)
    elig = validate_d9_finding_generation_eligibility(persisted_evidence_inventory=d9inv)
    findings = build_d9_operational_findings(persisted_evidence_inventory=d9inv, eligibility_validation=elig)
    blob = str(findings).lower() + str(d9inv).lower()
    assert "api_key" not in blob and "supabase_key" not in blob
    assert "select " not in blob and "insert " not in blob and "update " not in blob and "delete " not in blob
    assert "predict" not in blob and "alpha" not in blob and "trading signal" not in blob


def test_dashboard_cards_required_fields_and_stable_checksum_and_report_behavior():
    inv_in, lin, model, cert = _d8c_seed()
    d9inv1 = build_d9_persisted_evidence_inventory(d8c_readback_inventory=inv_in, d8c_lineage_validation=lin, d8c_dashboard_consumption_model=model, d8c_certification=cert)
    d9inv2 = build_d9_persisted_evidence_inventory(d8c_readback_inventory=inv_in, d8c_lineage_validation=lin, d8c_dashboard_consumption_model=model, d8c_certification=cert)
    assert d9inv1["inventory_checksum"] == d9inv2["inventory_checksum"]
    elig = validate_d9_finding_generation_eligibility(persisted_evidence_inventory=d9inv1)
    findings = build_d9_operational_findings(persisted_evidence_inventory=d9inv1, eligibility_validation=elig)
    summary = build_d9_expectation_intelligence_summary(eligibility_validation=elig, operational_findings=findings)
    cert9 = certify_d9_finding_generation(persisted_evidence_inventory=d9inv1, eligibility_validation=elig, operational_findings=findings)
    cards = build_d9_dashboard_operational_cards(expectation_intelligence_summary=summary, certification=cert9)
    req_cards = {"finding_generation_status", "dominant_operational_state", "finding_count", "replay_operational_readiness", "evidence_confidence_band", "strongest_integrity_signal", "strongest_operational_constraint", "unresolved_constraints", "recommendation"}
    assert req_cards.issubset(set(cards.keys()))
    report = build_d9_report_payload(persisted_evidence_inventory=d9inv1, eligibility_validation=elig, operational_findings=findings, expectation_intelligence_summary=summary, dashboard_cards=cards, certification=cert9)
    md = build_d9_report_markdown(report_payload=report)
    assert report["no_direct_sql_bypass_used"] is True
    assert "Governance Boundaries" in md


def test_governance_integrity_finding_present_when_governance_intact():
    inv_in, lin, model, cert = _d8c_seed()
    d9inv = build_d9_persisted_evidence_inventory(d8c_readback_inventory=inv_in, d8c_lineage_validation=lin, d8c_dashboard_consumption_model=model, d8c_certification=cert)
    elig = validate_d9_finding_generation_eligibility(persisted_evidence_inventory=d9inv)
    findings = build_d9_operational_findings(persisted_evidence_inventory=d9inv, eligibility_validation=elig)
    cats = {f["category"] for f in findings}
    assert "governance_integrity" in cats
