from pathlib import Path

from transmission_layers.expectation_failure import replay_ecology as mod


def _full_payload():
    return {
        "metrics": {
            "weak_signal_attribution": {
                "weak_signal_attribution_count": 2,
                "weak_signal_candidate_count": 10,
                "weak_signal_attribution_ratio": 0.2,
                "weak_signal_entities_observed": ["A"],
                "weak_signal_entities_missing": ["B"],
            },
            "contradiction_persistence_migration": {
                "contradiction_cluster_count": 3,
                "persistent_contradiction_count": 1,
                "migrated_contradiction_count": 1,
                "cross_cluster_contradiction_count": 1,
                "contradiction_persistence_ratio": 0.33,
            },
            "propagation_diversity": {
                "propagation_bridge_count": 4,
                "distinct_propagation_role_count": 3,
                "non_obvious_bridge_count": 2,
                "cross_cluster_bridge_count": 1,
                "propagation_diversity_score": 0.8,
            },
            "topology_drift": {
                "topology_drift_indicator": True,
                "new_bridge_count": 1,
                "disappeared_bridge_count": 0,
                "changed_bridge_count": 1,
                "topology_drift_score": 0.5,
            },
            "replay_saturation_monoculture": {
                "saturation_score": 0.4,
                "concentration_score": 0.6,
                "dominant_theme_share": 0.7,
                "repeated_entity_share": 0.5,
                "diversity_gain_indicator": True,
            },
            "megacap_semantic_gravity": {
                "megacap_attribution_count": 3,
                "total_attribution_count": 8,
                "megacap_concentration_ratio": 0.375,
                "non_megacap_bridge_count": 2,
                "megacap_gravity_status": "balanced",
            },
            "replay_richness": {
                "replay_entity_count": 14,
                "distinct_role_count": 5,
                "distinct_cluster_count": 4,
                "novel_bridge_count": 3,
                "richness_score": 0.9,
            },
        }
    }


def _emit(payload, replay_phase="BASELINE", wave_id="W1", scope_id="S1", candidate_count=10, stamp="T1"):
    return mod.emit_lr6_replay_metric_evidence(
        replay_phase=replay_phase,
        wave_id=wave_id,
        candidate_scope_id=scope_id,
        candidate_count=candidate_count,
        timestamp_or_snapshot_label=stamp,
        replay_observation_payload=payload,
    )


def test_public_apis_exist():
    for name in [
        "emit_lr6_replay_metric_evidence",
        "build_lr6_evid6_hook_context",
        "build_lr6_evid6_supported_metric_dimensions",
        "build_lr6_evid6_required_field_contract",
        "validate_lr6_evid6_metric_payload",
        "build_lr6_evid6_emission_quality_summary",
        "build_lr6_evid6_evid3_compatibility_summary",
        "build_lr6_evid6_supervisor_review",
        "build_lr6_evid6_markdown_report",
        "certify_lr6_evid6_hook_boundary",
    ]:
        assert hasattr(mod, name)


def test_deterministic_and_seven_records():
    one = _emit(_full_payload())
    two = _emit(_full_payload())
    assert one == two
    assert len(one) == 7


def test_measured_partial_missing_scaffold_not_comparable_statuses():
    measured = _emit(_full_payload())
    assert all(r["evidence_status"] == "MEASURED" for r in measured)

    partial_payload = _full_payload()
    partial_payload["metrics"]["weak_signal_attribution"] = {"weak_signal_attribution_count": 1}
    partial_rec = [r for r in _emit(partial_payload) if r["metric_dimension"] == "weak_signal_attribution"][0]
    assert partial_rec["evidence_status"] == "PARTIAL"

    missing = _emit({})
    assert all(r["evidence_status"] == "MISSING" for r in missing)

    scaffold = _emit({"governance_review": {"approved": False}})
    assert all(r["evidence_status"] == "SCAFFOLD_ONLY" for r in scaffold)
    assert all(r["comparison_ready"] is False for r in scaffold)

    not_comparable = _emit(_full_payload(), replay_phase="RUN1_REVIEW")
    assert all(r["evidence_status"] == "NOT_COMPARABLE" for r in not_comparable)


def test_comparison_ready_and_invalid_fields_safety_and_evid3_keys():
    records = _emit(_full_payload(), replay_phase="ENRICHED")
    assert all(r["comparison_ready"] is True for r in records)

    blocked = _emit(_full_payload(), wave_id="")
    assert all(r["comparison_ready"] is False for r in blocked)

    invalid_payload = _full_payload()
    invalid_payload["metrics"]["weak_signal_attribution"]["weak_signal_attribution_count"] = -1
    rec = [r for r in _emit(invalid_payload) if r["metric_dimension"] == "weak_signal_attribution"][0]
    assert rec["evidence_status"] == "PARTIAL"
    assert "weak_signal_attribution_count" not in rec["measured_fields"]

    for key in [
        "evidence_record_id", "replay_phase", "wave_id", "candidate_scope_id", "candidate_count",
        "timestamp_or_snapshot_label", "metric_dimension", "measured_fields", "evidence_status",
        "source_artifact", "source_module", "comparison_ready", "scaffold_only", "notes"
    ]:
        assert key in records[0]


def test_boundary_report_and_no_execution_sql_persistence_prediction_trading_paths():
    boundary = mod.certify_lr6_evid6_hook_boundary()
    assert boundary["hook_only"] is True
    assert boundary["in_memory_only"] is True
    assert boundary["evidence_only"] is True
    assert boundary["execution_authorized"] is False
    assert boundary["no_prediction"] is True
    assert boundary["no_trading"] is True
    assert boundary["no_direct_sql"] is True
    assert boundary["no_live_ingestion"] is True
    assert boundary["no_persistence_write"] is True
    assert boundary["no_governed_activation"] is True
    assert boundary["no_interpretation_claims"] is True

    report = mod.build_lr6_evid6_markdown_report()
    for section in [
        "## objective",
        "## EVID5 basis",
        "## hook signature",
        "## supported metric dimensions",
        "## required field contract",
        "## extraction rules",
        "## status rules",
        "## validation rules",
        "## scaffold detection",
        "## EVID3 compatibility",
        "## boundary certification",
        "## recommendation for next step",
    ]:
        assert section in report

    file_report = Path("reports/lr6_evid6_minimal_in_memory_metrics_emission_hook.md").read_text(encoding="utf-8")
    assert "## objective" in file_report
