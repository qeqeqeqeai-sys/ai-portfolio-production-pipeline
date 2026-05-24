from transmission_layers.expectation_failure.dashboard_operationalization.d7_streamlit_dashboard_viewer import (
    build_d7_dashboard_view_model,
    load_d7_dashboard_evidence_maps,
    load_d7_dashboard_findings,
    load_d7_dashboard_narratives,
    load_d7_dashboard_operational_integrity,
)


class _Resp:
    def __init__(self, data):
        self.data = data


class _Query:
    def __init__(self, rows):
        self.rows = list(rows)

    def select(self, _):
        return self

    def order(self, key, desc=True):
        self.rows = sorted(self.rows, key=lambda x: str(x.get(key) or ""), reverse=desc)
        return self

    def limit(self, n):
        self.rows = self.rows[:n]
        return self

    def execute(self):
        return _Resp(self.rows)


class FakeReadOnlyClient:
    def __init__(self, tables):
        self.tables = tables
        self.write_calls = []

    def table(self, name):
        return _Query(self.tables.get(name, []))

    def insert(self, *args, **kwargs):
        self.write_calls.append((args, kwargs))


def _build_client():
    return FakeReadOnlyClient({
        "dashboard_finding_records": [
            {"finding_id": "F2", "run_id": "run-2", "created_at": "2026-05-24T01:00:00Z", "finding_title": "Elevated spread", "finding_type": "credit", "severity": "high", "direction": "worsening", "confidence": 0.86, "finding_summary": "spread widening", "evidence_refs": ["EV2"], "lineage_refs": ["O5"]},
            {"finding_id": "F1", "run_id": "run-1", "created_at": "2026-05-23T01:00:00Z", "finding_title": "Valuation stretch", "finding_type": "valuation", "severity": "medium", "direction": "worsening", "confidence": 0.74, "finding_summary": "percentile elevated", "evidence_refs": ["EV1"], "lineage_refs": ["O5"]},
        ],
        "dashboard_narrative_records": [
            {"record_id": "N1", "run_id": "run-2", "created_at": "2026-05-24T01:00:00Z", "narrative_section": "expectation_fragility", "narrative_text": "Fragility concentrated in AI semis.", "related_findings": ["F2"]}
        ],
        "dashboard_evidence_map_records": [
            {"record_id": "E1", "run_id": "run-2", "created_at": "2026-05-24T01:00:00Z", "finding_id": "F2", "evidence_ref": "EV2", "evidence_metadata": {"metric": "credit_spread"}}
        ],
        "dashboard_export_manifests": [
            {"manifest_id": "M1", "run_id": "run-2", "created_at": "2026-05-24T01:00:00Z", "export_manifest_checksum": "chk-export", "record_counts": {"findings": 2}}
        ],
        "dashboard_persistence_audit_records": [
            {"audit_id": "A1", "run_id": "run-2", "created_at": "2026-05-24T01:00:00Z", "audit_status": "EXECUTED", "persisted_record_count": 4, "target_table": "dashboard_finding_records"}
        ],
        "dashboard_replay_metadata_records": [
            {"replay_id": "R1", "run_id": "run-2", "created_at": "2026-05-24T01:00:00Z", "replay_checksum": "chk-replay", "continuity_status": "VERIFIED"}
        ],
    })


def test_d7_helper_api_presence_and_import_smoke():
    assert callable(load_d7_dashboard_findings)
    assert callable(load_d7_dashboard_narratives)
    assert callable(load_d7_dashboard_evidence_maps)
    assert callable(load_d7_dashboard_operational_integrity)
    assert callable(build_d7_dashboard_view_model)


def test_d7_view_model_deterministic_shape_and_ordering():
    client = _build_client()
    findings = load_d7_dashboard_findings(client)
    narratives = load_d7_dashboard_narratives(client)
    evidence = load_d7_dashboard_evidence_maps(client)
    integrity = load_d7_dashboard_operational_integrity(client)

    vm1 = build_d7_dashboard_view_model(findings_payload=findings, narratives_payload=narratives, evidence_payload=evidence, integrity_payload=integrity)
    vm2 = build_d7_dashboard_view_model(findings_payload=findings, narratives_payload=narratives, evidence_payload=evidence, integrity_payload=integrity)

    assert vm1["view_model_checksum"] != ""
    assert vm1["findings"][0]["finding_id"] == "F2"
    assert vm1["overview"]["latest_operational_run"] == "run-2"
    assert vm1["schema_version"] == vm2["schema_version"]
    assert vm1["invariant_flags"]["read_only"] is True


def test_d7_missing_data_degraded_and_no_write_guarantee():
    findings = load_d7_dashboard_findings(None)
    narratives = load_d7_dashboard_narratives(None)
    evidence = load_d7_dashboard_evidence_maps(None)
    integrity = load_d7_dashboard_operational_integrity(None)
    vm = build_d7_dashboard_view_model(findings_payload=findings, narratives_payload=narratives, evidence_payload=evidence, integrity_payload=integrity)

    assert findings["status"] == "degraded"
    assert vm["overview"]["latest_operational_run"] is None
    assert vm["integrity"]["latest_export_manifest_checksum"] is None
    assert vm["invariant_flags"]["no_writes"] is True


def test_d7_supabase_abstraction_boundary_read_only_usage():
    client = _build_client()
    _ = load_d7_dashboard_findings(client)
    _ = load_d7_dashboard_operational_integrity(client)
    assert client.write_calls == []
