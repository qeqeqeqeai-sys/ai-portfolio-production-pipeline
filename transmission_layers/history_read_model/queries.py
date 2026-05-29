from __future__ import annotations

from typing import Any


def _execute(query: Any) -> Any:
    result = query.execute()
    return getattr(result, "data", result)


def get_phase_run_summary(client: Any, phase_id: str) -> Any:
    return _execute(
        client.table("sefi_phase_runs")
        .select("phase_id,phase_name,status,run_id,artifact_id,created_at,loaded_at,completed_at,payload_jsonb")
        .eq("phase_id", phase_id)
        .order("loaded_at", desc=True)
    )


def get_window_metrics(client: Any, phase_id: str, window_days: int) -> Any:
    return _execute(
        client.table("sefi_window_metrics")
        .select("phase_id,phase_name,window_days,completeness,replay_density,replay_saturation,contradiction_burden,sector_hhi,subsector_hhi,effective_symbol_count,artifact_id,run_id,loaded_at,payload_jsonb")
        .eq("phase_id", phase_id)
        .eq("window_days", int(window_days))
        .order("loaded_at", desc=True)
    )


def get_sector_morphology(client: Any, phase_id: str) -> Any:
    return _execute(
        client.table("sefi_sector_morphology")
        .select("phase_id,phase_name,morphology_type,sector,subsector,symbol_count,symbol_share,rank,artifact_id,run_id,loaded_at,payload_jsonb")
        .eq("phase_id", phase_id)
        .order("morphology_type")
        .order("rank")
    )


def get_symbol_metrics(client: Any, phase_id: str, symbol: str) -> Any:
    return _execute(
        client.table("sefi_symbol_metrics")
        .select("phase_id,phase_name,symbol,window_days,metric_type,metric_value,artifact_id,run_id,loaded_at,payload_jsonb")
        .eq("phase_id", phase_id)
        .eq("symbol", symbol.upper())
        .order("loaded_at", desc=True)
    )


def get_observation_facts(client: Any, phase_id: str, *, entity_type: str | None = None, entity_id: str | None = None, window_days: int | None = None) -> Any:
    query = (
        client.table("sefi_observation_facts")
        .select("phase_id,phase_name,window_days,entity_type,entity_id,metric_name,metric_value,artifact_id,run_id,loaded_at,payload_jsonb")
        .eq("phase_id", phase_id)
    )
    if entity_type is not None:
        query = query.eq("entity_type", entity_type)
    if entity_id is not None:
        query = query.eq("entity_id", entity_id)
    if window_days is not None:
        query = query.eq("window_days", int(window_days))
    return _execute(query.order("loaded_at", desc=True))


def get_latest_completed_phase(client: Any, prefix: str) -> Any:
    return _execute(
        client.table("sefi_run_registry")
        .select("phase_id,phase_name,status,run_id,artifact_id,completed_at,loaded_at,payload_jsonb")
        .ilike("phase_name", f"{prefix}%")
        .in_("status", ["ok", "success"])
        .order("completed_at", desc=True)
        .limit(1)
    )
