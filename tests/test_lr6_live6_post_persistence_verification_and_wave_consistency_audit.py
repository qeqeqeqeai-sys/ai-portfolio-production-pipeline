from transmission_layers.expectation_failure.replay_ecology.lr6_live6_post_persistence_verification_and_wave_consistency_audit import *


def _rows():
    rows = []
    for i in range(1, 6):
        rows.append(
            {
                "created_at": f"2026-05-25T00:00:0{i}Z",
                "wave_id": "LR6_LIVE5_WAVE_1FB274FE8C0A" if i % 2 else "LR6_LIVE5_WAVE_62418FB64AB0",
                "entity_id": f"LIVE5_E{i}",
                "metric_target": "replay_richness",
                "metric_dimension": "replay_richness",
                "duplicate_prevention_key": f"LR6_LIVE5_WAVE_001|LIVE5_E{i}|replay_richness|W0",
                "payload": {"entity_id": f"LIVE5_E{i}"},
                "source_artifact_refs": [f"artifact://lr6/live5/LIVE5_E{i}"],
                "lineage_metadata": {"source_artifact_refs": [f"artifact://lr6/live5/LIVE5_E{i}"]},
                "rollback_metadata": {"rollback_ready": True},
                "evidence_status": "MEASURED",
                "comparison_ready": False,
                "scaffold_only": False,
                "richness_score": 0.2 * i,
                "diversity_ratio": 0.1 * i,
                "concentration_warning": False,
                "adapter_name": "replay_richness_wave0_shadow_append_only_adapter",
                "execution_mode": "append_only_insert",
            }
        )
    return rows


def test_apis_exist():
    required = [
        build_lr6_live6_audit_context,
        build_lr6_live6_persistence_verification,
        build_lr6_live6_duplicate_prevention_review,
        build_lr6_live6_wave_consistency_audit,
        build_lr6_live6_lineage_rollback_review,
        build_lr6_live6_readback_review,
        build_lr6_live6_append_only_audit,
        build_lr6_live6_boundary_review,
        build_lr6_live6_supervisor_review,
        build_lr6_live6_markdown_report,
        certify_lr6_live6_audit_boundary,
    ]
    assert all(callable(f) for f in required)


def test_persistence_duplicate_wave_lineage_append_only_boundary():
    context = build_lr6_live6_audit_context(persisted_rows=_rows())
    p = build_lr6_live6_persistence_verification(context)
    assert p["rows_exist"] is True and p["row_count"] == 5 and p["created_at_iso_parseable"] is True
    d = build_lr6_live6_duplicate_prevention_review(context)
    assert d["keys_unique"] is True and d["simulated_rerun_duplicate_blocked"] is True
    w = build_lr6_live6_wave_consistency_audit(context)
    assert w["semantics_classification"] == "row_level_fallback_wave_id"
    assert w["normalization_required_before_live7"] is True
    l = build_lr6_live6_lineage_rollback_review(context)
    assert l["lineage_metadata_present"] is True and l["rollback_metadata_present"] is True
    a = build_lr6_live6_append_only_audit(context)
    assert a["append_only_semantics_preserved"] is True and a["direct_sql_used"] is False
    b = build_lr6_live6_boundary_review(context)
    assert b["scaling_enabled"] is False and b["topology_metrics_persisted"] is False


def test_report_sections_and_boundary_flags_exact():
    review = build_lr6_live6_supervisor_review(persisted_rows=_rows())
    report = build_lr6_live6_markdown_report(review)
    for s in [
        "## audit summary",
        "## duplicate prevention findings",
        "## wave consistency findings",
        "## lineage/rollback findings",
        "## readback findings",
        "## append-only verification findings",
        "## governance/boundary findings",
        "## recommendation for LIVE7 or remediation phase",
        "## boundary certification",
    ]:
        assert s in report
    assert certify_lr6_live6_audit_boundary() == {
        "verification_audit_only": True,
        "scaling_authorized": False,
        "new_metrics_enabled": False,
        "topology_drift_enabled": False,
        "contradiction_persistence_migration_enabled": False,
        "prediction_enabled": False,
        "trading_enabled": False,
        "schema_expansion_enabled": False,
        "direct_sql_bypass_enabled": False,
        "append_only_required": True,
        "replay_richness_only": True,
        "max_5_bounded": True,
    }
