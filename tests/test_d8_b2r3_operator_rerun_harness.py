from pathlib import Path

from transmission_layers.expectation_failure.expectation_intelligence import d8_b2r3_operator_rerun_harness as mod


class _R:
    def __init__(self, data=None, count=None):
        self.data = data or []
        self.count = count


class _T:
    def __init__(self, rows):
        self.rows = rows

    def select(self, *_a, **_k):
        return self

    def limit(self, *_a, **_k):
        return self

    def execute(self):
        return _R(data=self.rows, count=len(self.rows))


class _ReadOnlyClient:
    def __init__(self, mapping):
        self.mapping = mapping

    def table(self, name):
        return _T(self.mapping.get(name, []))


def test_missing_credentials_is_safe_blocked_status():
    out = mod.build_operator_rerun_payload(env={})
    assert out["credential_audit"]["status"] == "CREDENTIALS_MISSING"
    assert out["connectivity_audit"]["read_only_connectivity_status"] == "READ_ONLY_CONNECTIVITY_NOT_ATTEMPTED"
    assert out["final_status"] == "SOURCE_BLOCKED_CREDENTIALS_MISSING"


def test_secret_safety_and_no_leakage():
    secret = "super-secret-key"
    out = mod.build_operator_rerun_payload(env={"SUPABASE_URL": "https://x.supabase.co", "SUPABASE_KEY": secret})
    rendered = mod.render_operator_report(out)
    assert secret not in str(out)
    assert secret not in rendered
    assert "supabase_url_present" in rendered
    assert "fingerprint" in rendered.lower()


def test_read_only_client_no_write_apis_called():
    client = _ReadOnlyClient({
        "dashboard_replay_metadata_records": [{"run_id": "r1", "run_timestamp": "2026-05-20T00:00:00Z", "payload_checksum": "c1", "source_trace": "persisted_replay", "payload_reference": "p1"}],
        "dashboard_export_manifests": [{"manifest_id": "m1"}],
    })
    out = mod.build_operator_rerun_payload(
        env={"SUPABASE_URL": "https://x.supabase.co", "SUPABASE_KEY": "k"},
        runtime_config={"supabase_url": "https://x.supabase.co", "supabase_key": "k", "credentials_present": True},
        client=client,
    )
    assert out["no_write_confirmed"] is True
    assert out["connectivity_audit"]["read_only_connectivity_status"] == "READ_ONLY_CONNECTIVITY_OK"


def test_report_write_and_deterministic_schema(tmp_path: Path):
    p = tmp_path / "report.md"
    out = mod.run_and_write_report(report_path=p, env={})
    text = p.read_text(encoding="utf-8")
    for key in [
        "Execution timestamp (UTC)", "credential_status", "client_status", "read_only_connectivity_status",
        "expected_tables", "accessible_tables", "replay_metadata_row_count", "manifest_row_count",
        "dashboard_replay_row_count", "d7_derived_historical_source_count", "d8_b2_candidate_source_count",
        "final_status", "recommendation", "Explicit no-write confirmation"
    ]:
        assert key in text
    assert out["recommendation"] in {"BLOCKED_MISSING_CREDENTIALS", "BLOCKED_PARTIAL_CREDENTIALS", "BLOCKED_CLIENT_CONSTRUCTION", "BLOCKED_READ_ONLY_CONNECTIVITY", "READY_FOR_D8_B2R_RERUN", "BLOCKED_CLIENT_CONFIGURATION", "BLOCKED_EMPTY_SOURCE", "BLOCKED_SCHEMA_OR_SHAPE_MISMATCH", "BLOCKED_NO_VALID_CANDIDATES", "READY_FOR_D8_B2_DRY_RUN_RETRY"}
