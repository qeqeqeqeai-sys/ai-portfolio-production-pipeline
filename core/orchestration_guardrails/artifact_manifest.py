from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any


def load_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: str, payload: Dict[str, Any]) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


def build_artifact_manifest(
    context_file: str,
    validation_summary_file: str,
    telemetry_snapshot_file: str,
    output_file: str,
) -> None:

    context = load_json(context_file)

    manifest = {
        "workflow_name": context.get("workflow_name"),
        "github_run_id": context.get("github_run_id"),
        "theme_name": context.get("theme_name"),
        "run_date_sgt": context.get("resolved_run_date_sgt"),
        "artifacts": {
            "execution_context": context_file,
            "validation_summary": validation_summary_file,
            "telemetry_snapshot": telemetry_snapshot_file,
        },
    }

    write_json(output_file, manifest)
