from transmission_layers.expectation_failure.replay_ecology.curated_stock_universe import (
    build_curated_300_stock_ecosystem_summary,
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


def test_unique_and_required_fields():
    rows = load_curated_300_stock_universe()
    assert validate_unique_tickers(rows)
    assert validate_required_fields(rows)


def test_diversity_and_anti_monoculture():
    rows = load_curated_300_stock_universe()
    assert validate_sector_diversity(rows, min_sectors=8)
    assert validate_semantic_cluster_diversity(rows, min_clusters=10)
    assert validate_anti_monoculture_distribution(rows, max_cluster_share=0.20)


def test_no_prediction_fields_and_no_external_dependency_for_fmp_validation():
    rows = load_curated_300_stock_universe()
    assert validate_no_prediction_fields(rows)
    assert validate_fmp_symbol_coverage(rows)


def test_summary_is_deterministic_and_guardrails_explicit():
    rows = load_curated_300_stock_universe()
    s1 = build_curated_300_stock_ecosystem_summary(rows)
    s2 = build_curated_300_stock_ecosystem_summary(rows)
    assert s1 == s2
    assert s1["experimental_observation_substrate_only"] is True
    assert s1["prediction_or_trading_logic_introduced"] is False
    assert s1["governed_lr6_activation_performed"] is False
