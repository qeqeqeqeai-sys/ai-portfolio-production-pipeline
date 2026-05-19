"""Tier 4B deterministic structural memory indexing."""
from __future__ import annotations

from typing import Any, Dict, List

from .topology_hashing import normalize_deterministic


class StructuralMemoryStore:
    def __init__(self) -> None:
        self._entries: List[Dict[str, Any]] = []

    def add_snapshot(self, snapshot: Dict[str, Any]) -> None:
        self._entries.append(normalize_deterministic(snapshot))
        self._entries = sorted(self._entries, key=lambda s: (str(s.get("run_date_sgt", "")), str(s.get("simulation_run_id", "")), str(s.get("topology_hash", ""))))

    def all_snapshots(self) -> List[Dict[str, Any]]:
        return [normalize_deterministic(s) for s in self._entries]

    def query(self, run_date: str | None = None, simulation_health_state: str | None = None, topology_hash: str | None = None, resilience_regime: str | None = None, cascading_failure_presence: bool | None = None, chokepoint_concentration_bucket: str | None = None) -> List[Dict[str, Any]]:
        out = []
        for snapshot in self._entries:
            if run_date is not None and str(snapshot.get("run_date_sgt")) != str(run_date):
                continue
            if simulation_health_state is not None and str(snapshot.get("simulation_health_state")) != str(simulation_health_state):
                continue
            if topology_hash is not None and str(snapshot.get("topology_hash")) != str(topology_hash):
                continue
            if resilience_regime is not None:
                r = float(snapshot.get("resilience", 0.0))
                bucket = "low" if r < 0.34 else "medium" if r < 0.67 else "high"
                if bucket != resilience_regime:
                    continue
            if cascading_failure_presence is not None:
                has_cascade = str(snapshot.get("simulation_health_state", "")) == "cascading_failure"
                if has_cascade != cascading_failure_presence:
                    continue
            if chokepoint_concentration_bucket is not None:
                overloaded = sum(1 for m in snapshot.get("node_structural_metrics", {}).values() if float(m.get("is_overloaded", 0.0)) >= 1.0)
                total = max(1, len(snapshot.get("node_structural_metrics", {})))
                concentration = overloaded / total
                bucket = "low" if concentration < 0.2 else "medium" if concentration < 0.5 else "high"
                if bucket != chokepoint_concentration_bucket:
                    continue
            out.append(normalize_deterministic(snapshot))
        return out
