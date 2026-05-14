"""CLI entrypoint for Tier 3A orchestration guardrails (advisory mode)."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m core.orchestration_guardrails.cli",
        description="Tier 3A orchestration guardrails CLI (advisory mode).",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    preflight = subparsers.add_parser(
        "preflight",
        help="Run advisory preflight checks and print a structured summary.",
    )
    preflight.add_argument("--workflow-name", required=True, help="Workflow name.")
    preflight.add_argument("--run-id", required=True, help="Run identifier.")
    preflight.add_argument("--run-mode", required=True, help="Run mode (for example: manual).")

    return parser


def _run_preflight(args: argparse.Namespace) -> int:
    summary = {
        "command": "preflight",
        "mode": "advisory",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "workflow": {
            "name": args.workflow_name,
            "run_id": str(args.run_id),
            "run_mode": args.run_mode,
        },
        "guardrails": {
            "status": "advisory_only",
            "blocking": False,
            "checks": [],
        },
        "notes": [
            "No secrets are printed by this command.",
            "Preflight exits 0 unless a CLI/runtime error occurs.",
        ],
    }

    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()

    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return int(exc.code)

    try:
        if args.command == "preflight":
            return _run_preflight(args)

        parser.error(f"Unsupported command: {args.command}")
        return 2
    except Exception as exc:  # pragma: no cover - defensive runtime handling
        print(f"Runtime error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
