from copy import deepcopy

from transmission_layers.expectation_failure import path2a_cohort_registry_foundation as p2a
from transmission_layers.expectation_failure import path3a_structural_resilience_foundation as p3a
from transmission_layers.expectation_failure import path5a_structural_transmission_graph as p5a
from transmission_layers.expectation_failure.dashboard_operationalization import (
    build_o1_dashboard_view_model,
    build_o1_governance_boundary_summary,
    build_o1_layer_inventory,
    build_o1_operational_status,
    build_o1_operational_visibility_report,
    build_o1_replay_lineage_summary,
    certify_o1_operational_visibility,
)


def _ready_obs():
    return {lid: {"observed_status": "available", "checksum_present": True, "replay_metadata_present": True, "supervisor_closeout_present": True} for lid in ["path1","path2","path3","path5a","path5b","path5c","path5d","path5e"]}


def test_public_apis_presence_and_exports():
    assert callable(build_o1_layer_inventory)
    assert callable(build_o1_operational_status)
    assert callable(build_o1_replay_lineage_summary)
    assert callable(build_o1_governance_boundary_summary)
    assert callable(build_o1_dashboard_view_model)
    assert callable(certify_o1_operational_visibility)
    assert callable(build_o1_operational_visibility_report)


def test_deterministic_outputs_and_checksum_stability_and_ordering():
    obs = _ready_obs()
    a = build_o1_dashboard_view_model(obs)
    b = build_o1_dashboard_view_model(obs)
    assert a == b
    assert a["certification_summary"]["checksum"] == b["certification_summary"]["checksum"]
    assert [i["layer_id"] for i in a["layer_inventory"]] == ["path1", "path2", "path3", "path5a", "path5b", "path5c", "path5d", "path5e"]


def test_ready_degraded_blocked_paths_and_immutability():
    ready = build_o1_operational_status(build_o1_layer_inventory(_ready_obs()))
    assert ready["overall_status"] == "O1_OPERATIONAL_READY"

    degraded_obs = _ready_obs()
    degraded_obs["path5d"]["checksum_present"] = False
    degraded = build_o1_operational_status(build_o1_layer_inventory(degraded_obs))
    assert degraded["overall_status"] == "O1_OPERATIONAL_DEGRADED"

    blocked = build_o1_operational_status([])
    assert blocked["overall_status"] == "O1_OPERATIONAL_BLOCKED"

    orig = _ready_obs()
    clone = deepcopy(orig)
    build_o1_dashboard_view_model(orig)
    assert orig == clone


def test_lineage_governance_view_model_and_report_smoke():
    obs = _ready_obs()
    obs["path2"]["checksum_present"] = False
    lineage = build_o1_replay_lineage_summary(build_o1_layer_inventory(obs))
    assert "path2" in lineage["missing_checksum_layers"]

    gov = build_o1_governance_boundary_summary()
    assert "prediction" in gov["forbidden"]
    assert "trading recommendations" in gov["forbidden"]
    assert "portfolio optimization" in gov["forbidden"]

    vm = build_o1_dashboard_view_model(_ready_obs())
    for key in ["page_id", "page_title", "generated_at_policy", "operational_status", "layer_inventory", "replay_lineage", "governance_boundaries", "supervisor_cards", "alert_cards", "readiness_cards", "certification_summary"]:
        assert key in vm

    report = build_o1_operational_visibility_report(_ready_obs())
    assert report["final_supervisor_interpretation"]


def test_no_forbidden_language_in_outputs_and_non_regression_import_smoke():
    text = str(build_o1_operational_visibility_report(_ready_obs())).lower()
    assert "recommend buy" not in text
    assert "trade now" not in text
    assert "optimize portfolio" not in text

    assert callable(getattr(p2a, "build_path2a_cohort_registry_report"))
    assert callable(getattr(p3a, "run_p3a_structural_resilience_foundation"))
    assert callable(getattr(p5a, "run_path5a_structural_transmission_graph"))
