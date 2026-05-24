from transmission_layers.expectation_failure.expectation_intelligence.d8_b2r2_supabase_runtime_connectivity import (
    audit_supabase_read_only_connectivity,
    audit_supabase_runtime_credentials,
    build_d8_b2r2_connectivity_report_payload,
    compare_dashboard_vs_operator_runtime_credentials,
)
from transmission_layers.expectation_failure.expectation_intelligence.d8_b2r_replay_candidate_source_repair_audit import build_d8_b2r_source_repair_report_payload


class _Result:
    def __init__(self, data=None, count=None):
        self.data = data or []
        self.count = count


class _Table:
    def __init__(self, fail=False, error_message="read failed"):
        self.fail = fail
        self.error_message = error_message
        self.ops = []
        self.selected = None

    def select(self, *args, **_kwargs):
        self.ops.append("select")
        self.selected = args[0] if args else None
        if self.fail:
            raise RuntimeError(self.error_message)
        return self

    def limit(self, *_args, **_kwargs):
        self.ops.append("limit")
        return self

    def execute(self):
        self.ops.append("execute")
        return _Result(data=[{"id": 1}], count=1)


class _Client:
    def __init__(self, fail=False, error_message="read failed"):
        self.fail = fail
        self.error_message = error_message
        self.writes = 0
        self.probes = {}

    def table(self, name):
        t = _Table(fail=self.fail, error_message=self.error_message)
        self.probes[name] = t
        return t


def test_credentials_missing():
    audit = audit_supabase_runtime_credentials(env={})
    assert audit["status"] == "CREDENTIALS_MISSING"


def test_credentials_partial():
    audit = audit_supabase_runtime_credentials(env={"SUPABASE_URL": "https://x"})
    assert audit["status"] == "CREDENTIALS_PARTIAL"


def test_credentials_anon_pair():
    audit = audit_supabase_runtime_credentials(env={"SUPABASE_URL": "https://x", "SUPABASE_ANON_KEY": "anon"})
    assert audit["status"] == "CREDENTIALS_READY"


def test_credentials_service_role_pair():
    audit = audit_supabase_runtime_credentials(env={"SUPABASE_URL": "https://x", "SUPABASE_SERVICE_ROLE_KEY": "svc"})
    assert audit["status"] == "CREDENTIALS_READY"


def test_credentials_alias_pair():
    audit = audit_supabase_runtime_credentials(env={"SUPABASE_URL": "https://x", "SUPABASE_KEY": "alias"})
    assert audit["status"] == "CREDENTIALS_READY"


def test_no_secret_leakage():
    audit = audit_supabase_runtime_credentials(env={"SUPABASE_URL": "https://x", "SUPABASE_KEY": "super-secret"})
    assert "super-secret" not in str(audit)


def test_connectivity_not_attempted_when_missing():
    cred = audit_supabase_runtime_credentials(env={})
    out = audit_supabase_read_only_connectivity(credential_audit=cred)
    assert out["read_only_connectivity_status"] == "READ_ONLY_CONNECTIVITY_NOT_ATTEMPTED"


def test_connectivity_success_with_injected_client():
    cred = audit_supabase_runtime_credentials(env={"SUPABASE_URL": "https://x", "SUPABASE_KEY": "k"})
    client = _Client()
    out = audit_supabase_read_only_connectivity(credential_audit=cred, client=client)
    assert out["client_status"] == "CLIENT_RESOLVED"
    assert out["read_only_connectivity_status"] == "READ_ONLY_CONNECTIVITY_OK"
    assert client.probes["dashboard_replay_metadata_records"].selected == "record_id"
    assert out["table_probe"][0]["probe_column_assumption_removed"] is True


def test_connectivity_failure_handling():
    cred = audit_supabase_runtime_credentials(env={"SUPABASE_URL": "https://x", "SUPABASE_KEY": "k"})
    out = audit_supabase_read_only_connectivity(credential_audit=cred, client=_Client(fail=True))
    assert out["read_only_connectivity_status"] == "READ_ONLY_CONNECTIVITY_BLOCKED"
    assert out["connectivity_exception_class"] == "RuntimeError"


def test_missing_column_maps_to_shape_mismatch_not_table_not_found():
    cred = audit_supabase_runtime_credentials(env={"SUPABASE_URL": "https://x", "SUPABASE_KEY": "k"})
    out = audit_supabase_read_only_connectivity(
        credential_audit=cred,
        client=_Client(fail=True, error_message="column dashboard_replay_metadata_records.id does not exist (SQLSTATE 42703)"),
    )
    assert out["blocked_category"] == "shape_mismatch"
    assert out["blocked_category"] != "table_not_found"
    assert out["table_probe"][-1]["table_probe_error_code"] == "42703"


def test_dashboard_operator_comparison():
    out = compare_dashboard_vs_operator_runtime_credentials(
        dashboard_runtime={"supabase_url_present": True, "supabase_key_present": True},
        operator_runtime={"supabase_url_present": False, "supabase_key_present": False},
    )
    assert out["runtime_mismatch_detected"] is True


def test_d8_b2r_integration_status_mapping():
    report = build_d8_b2r2_connectivity_report_payload(
        credential_audit={"status": "CREDENTIALS_MISSING"},
        connectivity_audit={"client_status": "CLIENT_UNRESOLVED", "read_only_connectivity_status": "READ_ONLY_CONNECTIVITY_NOT_ATTEMPTED"},
        dashboard_operator_comparison={},
    )
    d8 = build_d8_b2r_source_repair_report_payload(client_audit={"client_resolved": False}, source_audit={"accessible_tables": []}, runtime_connectivity=report)
    assert d8["recommendation"] == "BLOCKED_MISSING_CREDENTIALS"


def test_no_write_governance_boundary():
    cred = audit_supabase_runtime_credentials(env={"SUPABASE_URL": "https://x", "SUPABASE_KEY": "k"})
    out = audit_supabase_read_only_connectivity(credential_audit=cred, client=_Client())
    assert all("insert" not in str(x).lower() for x in [cred, out])


def test_status_mapping_for_connectivity_categories():
    runtime = {
        "recommendation": "BLOCKED_READ_ONLY_CONNECTIVITY",
        "connectivity_audit": {"blocked_category": "permission_failure"},
    }
    d8 = build_d8_b2r_source_repair_report_payload(client_audit={"client_resolved": True}, source_audit={}, runtime_connectivity=runtime)
    assert d8["status"] == "SOURCE_BLOCKED_PERMISSION_FAILURE"


def test_status_mapping_for_shape_mismatch():
    runtime = {
        "recommendation": "BLOCKED_READ_ONLY_CONNECTIVITY",
        "connectivity_audit": {"blocked_category": "shape_mismatch"},
    }
    d8 = build_d8_b2r_source_repair_report_payload(client_audit={"client_resolved": True}, source_audit={}, runtime_connectivity=runtime)
    assert d8["status"] == "SOURCE_BLOCKED_SHAPE_MISMATCH"
