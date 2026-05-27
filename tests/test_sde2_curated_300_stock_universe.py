from transmission_layers.expectation_failure.replay_ecology.curated_stock_universe import (
    build_curated_300_stock_ecosystem_summary,
    build_topology_diversity_scaffolding,
    compute_diversification_controls,
    load_curated_300_stock_universe,
    validate_anti_monoculture_distribution,
    validate_curated_300_stock_count,
    validate_fmp_symbol_coverage,
    validate_no_prediction_fields,
    validate_required_fields,
    validate_sector_diversity,
    validate_semantic_cluster_diversity,
    validate_unique_tickers,
)


def test_curated_300_stock_count_and_deterministic_ordering():
    r1 = load_curated_300_stock_universe()
    r2 = load_curated_300_stock_universe()
    assert validate_curated_300_stock_count(r1)
    assert [r["ticker"] for r in r1] == [r["ticker"] for r in r2]


def test_required_fields_and_diversity():
    rows = load_curated_300_stock_universe()
    assert validate_unique_tickers(rows)
    assert validate_required_fields(rows)
    assert validate_sector_diversity(rows, min_sectors=8)
    assert validate_semantic_cluster_diversity(rows, min_clusters=10)
    assert validate_anti_monoculture_distribution(rows, max_cluster_share=0.20)


def test_diversification_controls_and_stability():
    rows = load_curated_300_stock_universe()
    c1 = compute_diversification_controls(rows)
    c2 = compute_diversification_controls(rows)
    assert c1 == c2
    assert "Technology" in c1["sector_cap_breaches"]
    relaxed = compute_diversification_controls(rows, sector_cap=0.30, theme_cap=0.40)
    assert relaxed["sector_cap_breaches"] == []
    assert relaxed["theme_cap_breaches"] == []
    assert 0 <= c1["anti_monoculture_score"] <= 1
    assert c1["ecosystem_entropy_score"] > 0


def test_topology_scaffolding_and_summary_governance_certification():
    rows = load_curated_300_stock_universe()
    topo = build_topology_diversity_scaffolding(rows)
    s1 = build_curated_300_stock_ecosystem_summary(rows)
    s2 = build_curated_300_stock_ecosystem_summary(rows)
    assert s1 == s2
    assert topo["adjacency_diversity_summary"]["unique_topology_clusters"] >= 10
    assert s1["observational_only"] is True
    assert s1["no_recursive_replay_operationalization"] is True
    assert s1["no_autonomous_replay"] is True
    assert s1["no_topology_activation"] is True
    assert s1["no_self_modifying_pathways"] is True
    assert s1["no_prediction_or_trading_execution"] is True


def test_no_prediction_fields_and_no_sql_write_introduction():
    rows = load_curated_300_stock_universe()
    assert validate_no_prediction_fields(rows)
    assert validate_fmp_symbol_coverage(rows)
    module_text = open(
        "transmission_layers/expectation_failure/replay_ecology/curated_stock_universe.py",
        encoding="utf-8",
    ).read().lower()
    assert "insert into" not in module_text
    assert "update " not in module_text
    assert "delete from" not in module_text
    assert "autonomous" not in module_text or "no_autonomous_replay" in module_text
