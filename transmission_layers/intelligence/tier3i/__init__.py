"""Tier 3I intelligence layer package."""

from .edge_quality import SCORING_VERSION as EDGE_QUALITY_SCORING_VERSION, score_edge_quality, score_edges
from .structural_influence import SCORING_VERSION as STRUCTURAL_INFLUENCE_SCORING_VERSION, score_structural_influence
from .intelligence_summary import SCORING_VERSION as INTELLIGENCE_SUMMARY_SCORING_VERSION, build_intelligence_summary
from .path_explainability import SCORING_VERSION as PATH_EXPLAINABILITY_SCORING_VERSION, explain_paths
from .structural_regime import SCORING_VERSION as STRUCTURAL_REGIME_SCORING_VERSION, compute_structural_regime
from .regime_drift import SCORING_VERSION as REGIME_DRIFT_SCORING_VERSION, compute_regime_drift
from .contagion_mapping import SCORING_VERSION as CONTAGION_MAPPING_SCORING_VERSION, map_structural_contagion
from .historical_replay import SCORING_VERSION as HISTORICAL_REPLAY_SCORING_VERSION, build_historical_structural_replay

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
