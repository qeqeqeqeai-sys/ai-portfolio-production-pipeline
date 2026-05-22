from copy import deepcopy

from transmission_layers.expectation_failure.dashboard_operationalization import (
    build_dashboard_o9_acceptance_report_payload,
    build_dashboard_o9_acceptance_scope,
    evaluate_dashboard_degraded_sections,
    evaluate_dashboard_o8_verification_visibility,
    evaluate_dashboard_real_data_presence,
    evaluate_dashboard_section_population,
    run_dashboard_o9_real_data_load_acceptance,
)


class _FakeResult:
    def __init__(self, data):
        self.data = data


class _FakeQuery:
    def __init__(self, rows):
        self._rows = rows

    def select(self, *_args, **_kwargs):
        return self

    def eq(self, *_args, **_kwargs):
        return self

    def order(self, *_args, **_kwargs):
        return self

    def limit(self, *_args, **_kwargs):
        return self

    def execute(self):
        return _FakeResult(self._rows)


class _FakeReadOnlyClient:
    def __init__(self, rows):
        self.rows = rows

    def table(self, _table_name):
        return _FakeQuery(self.rows)


def _build_section(rows=None, status="ok"):
    return {"rows": list(rows or []), "status": status}


def _full_snapshot():
    return {
        "entity_facts": _build_section([{"id": 1}]),
        "subsector_facts": _build_section([{"id": 1}]),
        "alert_facts": _build_section([{"id": 1}]),
        "benchmark_facts": _build_section([{"id": 1}]),
        "replay_facts": _build_section([{"id": 1}]),
        "evidence_facts": _build_section([{"id": 1}]),
        "certification_metadata": _build_section([{"id": 1}]),
    }


def test_full_snapshot_is_accepted_and_deterministic():
    snapshot = _full_snapshot()
    first = run_dashboard_o9_real_data_load_acceptance(snapshot=snapshot, o8_result={"status": "verified"})
    second = run_dashboard_o9_real_data_load_acceptance(snapshot=snapshot, o8_result={"status": "verified"})
    assert first == second
    assert first["status"] == "accepted"


def test_partial_snapshot_accepted_with_degraded_sections():
    snapshot = _full_snapshot()
    snapshot["evidence_facts"] = _build_section([], status="degraded")
    result = run_dashboard_o9_real_data_load_acceptance(snapshot=snapshot)
    assert result["status"] == "accepted_with_degraded_sections"
    assert "evidence_facts" in result["degraded_sections"]


def test_empty_snapshot_provisional():
    result = run_dashboard_o9_real_data_load_acceptance(snapshot={})
    assert result["status"] == "provisional"


def test_empty_degraded_snapshot_blocked():
    snapshot = {k: _build_section([], status="degraded") for k in build_dashboard_o9_acceptance_scope()["required_sections"]}
    result = run_dashboard_o9_real_data_load_acceptance(snapshot=snapshot)
    assert result["status"] == "blocked"


def test_o8_visibility_and_missing_handled():
    visible = evaluate_dashboard_o8_verification_visibility({"status": "verified"})
    missing = evaluate_dashboard_o8_verification_visibility(None)
    assert visible["o8_status_visible"] is True
    assert missing["o8_verification_status"] == "not_provided"


def test_invalid_client_handled():
    result = run_dashboard_o9_real_data_load_acceptance(client=object(), snapshot=_full_snapshot())
    assert result["status"] == "invalid_client"


def test_runtime_path_loads_without_writes_rpc_or_raw_sql():
    client = _FakeReadOnlyClient([{"run_id": "R1"}])
    result = run_dashboard_o9_real_data_load_acceptance(client=client, config_or_secrets={"supabase_url": "u", "supabase_key": "k"})
    assert result["status"] in {"accepted", "accepted_with_degraded_sections"}
    assert "rpc" in result["forbidden_operations"]
    assert "raw_sql" in result["forbidden_operations"]


def test_immutable_input_safety_and_report_determinism():
    snapshot = _full_snapshot()
    snapshot_before = deepcopy(snapshot)
    result = run_dashboard_o9_real_data_load_acceptance(snapshot=snapshot, o8_result={"status": "verified"})
    report1 = build_dashboard_o9_acceptance_report_payload(result)
    report2 = build_dashboard_o9_acceptance_report_payload(result)
    assert snapshot == snapshot_before
    assert report1 == report2


def test_supporting_evaluators_and_exports():
    snapshot = _full_snapshot()
    presence = evaluate_dashboard_real_data_presence(snapshot)
    pop = evaluate_dashboard_section_population(snapshot)
    degraded = evaluate_dashboard_degraded_sections(snapshot)
    assert presence["has_real_data"] is True
    assert len(pop["populated_sections"]) == 7
    assert degraded == []
    assert isinstance(build_dashboard_o9_acceptance_scope(), dict)


def test_non_regression_smoke_o4_o5_o6_o7_o8():
    from transmission_layers.expectation_failure.dashboard_operationalization import (
        build_dashboard_o4_ui_manifest,
        build_dashboard_o4_view_model,
        build_dashboard_o5_closeout_report,
        build_dashboard_o6_read_adapter_report_payload,
        build_dashboard_o7_runtime_report_payload,
        build_dashboard_o8_deployment_report_payload,
    )

    assert "checksum" in build_dashboard_o4_ui_manifest(build_dashboard_o4_view_model({}))
    assert "executive_conclusion" in build_dashboard_o5_closeout_report()
    assert "objective" in build_dashboard_o6_read_adapter_report_payload()
    assert "objective" in build_dashboard_o7_runtime_report_payload()
    assert "objective" in build_dashboard_o8_deployment_report_payload()
