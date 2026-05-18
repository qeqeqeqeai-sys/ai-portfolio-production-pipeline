import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import json

from transmission_layers.asset_discovery.tier3h5.canonical_registry_resolution import (
    resolve_security_from_registry,
    summarize_registry_resolution,
)
from transmission_layers.asset_discovery.tier3h5.canonical_registry_resolution_observability import write_registry_resolution_summary


REGISTRY_FIXTURE = [
    {
        "security_id": "sec_nasdaq_exm_common",
        "issuer_id": "issuer_1",
        "ticker": "EXM",
        "exchange": "NASDAQ",
        "security_type": "common_stock",
        "is_active": True,
        "source_name": "fixture_us_listings",
    },
    {
        "security_id": "sec_nyse_exm_preferred",
        "issuer_id": "issuer_1",
        "ticker": "EXM",
        "exchange": "NYSE",
        "security_type": "preferred_stock",
        "is_active": True,
        "source_name": "fixture_cross_listing",
    },
]


def test_exact_ticker_exchange_match() -> None:
    result = resolve_security_from_registry(" exm ", " nasdaq ", REGISTRY_FIXTURE)
    assert result.resolution_status == "accepted"
    assert result.match_rule == "exact_exchange_ticker"


def test_no_match() -> None:
    result = resolve_security_from_registry("NOPE", "NASDAQ", REGISTRY_FIXTURE)
    assert result.resolution_status == "no_match"
    assert result.match_rule == "no_match"


def test_missing_ticker_invalid_input() -> None:
    result = resolve_security_from_registry("", "NASDAQ", REGISTRY_FIXTURE)
    assert result.resolution_status == "invalid_input"


def test_missing_exchange_invalid_input() -> None:
    result = resolve_security_from_registry("EXM", "", REGISTRY_FIXTURE)
    assert result.resolution_status == "invalid_input"


def test_multiple_match_conflict() -> None:
    duplicated = REGISTRY_FIXTURE + [dict(REGISTRY_FIXTURE[0], security_id="sec_nasdaq_exm_common_2")]
    result = resolve_security_from_registry("EXM", "NASDAQ", duplicated)
    assert result.resolution_status == "conflict"
    assert result.match_rule == "multiple_registry_matches"


def test_security_type_narrowing() -> None:
    duplicated = REGISTRY_FIXTURE + [
        {
            "security_id": "sec_nasdaq_exm_preferred",
            "issuer_id": "issuer_1",
            "ticker": "EXM",
            "exchange": "NASDAQ",
            "security_type": "preferred_stock",
            "is_active": True,
            "source_name": "fixture_cross_listing",
        }
    ]
    result = resolve_security_from_registry("EXM", "NASDAQ", duplicated, security_type="preferred_stock")
    assert result.resolution_status == "accepted"
    assert result.match_rule == "exact_exchange_ticker_security_type"


def test_deterministic_explanation_text() -> None:
    first = resolve_security_from_registry("EXM", "NASDAQ", REGISTRY_FIXTURE)
    second = resolve_security_from_registry("EXM", "NASDAQ", REGISTRY_FIXTURE)
    assert first.explanation == second.explanation


def test_summary_json_generation(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    results = [
        resolve_security_from_registry("EXM", "NASDAQ", REGISTRY_FIXTURE),
        resolve_security_from_registry("NOPE", "NASDAQ", REGISTRY_FIXTURE),
        resolve_security_from_registry("", "NASDAQ", REGISTRY_FIXTURE),
    ]
    summary = summarize_registry_resolution(results)
    write_registry_resolution_summary(summary)
    payload = json.loads(Path("logs/tier3h5_registry_resolution_summary.json").read_text(encoding="utf-8"))
    assert payload["registry_resolution_attempts"] == 3
    assert payload["status"] in {"success", "completed_with_findings"}
