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
DEFAULT_VALIDATION_SUMMARY_FILE = "logs/validation_summary.json"
DEFAULT_TELEMETRY_SNAPSHOT_FILE = "logs/telemetry_context_snapshot.json"
DEFAULT_ARTIFACT_MANIFEST_FILE = "logs/context_artifact_manifest.json"


# ----------------------------------------------------------------------
# Tier 3A — Advisory preflight
# ----------------------------------------------------------------------
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


# ----------------------------------------------------------------------
# Tier 3C — Shared execution context commands
# ----------------------------------------------------------------------
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


# ----------------------------------------------------------------------
# Tier 3D — Context-aware validation and telemetry commands
# ----------------------------------------------------------------------
def cmd_validation_summarize(args: argparse.Namespace) -> int:
    """
    Create logs/validation_summary.json from execution_context.json and
    validation gate results.

    This is intentionally additive and advisory-safe. It does not change
    validation behavior; it only records the validation outcome in a reusable
    context-aware JSON format.
    """
    from core.orchestration_guardrails.validation_context import summarize_validation

    summarize_validation(
        context_file=args.context_file,
        source=args.source,
        validation_status=args.validation_status,
        warnings_count=args.warnings_count,
        errors_count=args.errors_count,
        hard_fail_count=args.hard_fail_count,
        output_file=args.output_file,
    )

    print(f"[validation_context] validation summary written to {args.output_file}")
    print(f"[validation_context] validation_status={args.validation_status}")
    print(f"[validation_context] warnings_count={args.warnings_count}")
    print(f"[validation_context] errors_count={args.errors_count}")
    print(f"[validation_context] hard_fail_count={args.hard_fail_count}")

    return 0


def cmd_validation_check_env_consistency(args: argparse.Namespace) -> int:
    """
    Advisory-only consistency check between RUN_DATE_SGT and the shared
    execution context.

    This command is deliberately non-fatal. It prints warnings but returns 0
    unless there is a true runtime error such as an unreadable context file.
    """
    from core.orchestration_guardrails.validation_context import check_env_consistency

    warnings = check_env_consistency(
        context_file=args.context_file,
        run_date_sgt=args.run_date_sgt,
        github_run_id=args.github_run_id,
        theme_name=args.theme_name,
        workflow_name=args.workflow_name,
        validation_summary_file=args.validation_summary_file,
        telemetry_snapshot_file=args.telemetry_snapshot_file,
        artifact_manifest_file=args.artifact_manifest_file,
    )

    if warnings:
        for warning in warnings:
            print(f"[validation_context][warning] {warning}")
    else:
        print("[validation_context] environment consistency check passed")

    return 0


def cmd_telemetry_snapshot(args: argparse.Namespace) -> int:
    """
    Create logs/telemetry_context_snapshot.json by combining execution context,
    validation summary, pipeline status, and runtime metrics.
    """
    from core.orchestration_guardrails.telemetry_context import create_telemetry_snapshot

    create_telemetry_snapshot(
        context_file=args.context_file,
        validation_summary_file=args.validation_summary_file,
        pipeline_status=args.pipeline_status,
        runtime_seconds=args.runtime_seconds,
        output_file=args.output_file,
    )

    print(f"[telemetry_context] telemetry snapshot written to {args.output_file}")
    print(f"[telemetry_context] pipeline_status={args.pipeline_status}")
    print(f"[telemetry_context] runtime_seconds={args.runtime_seconds}")

    return 0


def cmd_artifact_manifest(args: argparse.Namespace) -> int:
    """
    Create logs/context_artifact_manifest.json so uploaded artifacts can be
    traced back to the shared execution context and validation/telemetry files.
    """
    from core.orchestration_guardrails.artifact_manifest import build_artifact_manifest

    build_artifact_manifest(
        context_file=args.context_file,
        validation_summary_file=args.validation_summary_file,
        telemetry_snapshot_file=args.telemetry_snapshot_file,
        output_file=args.output_file,
    )

    print(f"[artifact_manifest] context artifact manifest written to {args.output_file}")

    return 0




# ----------------------------------------------------------------------
# Tier 3E — Cross-workflow operational aggregation commands
# ----------------------------------------------------------------------
def cmd_aggregate_operational_summary(args: argparse.Namespace) -> int:
    from core.orchestration_guardrails.operational_aggregation import (
        aggregate_operational_summary,
    )

    result = aggregate_operational_summary(
        context_file=args.context_file,
        validation_summary_file=args.validation_summary_file,
        telemetry_snapshot_file=args.telemetry_snapshot_file,
        artifact_manifest_file=args.artifact_manifest_file,
        output_dir=args.output_dir,
    )

    print("[operational_aggregation] files written:")
    for path in result["files_written"]:
        print(f"[operational_aggregation] - {path}")
    print(f"[operational_aggregation] operational_status={result['operational_status']}")
    print(f"[operational_aggregation] warnings_count={result['warnings_count']}")

    return 0


# ----------------------------------------------------------------------
# Parser construction
# ----------------------------------------------------------------------
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

    # ------------------------------------------------------------------
    # Tier 3D validation commands
    # ------------------------------------------------------------------
    validation = subparsers.add_parser("validation")
    validation_subparsers = validation.add_subparsers(dest="validation_command")

    validation_summarize = validation_subparsers.add_parser("summarize")
    validation_summarize.add_argument("--context-file", default=DEFAULT_CONTEXT_FILE)
    validation_summarize.add_argument("--source", required=True)
    validation_summarize.add_argument("--validation-status", required=True)
    validation_summarize.add_argument("--warnings-count", type=int, default=0)
    validation_summarize.add_argument("--errors-count", type=int, default=0)
    validation_summarize.add_argument("--hard-fail-count", type=int, default=0)
    validation_summarize.add_argument(
        "--output-file",
        default=DEFAULT_VALIDATION_SUMMARY_FILE,
    )
    validation_summarize.set_defaults(func=cmd_validation_summarize)

    validation_check_env = validation_subparsers.add_parser("check-env-consistency")
    validation_check_env.add_argument("--context-file", default=DEFAULT_CONTEXT_FILE)
    validation_check_env.add_argument("--run-date-sgt", default="")
    validation_check_env.add_argument("--github-run-id", default="")
    validation_check_env.add_argument("--theme-name", default="")
    validation_check_env.add_argument("--workflow-name", default="")
    validation_check_env.add_argument(
        "--validation-summary-file",
        default=DEFAULT_VALIDATION_SUMMARY_FILE,
    )
    validation_check_env.add_argument(
        "--telemetry-snapshot-file",
        default=DEFAULT_TELEMETRY_SNAPSHOT_FILE,
    )
    validation_check_env.add_argument(
        "--artifact-manifest-file",
        default=DEFAULT_ARTIFACT_MANIFEST_FILE,
    )
    validation_check_env.set_defaults(func=cmd_validation_check_env_consistency)

    # ------------------------------------------------------------------
    # Tier 3D telemetry commands
    # ------------------------------------------------------------------
    telemetry = subparsers.add_parser("telemetry")
    telemetry_subparsers = telemetry.add_subparsers(dest="telemetry_command")

    telemetry_snapshot = telemetry_subparsers.add_parser("snapshot")
    telemetry_snapshot.add_argument("--context-file", default=DEFAULT_CONTEXT_FILE)
    telemetry_snapshot.add_argument(
        "--validation-summary-file",
        default=DEFAULT_VALIDATION_SUMMARY_FILE,
    )
    telemetry_snapshot.add_argument("--pipeline-status", required=True)
    telemetry_snapshot.add_argument("--runtime-seconds", type=int, required=True)
    telemetry_snapshot.add_argument(
        "--output-file",
        default=DEFAULT_TELEMETRY_SNAPSHOT_FILE,
    )
    telemetry_snapshot.set_defaults(func=cmd_telemetry_snapshot)

    # ------------------------------------------------------------------
    # Tier 3D artifact manifest commands
    # ------------------------------------------------------------------
    artifact = subparsers.add_parser("artifact")
    artifact_subparsers = artifact.add_subparsers(dest="artifact_command")

    artifact_manifest = artifact_subparsers.add_parser("manifest")
    artifact_manifest.add_argument("--context-file", default=DEFAULT_CONTEXT_FILE)
    artifact_manifest.add_argument(
        "--validation-summary-file",
        default=DEFAULT_VALIDATION_SUMMARY_FILE,
    )
    artifact_manifest.add_argument(
        "--telemetry-snapshot-file",
        default=DEFAULT_TELEMETRY_SNAPSHOT_FILE,
    )
    artifact_manifest.add_argument(
        "--output-file",
        default=DEFAULT_ARTIFACT_MANIFEST_FILE,
    )
    artifact_manifest.set_defaults(func=cmd_artifact_manifest)

    # ------------------------------------------------------------------
    # Tier 3E aggregation commands
    # ------------------------------------------------------------------
    aggregate = subparsers.add_parser("aggregate")
    aggregate_subparsers = aggregate.add_subparsers(dest="aggregate_command")

    operational_summary = aggregate_subparsers.add_parser("operational-summary")
    operational_summary.add_argument("--context-file", default=DEFAULT_CONTEXT_FILE)
    operational_summary.add_argument(
        "--validation-summary-file",
        default=DEFAULT_VALIDATION_SUMMARY_FILE,
    )
    operational_summary.add_argument(
        "--telemetry-snapshot-file",
        default=DEFAULT_TELEMETRY_SNAPSHOT_FILE,
    )
    operational_summary.add_argument(
        "--artifact-manifest-file",
        default=DEFAULT_ARTIFACT_MANIFEST_FILE,
    )
    operational_summary.add_argument("--output-dir", default="logs")
    operational_summary.set_defaults(func=cmd_aggregate_operational_summary)

    return parser


# ----------------------------------------------------------------------
# Entrypoint
# ----------------------------------------------------------------------
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
