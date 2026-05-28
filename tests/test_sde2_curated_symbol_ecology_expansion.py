from __future__ import annotations

import hashlib
import json

from transmission_layers.expectation_failure.real_data.sde2_curated_symbol_ecology_expansion import (
    build_sde2_artifacts,
    get_sde2_curated_symbol_universe,
    get_sde2_diversity_metrics,
    get_sde2_symbol_categories,
    get_sde2_symbol_validation_metadata,
    validate_sde2_constraints,
)


def test_universe_size_and_required_category_coverage():
    symbols = get_sde2_curated_symbol_universe()
    categories = get_sde2_symbol_categories()
    assert 150 <= len(symbols) <= 300
    assert len(categories) >= 20


def test_deterministic_output_and_metrics():
    h1 = hashlib.sha256(json.dumps(get_sde2_curated_symbol_universe()).encode()).hexdigest()
    h2 = hashlib.sha256(json.dumps(get_sde2_curated_symbol_universe()).encode()).hexdigest()
    assert h1 == h2
    assert get_sde2_diversity_metrics() == get_sde2_diversity_metrics()


def test_duplicate_symbol_handling_and_primary_category_assignment():
    symbols = get_sde2_curated_symbol_universe()
    metadata = get_sde2_symbol_validation_metadata()
    assert "GOOG" not in symbols
    assert "GOOGL" in symbols
    assert len(symbols) == len(set(symbols))
    assert metadata["GLD"]["category_overlap_count"] >= 2
    assert metadata["GLD"]["primary_category"] == "commodities"
    assert "volatility_defensive_assets" in metadata["GLD"]["secondary_categories"]


def test_anti_monoculture_constraints_and_high_risk_reporting():
    checks = validate_sde2_constraints()
    assert checks["passes"] is True
    assert checks["max_sector_concentration_ratio"] <= 0.42
    assert checks["minimum_category_diversity_count"] >= 20
    assert checks["minimum_contradiction_diversity_ratio"] >= 0.03
    assert {"FANUY", "RBT", "SENT"}.issubset(set(checks["high_risk_tickers"]))


def test_artifacts_bounded_and_governance_and_metadata(tmp_path):
    out = build_sde2_artifacts(output_root=str(tmp_path / "sde2"))
    payload = json.loads(open(out["json_path"], encoding="utf-8").read())
    assert payload["governance_certification"]["observational_only_semantics"] is True
    assert payload["governance_certification"]["no_prediction_or_trading_logic"] is True
    assert "bounded_exclusion_replacement_list" in payload
    assert "symbol_validation_metadata" in payload
    assert payload["symbol_validation_metadata"]["FANUY"]["fmp_availability_risk"] == "high"
    assert len(open(out["json_path"], encoding="utf-8").read()) < 250_000
    assert len(open(out["md_path"], encoding="utf-8").read()) < 40_000


def test_cflt_replaced_with_ddog_and_count_stable():
    symbols = get_sde2_curated_symbol_universe()
    categories = get_sde2_symbol_categories()
    assert "CFLT" not in symbols
    assert "DDOG" in symbols
    assert "AKAM" in symbols
    assert len(categories["cloud_software_infrastructure"]) == 18


def test_para_replaced_with_wbd_first_preference_fallback_to_foxa():
    symbols = get_sde2_curated_symbol_universe()
    categories = get_sde2_symbol_categories()
    communication = categories["communication_platforms"]
    assert "WBD" in symbols
    assert "PARA" not in symbols
    assert "FOXA" in symbols
    assert communication[communication.index("FOXA")] == "FOXA"
    assert symbols.count("FOXA") == 1
    assert len(symbols) == len(set(symbols))

