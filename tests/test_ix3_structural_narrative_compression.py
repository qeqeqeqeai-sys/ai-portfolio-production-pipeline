from copy import deepcopy
from transmission_layers.expectation_failure.expectation_intelligence import build_ix3_insight_cluster_inventory, build_ix3_redundancy_and_overlap_analysis, build_ix3_compressed_structural_narratives, build_ix3_dominant_theme_summary, build_ix3_operator_narrative_brief, build_ix3_cluster_priority_ranking, build_ix3_dashboard_payload, certify_ix3_structural_narrative_compression


def _fixtures():
    ix1=[
        {"insight_id":"i1","summary":"contradiction persistence anomaly","bucket":"HIGH_SIGNIFICANCE_STRUCTURAL_NARRATIVE"},
        {"insight_id":"i2","summary":"semantic fragility continuity fracture","bucket":"HIGH_SEMANTIC_FRAGILITY_CLUSTER"},
        {"insight_id":"i3","summary":"transition anomaly recurring structural pattern","bucket":"MODERATE_OPERATOR_RELEVANCE"},
    ]
    ix2=[
        {"insight_id":"i1","supporting_replay_refs":["r1"],"supporting_transition_refs":["t1"],"supporting_diagnostic_refs":["d1"],"supporting_theme_refs":["th1"],"supporting_regime_refs":[],"supporting_confidence_refs":["c1"],"supporting_continuity_refs":["cn1"],"evidence_count":6},
        {"insight_id":"i2","supporting_replay_refs":["r2"],"supporting_transition_refs":[],"supporting_diagnostic_refs":[],"supporting_theme_refs":[],"supporting_regime_refs":[],"supporting_confidence_refs":[],"supporting_continuity_refs":[],"evidence_count":1},
        {"insight_id":"i3","supporting_replay_refs":["r3"],"supporting_transition_refs":["t3"],"supporting_diagnostic_refs":["d3"],"supporting_theme_refs":["th3"],"supporting_regime_refs":[],"supporting_confidence_refs":[],"supporting_continuity_refs":[],"evidence_count":4},
    ]
    deltas=[{"insight_id":"i1","delta_classification":"PERSISTENT_INSIGHT"},{"insight_id":"i2","delta_classification":"EMERGING_INSIGHT"},{"insight_id":"i3","delta_classification":"VOLATILE_INSIGHT"}]
    return ix1,ix2,deltas


def test_ix3_deterministic_pipeline_and_certification():
    ix1,ix2,deltas=_fixtures(); src=deepcopy((ix1,ix2,deltas))
    clusters=build_ix3_insight_cluster_inventory(ix1_insight_priority_ranking=ix1, ix2_insight_evidence_map=ix2, ix2_cross_run_delta_tracker=deltas)
    redundancy=build_ix3_redundancy_and_overlap_analysis(insight_cluster_inventory=clusters)
    narratives=build_ix3_compressed_structural_narratives(insight_cluster_inventory=clusters)
    themes=build_ix3_dominant_theme_summary(insight_cluster_inventory=clusters)
    ranking=build_ix3_cluster_priority_ranking(insight_cluster_inventory=clusters)
    brief=build_ix3_operator_narrative_brief(compressed_structural_narratives=narratives, insight_cluster_inventory=clusters, cluster_priority_ranking=ranking, redundancy_and_overlap_analysis=redundancy)
    dashboard=build_ix3_dashboard_payload(insight_cluster_inventory=clusters, redundancy_and_overlap_analysis=redundancy, compressed_structural_narratives=narratives, dominant_theme_summary=themes, cluster_priority_ranking=ranking, operator_narrative_brief=brief)
    cert=certify_ix3_structural_narrative_compression(dashboard_payload=dashboard)
    assert cert["status"] in {"CERTIFIED_STRUCTURAL_NARRATIVE_COMPRESSION","DEGRADED_STRUCTURAL_NARRATIVE_COMPRESSION"}
    assert dashboard["Explicit Non-Predictive Notice"] and dashboard["Explicit Non-Execution Notice"]
    assert ix1==src[0] and ix2==src[1] and deltas==src[2]
    assert all(set(n["supporting_evidence_refs"]).issubset({e for c in clusters for e in c["evidence_refs"]}) for n in narratives)
    text=" ".join((str(n.get("narrative_title",""))+" "+str(n.get("compressed_finding",""))).lower() for n in narratives)
    for forbidden in ("buy", "sell", "autonomous conclusion", "forecast"):
        assert forbidden not in text


def test_ix3_missing_partial_data_behavior():
    clusters=build_ix3_insight_cluster_inventory(ix1_insight_priority_ranking=[], ix2_insight_evidence_map=[], ix2_cross_run_delta_tracker=[])
    assert clusters==[]
