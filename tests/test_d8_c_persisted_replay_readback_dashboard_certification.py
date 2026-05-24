from transmission_layers.expectation_failure.expectation_intelligence import (
    build_d8c_persisted_readback_inventory,
    validate_d8c_replay_manifest_lineage,
    build_d8c_dashboard_consumption_model,
    certify_d8c_dashboard_consumption,
    build_d8c_certification_report_payload,
    build_d8c_certification_report_markdown,
)


class R:
    def __init__(self, data):
        self.data = data


class T:
    def __init__(self, c, n):
        self.c, self.n = c, n

    def select(self, *_args, **_kwargs):
        return self

    def execute(self):
        self.c.read_tables.append(self.n)
        return R(self.c.db.get(self.n, []))


class C:
    def __init__(self, replay=None, manifest=None):
        self.db = {
            "dashboard_replay_metadata_records": replay or [],
            "dashboard_export_manifests": manifest or [],
            "disallowed": [{"x": 1}],
        }
        self.read_tables = []

    def table(self, n):
        return T(self, n)


def _sample_rows():
    replay = [
        {"replay_id": "O6RM-D551524B575A3DC1", "source_payload_checksum": "aaa"},
        {"replay_id": "D6REP-200578C505B6", "source_payload_checksum": "bbb"},
    ]
    manifest = [{"manifest_checksum": "mmm", "export_checksum": "eee"}]
    return replay, manifest


def test_api_export_presence():
    assert callable(build_d8c_persisted_readback_inventory)
    assert callable(validate_d8c_replay_manifest_lineage)


def test_deterministic_output_and_input_immutability():
    replay, manifest = _sample_rows()
    replay_in = list(replay)
    manifest_in = list(manifest)
    inv = build_d8c_persisted_readback_inventory(replay_rows=replay_in, manifest_rows=manifest_in)
    assert inv["replay_ids"] == sorted(inv["replay_ids"])
    assert replay_in == replay
    assert manifest_in == manifest


def test_empty_rows_blocked_consumption():
    inv = build_d8c_persisted_readback_inventory(replay_rows=[], manifest_rows=[])
    lineage = validate_d8c_replay_manifest_lineage(replay_rows=[], manifest_rows=[])
    model = build_d8c_dashboard_consumption_model(readback_inventory=inv, lineage_validation=lineage)
    cert = certify_d8c_dashboard_consumption(readback_inventory=inv, lineage_validation=lineage, dashboard_consumption_model=model)
    assert cert["certification_status"] == "BLOCKED_DASHBOARD_CONSUMPTION"


def test_replay_without_manifest_blocked():
    replay, _ = _sample_rows()
    inv = build_d8c_persisted_readback_inventory(replay_rows=replay, manifest_rows=[])
    lineage = validate_d8c_replay_manifest_lineage(replay_rows=replay, manifest_rows=[])
    model = build_d8c_dashboard_consumption_model(readback_inventory=inv, lineage_validation=lineage)
    cert = certify_d8c_dashboard_consumption(readback_inventory=inv, lineage_validation=lineage, dashboard_consumption_model=model)
    assert cert["certification_status"] == "BLOCKED_DASHBOARD_CONSUMPTION"


def test_certified_with_complete_lineage():
    replay, manifest = _sample_rows()
    inv = build_d8c_persisted_readback_inventory(replay_rows=replay, manifest_rows=manifest)
    lineage = validate_d8c_replay_manifest_lineage(replay_rows=replay, manifest_rows=manifest)
    model = build_d8c_dashboard_consumption_model(readback_inventory=inv, lineage_validation=lineage)
    cert = certify_d8c_dashboard_consumption(readback_inventory=inv, lineage_validation=lineage, dashboard_consumption_model=model)
    assert lineage["lineage_status"] == "LINEAGE_OK"
    assert cert["certification_status"] == "CERTIFIED_DASHBOARD_CONSUMABLE"


def test_missing_checksum_lineage_degraded_with_reason():
    replay = [{"replay_id": "A"}]
    manifest = [{"manifest_checksum": "m"}]
    lineage = validate_d8c_replay_manifest_lineage(replay_rows=replay, manifest_rows=manifest)
    assert lineage["lineage_status"] == "LINEAGE_DEGRADED"
    assert "missing_replay_checksum_lineage" in lineage["degraded_reasons"]


def test_dashboard_model_required_fields_and_no_secret_leakage():
    replay, manifest = _sample_rows()
    inv = build_d8c_persisted_readback_inventory(replay_rows=replay, manifest_rows=manifest)
    lineage = validate_d8c_replay_manifest_lineage(replay_rows=replay, manifest_rows=manifest)
    model = build_d8c_dashboard_consumption_model(readback_inventory=inv, lineage_validation=lineage)
    for key in ["replay_persistence_status", "replay_row_count", "manifest_row_count", "latest_replay_ids", "latest_manifest_checksums", "lineage_status", "replay_candidate_readiness", "dashboard_consumption_status", "recommendation"]:
        assert key in model
    blob = str(model).lower()
    assert "supabase_key" not in blob
    assert "api_key" not in blob


def test_fake_client_reads_only_approved_tables_and_no_sql_usage():
    replay, manifest = _sample_rows()
    c = C(replay=replay, manifest=manifest)
    inv = build_d8c_persisted_readback_inventory(client=c)
    assert inv["replay_row_count"] == 2
    assert c.read_tables == ["dashboard_replay_metadata_records", "dashboard_export_manifests"]


def test_report_payload_and_markdown_stable_shape():
    replay, manifest = _sample_rows()
    inv = build_d8c_persisted_readback_inventory(replay_rows=replay, manifest_rows=manifest)
    lineage = validate_d8c_replay_manifest_lineage(replay_rows=replay, manifest_rows=manifest)
    model = build_d8c_dashboard_consumption_model(readback_inventory=inv, lineage_validation=lineage)
    cert = certify_d8c_dashboard_consumption(readback_inventory=inv, lineage_validation=lineage, dashboard_consumption_model=model)
    report = build_d8c_certification_report_payload(readback_inventory=inv, lineage_validation=lineage, dashboard_consumption_model=model, certification=cert)
    md = build_d8c_certification_report_markdown(report_payload=report)
    assert report["no_direct_sql_bypass_used"] is True
    assert "Certification Result" in md
