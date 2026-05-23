import hashlib
import json
from pathlib import Path

import transmission_layers.expectation_failure.dashboard_operationalization as pkg
from transmission_layers.expectation_failure.dashboard_operationalization import d2_dashboard_supabase_schema as d2


def test_public_api_presence():
    for name in [
        "build_d2_dashboard_table_inventory",
        "build_d2_dashboard_column_contract",
        "build_d2_dashboard_index_contract",
        "build_d2_dashboard_constraint_contract",
        "build_d2_dashboard_supabase_schema_contract",
        "certify_d2_dashboard_supabase_schema",
        "build_d2_dashboard_supabase_schema_report",
    ]:
        assert hasattr(d2, name)


def test_package_export_presence_and_o1_o9_smoke():
    assert hasattr(pkg, "build_d2_dashboard_table_inventory")
    assert hasattr(pkg, "build_o1_operational_visibility_report")
    assert hasattr(pkg, "build_o9_dashboard_operationalization_closeout_payload")


def test_deterministic_repeated_output_and_checksum_stability():
    c1 = d2.build_d2_dashboard_supabase_schema_contract()
    c2 = d2.build_d2_dashboard_supabase_schema_contract()
    assert c1 == c2
    checkable = dict(c1)
    checkable.pop("contract_checksum")
    digest = hashlib.sha256(json.dumps(checkable, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    assert c1["contract_checksum"] == digest


def test_required_table_column_index_constraint_coverage():
    tables = d2.build_d2_dashboard_table_inventory()
    columns = d2.build_d2_dashboard_column_contract()
    indexes = d2.build_d2_dashboard_index_contract()
    constraints = d2.build_d2_dashboard_constraint_contract()
    for table in d2._REQUIRED_TABLES:
        assert table in tables
        assert table in columns
        assert table in indexes
        assert table in constraints
        assert constraints[table]["primary_key"] == ["record_id"]
        for field in ["source_payload_checksum", "export_checksum", "payload", "lineage_refs", "evidence_refs"]:
            assert field in columns[table]


def test_migration_file_exists_and_contains_required_sql_fragments():
    path = Path(d2.MIGRATION_PATH)
    assert path.exists()
    sql = path.read_text(encoding="utf-8")
    for table in d2._REQUIRED_TABLES:
        assert table in sql
    for required in [
        "PRIMARY KEY",
        "record_type",
        "source_payload_checksum",
        "export_checksum",
        "USING GIN (payload)",
        "USING GIN (lineage_refs)",
        "USING GIN (evidence_refs)",
        "dashboard_finding_records_finding_id_idx",
        "dashboard_narrative_records_narrative_section_idx",
        "dashboard_persistence_audit_records_write_status_idx",
    ]:
        assert required in sql


def test_certification_happy_path():
    result = d2.certify_d2_dashboard_supabase_schema()
    assert result["status"] == d2.CERTIFIED_DASHBOARD_SCHEMA_READY


def test_certification_degraded_and_blocked_paths():
    contract = d2.build_d2_dashboard_supabase_schema_contract()
    contract["column_contract"]["dashboard_finding_records"] = ["record_id"]
    degraded = d2.certify_d2_dashboard_supabase_schema(contract)
    assert degraded["status"] == d2.DEGRADED_DASHBOARD_SCHEMA_READY

    blocked_contract = d2.build_d2_dashboard_supabase_schema_contract()
    blocked_contract["table_inventory"] = []
    blocked = d2.certify_d2_dashboard_supabase_schema(blocked_contract)
    assert blocked["status"] == d2.BLOCKED_DASHBOARD_SCHEMA_INVALID


def test_no_forbidden_live_behavior_strings():
    code = Path("transmission_layers/expectation_failure/dashboard_operationalization/d2_dashboard_supabase_schema.py").read_text(encoding="utf-8").lower()
    for forbidden in ["import requests", "from requests", "import openai", "from openai", "os.environ["]:
        assert forbidden not in code
