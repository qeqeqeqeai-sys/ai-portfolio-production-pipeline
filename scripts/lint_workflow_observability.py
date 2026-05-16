#!/usr/bin/env python3
"""Lint GitHub Actions workflows for observability guardrail coverage.

This validator is intentionally marker-based and lightweight. It checks that
workflows under .github/workflows that participate in the platform observability
pattern do not drift into partial Tier 3E / Tier 3F coverage.

Rules:
- If a workflow contains Tier 3E aggregation, it must also contain Tier 3F trend analysis.
- If a workflow contains Tier 3F trend analysis, it must also contain Tier 3E aggregation.
- Workflows with either Tier 3E or Tier 3F must upload observability artifacts.
- Tier 3F workflows should expose the expected platform trend artifact names.

The script does not rewrite files.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


TIER_3E_PATTERN = re.compile(
    r"python\s+-m\s+core\.orchestration_guardrails\.cli\s+aggregate\s+operational-summary"
)
TIER_3F_PATTERN = re.compile(
    r"python\s+-m\s+core\.orchestration_guardrails\.cli\s+trend\s+analyze"
)
UPLOAD_ARTIFACT_MARKER = "actions/upload-artifact"

TIER_3F_EXPECTED_ARTIFACTS = (
    "logs/platform_execution_consistency.json",
    "logs/platform_operational_trend_summary.json",
    "logs/platform_recurring_warnings.json",
    "logs/platform_runtime_drift_summary.json",
    "logs/platform_workflow_health_score.json",
)


@dataclass(frozen=True)
class WorkflowLintResult:
    path: Path
    tier_3e_present: bool
    tier_3f_present: bool
    artifact_upload_present: bool
    missing_trend_artifacts: tuple[str, ...]
    errors: tuple[str, ...]
    warnings: tuple[str, ...]


def _iter_workflows(root: Path) -> Iterable[Path]:
    workflows_dir = root / ".github" / "workflows"
    if not workflows_dir.exists():
        return ()
    return sorted(
        path
        for path in workflows_dir.iterdir()
        if path.is_file() and path.suffix in {".yml", ".yaml"}
    )


def _normalize_command_text(text: str) -> str:
    text = text.replace("\\\r\n", " ")
    text = text.replace("\\\n", " ")
    text = text.replace("\\\r", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _lint_workflow(path: Path, root: Path) -> WorkflowLintResult:
    raw_text = path.read_text(encoding="utf-8")
    normalized_text = _normalize_command_text(raw_text)

    tier_3e_present = bool(TIER_3E_PATTERN.search(normalized_text))
    tier_3f_present = bool(TIER_3F_PATTERN.search(normalized_text))
    artifact_upload_present = UPLOAD_ARTIFACT_MARKER in raw_text

    errors: list[str] = []
    warnings: list[str] = []

    if tier_3e_present and not tier_3f_present:
        errors.append("Tier 3E present but Tier 3F trend analysis is missing")

    if tier_3f_present and not tier_3e_present:
        errors.append("Tier 3F present but Tier 3E operational aggregation is missing")

    if (tier_3e_present or tier_3f_present) and not artifact_upload_present:
        errors.append("Tier 3E/Tier 3F workflow is missing actions/upload-artifact")

    missing_trend_artifacts = tuple(
        artifact for artifact in TIER_3F_EXPECTED_ARTIFACTS if artifact not in raw_text
    )

    if tier_3f_present and missing_trend_artifacts:
        warnings.append(
            "Tier 3F present but one or more expected trend artifact paths are not explicitly uploaded"
        )

    return WorkflowLintResult(
        path=path.relative_to(root),
        tier_3e_present=tier_3e_present,
        tier_3f_present=tier_3f_present,
        artifact_upload_present=artifact_upload_present,
        missing_trend_artifacts=missing_trend_artifacts,
        errors=tuple(errors),
        warnings=tuple(warnings),
    )


def _format_bool(value: bool) -> str:
    return "yes" if value else "no"


def _print_report(results: list[WorkflowLintResult], strict_warnings: bool) -> None:
    print("# Workflow Observability Lint Report")
    print()
    print(f"Workflows scanned: {len(results)}")
    print()
    print("| Workflow | Tier 3E | Tier 3F | Artifact upload | Errors | Warnings |")
    print("|---|---:|---:|---:|---:|---:|")

    for result in results:
        print(
            "| "
            f"{result.path} | "
            f"{_format_bool(result.tier_3e_present)} | "
            f"{_format_bool(result.tier_3f_present)} | "
            f"{_format_bool(result.artifact_upload_present)} | "
            f"{len(result.errors)} | "
            f"{len(result.warnings)} |"
        )

    print()

    for result in results:
        if not result.errors and not result.warnings:
            continue

        print(f"## {result.path}")

        for error in result.errors:
            print(f"ERROR: {error}")

        for warning in result.warnings:
            print(f"WARNING: {warning}")

        if result.missing_trend_artifacts:
            print("Missing expected Tier 3F artifact paths:")
            for artifact in result.missing_trend_artifacts:
                print(f"- {artifact}")

        print()

    total_errors = sum(len(result.errors) for result in results)
    total_warnings = sum(len(result.warnings) for result in results)

    print("## Summary")
    print(f"Errors: {total_errors}")
    print(f"Warnings: {total_warnings}")

    if strict_warnings and total_warnings:
        print("Strict warning mode: warnings are treated as failures.")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Lint .github/workflows for Tier 3E/Tier 3F observability coverage."
    )
    parser.add_argument(
        "--root",
        default=".",
        help="Repository root. Defaults to current working directory.",
    )
    parser.add_argument(
        "--strict-warnings",
        action="store_true",
        help="Treat warnings as failures.",
    )
    args = parser.parse_args()

    root = Path(args.root).resolve()
    workflows = list(_iter_workflows(root))

    if not workflows:
        print("No workflow files found under .github/workflows", file=sys.stderr)
        return 1

    results = [_lint_workflow(path, root) for path in workflows]
    _print_report(results, strict_warnings=args.strict_warnings)

    total_errors = sum(len(result.errors) for result in results)
    total_warnings = sum(len(result.warnings) for result in results)

    if total_errors:
        return 1

    if args.strict_warnings and total_warnings:
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
