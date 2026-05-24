from transmission_layers.expectation_failure.expectation_intelligence.d8_b1_controlled_replay_expansion import build_d8_b1_controlled_backfill_plan
from transmission_layers.expectation_failure.expectation_intelligence.d8_b2_controlled_replay_backfill_execution import (
    build_backfill_audit_manifest,
    build_backfill_execution_plan,
    execute_controlled_replay_backfill,
    validate_backfill_candidates,
    validate_backfill_execution_governance,
)


class _FakeTable:
    def __init__(self, name, sink):
        self.name = name
        self.sink = sink

    def insert(self, records):
        self.sink.append((self.name, "insert", list(records)))
        return self

    def execute(self):
        return type("Resp", (), {"data": True})()


class _FakeClient:
    def __init__(self):
        self.calls = []

    def table(self, name):
        self.calls.append((name, "table"))
        return _FakeTable(name, self.calls)


def _candidate(i, ts="2026-05-20T00:00:00Z"):
    return {"run_id": f"r{i}", "run_timestamp": ts, "payload_checksum": f"c{i}", "source_trace": "persisted_replay"}


def test_dry_run_true_performs_zero_writes():
    client = _FakeClient()
    out = execute_controlled_replay_backfill(candidates=[_candidate(1)], client=client)
    assert out["status"] == "BACKFILL_DRY_RUN_ONLY"
    assert out["inserted_count"] == 0
    assert not any(c for c in client.calls if isinstance(c, tuple) and len(c) > 1 and c[1] == "insert")


def test_dry_run_false_requires_client_and_approval_flags():
    out = execute_controlled_replay_backfill(candidates=[_candidate(1)], dry_run=False, approval_flags={"approved_for_execution": True, "approved_by_governance": True})
    assert out["status"] == "BACKFILL_BLOCKED_GOVERNANCE"
    out2 = execute_controlled_replay_backfill(candidates=[_candidate(1)], dry_run=False, client=_FakeClient(), approval_flags={})
    assert out2["status"] == "BACKFILL_BLOCKED_GOVERNANCE"


def test_governance_rejects_forbidden_capabilities():
    gov = validate_backfill_execution_governance(dry_run=False, client=_FakeClient(), approval_flags={"approved_for_execution": True, "approved_by_governance": True}, forbidden_capabilities={"network_calls": True})
    assert gov["status"] == "GOVERNANCE_BLOCKED"


def test_candidate_validation_missing_fields_duplicates_existing_and_non_determinism():
    cands = [_candidate(1), {"run_id": "r2", "run_timestamp": "2026/05/20", "payload_checksum": "c2", "source_trace": "x"}, {"run_id": "r1", "run_timestamp": "2026-05-21T00:00:00Z", "payload_checksum": "c3", "source_trace": "x"}, {"run_timestamp": "2026-05-22T00:00:00Z", "payload_checksum": "c4", "source_trace": "x"}]
    out = validate_backfill_candidates(candidates=cands, existing_replay_ids=["r9", "r1"])
    assert len(out["accepted_candidates"]) == 0
    reasons = {r["run_id"]: r["reasons"] for r in out["rejected_candidates"]}
    assert "already_present_in_replay_inventory" in reasons["r1"]


def test_deterministic_ordering_and_checksum_stability():
    cands = [_candidate(2, "2026-05-22T00:00:00Z"), _candidate(1, "2026-05-21T00:00:00Z")]
    gov = validate_backfill_execution_governance()
    p1 = build_backfill_execution_plan(candidates=cands, governance=gov, dry_run=True)
    p2 = build_backfill_execution_plan(candidates=list(reversed(cands)), governance=gov, dry_run=True)
    assert p1["execution_plan_checksum"] == p2["execution_plan_checksum"]


def test_append_only_execution_and_partial_rejections():
    client = _FakeClient()
    cands = [_candidate(1), {"run_id": "r2", "run_timestamp": "2026-05-20T00:00:00Z", "source_trace": "x"}]
    out = execute_controlled_replay_backfill(candidates=cands, dry_run=False, client=client, approval_flags={"approved_for_execution": True, "approved_by_governance": True})
    assert out["status"] == "BACKFILL_PARTIAL_WITH_REJECTIONS"
    assert out["inserted_count"] == 1
    assert any(call[0] == "dashboard_replay_metadata_records" for call in client.calls)


def test_audit_manifest_completeness_and_d8_b1_integration():
    b1 = build_d8_b1_controlled_backfill_plan(replay_metadata_rows=[{"replay_id": "x"}], historical_runs_payloads=[], governance_inventory={"approved": True})
    gov = validate_backfill_execution_governance()
    plan = build_backfill_execution_plan(d8_b1_backfill_plan=b1, candidates=[_candidate(1)], governance=gov)
    manifest = build_backfill_audit_manifest(plan=plan, governance=gov, dry_run=True, write_count=0)
    assert "candidate_ids" in manifest and "checksum_lineage" in manifest and "manifest_checksum" in manifest
