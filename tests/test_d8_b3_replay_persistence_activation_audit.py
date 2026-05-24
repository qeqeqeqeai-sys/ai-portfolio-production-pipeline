from transmission_layers.expectation_failure.expectation_intelligence.d8_b3_replay_persistence_activation_audit import (
    STATUSES,
    audit_replay_persistence_gates,
    build_d8_b3_replay_activation_report_payload,
)

class Resp:
    def __init__(self, data): self.data = data
class Table:
    def __init__(self, rows): self.rows = rows
    def select(self, *_): return self
    def limit(self, *_): return self
    def execute(self): return Resp(self.rows)
class Client:
    def __init__(self, tables): self.tables=tables
    def table(self, name): return Table(self.tables.get(name, []))

def test_replay_persistence_disabled():
    out = build_d8_b3_replay_activation_report_payload(client=Client({}), persistence_enabled=False)
    assert out["status"] == STATUSES["DISABLED"]

def test_empty_replay_output():
    out = build_d8_b3_replay_activation_report_payload(client=Client({"dashboard_replay_metadata_records":[],"dashboard_export_manifests":[]}), persistence_enabled=True)
    assert out["status"] in {STATUSES["EMPTY_OUTPUT"], STATUSES["DRY_RUN_BLOCKED"]}

def test_replay_payload_completeness_and_manifest_detection():
    c = Client({
        "dashboard_replay_metadata_records":[{"record_id":"R1","replay_checksum":"x","payload":{},"replay_metadata":{}}],
        "dashboard_export_manifests":[{"record_id":"M1","manifest_checksum":"m","payload":{},"replay_metadata":{}}],
    })
    out = build_d8_b3_replay_activation_report_payload(client=c, dry_run=True)
    assert out["record_production"]["deterministic_checksum_lineage_present"] is True
    assert out["record_production"]["manifest_payload_count"] == 1

def test_dry_run_preview_and_no_write_confirmation():
    out = build_d8_b3_replay_activation_report_payload(client=Client({}), dry_run=True)
    assert out["dry_run_seeding_preview"]["no_write_confirmation"] is True

def test_approved_table_validation_and_no_uncontrolled_writes():
    gates = audit_replay_persistence_gates(dry_run=True, persistence_enabled=True, client_resolved=True)
    assert "dry_run_no_write_gate" in gates["blocked_reasons"]

def test_no_secret_leakage_and_d8b2_compatibility_shape():
    out = build_d8_b3_replay_activation_report_payload(client=Client({}))
    assert "supabase_key" not in str(out).lower()
    assert "candidate_inventory_potential" in out["record_production"]
