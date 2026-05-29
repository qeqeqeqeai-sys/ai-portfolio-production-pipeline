from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Sequence

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from transmission_layers.expectation_failure.real_data.sefi_observation_universe import (
    BOUNDED_SAMPLE_SIZE,
    build_sefi_observation_universe_rows,
    load_sefi_universe_symbols,
)


class _Response:
    def __init__(self, data: list[dict[str, Any]]):
        self.data = data


class _Query:
    def __init__(self, rows: Sequence[dict[str, Any]]):
        self._rows = list(rows)

    def select(self, _columns: str) -> "_Query":
        return self

    def eq(self, key: str, value: Any) -> "_Query":
        self._rows = [row for row in self._rows if row.get(key) == value]
        return self

    def order(self, key: str) -> "_Query":
        self._rows = sorted(self._rows, key=lambda row: str(row.get(key, "")))
        return self

    def limit(self, value: int) -> "_Query":
        self._rows = self._rows[: int(value)]
        return self

    def execute(self) -> _Response:
        return _Response([dict(row) for row in self._rows])


class _Client:
    def __init__(self, rows: Sequence[dict[str, Any]]):
        self._rows = list(rows)

    def table(self, name: str) -> _Query:
        if name != "sefi_observation_universe":
            raise AssertionError(f"unexpected table read: {name}")
        return _Query(self._rows)


def _compact(symbols: Sequence[str], telemetry: dict[str, Any]) -> dict[str, Any]:
    return {
        "universe_source_used": telemetry.get("universe_source_used"),
        "universe_count": telemetry.get("universe_count", len(symbols)),
        "universe_digest": telemetry.get("universe_digest"),
        "fallback_reason": telemetry.get("fallback_reason"),
        "bounded_sample_symbols": list(telemetry.get("bounded_sample_symbols", []))[:BOUNDED_SAMPLE_SIZE],
    }


def _run_smoke() -> dict[str, Any]:
    valid_rows = build_sefi_observation_universe_rows()
    invalid_count_rows = valid_rows[:-1]
    invalid_digest_rows = [dict(row) for row in valid_rows]
    invalid_digest_rows[0]["symbol"] = "ZZZTEST"
    cases = {
        "db_valid": _Client(valid_rows),
        "db_invalid_count": _Client(invalid_count_rows),
        "db_digest_mismatch": _Client(invalid_digest_rows),
    }
    out: dict[str, Any] = {}
    for name, client in cases.items():
        symbols, telemetry = load_sefi_universe_symbols(client=client)
        out[name] = _compact(symbols, telemetry)
    symbols, telemetry = load_sefi_universe_symbols(allow_db=False)
    out["config_fallback"] = _compact(symbols, telemetry)
    out["load_instruction_if_db_empty"] = "python scripts/load_sefi_observation_universe.py --execute"
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke-check SEFI DB-default universe source without printing full symbol lists.")
    parser.add_argument("--write-report", default="")
    args = parser.parse_args()
    result = _run_smoke()
    failures = [
        name for name, payload in result.items()
        if isinstance(payload, dict) and payload.get("universe_count") != 241
    ]
    text = json.dumps(result, indent=2, sort_keys=True)
    print(text)
    if args.write_report:
        path = Path(args.write_report)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text + "\n", encoding="utf-8")
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
