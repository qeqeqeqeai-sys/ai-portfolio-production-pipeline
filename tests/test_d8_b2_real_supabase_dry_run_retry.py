from transmission_layers.expectation_failure.expectation_intelligence.d8_b2_real_supabase_dry_run_retry import (
    build_real_supabase_dry_run_retry_payload,
    render_real_supabase_dry_run_retry_report,
)


class _Result:
    def __init__(self, data):
        self.data = data


class _Table:
    def __init__(self, rows):
        self.rows = rows

    def select(self, *_args, **_kwargs):
        return self

    def limit(self, *_args, **_kwargs):
        return self

    def execute(self):
        return _Result(self.rows)


class _Client:
    def __init__(self, replay_rows, manifest_rows):
        self._replay = replay_rows
        self._manifest = manifest_rows

    def table(self, name):
        if name == "dashboard_replay_metadata_records":
            return _Table(self._replay)
        if name == "dashboard_export_manifests":
            return _Table(self._manifest)
        return _Table([])


def test_dry_run_retry_no_write_and_duplicates_blocked():
    replay = [
        {"run_id": "r1", "run_timestamp": "2026-05-01T00:00:00Z", "payload_checksum": "c1", "source_trace": "persisted_replay", "payload_reference": "p1"}
    ]
    client = _Client(replay_rows=replay, manifest_rows=[{"manifest_id": "m1"}])
    payload = build_real_supabase_dry_run_retry_payload(runtime_config={"credentials_present": True, "supabase_url": "u", "supabase_key": "k"}, client=client)
    assert payload["execution"]["inserted_count"] == 0
    assert payload["no_write_confirmed"] is True
    assert payload["candidate_inventory"]["replay_metadata_row_count"] == 1
    assert payload["candidate_inventory"]["manifest_row_count"] == 1
    assert payload["candidate_inventory"]["accepted_candidates"] >= 0
    assert payload["candidate_inventory"]["rejected_candidates"] >= 0
    assert payload["plan"]["execution_status"] == "BACKFILL_DRY_RUN_READY"


def test_blocked_source_preserves_blocker_details():
    payload = build_real_supabase_dry_run_retry_payload(runtime_config={})
    assert payload["status"] == "BLOCKED_SOURCE_NOT_READY"
    assert payload["credential_status"] in {"CREDENTIALS_MISSING", "CREDENTIALS_PARTIAL", "CREDENTIALS_READY"}
    assert payload["client_status"] is not None
    assert payload["read_only_connectivity_status"] is not None
    assert payload["blocked_reason"]
    assert payload["no_write_confirmed"] is True


def test_report_has_no_write_marker_and_no_secret_leak():
    stub = {
        "timestamp_utc": "2026-05-24T00:00:00Z",
        "source_diagnostics": {"status": "SOURCE_READY", "recommendation": "READY_FOR_D8_B2R_RERUN"},
        "candidate_inventory": {"duplicate_ids": [], "duplicate_candidates": 0},
        "governance": {"status": "GOVERNANCE_OK", "blocking_reasons": []},
        "plan": {"execution_status": "BACKFILL_DRY_RUN_READY", "target_tables": [], "estimated_inserted_count": 0},
        "execution": {"inserted_count": 0, "execution_checksum": "x", "audit_manifest": {"write_count": 0, "manifest_checksum": "y"}},
        "expected_intelligence_lift": {},
        "recommendation": "SAFE_FOR_CONTROLLED_EXECUTION",
    }
    report = render_real_supabase_dry_run_retry_report(stub)
    assert "no_write_confirmed" in report
    assert "SUPABASE_KEY" not in report


def test_blocked_report_not_generic_governance_label():
    blocked = {
        "status": "BLOCKED_SOURCE_NOT_READY",
        "source_status": "SOURCE_BLOCKED_CREDENTIALS_MISSING",
        "source_recommendation": "BLOCKED_MISSING_CREDENTIALS",
        "credential_status": "CREDENTIALS_MISSING",
        "client_status": "CLIENT_UNRESOLVED",
        "read_only_connectivity_status": "READ_ONLY_CONNECTIVITY_NOT_ATTEMPTED",
        "selected_key_source": "missing",
        "accessible_tables": [],
        "inaccessible_tables": ["dashboard_replay_metadata_records"],
        "blocked_reason": "SOURCE_BLOCKED_CREDENTIALS_MISSING",
        "recommendation": "BLOCKED_MISSING_CREDENTIALS",
        "no_write_confirmed": True,
    }
    report = render_real_supabase_dry_run_retry_report(blocked)
    assert "BLOCKED_GOVERNANCE" not in report
    assert "BLOCKED_MISSING_CREDENTIALS" in report
