"""Tier 3I intelligence layer package.

This package intentionally avoids eager submodule imports so that CLI-capable
modules can be executed with ``python -m`` without triggering ``runpy``
RuntimeWarning messages about preloaded modules.
"""

from importlib import import_module
from typing import Any

__all__ = [
    "EDGE_QUALITY_SCORING_VERSION",
    "STRUCTURAL_INFLUENCE_SCORING_VERSION",
    "score_edge_quality",
    "score_edges",
    "score_structural_influence",
    "INTELLIGENCE_SUMMARY_SCORING_VERSION",
    "build_intelligence_summary",
    "PATH_EXPLAINABILITY_SCORING_VERSION",
    "explain_paths",
    "STRUCTURAL_REGIME_SCORING_VERSION",
    "compute_structural_regime",
    "REGIME_DRIFT_SCORING_VERSION",
    "compute_regime_drift",
    "CONTAGION_MAPPING_SCORING_VERSION",
    "map_structural_contagion",
    "HISTORICAL_REPLAY_SCORING_VERSION",
    "build_historical_structural_replay",
]

_EXPORT_TO_MODULE = {
    "EDGE_QUALITY_SCORING_VERSION": "edge_quality",
    "score_edge_quality": "edge_quality",
    "score_edges": "edge_quality",
    "STRUCTURAL_INFLUENCE_SCORING_VERSION": "structural_influence",
    "score_structural_influence": "structural_influence",
    "INTELLIGENCE_SUMMARY_SCORING_VERSION": "intelligence_summary",
    "build_intelligence_summary": "intelligence_summary",
    "PATH_EXPLAINABILITY_SCORING_VERSION": "path_explainability",
    "explain_paths": "path_explainability",
    "STRUCTURAL_REGIME_SCORING_VERSION": "structural_regime",
    "compute_structural_regime": "structural_regime",
    "REGIME_DRIFT_SCORING_VERSION": "regime_drift",
    "compute_regime_drift": "regime_drift",
    "CONTAGION_MAPPING_SCORING_VERSION": "contagion_mapping",
    "map_structural_contagion": "contagion_mapping",
    "HISTORICAL_REPLAY_SCORING_VERSION": "historical_replay",
    "build_historical_structural_replay": "historical_replay",
}


def __getattr__(name: str) -> Any:
    """Lazily expose Tier 3I public symbols from their owning submodules."""
    module_name = _EXPORT_TO_MODULE.get(name)
    if module_name is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    module = import_module(f".{module_name}", __name__)
    value = getattr(module, name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    """Return dynamic module attributes for developer ergonomics."""
    return sorted(list(globals().keys()) + __all__)
