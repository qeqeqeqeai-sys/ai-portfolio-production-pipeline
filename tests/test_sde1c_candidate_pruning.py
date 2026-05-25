from pathlib import Path

from transmission_layers.expectation_failure.semantic_ecosystem.sde1c_candidate_pruning import (
    build_sde1_candidate_scorecard,
    build_sde1c_pruning_report_payload,
    load_sde1_candidate_universe,
    prune_sde1_candidate_universe,
    rank_sde1_candidates,
)

CONFIG = Path("configs/sde1_curated_entity_ecosystems.yaml")


def _loaded():
    return load_sde1_candidate_universe(CONFIG)


def test_scoring_determinism():
    data = _loaded()
    candidate = data["candidates"][0]
    s1 = build_sde1_candidate_scorecard(candidate, data["ecosystems"])
    s2 = build_sde1_candidate_scorecard(candidate, data["ecosystems"])
    assert s1 == s2


def test_ranking_determinism():
    data = _loaded()
    r1 = rank_sde1_candidates(data["candidates"], data["ecosystems"])
    r2 = rank_sde1_candidates(data["candidates"], data["ecosystems"])
    assert [x["candidate"]["entity_id"] for x in r1] == [x["candidate"]["entity_id"] for x in r2]


def test_pruning_target_count_and_ecosystem_representation():
    data = _loaded()
    result = prune_sde1_candidate_universe(data["candidates"], data["ecosystems"], target_count=300)
    assert len(result["selected"]) == 300
    primary = {r["candidate"]["primary_ecosystem"] for r in result["selected"]}
    assert primary == set(data["ecosystems"].keys())


def test_anti_monoculture_cap_preserved():
    data = _loaded()
    result = prune_sde1_candidate_universe(data["candidates"], data["ecosystems"], target_count=300)
    counts = {}
    for row in result["selected"]:
        eco = row["candidate"]["primary_ecosystem"]
        counts[eco] = counts.get(eco, 0) + 1
    assert max(counts.values()) <= result["per_family_cap"]
    assert counts.get("ai_compute_core", 0) + counts.get("hyperscaler_cloud_demand", 0) <= result["ai_hyperscaler_combined_cap"]


def test_low_information_penalized_and_richer_propagation_ranked_higher():
    data = _loaded()
    ranked = rank_sde1_candidates(data["candidates"], data["ecosystems"])
    info = [r for r in ranked if r["scorecard"]["information_quality_score"] < 0.60]
    strong = [r for r in ranked if r["scorecard"]["propagation_link_score"] > 0.6 and r["scorecard"]["contradiction_surface_score"] > 0.6]
    weak = [r for r in ranked if r["scorecard"]["information_quality_score"] < 0.60]
    assert all(r["scorecard"]["low_information_penalty"] > 0 for r in info)
    assert strong and weak
    assert max(r["scorecard"]["total_score"] for r in strong) > max(r["scorecard"]["total_score"] for r in weak)


def test_tie_breakers_are_deterministic():
    data = _loaded()
    ranked = rank_sde1_candidates(data["candidates"], data["ecosystems"])
    for prev, cur in zip(ranked, ranked[1:]):
        if prev["scorecard"]["total_score"] == cur["scorecard"]["total_score"]:
            assert prev["candidate"]["entity_id"] < cur["candidate"]["entity_id"]


def test_no_sql_replay_or_persistence_paths_introduced_in_artifacts():
    payload = build_sde1c_pruning_report_payload(CONFIG)
    text = str(payload).lower() + "\n" + Path("transmission_layers/expectation_failure/semantic_ecosystem/sde1c_candidate_pruning.py").read_text().lower()

    allowed_governance_markers = {
        "no_replay_execution_introduced",
        "no_persistence_write_path_introduced",
    }
    for marker in allowed_governance_markers:
        assert marker in text

    banned_patterns = [
        "execute_replay",
        "run_replay",
        "persist_",
        "write_",
        "insert_into",
        "supabase.table",
        "rpc(",
        "sql(",
        "create table",
        "drop table",
        "trading_signal",
        "buy_signal",
        "sell_signal",
    ]

    for pattern in banned_patterns:
        if pattern in {"persist_", "write_"}:
            sanitized = text
            for marker in allowed_governance_markers:
                sanitized = sanitized.replace(marker, "")
            assert pattern not in sanitized
        else:
            assert pattern not in text


def test_additive_architecture_preserved():
    assert Path("transmission_layers/expectation_failure/semantic_ecosystem/sde1c_candidate_pruning.py").exists()
    assert Path("configs/sde1c_pruned_entity_universe.yaml").exists()
    assert Path("reports/sde1c_candidate_pruning_topology_quality_report.md").exists()
