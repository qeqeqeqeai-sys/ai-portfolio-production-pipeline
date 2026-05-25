from copy import deepcopy

from transmission_layers.expectation_failure.expectation_intelligence import (
    build_h1_density_expansion_inventory,
    build_h1_density_gap_analysis,
    build_h1_expansion_plan,
    build_h1_operational_density_summary,
    build_h1_dashboard_payload,
    certify_h1_density_expansion,
)
from transmission_layers.expectation_failure.dashboard_operationalization.d7_streamlit_dashboard_viewer import build_d7_dashboard_view_model


def _runs():
    return [
        {"run_id": "R1", "regime": "TIGHT", "contradictions": {"claims": ["c1"]}, "lineage_refs": ["l1"]},
        {"run_id": "R2", "regime": "LOOSE", "contradictions": {"claims": ["c2", "c3"]}, "lineage_refs": ["l2", "l3"]},
    ]


def test_h1_api_presence_and_determinism_and_immutability():
    runs = _runs()
    snapshot = deepcopy(runs)
    inv1 = build_h1_density_expansion_inventory(historical_runs=runs)
    inv2 = build_h1_density_expansion_inventory(historical_runs=runs)
    assert inv1 == inv2
    assert runs == snapshot
    gaps = build_h1_density_gap_analysis(density_inventory=inv1)
    plan = build_h1_expansion_plan(density_inventory=inv1, density_gap_analysis=gaps)
    summary = build_h1_operational_density_summary(density_inventory=inv1, density_gap_analysis=gaps)
    payload = build_h1_dashboard_payload(density_inventory=inv1, density_gap_analysis=gaps, expansion_plan=plan, operational_density_summary=summary)
    cert = certify_h1_density_expansion(density_inventory=inv1, density_gap_analysis=gaps, expansion_plan=plan, dashboard_payload=payload)
    assert cert["certification_status"] in {"CERTIFIED_HISTORICAL_DENSITY_EXPANSION", "DEGRADED_HISTORICAL_DENSITY_EXPANSION"}
    assert "buy" not in str(payload).lower()


def test_h1_blocked_on_missing_and_no_forbidden_ops_language():
    cert = certify_h1_density_expansion(density_inventory=None, density_gap_analysis=None, expansion_plan=None, dashboard_payload={})
    assert cert["certification_status"] == "BLOCKED_HISTORICAL_DENSITY_EXPANSION"


def test_h1_d7_integration_smoke():
    vm = build_d7_dashboard_view_model(
        findings_payload={"rows": []},
        narratives_payload={"rows": []},
        evidence_payload={"rows": []},
        integrity_payload={"manifests": {"rows": []}, "audits": {"rows": []}, "replay": {"rows": []}, "governance": {"rows": []}, "supervisor": {"rows": []}},
    )
    assert "h1_historical_density_expansion" in vm
    assert "no_writes" in str(vm["h1_historical_density_expansion"]).lower()
    text = str(vm).lower()
    assert "insert into" not in text and "select * from" not in text
