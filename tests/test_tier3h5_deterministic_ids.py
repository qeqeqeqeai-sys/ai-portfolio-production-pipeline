import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from transmission_layers.asset_discovery.tier3h5.canonical_registry_ids import generate_issuer_id, generate_security_id


def test_issuer_id_stability() -> None:
    a = generate_issuer_id("EXAMPLE HOLDINGS INC", "0001234567")
    b = generate_issuer_id("EXAMPLE HOLDINGS INC", "0001234567")
    assert a == b


def test_security_id_stability() -> None:
    a = generate_security_id("NASDAQ", "EXM", "common_stock")
    b = generate_security_id("NASDAQ", "EXM", "common_stock")
    assert a == b
