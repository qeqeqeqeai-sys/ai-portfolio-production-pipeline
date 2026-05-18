import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from transmission_layers.asset_discovery.tier3h5.canonical_registry_ids import generate_issuer_id, generate_security_id


def test_deterministic_id_stability() -> None:
    issuer_id_1 = generate_issuer_id("EXAMPLE HOLDINGS INC", "0001234567")
    issuer_id_2 = generate_issuer_id("EXAMPLE HOLDINGS INC", "0001234567")
    assert issuer_id_1 == issuer_id_2

    security_id_1 = generate_security_id("NASDAQ", "EXM", "common_stock")
    security_id_2 = generate_security_id("NASDAQ", "EXM", "common_stock")
    assert security_id_1 == security_id_2
