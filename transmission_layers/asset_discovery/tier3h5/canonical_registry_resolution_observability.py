from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def emit_tier3h5_resolution_diagnostics(summary: dict[str, Any]) -> None:
    print(
        "[tier3h5] "
        f"registry_resolution_attempts={summary['registry_resolution_attempts']} "
        f"registry_resolution_accepted={summary['registry_resolution_accepted']} "
        f"registry_resolution_no_match={summary['registry_resolution_no_match']} "
        f"registry_resolution_conflicts={summary['registry_resolution_conflicts']} "
        f"registry_resolution_invalid_input={summary['registry_resolution_invalid_input']}"
    )
    print(
        "[tier3h5] "
        f"exact_exchange_ticker_matches={summary['exact_exchange_ticker_matches']} "
        f"exact_exchange_ticker_security_type_matches={summary['exact_exchange_ticker_security_type_matches']} "
        f"deterministic_resolution_failures={summary['deterministic_resolution_failures']} "
        f"status={summary['status']}"
    )


def write_registry_resolution_summary(
    summary: dict[str, Any], output_path: str = "logs/tier3h5_registry_resolution_summary.json"
) -> Path:
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    return out
