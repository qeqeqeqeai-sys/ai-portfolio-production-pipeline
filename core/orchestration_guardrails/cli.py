from __future__ import annotations

import argparse
import sys
from pathlib import Path

from core.orchestration_guardrails.context_io import (
    append_github_env,
    extract_field_from_json,
    read_context,
    write_context,
)
from core.orchestration_guardrails.execution_context import ExecutionContext


DEFAULT_CONTEXT_FILE = "logs/execution_context.json"


def cmd_preflight(args: argparse.Namespace) -> int:
    """
    Existing advisory preflight placeholder.

    Keep your current working preflight implementation here if already present.
    This stub is intentionally advisory-only.
    """
    print("[orchestration_guardrails] Advisory preflight completed.")
    print(f"[orchestration_guardrails] workflow={getattr(args, 'workflow_name', '')}")
    print(f"[orchestration_guardrails] theme={getattr(args, 'theme_name', '')}")
    return 0


def cmd_context_resolve(args: argparse.Namespace) -> int:
    context = ExecutionContext.resolve(
        workflow_name=args.workflow_name,
        github_run_id=args.run_id,
        run_mode=args.run_mode,
        theme_name=args.theme_name,
        requested_run_date_sgt=args.requested_run_date_sgt,
    )

    write_context(args.output_file, context)

    print(f"[execution_context] resolved context written to {args.output_file}")
    print(f"[execution_context] resolved_run_date_sgt={context.resolved_run_date_sgt}")

    return 0


def cmd_context_export_github_env(args: argparse.Namespace) -> int:
    context = read_context(args.context_file)

    env_file = args.github_env_file

    if not env_file:
        env_file = str(Path.cwd() / "github_env.local")

    env_vars = context.github_env_vars(context_file=args.context_file)
    append_github_env(env_file, env_vars)

    print(f"[execution_context] exported GitHub env vars to {env_file}")
    for key, value in env_vars.items():
        print(f"[execution_context] {key}={value}")

    return 0


def cmd_context_update_from_json(args: argparse.Namespace) -> int:
    context = read_context(args.context_file)

    value = extract_field_from_json(args.source_json, args.field)

    context.update_field(args.target_field, value)

    write_context(args.context_file, context)

    print(
        "[execution_context] updated "
        f"{args.target_field} from {args.source_json}:{args.field} "
        f"value={value}"
    )

    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m core.orchestration_guardrails.cli"
    )

    subparsers = parser.add_subparsers(dest="command")

    # ------------------------------------------------------------------
    # Existing advisory preflight command
    # ------------------------------------------------------------------
    preflight = subparsers.add_parser("preflight")
    preflight.add_argument("--workflow-name", default="")
    preflight.add_argument("--theme-name", default="ai")
    preflight.add_argument("--run-date-sgt", default="")
    preflight.set_defaults(func=cmd_preflight)

    # ------------------------------------------------------------------
    # Shared execution context commands
    # ------------------------------------------------------------------
    context = subparsers.add_parser("context")
    context_subparsers = context.add_subparsers(dest="context_command")

    resolve = context_subparsers.add_parser("resolve")
    resolve.add_argument("--workflow-name", required=True)
    resolve.add_argument("--run-id", required=True)
    resolve.add_argument("--run-mode", required=True)
    resolve.add_argument("--theme-name", default="ai")
    resolve.add_argument("--requested-run-date-sgt", default="")
    resolve.add_argument("--output-file", default=DEFAULT_CONTEXT_FILE)
    resolve.set_defaults(func=cmd_context_resolve)

    export_env = context_subparsers.add_parser("export-github-env")
    export_env.add_argument("--context-file", default=DEFAULT_CONTEXT_FILE)
    export_env.add_argument("--github-env-file", default="")
    export_env.set_defaults(func=cmd_context_export_github_env)

    update_from_json = context_subparsers.add_parser("update-from-json")
    update_from_json.add_argument("--context-file", default=DEFAULT_CONTEXT_FILE)
    update_from_json.add_argument("--source-json", required=True)
    update_from_json.add_argument("--field", required=True)
    update_from_json.add_argument("--target-field", required=True)
    update_from_json.set_defaults(func=cmd_context_update_from_json)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if not hasattr(args, "func"):
        parser.print_help()
        return 1

    try:
        return args.func(args)
    except Exception as exc:
        print(f"[orchestration_guardrails] ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
