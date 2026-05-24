from transmission_layers.expectation_failure.dashboard_operationalization.d7_streamlit_dashboard_viewer import (
    D7_PHYSICAL_COLUMNS_BY_TABLE,
    build_d7_dashboard_view_model,
    build_d7_runtime_diagnostics,
    load_d7_dashboard_evidence_maps,
    load_d7_dashboard_findings,
    load_d7_dashboard_narratives,
    load_d7_dashboard_operational_integrity,
)


class _Resp:
    def __init__(self, data):
        self.data = data


class _Query:
    def __init__(self, rows, client, table):
        self.rows = list(rows)
        self.client = client
        self.table = table

    def select(self, cols):
        self.client.selections.append((self.table, cols))
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
        self.selections = []

    def table(self, name):
        return _Query(self.tables.get(name, []), self, name)

    def insert(self, *args, **kwargs):
        self.write_calls.append((args, kwargs))


def _build_client():
    return FakeReadOnlyClient({
        "dashboard_finding_records": [
            {"record_id": "FR2", "finding_id": "F2", "created_at": "2026-05-24T01:00:00Z", "finding_title": "Elevated spread", "finding_type": "credit", "finding_severity": "high", "finding_direction": "worsening", "confidence_label": "high", "evidence_refs": ["EV2"], "lineage_refs": ["O5"], "source_payload_checksum": "abcdef1234567890", "payload": {"replay_id": "replay-2", "finding_summary": "spread widening"}, "replay_metadata": {}},
        ],
        "dashboard_narrative_records": [
            {"record_id": "N1", "created_at": "2026-05-24T01:00:00Z", "narrative_section": "expectation_fragility", "related_finding_ids": ["F2"], "payload": {"narrative_text": "Fragility concentrated in AI semis."}, "replay_metadata": {"replay_id": "replay-2"}}
        ],
        "dashboard_evidence_map_records": [
            {"record_id": "E1", "created_at": "2026-05-24T01:00:00Z", "finding_id": "F2", "evidence_ref": "EV2", "payload": {"evidence_metadata": {"metric": "credit_spread"}}, "replay_metadata": {}}
        ],
        "dashboard_export_manifests": [
            {"record_id": "MREC1", "manifest_id": "M1", "created_at": "2026-05-24T01:00:00Z", "manifest_checksum": "chk-export", "payload": {"record_counts": {"findings": 1}}, "replay_metadata": {}}
        ],
        "dashboard_persistence_audit_records": [
            {"record_id": "A1", "audit_id": "A1", "created_at": "2026-05-24T01:00:00Z", "write_status": "EXECUTED", "target_table": "dashboard_finding_records", "payload": {}, "replay_metadata": {}}
        ],
        "dashboard_replay_metadata_records": [
            {"record_id": "R1", "replay_id": "R1", "created_at": "2026-05-24T01:00:00Z", "replay_checksum": "chk-replay", "payload": {"continuity_status": "VERIFIED"}, "replay_metadata": {}}
        ],
    })


def test_d7_no_invalid_column_references_in_selects():
    client = _build_client()
    _ = load_d7_dashboard_findings(client)
    _ = load_d7_dashboard_narratives(client)
    _ = load_d7_dashboard_evidence_maps(client)
    _ = load_d7_dashboard_operational_integrity(client)
    invalid = {"severity", "narrative_text", "evidence_metadata", "export_manifest_checksum", "audit_status", "continuity_status"}
    selected_cols = set()
    for _, cols in client.selections:
        selected_cols.update(cols.split(","))
    assert selected_cols.isdisjoint(invalid)


def test_d7_view_model_uses_d2_mappings_and_payload_fallbacks():
    client = _build_client()
    vm = build_d7_dashboard_view_model(
        findings_payload=load_d7_dashboard_findings(client),
        narratives_payload=load_d7_dashboard_narratives(client),
        evidence_payload=load_d7_dashboard_evidence_maps(client),
        integrity_payload=load_d7_dashboard_operational_integrity(client),
    )
    assert vm["findings"][0]["severity"] == "high"
    assert vm["narratives"][0]["narrative_text"] == "Fragility concentrated in AI semis."
    assert vm["evidence_maps"][0]["evidence_metadata"]["metric"] == "credit_spread"
    assert vm["integrity"]["latest_export_manifest_checksum"] == "chk-export"
    assert vm["integrity"]["latest_persistence_audit_status"] == "EXECUTED"
    assert vm["integrity"]["verification_continuity"] == "VERIFIED"


def test_d7_diagnostics_counts_work_without_invalid_columns():
    client = _build_client()
    findings = load_d7_dashboard_findings(client)
    narratives = load_d7_dashboard_narratives(client)
    evidence = load_d7_dashboard_evidence_maps(client)
    integrity = load_d7_dashboard_operational_integrity(client)
    out = build_d7_runtime_diagnostics(
        runtime_config={"supabase_url": "https://abc123.supabase.co", "supabase_key": "anon", "credentials_present": True},
        client_resolution={"client_resolved": True, "client_factory_source": "supabase_package"},
        table_payloads={
            "dashboard_finding_records": findings,
            "dashboard_narrative_records": narratives,
            "dashboard_evidence_map_records": evidence,
            "dashboard_export_manifests": integrity["manifests"],
            "dashboard_persistence_audit_records": integrity["audits"],
            "dashboard_replay_metadata_records": integrity["replay"],
        },
    )
    assert out["table_diagnostics"]["dashboard_finding_records"]["row_count"] == 1


def test_d7_schema_map_has_only_allowed_keys_subset():
    assert "dashboard_finding_records" in D7_PHYSICAL_COLUMNS_BY_TABLE
    assert "severity" not in D7_PHYSICAL_COLUMNS_BY_TABLE["dashboard_finding_records"]
