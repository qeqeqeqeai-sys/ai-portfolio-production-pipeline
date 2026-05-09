"""
run_production_validation_gates.py

CLI entrypoint for GitHub Actions validation gate.

Exit codes:
- 0 = validation passed
- 1 = validation failed intentionally
"""

import sys

from production_validation_gates import run_all_validations


def main() -> int:
    summary = run_all_validations()

    if summary.should_fail_pipeline:
        print("[VALIDATION_GATE_FAILED] Pipeline intentionally failed due to validation errors.")
        return 1

    print("[VALIDATION_GATE_PASSED] Pipeline passed production validation gates.")
    return 0


if __name__ == "__main__":
    sys.exit(main())