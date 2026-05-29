"""SEFI history Supabase read-model helpers."""

from .loader import (
    ArtifactLoadError,
    build_read_model_rows,
    build_rows_from_artifact,
    deterministic_duplicate_key,
    load_rows_to_supabase,
)

from .observation_query import (
    build_observation_intelligence_report,
    get_fragility_leaderboard,
    get_latest_metric_snapshot,
    get_metric_series,
    get_morphology_recurrence,
    get_observation_fact_summary,
    get_stability_transition_summary,
    get_top_deteriorating_metrics,
    get_top_persistent_structures,
)
from .queries import (
    get_latest_completed_phase,
    get_observation_facts,
    get_phase_run_summary,
    get_sector_morphology,
    get_symbol_metrics,
    get_window_metrics,
)

__all__ = [
    "ArtifactLoadError",
    "build_read_model_rows",
    "build_rows_from_artifact",
    "deterministic_duplicate_key",
    "load_rows_to_supabase",
    "get_latest_completed_phase",
    "get_phase_run_summary",
    "get_sector_morphology",
    "get_symbol_metrics",
    "get_observation_facts",
    "build_observation_intelligence_report",
    "get_fragility_leaderboard",
    "get_latest_metric_snapshot",
    "get_metric_series",
    "get_morphology_recurrence",
    "get_observation_fact_summary",
    "get_stability_transition_summary",
    "get_top_deteriorating_metrics",
    "get_top_persistent_structures",
    "get_window_metrics",
]
