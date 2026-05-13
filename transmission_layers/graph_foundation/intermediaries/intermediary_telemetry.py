"""Telemetry persistence for Phase 5A.2."""
from __future__ import annotations

from typing import Any

from intermediary_utils import SupabaseClient


def persist_telemetry(client: SupabaseClient, row: dict[str, Any]) -> None:
    client.upsert("structural_theme_graph_intermediary_telemetry", [row], on_conflict="run_id")


def persist_validations(client: SupabaseClient, rows: list[dict[str, Any]]) -> int:
    return client.upsert("structural_theme_graph_intermediary_validation", rows, on_conflict="run_id,validation_name")
