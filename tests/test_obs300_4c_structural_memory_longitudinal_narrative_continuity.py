from transmission_layers.expectation_failure.obs300_4c_structural_memory_longitudinal_narrative_continuity import (
    build_obs300_4c_structural_memory_longitudinal_narrative_continuity,
)


def _payload() -> dict[str, object]:
    families = ["contradiction", "resilience", "fragmentation", "transition", "recovery", "pressure"]
    payload: dict[str, object] = {}
    for i, family in enumerate(families):
        base = 52 + (i * 6)
        payload[f"{family}_recurrence"] = base
        payload[f"{family}_lineage_depth"] = base + 2
        payload[f"{family}_pathway_stability"] = base - 1
        payload[f"{family}_narrative_alignment"] = base + 1
        payload[f"{family}_normalization_continuity"] = base - 3
        payload[f"{family}_topology_continuity"] = base
        payload[f"{family}_persistence"] = base + 4
        payload[f"{family}_bridge_reuse"] = base + 2
        payload[f"{family}_fragmentation_pressure"] = 40 + i * 5
        payload[f"{family}_contradiction_recurrence"] = 48 + i * 4
    return payload


def test_obs300_4c_deterministic_outputs_and_core_surfaces():
    first = build_obs300_4c_structural_memory_longitudinal_narrative_continuity(_payload())
    second = build_obs300_4c_structural_memory_longitudinal_narrative_continuity(_payload())

    assert first == second
    assert first["module"] == "OBS300-4C"
    assert "structural_memory_layer" in first
    assert "ecosystem_lineage_observation" in first
    assert "narrative_continuity_observation" in first
    assert "structural_memory_compression" in first
    assert "operator_facing_visualization_payloads" in first


def test_obs300_4c_bounded_payload_and_classification_stability():
    result = build_obs300_4c_structural_memory_longitudinal_narrative_continuity(_payload())

    rows = result["structural_memory_layer"]["tracked_structures"]
    assert len(rows) == 6
    for row in rows:
        assert 0 <= row["continuity_score"] <= 100
        assert 0 <= row["narrative_continuity_score"] <= 100

    lineage = result["structural_memory_compression"]["compressed_lineage_summaries"]
    assert len(lineage) <= 6

    classes = set(result["ecosystem_continuity_classification"].values())
    assert classes.issubset(
        {
            "transient",
            "recurring",
            "persistent",
            "entrenched",
            "stabilizing",
            "re-cohering",
            "decompression_continuing",
            "fragmentation_persistent",
        }
    )


def test_obs300_4c_governance_boundaries_and_no_autonomous_behaviors():
    result = build_obs300_4c_structural_memory_longitudinal_narrative_continuity(_payload())

    assert result["governance_certification"] == {
        "observational_only": True,
        "no_recursive_replay_operationalization": True,
        "no_autonomous_replay": True,
        "no_topology_activation": True,
        "no_self_modifying_pathways": True,
        "no_prediction_or_trading_execution": True,
        "no_sql_write_introduction": True,
    }

    arch = result["structural_memory_architecture_summary"]
    assert arch["graph_execution_engine_required"] is False
    assert arch["sql_write_required"] is False


def test_obs300_4c_lineage_and_continuity_scoring_stability():
    result = build_obs300_4c_structural_memory_longitudinal_narrative_continuity(_payload())

    lineage = result["ecosystem_lineage_observation"]["ecosystem_lineage_summaries"]
    assert lineage == sorted(lineage, key=lambda r: -r["continuity_score"])

    continuity_scores = result["narrative_continuity_observation"]["narrative_continuity_scoring"]
    topology_scores = result["narrative_continuity_observation"]["topology_continuity_scoring"]
    assert continuity_scores.keys() == topology_scores.keys()
