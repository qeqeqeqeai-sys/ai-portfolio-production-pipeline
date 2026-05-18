from __future__ import annotations

import json
from pathlib import Path
from typing import Any

LOG_DIR = Path("logs")
SUMMARY_PATH = LOG_DIR / "tier3h5_registry_foundation_summary.json"


def write_registry_summary(summary: dict[str, Any]) -> Path:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    return SUMMARY_PATH
