"""Dashboard O7 Streamlit runtime boundary for deterministic Supabase read-only loading."""

from __future__ import annotations

from collections import OrderedDict
from copy import deepcopy
from typing import Any, Mapping
import os

SCHEMA_VERSION = "dashboard_o7_streamlit_supabase_runtime_v1"
MODULE_VERSION = "1.0.0"
DEFAULT_CACHE_TTL_SECONDS = 120


def _safe_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def build_streamlit_supabase_runtime_config(*, supabase_url: str | None = None, supabase_key: str | None = None, run_id: str | None = None, as_of_date: str | None = None, cache_ttl_seconds: int = DEFAULT_CACHE_TTL_SECONDS) -> OrderedDict:
    cfg = OrderedDict([
        ("supabase_url", _safe_text(supabase_url) or _safe_text(os.getenv("SUPABASE_URL"))),
        ("supabase_key", _safe_text(supabase_key) or _safe_text(os.getenv("SUPABASE_ANON_KEY")) or _safe_text(os.getenv("SUPABASE_KEY"))),
        ("run_id", _safe_text(run_id)),
        ("as_of_date", _safe_text(as_of_date)),
    ])
    ttl = int(cache_ttl_seconds) if isinstance(cache_ttl_seconds, int) else DEFAULT_CACHE_TTL_SECONDS
    cfg["cache_ttl_seconds"] = 30 if ttl < 30 else min(ttl, 3600)
    cfg["credentials_present"] = bool(cfg["supabase_url"] and cfg["supabase_key"])
    cfg["refresh_policy"] = "manual_or_rerun_only"
    cfg["background_polling_enabled"] = False
    return cfg


def _resolve_client(runtime_config: Mapping[str, Any], *, client: Any | None = None, client_factory: Any | None = None):
    if client is not None:
        return client
    if not runtime_config.get("credentials_present"):
        return None
    if client_factory is None:
        try:
            from supabase import create_client as client_factory  # type: ignore
        except Exception:
            return None
    return client_factory(runtime_config["supabase_url"], runtime_config["supabase_key"])


def resolve_streamlit_supabase_mode(runtime_config: Mapping[str, Any], *, snapshot: Mapping[str, Any] | None = None) -> str:
    if not runtime_config.get("credentials_present"):
        return "fallback_demo_mode"
    if snapshot is None:
        return "read_only_supabase_mode"
    sections = ["entity_facts", "subsector_facts", "alert_facts", "benchmark_facts", "replay_facts", "evidence_facts", "certification_metadata"]
    degraded = any((snapshot.get(k) or {}).get("status") == "degraded" for k in sections)
    return "degraded_data_loading_mode" if degraded else "read_only_supabase_mode"


def load_streamlit_dashboard_snapshot(*, runtime_config: Mapping[str, Any], fallback_payload: Mapping[str, Any], client: Any | None = None, client_factory: Any | None = None) -> OrderedDict:
    config = deepcopy(dict(runtime_config))
    payload = deepcopy(dict(fallback_payload))
    mode = resolve_streamlit_supabase_mode(config)
    if mode == "fallback_demo_mode":
        return OrderedDict([("mode", mode), ("snapshot", None), ("payload", payload), ("status", "ok")])

    try:
        from .dashboard_o6_supabase_read_adapter import build_dashboard_supabase_snapshot

        supabase_client = _resolve_client(config, client=client, client_factory=client_factory)
        snapshot = build_dashboard_supabase_snapshot(supabase_client, run_id=config.get("run_id"), as_of_date=config.get("as_of_date"))
        mode = resolve_streamlit_supabase_mode(config, snapshot=snapshot)
    except Exception as exc:
        snapshot = OrderedDict([("error", f"{type(exc).__name__}: {str(exc)[:200]}")])
        mode = "degraded_data_loading_mode"

    return OrderedDict([("mode", mode), ("snapshot", snapshot), ("payload", payload), ("status", "ok")])


def build_dashboard_o7_runtime_report_payload() -> OrderedDict:
    return OrderedDict([
        ("schema_version", SCHEMA_VERSION),
        ("module_version", MODULE_VERSION),
        ("objective", "Runtime-only Streamlit Supabase client boundary with deterministic read-only fallback/degraded behavior."),
        ("runtime_boundary", "Client creation/resolution only at Streamlit runtime boundary; O6 remains injected-client-only."),
        ("read_only_guarantees", ["no_writes", "no_inserts_updates_deletes", "no_rpc", "no_raw_sql", "bounded_table_access_via_o6"]),
        ("refresh_model", OrderedDict([("manual_or_rerun_only", True), ("background_polling", False), ("cache_ttl_bounds_seconds", [30, 3600])])),
        ("modes", ["read_only_supabase_mode", "fallback_demo_mode", "degraded_data_loading_mode"]),
        ("deterministic_guarantees", ["immutable_input_safe", "deterministic_mode_resolution", "deterministic_fallback_payload_passthrough", "additive_only"]),
    ])


__all__ = [
    "build_streamlit_supabase_runtime_config",
    "resolve_streamlit_supabase_mode",
    "load_streamlit_dashboard_snapshot",
    "build_dashboard_o7_runtime_report_payload",
]
