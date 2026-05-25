from collections import OrderedDict

from transmission_layers.expectation_failure.expectation_intelligence import (
    build_h2_pre_expansion_baseline,
    build_h2_governed_expansion_recommendation,
    build_h2_operator_execution_checklist,
    build_h2_d21_command_template,
    build_h2_post_expansion_comparison,
    build_h2_cycle_dashboard_payload,
    certify_h2_governed_replay_expansion_cycle,
    H2_DENSITY_IMPROVED,
    H2_DENSITY_UNCHANGED,
    H2_DENSITY_DEGRADED,
    H2_POST_RUN_INSUFFICIENT_DATA,
)
from transmission_layers.expectation_failure.dashboard_operationalization.d7_streamlit_dashboard_viewer import (
    D7_RENDER_SECTION_ORDER,
    build_d7_dashboard_view_model,
)


def _h1_payload(depth=4, regimes=2, contradictions=4, linkage=1.0, recurring=2, movements=2, lineage=3):
    return OrderedDict([
        ("Historical Density Overview", OrderedDict([("current_replay_depth", depth)])),
        ("Replay Coverage", OrderedDict([("run_count", depth), ("distinct_runs", depth)])),
        ("Regime Diversity", OrderedDict([("distinct_regimes", regimes)])),
        ("Contradiction Evolution Richness", OrderedDict([("contradiction_claim_count", contradictions)])),
        ("Continuity Linkage Density", OrderedDict([("avg_linkage_per_run", linkage)])),
        ("Recurring Finding Density", OrderedDict([("cluster_count", recurring)])),
        ("Confidence Movement Density", OrderedDict([("movement_count", movements)])),
        ("Lineage Richness", OrderedDict([("distinct_lineage_refs", lineage)])),
        ("Recommended Expansion Plan", OrderedDict([("recommended_expansion_batch_size", 3), ("recommended_next_replay_window_ranges", ["window_005_to_007"])])),
    ])


def test_h2_deterministic_cycle_and_certification():
    h1 = _h1_payload()
    baseline = build_h2_pre_expansion_baseline(h1_dashboard_payload=h1, h1_certification={"certification_status": "CERTIFIED"})
    rec = build_h2_governed_expansion_recommendation(h1_expansion_plan=h1["Recommended Expansion Plan"], pre_expansion_baseline=baseline)
    checklist = build_h2_operator_execution_checklist(recommendation=rec)
    cmd = build_h2_d21_command_template(recommendation=rec)
    post = build_h2_post_expansion_comparison(pre_expansion_baseline=baseline, post_h1_dashboard_payload=_h1_payload(depth=5, regimes=3, contradictions=6, linkage=1.2, recurring=3, movements=3, lineage=5))
    payload = build_h2_cycle_dashboard_payload(pre_expansion_baseline=baseline, governed_expansion_recommendation=rec, operator_execution_checklist=checklist, d21_command_template=cmd, post_expansion_comparison=post)
    cert = certify_h2_governed_replay_expansion_cycle(pre_expansion_baseline=baseline, governed_expansion_recommendation=rec, operator_execution_checklist=checklist, d21_command_template=cmd, cycle_dashboard_payload=payload)

    assert list(payload.keys()) == ["Pre-Expansion Baseline", "Governed Expansion Recommendation", "Operator Execution Checklist", "D21 Command Template", "Post-Expansion Comparison", "Governance/Lineage Controls"]
    assert "operator-approval-token" in cmd and "<REQUIRED_OPERATOR_APPROVAL_TOKEN>" in cmd
    assert "select " not in cmd.lower()
    assert cert["no_writes_by_h2"] is True
    assert post["density_improvement_verdict"] == H2_DENSITY_IMPROVED


def test_h2_post_verdicts_and_insufficient():
    h1 = _h1_payload()
    baseline = build_h2_pre_expansion_baseline(h1_dashboard_payload=h1)
    assert build_h2_post_expansion_comparison(pre_expansion_baseline=baseline, post_h1_dashboard_payload=h1)["density_improvement_verdict"] == H2_DENSITY_UNCHANGED
    degraded = build_h2_post_expansion_comparison(pre_expansion_baseline=baseline, post_h1_dashboard_payload=_h1_payload(depth=3, regimes=1, contradictions=1, linkage=0.2, recurring=0, movements=0, lineage=1))
    assert degraded["density_improvement_verdict"] == H2_DENSITY_DEGRADED
    assert build_h2_post_expansion_comparison(pre_expansion_baseline={}, post_h1_dashboard_payload=h1)["density_improvement_verdict"] == H2_POST_RUN_INSUFFICIENT_DATA


def test_h2_d7_integration_and_ordering():
    vm = build_d7_dashboard_view_model(findings_payload={"rows": []}, narratives_payload={"rows": []}, evidence_payload={"rows": []}, integrity_payload={"replay": {"rows": []}, "manifests": {"rows": []}, "audits": {"rows": []}, "governance": {"rows": []}, "supervisor": {"rows": []}})
    assert "h2_governed_replay_expansion_cycle" in vm
    assert D7_RENDER_SECTION_ORDER[:8] == (
        "e6_expectation_executive_summary",
        "d15_historical_operational_intelligence",
        "d16_historical_findings_operator_narrative",
        "d17_historical_confidence_lineage",
        "d18_cross_run_confidence_delta_operator_triage",
        "d19_triage_explainability_continuity_taxonomy",
        "h1_historical_density_expansion",
        "h2_governed_replay_expansion_cycle",
    )
