#!/usr/bin/env python3
from __future__ import annotations

import json
from collections import OrderedDict
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from transmission_layers.expectation_failure.dashboard_operationalization.dashboard_o7_streamlit_supabase_runtime import (
    build_streamlit_supabase_runtime_config,
    resolve_streamlit_supabase_client,
)
from transmission_layers.expectation_failure.dashboard_operationalization.d7_streamlit_dashboard_viewer import (
    load_d7_dashboard_findings,
    load_d7_dashboard_narratives,
    load_d7_dashboard_evidence_maps,
    load_d7_dashboard_operational_integrity,
    build_d7_dashboard_view_model,
)


def _build_payload() -> OrderedDict:
    runtime = build_streamlit_supabase_runtime_config()
    resolution = resolve_streamlit_supabase_client(runtime)
    if not resolution.get("client_resolved"):
        return OrderedDict([
            ("inspection_status", "BLOCKED_MISSING_CREDENTIALS"),
            ("reason", "supabase_client_not_resolved"),
            ("runtime", OrderedDict([
                ("credentials_present", bool(runtime.get("credentials_present"))),
                ("client_factory_source", resolution.get("client_factory_source")),
            ])),
        ])

    client = resolution.get("client")
    findings = load_d7_dashboard_findings(client)
    narratives = load_d7_dashboard_narratives(client)
    evidence = load_d7_dashboard_evidence_maps(client)
    integrity = load_d7_dashboard_operational_integrity(client)
    vm = build_d7_dashboard_view_model(
        findings_payload=findings,
        narratives_payload=narratives,
        evidence_payload=evidence,
        integrity_payload=integrity,
    )

    d15 = vm.get("d15_historical_operational_intelligence", {})
    d16 = vm.get("d16_historical_findings_operator_narrative", {})
    d17 = vm.get("d17_historical_confidence_lineage", {})
    d18 = vm.get("d18_cross_run_confidence_delta_operator_triage", {})
    d19 = vm.get("d19_triage_explainability_continuity_taxonomy", {})
    h1 = vm.get("h1_historical_density_expansion", {})
    h2 = vm.get("h2_governed_replay_expansion_cycle", {})

    return OrderedDict([
        ("inspection_status", "READY"),
        ("d7_render_status", vm.get("render_status", "UNKNOWN")),
        ("row_counts", OrderedDict([
            ("replay", int(((integrity.get("replay") or {}).get("row_count") or 0))),
            ("manifests", int(((integrity.get("manifests") or {}).get("row_count") or 0))),
        ])),
        ("d15_to_d19", OrderedDict([
            ("d15", d15.get("historical_replay_depth")),
            ("d16", d16.get("historical_replay_depth")),
            ("d17", d17.get("historical_replay_depth")),
            ("d18", d18.get("historical_replay_depth")),
            ("d19", d19.get("historical_replay_depth")),
        ])),
        ("h1", OrderedDict([
            ("certification_status", ((h1.get("certification") or {}).get("certification_status"))),
            ("density_inventory", h1.get("density_inventory")),
            ("density_gap_analysis", h1.get("density_gap_analysis")),
            ("operational_density_summary", h1.get("operational_density_summary")),
        ])),
        ("h2", OrderedDict([
            ("certification_status", ((h2.get("certification") or {}).get("certification_status"))),
            ("pre_expansion_baseline", h2.get("Pre-Expansion Baseline")),
            ("post_expansion_comparison", h2.get("Post-Expansion Comparison")),
            ("recommendation", h2.get("Governed Expansion Recommendation")),
        ])),
    ])


if __name__ == "__main__":
    print(json.dumps(_build_payload(), indent=2, sort_keys=False))
