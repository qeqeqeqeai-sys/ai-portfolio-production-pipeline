from copy import deepcopy

from transmission_layers.expectation_failure import dashboard_operationalization as mod
from transmission_layers.expectation_failure.dashboard_operationalization.dashboard_o8_supabase_deployment_verification import (
    build_dashboard_o8_deployment_report_payload,
    build_dashboard_o8_verification_scope,
    run_dashboard_o8_deployment_smoke_test,
    verify_dashboard_column_contracts,
    verify_dashboard_supabase_credentials,
    verify_dashboard_table_reachability,
)


class _Result:
    def __init__(self, data):
        self.data = data


class FakeQuery:
    def __init__(self, table, data, calls, fail_tables):
        self.table = table
        self.data = data
        self.calls = calls
        self.fail_tables = fail_tables

    def select(self, columns):
        self.calls.append(("select", self.table, columns))
        return self

    def limit(self, value):
        self.calls.append(("limit", self.table, value))
        self.data = self.data[:value]
        return self

    def execute(self):
        self.calls.append(("execute", self.table))
        if self.table in self.fail_tables:
            raise RuntimeError("table failed")
        return _Result(self.data)


class FakeClient:
    def __init__(self, datasets, fail_tables=None):
        self.datasets = deepcopy(datasets)
        self.fail_tables = set(fail_tables or [])
        self.calls = []

    def table(self, name):
        self.calls.append(("table", name))
        return FakeQuery(name, deepcopy(self.datasets.get(name, [])), self.calls, self.fail_tables)


def _full_dataset():
    scope = build_dashboard_o8_verification_scope()
    out = {}
    for t in scope["allowed_tables"]:
        cols = scope["allowed_columns"][t]
        out[t] = [{c: f"v_{c}" for c in cols}]
    return out


def test_api_exports_additive_and_scope_deterministic():
    for n in [
        "build_dashboard_o8_verification_scope",
        "verify_dashboard_supabase_credentials",
        "verify_dashboard_table_reachability",
        "verify_dashboard_column_contracts",
        "run_dashboard_o8_deployment_smoke_test",
        "build_dashboard_o8_deployment_report_payload",
    ]:
        assert hasattr(mod, n)
    assert build_dashboard_o8_verification_scope() == build_dashboard_o8_verification_scope()


def test_credentials_missing_degraded_and_immutable_inputs():
    cfg = {"supabase_url": "", "supabase_key": ""}
    original = deepcopy(cfg)
    out = verify_dashboard_supabase_credentials(cfg)
    assert cfg == original
    assert out["status"] == "degraded"


def test_invalid_client_handling():
    out = run_dashboard_o8_deployment_smoke_test(client=object(), config_or_secrets={"supabase_url": "u", "supabase_key": "k"})
    assert out["status"] == "invalid_client"


def test_table_reachability_success_and_failure_and_limit_clamping_and_no_writes_rpc_sql():
    ok_client = FakeClient(_full_dataset())
    ok = verify_dashboard_table_reachability(ok_client, sample_limit=999)
    assert ok["status"] == "verified"
    assert ok["applied_sample_limit"] == 5

    bad_client = FakeClient(_full_dataset(), fail_tables={"dashboard_alert_facts"})
    bad = verify_dashboard_table_reachability(bad_client, sample_limit=0)
    assert bad["status"] == "blocked"
    assert bad["applied_sample_limit"] == 1

    low = str(ok_client.calls).lower()
    for forbidden in ["insert", "update", "delete", "upsert", "rpc", "sql"]:
        assert forbidden not in low


def test_column_contract_success_and_mismatch():
    good = verify_dashboard_column_contracts(FakeClient(_full_dataset()))
    assert good["status"] == "verified"

    broken_data = _full_dataset()
    broken_data["dashboard_entity_facts"] = [{"run_id": "x"}]
    mismatch = verify_dashboard_column_contracts(FakeClient(broken_data))
    assert mismatch["status"] == "contract_mismatch"


def test_deterministic_repeated_output_report_determinism_and_non_regression_smoke():
    cfg = {"supabase_url": "u", "supabase_key": "k"}
    client_a = FakeClient(_full_dataset())
    client_b = FakeClient(_full_dataset())
    a = run_dashboard_o8_deployment_smoke_test(client=client_a, config_or_secrets=cfg)
    b = run_dashboard_o8_deployment_smoke_test(client=client_b, config_or_secrets=deepcopy(cfg))
    assert a == b

    report_a = build_dashboard_o8_deployment_report_payload(a)
    report_b = build_dashboard_o8_deployment_report_payload(deepcopy(a))
    assert report_a == report_b

    from transmission_layers.expectation_failure.dashboard_operationalization.dashboard_o7_streamlit_supabase_runtime import build_dashboard_o7_runtime_report_payload
    from transmission_layers.expectation_failure.dashboard_operationalization.dashboard_o6_supabase_read_adapter import build_dashboard_o6_read_adapter_report_payload
    from transmission_layers.expectation_failure.dashboard_operationalization.dashboard_o5_operationalization_certification import build_dashboard_o5_closeout_report
    from transmission_layers.expectation_failure.dashboard_operationalization.dashboard_o4_streamlit_view_model import build_dashboard_o4_view_model, build_dashboard_o4_ui_manifest

    assert build_dashboard_o7_runtime_report_payload()["schema_version"]
    assert build_dashboard_o6_read_adapter_report_payload()["schema_version"]
    assert build_dashboard_o5_closeout_report()["schema_version"]
    assert build_dashboard_o4_ui_manifest(build_dashboard_o4_view_model({}))["schema_version"]
