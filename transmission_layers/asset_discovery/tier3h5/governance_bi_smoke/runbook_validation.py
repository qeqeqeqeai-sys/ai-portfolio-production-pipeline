from __future__ import annotations

from pathlib import Path


def validate_runbook_exists(path: str) -> bool:
    return Path(path).exists()
