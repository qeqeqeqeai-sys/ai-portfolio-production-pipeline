#!/usr/bin/env python3
"""Lint GitHub workflow observability tier usage.

Enforces that workflows including Tier 3F trend intelligence also include
Tier 3E operational aggregation.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

WORKFLOWS_DIR = Path('.github/workflows')

TIER_3E_PATTERN = re.compile(
    r"python\s+-m\s+core\.orchestration_guardrails\.cli\s+aggregate\s+operational-summary",
    re.MULTILINE,
)
TIER_3F_PATTERN = re.compile(
    r"python\s+-m\s+core\.orchestration_guardrails\.cli\s+trend\s+analyze",
    re.MULTILINE,
)


def _normalize_for_command_detection(text: str) -> str:
    # Normalize multiline GitHub Actions shell formatting (YAML wrapping and
    # shell continuation backslashes) so split commands still match reliably.
    normalized = text.replace("\\\n", " ")
    return re.sub(r"\s+", " ", normalized)


def lint_workflow(path: Path) -> list[str]:
    text = path.read_text(encoding='utf-8')
    normalized_text = _normalize_for_command_detection(text)

    tier_3e_present = bool(TIER_3E_PATTERN.search(normalized_text))
    tier_3f_present = bool(TIER_3F_PATTERN.search(normalized_text))

    errors: list[str] = []
    if tier_3f_present and not tier_3e_present:
        errors.append('ERROR: Tier 3F present but Tier 3E operational aggregation is missing')
    return errors


def main() -> int:
    if not WORKFLOWS_DIR.exists():
        print(f'No workflows directory found at {WORKFLOWS_DIR}')
        return 0

    failures = 0
    for workflow in sorted(WORKFLOWS_DIR.glob('*.yml')):
        errors = lint_workflow(workflow)
        if errors:
            print(f'[{workflow}]')
            for err in errors:
                print(err)
            failures += len(errors)

    return 1 if failures else 0


if __name__ == '__main__':
    raise SystemExit(main())
