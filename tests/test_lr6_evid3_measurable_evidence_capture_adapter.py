from pathlib import Path

from transmission_layers.expectation_failure import replay_ecology as mod


def _full_payload():
    metrics = {}
    for row in mod.build_lr6_evid2_metric_field_definitions():
        metrics[row["metric_dimension"]] = {k: 1 for k in row["required_fields"]}
    return {
        "wave_id": "W1",
        "candidate_scope_id": "SCOPE1",
        "candidate_count": 42,
        "timestamp_or_snapshot_label": "SNAP1",
        "metrics": metrics,
    }


def test_public_apis_exist():
    for name in [
        "build_lr6_evid3_adapter_context",
        "build_lr6_evid3_supported_payload_contracts",
        "adapt_lr6_evid3_payload_to_evidence_records",
        "adapt_lr6_evid3_baseline_payload",
        "adapt_lr6_evid3_enriched_payload",
        "build_lr6_evid3_metric_extractors",
        "build_lr6_evid3_extraction_quality_report",
        "build_lr6_evid3_comparison_readiness_report",
        "build_lr6_evid3_evid1_ready_payload",
        "build_lr6_evid3_supervisor_review",
        "build_lr6_evid3_markdown_report",
        "certify_lr6_evid3_adapter_boundary",
    ]:
        assert hasattr(mod, name)


def test_deterministic_output_and_seven_records_per_phase():
    payload = _full_payload()
    one = mod.adapt_lr6_evid3_baseline_payload(payload)
    two = mod.adapt_lr6_evid3_baseline_payload(payload)
    assert one == two
    assert len(one) == 7


def test_measured_partial_missing_statuses():
    payload = _full_payload()
    recs = mod.adapt_lr6_evid3_baseline_payload(payload)
    assert all(r["evidence_status"] == "MEASURED" for r in recs)

    dim = mod.EVID1_DIMENSIONS[0]
    required = mod.build_lr6_evid3_metric_extractors()[dim]["required_fields"]
    partial_payload = _full_payload()
    partial_payload["metrics"][dim] = {required[0]: 1}
    partial = [r for r in mod.adapt_lr6_evid3_baseline_payload(partial_payload) if r["metric_dimension"] == dim][0]
    assert partial["evidence_status"] == "PARTIAL"

    missing_payload = _full_payload()
    missing_payload["metrics"][dim] = {}
    missing = [r for r in mod.adapt_lr6_evid3_baseline_payload(missing_payload) if r["metric_dimension"] == dim][0]
    assert missing["evidence_status"] == "MISSING"


def test_scaffold_only_blocks_comparison_ready():
    payload = {
        "wave_id": "W1",
        "candidate_scope_id": "S1",
        "review": {"summary": "scaffold"},
        "governance": {"status": "draft"},
        "candidates": ["A", "B"],
    }
    recs = mod.adapt_lr6_evid3_payload_to_evidence_records(payload, "RUN1_REVIEW", "run1", "replay_ecology")
    assert len(recs) == 7
    assert all(r["evidence_status"] == "SCAFFOLD_ONLY" for r in recs)
    assert all(r["scaffold_only"] is True for r in recs)
    assert all(r["comparison_ready"] is False for r in recs)


def test_comparison_ready_requires_identifiers_and_measured():
    payload = _full_payload()
    recs = mod.adapt_lr6_evid3_baseline_payload(payload)
    assert all(r["comparison_ready"] is True for r in recs)

    bad = _full_payload()
    bad["candidate_scope_id"] = None
    recs2 = mod.adapt_lr6_evid3_baseline_payload(bad)
    assert all(r["comparison_ready"] is False for r in recs2)


def test_evid1_ready_payload_grouping_and_boundary_and_report():
    b = mod.adapt_lr6_evid3_baseline_payload(_full_payload())
    e = mod.adapt_lr6_evid3_enriched_payload(_full_payload())
    grouped = mod.build_lr6_evid3_evid1_ready_payload(b, e)
    assert set(grouped["paired_dimensions"]) == set(mod.EVID1_DIMENSIONS)
    assert set(grouped["comparison_ready_dimensions"]) == set(mod.EVID1_DIMENSIONS)

    boundary = mod.certify_lr6_evid3_adapter_boundary()
    assert boundary["adapter_only"] is True
    assert boundary["evidence_only"] is True
    assert boundary["execution_authorized"] is False
    assert boundary["no_direct_sql"] is True
    assert boundary["no_live_ingestion"] is True
    assert boundary["no_persistence_write"] is True
    assert boundary["no_prediction"] is True
    assert boundary["no_trading"] is True

    report = mod.build_lr6_evid3_markdown_report()
    for section in [
        "## objective",
        "## EVID1/EVID1A/EVID2 basis",
        "## supported payload contracts",
        "## evidence record output structure",
        "## metric extractors",
        "## scaffold-only detection",
        "## comparison readiness rules",
        "## EVID1-ready payload format",
        "## quality report behavior",
        "## boundary certification",
    ]:
        assert section in report

    file_report = Path("reports/lr6_evid3_measurable_evidence_capture_adapter.md").read_text(encoding="utf-8")
    assert "## objective" in file_report


def test_no_execution_sql_persistence_prediction_trading_paths():
    review = mod.build_lr6_evid3_supervisor_review()
    boundary = review["boundary_certification"]
    assert boundary["execution_authorized"] is False
    assert boundary["no_direct_sql"] is True
    assert boundary["no_live_ingestion"] is True
    assert boundary["no_persistence_write"] is True
    assert boundary["no_prediction"] is True
    assert boundary["no_trading"] is True
