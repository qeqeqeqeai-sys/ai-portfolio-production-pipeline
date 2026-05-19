"""Tier 4B deterministic structural memory indexing."""
from __future__ import annotations

from typing import Any, Dict, List


class StructuralMemoryStore:
    def __init__(self) -> None:
        self._entries: List[Dict[str, Any]] = []

    def add_snapshot(self, snapshot: Dict[str, Any]) -> None:
        self._entries.append(snapshot)
        self._entries.sort(key=lambda s: (str(s.get("run_date", "")), str(s.get("simulation_run_id", ""))))

    def all_snapshots(self) -> List[Dict[str, Any]]:
        return list(self._entries)

    def query(
        self,
        run_date: str | None = None,
        simulation_health_state: str | None = None,
        topology_hash: str | None = None,
        resilience_regime: str | None = None,
        cascading_failure_presence: bool | None = None,
    ) -> List[Dict[str, Any]]:
        out = []
        for snapshot in self._entries:
            if run_date is not None and str(snapshot.get("run_date")) != str(run_date):
                continue
            if simulation_health_state is not None and str(snapshot.get("simulation_health_state")) != str(simulation_health_state):
                continue
            if topology_hash is not None and str(snapshot.get("topology_hash")) != str(topology_hash):
                continue
            if resilience_regime is not None:
                resilience = float(snapshot.get("propagation_summary", {}).get("resilience_degradation_score", 0.0))
                bucket = "low" if resilience < 0.34 else "medium" if resilience < 0.67 else "high"
                if bucket != resilience_regime:
                    continue
            if cascading_failure_presence is not None:
                has_cascade = str(snapshot.get("simulation_health_state", "")) == "cascading_failure"
                if has_cascade != cascading_failure_presence:
                    continue
            out.append(snapshot)
        return list(out)
