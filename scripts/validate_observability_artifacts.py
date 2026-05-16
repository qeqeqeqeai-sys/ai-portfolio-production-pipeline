#!/usr/bin/env python3
"""Advisory validator for observability JSON artifacts under logs/.

Behavior:
- Missing expected files are warnings (advisory mode).
- Malformed JSON is an error.
- Missing required top-level keys is an error.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path


EXPECTED_ARTIFACT_KEYS: dict[str, tuple[str, ...]] = {
    "execution_context.json": ("execution_context",),
    "validation_summary.json": ("validation_summary",),
    "telemetry_context_snapshot.json": ("telemetry_context_snapshot",),
    "context_artifact_manifest.json": ("context_artifact_manifest",),
    "platform_operational_summary.json": ("platform_operational_summary",),
    "platform_operational_trend_summary.json": ("platform_operational_trend_summary",),
    "platform_workflow_health_score.json": ("platform_workflow_health_score",),
}


@dataclass(frozen=True)
class ValidationIssue:
    level: str
    file: str
    message: str


def _validate_file(path: Path, required_keys: tuple[str, ...]) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []

    if not path.exists():
        issues.append(
            ValidationIssue(
                level="WARNING",
                file=str(path),
                message="File is missing (advisory mode).",
            )
        )
        return issues

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        issues.append(
            ValidationIssue(
                level="ERROR",
                file=str(path),
                message=(
                    "Malformed JSON "
                    f"(line {exc.lineno}, column {exc.colno}): {exc.msg}"
                ),
            )
        )
        return issues

    if not isinstance(payload, dict):
        issues.append(
            ValidationIssue(
                level="ERROR",
                file=str(path),
                message="Top-level JSON value must be an object.",
            )
        )
        return issues

    missing_keys = [key for key in required_keys if key not in payload]
    if missing_keys:
        issues.append(
            ValidationIssue(
                level="ERROR",
                file=str(path),
                message=f"Missing required top-level keys: {', '.join(missing_keys)}",
            )
        )

    return issues


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate observability artifacts under logs/."
    )
    parser.add_argument(
        "--root",
        default=".",
        help="Repository root. Defaults to current working directory.",
    )
    args = parser.parse_args()

    root = Path(args.root).resolve()
    logs_dir = root / "logs"

    all_issues: list[ValidationIssue] = []
    for filename, required_keys in EXPECTED_ARTIFACT_KEYS.items():
        artifact_path = logs_dir / filename
        all_issues.extend(_validate_file(artifact_path, required_keys))

    print("# Observability Artifact Validation Report")
    print()
    print(f"Artifacts checked: {len(EXPECTED_ARTIFACT_KEYS)}")

    if all_issues:
        print()
        for issue in all_issues:
            print(f"{issue.level}: {issue.file} -> {issue.message}")

    total_errors = sum(1 for issue in all_issues if issue.level == "ERROR")
    total_warnings = sum(1 for issue in all_issues if issue.level == "WARNING")

    print()
    print("## Summary")
    print(f"Errors: {total_errors}")
    print(f"Warnings: {total_warnings}")

    return 1 if total_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
