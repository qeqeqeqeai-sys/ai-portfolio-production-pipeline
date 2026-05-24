"""One-off real D6 proving-cycle runner using injected Supabase client only."""

from __future__ import annotations

import os
import sys
from collections import OrderedDict
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from transmission_layers.expectation_failure.dashboard_operationalization.d6_operational_proving_cycle import (
    build_d6_operational_proving_report,
    build_d6_operational_proving_summary,
    execute_d6_operational_proving_cycle,
)
from transmission_layers.expectation_failure.dashboard_operationalization.dashboard_o7_streamlit_supabase_runtime import (
    build_streamlit_supabase_runtime_config,
    resolve_streamlit_supabase_client,
)


class SupabaseCredentialsMissingError(RuntimeError):
    """Raised when Supabase credentials are not available at script/runtime boundary."""


def _resolve_runtime_and_client() -> Any:
    runtime_config = build_streamlit_supabase_runtime_config(
        supabase_url=(os.getenv("SUPABASE_URL") or "").strip() or None,
        supabase_key=(
            (os.getenv("SUPABASE_SERVICE_ROLE_KEY") or "").strip()
            or (os.getenv("SUPABASE_ANON_KEY") or "").strip()
            or (os.getenv("SUPABASE_KEY") or "").strip()
            or None
        ),
    )

    resolution = resolve_streamlit_supabase_client(runtime_config)
    if not runtime_config.get("credentials_present"):
        raise SupabaseCredentialsMissingError(
            "Missing Supabase credentials: SUPABASE_URL and one of "
            "SUPABASE_SERVICE_ROLE_KEY|SUPABASE_ANON_KEY|SUPABASE_KEY are required."
        )
    if not resolution.get("client_resolved") or resolution.get("client") is None:
        raise RuntimeError(
            "Unable to resolve Supabase client "
            f"(error_type={resolution.get('client_error_type')}, "
            f"message={resolution.get('client_error_message_short')})."
        )
    return resolution["client"]


def _persisted_table_counts(cycle_result: dict[str, Any]) -> OrderedDict[str, int]:
    out: OrderedDict[str, int] = OrderedDict()
    for row in cycle_result.get("d3_persistence", {}).get("table_results", []):
        table = str(row.get("target_table") or "")
        out[table] = int(row.get("persisted_record_count") or 0)
    return out


def main() -> int:
    try:
        client = _resolve_runtime_and_client()
    except SupabaseCredentialsMissingError as exc:
        print(f"ERROR: {exc}")
        return 2

    result = execute_d6_operational_proving_cycle(client=client, dry_run=False)
    summary = build_d6_operational_proving_summary(result)
    report = build_d6_operational_proving_report(result)

    print(f"generated_finding_count={summary.get('finding_count')}")
    print(f"narrative_count={summary.get('narrative_count')}")
    print(f"persistence_status={summary.get('persistence_state')}")
    print(f"readback_verification_status={summary.get('readback_verification_status')}")
    print("persisted_table_counts=")
    for table, count in _persisted_table_counts(result).items():
        print(f"- {table}: {count}")
    print(f"supervisor_usefulness_evaluation={report.get('evaluation', {}).get('operational_usefulness')}")
    print(f"checksum_continuity={dict(summary.get('checksum_continuity', {}))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
