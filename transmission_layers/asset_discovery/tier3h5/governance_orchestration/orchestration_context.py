from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from transmission_layers.asset_discovery.tier3h5.governance_query.serialization import write_stable_json

RUNTIME_CONTEXT_PATH = Path("logs/tier3h5_orchestration_runtime_context.json")


def emit_runtime_context(stage_order: list[str], orchestration_mode: str = "deterministic_advisory_only") -> dict[str, Any]:
    now_sgt = datetime.now(UTC).astimezone(UTC) + timedelta(hours=8)
    payload = {
        "run_date_sgt": now_sgt.strftime("%Y-%m-%d"),
        "workflow_run_id": os.getenv("GITHUB_RUN_ID"),
        "repository_context": os.getenv("GITHUB_REPOSITORY"),
        "deterministic_stage_order": stage_order,
        "orchestration_mode": orchestration_mode,
        "advisory_only_flags": {
            "advisory_only_governance": True,
            "read_only_governance_exports": True,
            "exact_match_only": True,
        },
        "tier3h4_freeze_boundary_preserved": True,
    }
    write_stable_json(RUNTIME_CONTEXT_PATH, payload)
    return payload
