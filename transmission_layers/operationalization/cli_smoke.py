"""Deterministic operationalization CLI smoke entry point (Operationalization O1I)."""

from __future__ import annotations

import argparse
from pathlib import Path

from .audit_summary import build_operational_audit_summary
from .manifests import empty_manifest
from .serialization import stable_serialize


def _build_smoke_manifest() -> dict:
    return empty_manifest(
        run_id="run_o1i_cli_smoke",
        run_type="operationalization_cli_smoke",
        tier_scope="operationalization",
        generated_at_sgt="2026-05-21T00:00:00+08:00",
    )


def run_operationalization_cli_smoke(export_dir: str | Path, *, overwrite: bool = False) -> dict:
    """Run deterministic operationalization smoke flow and return stable report payload."""
    manifest = _build_smoke_manifest()
    audit = build_operational_audit_summary(manifest, export_dir, overwrite=overwrite)

    audit_summary = audit["audit_summary"]
    summary = {
        "audit_status": audit["audit_status"],
        "operation_mode": audit["operation_mode"],
        "validation_status": audit_summary["validation_status"],
        "readiness_status": audit_summary["readiness_status"],
        "readiness_classification": audit_summary["readiness_classification"],
        "export_status": audit_summary["export_status"],
        "export_ready": audit_summary["export_ready"],
        "persistence_status": audit_summary["persistence_status"],
        "verification_status": audit_summary["verification_status"],
        "is_verified": audit_summary["is_verified"],
    }

    return {
        "cli_status": "success",
        "operation": "operationalization_cli_smoke",
        "audit": audit,
        "summary": summary,
    }


def main(argv: list[str] | None = None) -> int:
    """Run CLI smoke with explicit export path and deterministic serialized output."""
    parser = argparse.ArgumentParser(prog="operationalization-cli-smoke")
    parser.add_argument("--export-dir", required=True)
    parser.add_argument("--overwrite", action="store_true")

    args = parser.parse_args(argv)

    result = run_operationalization_cli_smoke(args.export_dir, overwrite=args.overwrite)
    print(stable_serialize(result))

    return 0 if result["summary"]["is_verified"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
