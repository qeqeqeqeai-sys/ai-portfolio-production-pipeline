from copy import deepcopy

from transmission_layers.expectation_failure import dashboard_operationalization as mod
from transmission_layers.expectation_failure.dashboard_operationalization.dashboard_o7_streamlit_supabase_runtime import (
    build_dashboard_o7_runtime_report_payload,
    build_streamlit_supabase_runtime_config,
    load_streamlit_dashboard_snapshot,
    resolve_streamlit_supabase_mode,
)


class FakeClient:
    pass


def test_public_api_exports_are_additive():
    for name in [
        "build_streamlit_supabase_runtime_config",
        "resolve_streamlit_supabase_mode",
        "load_streamlit_dashboard_snapshot",
        "build_dashboard_o7_runtime_report_payload",
    ]:
        assert hasattr(mod, name)


def test_credentials_missing_resolves_fallback_mode_and_is_deterministic_and_immutable():
    payload = {"dashboard_entity_facts": [{"run_id": "r1"}]}
    original = deepcopy(payload)
    cfg = build_streamlit_supabase_runtime_config(supabase_url=None, supabase_key=None)
    a = load_streamlit_dashboard_snapshot(runtime_config=cfg, fallback_payload=payload)
    b = load_streamlit_dashboard_snapshot(runtime_config=cfg, fallback_payload=deepcopy(payload))
    assert payload == original
    assert a == b
    assert a["mode"] == "fallback_demo_mode"


def test_credentials_present_uses_injected_client_and_o6_path_only():
    calls = []

    def fake_factory(url, key):
        calls.append((url, key))
        return FakeClient()

    cfg = build_streamlit_supabase_runtime_config(supabase_url="u", supabase_key="k", run_id="r1")
    out = load_streamlit_dashboard_snapshot(runtime_config=cfg, fallback_payload={}, client_factory=fake_factory)
    assert out["mode"] in {"read_only_supabase_mode", "degraded_data_loading_mode"}
    assert calls == [("u", "k")]


def test_failure_resolves_degraded_mode():
    def bad_factory(url, key):
        raise RuntimeError("cannot create")

    cfg = build_streamlit_supabase_runtime_config(supabase_url="u", supabase_key="k")
    out = load_streamlit_dashboard_snapshot(runtime_config=cfg, fallback_payload={}, client_factory=bad_factory)
    assert out["mode"] == "degraded_data_loading_mode"


def test_no_writes_rpc_or_raw_sql_are_used_via_o6_snapshot_contract():
    cfg = build_streamlit_supabase_runtime_config(supabase_url="u", supabase_key="k")
    out = load_streamlit_dashboard_snapshot(runtime_config=cfg, fallback_payload={}, client=FakeClient())
    text = str(out).lower()
    for forbidden in ["insert", "update", "delete", "upsert", "rpc", "sql"]:
        assert forbidden not in text


def test_cache_refresh_configuration_is_bounded_and_mode_resolution_works():
    cfg = build_streamlit_supabase_runtime_config(cache_ttl_seconds=1)
    assert cfg["cache_ttl_seconds"] == 30
    assert cfg["background_polling_enabled"] is False
    assert cfg["refresh_policy"] == "manual_or_rerun_only"
    assert resolve_streamlit_supabase_mode(cfg) == "fallback_demo_mode"


def test_report_payload_stable_and_non_regression_smoke():
    a = build_dashboard_o7_runtime_report_payload()
    b = build_dashboard_o7_runtime_report_payload()
    assert a == b
    from transmission_layers.expectation_failure.dashboard_operationalization.dashboard_o6_supabase_read_adapter import build_dashboard_o6_read_adapter_report_payload
    assert build_dashboard_o6_read_adapter_report_payload()["schema_version"]
