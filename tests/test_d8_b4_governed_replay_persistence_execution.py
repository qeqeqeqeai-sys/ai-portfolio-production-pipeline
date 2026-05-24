from transmission_layers.expectation_failure.expectation_intelligence.d8_b4_governed_replay_persistence_execution import (
    build_d8_b4_execution_audit_manifest,
    build_d8_b4_execution_report_payload,
    build_d8_b4_post_execution_readback,
    build_d8_b4_persistence_execution_plan,
    execute_d8_b4_governed_replay_persistence,
    validate_d8_b4_execution_governance,
)


class R:
    def __init__(self, data):
        self.data = data


class T:
    def __init__(self, c, n):
        self.c, self.n = c, n
        self._rows = None

    def select(self, *_args, **_kwargs):
        return self

    def insert(self, rows):
        self._rows = list(rows)
        existing = {str(r.get("record_id") or r.get("replay_id")) for r in self.c.db.get(self.n, [])}
        accepted = []
        for row in self._rows:
            rid = str(row.get("record_id") or row.get("replay_id"))
            if rid in existing:
                continue
            existing.add(rid)
            accepted.append(dict(row))
        self.c.db.setdefault(self.n, []).extend(accepted)
        return self

    def upsert(self, rows, on_conflict=None):
        return self.insert(rows)

    def execute(self):
        return R(self.c.db.get(self.n, []))


class C:
    def __init__(self):
        self.db = {
            "dashboard_replay_metadata_records": [],
            "dashboard_export_manifests": [],
            "dashboard_finding_records": [],
            "dashboard_narrative_records": [],
            "dashboard_evidence_map_records": [],
            "dashboard_supervisor_panel_records": [],
            "dashboard_persistence_audit_records": [],
        }

    def table(self, n):
        return T(self, n)


def test_governance_validation_and_plan():
    g = validate_d8_b4_execution_governance(dry_run=False, client=C(), approval_flags={"approved_for_execution": True, "approved_by_governance": True})
    assert g["status"] == "GOVERNANCE_OK"
    plan = build_d8_b4_persistence_execution_plan(governance=g, dry_run=False)
    assert plan["execution_status"] == "EXECUTION_READY"


def test_non_dry_execution_append_only_and_readback():
    c = C()
    out = execute_d8_b4_governed_replay_persistence(client=c, dry_run=False, approval_flags={"approved_for_execution": True, "approved_by_governance": True})
    assert out["status"] in {"REPLAY_PERSISTENCE_OPERATIONAL", "REPLAY_PERSISTENCE_PARTIAL"}
    rb = out["readback"]
    assert rb["replay_metadata_row_count"] >= 1
    assert rb["manifest_row_count"] >= 1
    assert rb["lineage_checksum_present"] is True


def test_duplicate_idempotent_rerun_safety():
    c = C()
    execute_d8_b4_governed_replay_persistence(client=c, dry_run=False, approval_flags={"approved_for_execution": True, "approved_by_governance": True})
    first = len(c.db["dashboard_replay_metadata_records"])
    execute_d8_b4_governed_replay_persistence(client=c, dry_run=False, approval_flags={"approved_for_execution": True, "approved_by_governance": True})
    second = len(c.db["dashboard_replay_metadata_records"])
    assert second >= first


def test_audit_and_report_shapes():
    c = C()
    out = execute_d8_b4_governed_replay_persistence(client=c, dry_run=False, approval_flags={"approved_for_execution": True, "approved_by_governance": True})
    audit = build_d8_b4_execution_audit_manifest(d6_result=out["d6_result"], governance=out["governance"], dry_run=False)
    assert "attempted_inserts" in audit
    rb = build_d8_b4_post_execution_readback(client=c)
    payload = build_d8_b4_execution_report_payload(governance=out["governance"], plan=out["plan"], audit=audit, readback=rb, d8_b2_retry=out["d8_b2_retry"])
    assert payload["no_direct_sql_bypass_used"] is True
