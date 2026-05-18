import copy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from transmission_layers.asset_discovery.tier3h5.advisory_registry_hooks import run_advisory_registry_lookup


REGISTRY = [
    {"security_id": "sec_aapl_eq", "issuer_id": "iss_aapl", "ticker": "AAPL", "exchange": "NASDAQ", "security_type": "equity", "is_active": True},
    {"security_id": "sec_aapl_adr", "issuer_id": "iss_aapl", "ticker": "AAPL", "exchange": "NASDAQ", "security_type": "adr", "is_active": True},
]


def test_advisory_hook_disabled_noop() -> None:
    out = run_advisory_registry_lookup([{"ticker": "AAPL", "exchange": "NASDAQ"}], REGISTRY, enabled=False)
    assert out["advisory_registry_enabled"] is False
    assert out["registry_lookup_attempts"] == 0


def test_advisory_exact_match_and_no_mutation() -> None:
    candidates = [{"ticker": "AAPL", "exchange": "NASDAQ", "security_type": "equity"}]
    before = copy.deepcopy(candidates)
    out = run_advisory_registry_lookup(candidates, REGISTRY, enabled=True)
    assert out["registry_exact_matches"] == 1
    assert out["registry_conflicts"] == 0
    assert candidates == before


def test_advisory_no_match_conflict_invalid() -> None:
    out = run_advisory_registry_lookup(
        [
            {"ticker": "NONE", "exchange": "NASDAQ"},
            {"ticker": "AAPL", "exchange": "NASDAQ"},
            {"ticker": "", "exchange": "NASDAQ"},
        ],
        REGISTRY,
        enabled=True,
    )
    assert out["registry_no_match"] == 1
    assert out["registry_conflicts"] == 1
    assert out["registry_invalid_input"] == 1


def test_replay_stability() -> None:
    candidates = [{"ticker": "AAPL", "exchange": "NASDAQ", "security_type": "equity"}]
    a = run_advisory_registry_lookup(candidates, REGISTRY, enabled=True)
    b = run_advisory_registry_lookup(candidates, REGISTRY, enabled=True)
    assert a == b
