from __future__ import annotations

from importlib import import_module
from typing import Any

from .federation_determinism import stable_checksum


def collect_tier5_export_inventory() -> dict[str, Any]:
    module = import_module("transmission_layers.intelligence.tier5")
    exports = sorted(str(v) for v in getattr(module, "__all__", []))
    sort_helpers = sorted(name for name in exports if name.startswith("build_") and name.endswith("_sort_key"))
    score = 1.0 if sort_helpers else 0.0
    return {
        "tier5_public_exports": exports,
        "tier5_ranking_helpers": sort_helpers,
        "federation_export_contract_score": score,
        "federation_export_contracts_checksum": stable_checksum({"exports": exports, "helpers": sort_helpers, "score": score}, prefix="tier5h_exports"),
    }
