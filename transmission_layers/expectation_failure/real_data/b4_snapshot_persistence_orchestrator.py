"""B4 orchestrator wrapper for controlled snapshot persistence."""

from __future__ import annotations

from copy import deepcopy

from .b4_supabase_snapshot_repository import persist_certified_market_snapshot


def orchestrate_b4_snapshot_persistence(client, b3_certified_envelope: dict, allow_degraded: bool = False, table_names: dict | None = None) -> dict:
    frozen = deepcopy(b3_certified_envelope)
    return persist_certified_market_snapshot(
        client=client,
        envelope=frozen,
        table_names=table_names,
        allow_degraded=allow_degraded,
    )
