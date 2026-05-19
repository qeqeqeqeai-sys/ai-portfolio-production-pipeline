from __future__ import annotations

from pathlib import Path
import json


def build_state_transition_topology(manifest: dict[str, object]) -> dict[str, object]:
    history_root = Path("logs/history/tier3h5_governance_topology")
    transitions: list[dict[str, object]] = []
    status = "generated"
    if history_root.exists() and any(history_root.iterdir()):
        prior = sorted([p for p in history_root.iterdir() if p.is_dir()])[-1]
        prior_manifest_path = prior / "governance_topology_manifest.json"
        if prior_manifest_path.exists():
            prior_manifest = json.loads(prior_manifest_path.read_text(encoding="utf-8"))
            for key in ("phase_coverage_map", "artifact_coverage_map", "missing_inputs"):
                if prior_manifest.get(key) != manifest.get(key):
                    transitions.append({"transition_type": key, "previous": prior_manifest.get(key), "current": manifest.get(key)})
    else:
        status = "insufficient_state_history"
    return {
        "state_transition_topology_status": status,
        "transition_records": transitions,
        "transition_records_generated": len(transitions),
        "append_only_history_preserved": True,
    }
