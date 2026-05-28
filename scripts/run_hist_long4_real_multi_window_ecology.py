from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from transmission_layers.expectation_failure.real_data.hist_long4_real_multi_window_ecology import (
    DEFAULT_ARTIFACT_PATH,
    DEFAULT_OUTPUT_ROOT,
    DEFAULT_REPORT_PATH,
    REQUIRED_WINDOWS,
    write_hist_long4_review,
)


def _parse_windows(value: str) -> tuple[int, ...]:
    try:
        windows = tuple(int(item.strip()) for item in value.split(",") if item.strip())
    except ValueError as exc:
        raise argparse.ArgumentTypeError("windows must be a comma-separated integer list") from exc
    if windows != REQUIRED_WINDOWS:
        raise argparse.ArgumentTypeError("windows must be exactly 20,60,120")
    return windows


def main() -> None:
    parser = argparse.ArgumentParser(description="Run HIST-LONG-4 real multi-window ecology accumulation")
    parser.add_argument("--windows", type=_parse_windows, default=REQUIRED_WINDOWS, help="Comma-separated windows; must be exactly 20,60,120")
    parser.add_argument("--max-symbols", type=int, default=241)
    parser.add_argument("--symbol-chunk-size", type=int, default=50)
    parser.add_argument("--expected-chunk-count", type=int, default=5)
    parser.add_argument("--output-root", default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--report-path", default=DEFAULT_REPORT_PATH)
    parser.add_argument("--artifact-path", default=DEFAULT_ARTIFACT_PATH)
    parser.add_argument("--end-date", default=None)
    args = parser.parse_args()

    if not os.environ.get("FMP_API_KEY"):
        raise RuntimeError("FMP_API_KEY missing; HIST-LONG-4 fails closed")

    artifact = write_hist_long4_review(
        windows=args.windows,
        max_symbols=args.max_symbols,
        symbol_chunk_size=args.symbol_chunk_size,
        expected_chunk_count=args.expected_chunk_count,
        output_root=args.output_root,
        report_path=args.report_path,
        artifact_path=args.artifact_path,
        end_date=args.end_date,
    )
    print(json.dumps({"status": artifact["status"], "all_three_real_windows_completed": artifact["all_three_real_windows_completed"]}, sort_keys=True))


if __name__ == "__main__":
    main()
