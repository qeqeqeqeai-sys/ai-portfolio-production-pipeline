"""SEFI history Supabase read-model helpers."""

from .loader import (
    ArtifactLoadError,
    build_read_model_rows,
    build_rows_from_artifact,
    deterministic_duplicate_key,
    load_rows_to_supabase,
)

from .observation_fact_retrieval import (
    HARD_LIMIT as OBS_QUERY1_HARD_LIMIT,
    retrieve_observation_facts,
    render_observation_fact_retrieval_markdown,
    write_observation_fact_retrieval_outputs,
)

from .observation_intelligence_query import (
    get_changed_structures as get_obs_query2_changed_structures,
    get_dominant_structures as get_obs_query2_dominant_structures,
    get_persistent_structures as get_obs_query2_persistent_structures,
    get_recurrent_structures as get_obs_query2_recurrent_structures,
    get_transitioning_structures as get_obs_query2_transitioning_structures,
    get_weakening_structures as get_obs_query2_weakening_structures,
    retrieve_intelligence_question,
    render_intelligence_question_markdown,
    write_intelligence_question_outputs,
)

from .historical_live_comparison import (
    compare_historical_live_state,
    get_historically_weak_structures_strengthening_live,
    get_live_anomalies_vs_historical,
    get_live_baseline_deviations,
    get_live_recurring_historical_patterns,
    get_persistent_structures_weakening_live,
    render_historical_live_comparison_markdown,
    write_historical_live_comparison_outputs,
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
    "OBS_QUERY1_HARD_LIMIT",
    "retrieve_observation_facts",
    "render_observation_fact_retrieval_markdown",
    "write_observation_fact_retrieval_outputs",
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
    "get_obs_query2_changed_structures",
    "get_obs_query2_dominant_structures",
    "get_obs_query2_persistent_structures",
    "get_obs_query2_recurrent_structures",
    "get_obs_query2_transitioning_structures",
    "get_obs_query2_weakening_structures",
    "retrieve_intelligence_question",
    "render_intelligence_question_markdown",
    "write_intelligence_question_outputs",
    "compare_historical_live_state",
    "get_historically_weak_structures_strengthening_live",
    "get_live_anomalies_vs_historical",
    "get_live_baseline_deviations",
    "get_live_recurring_historical_patterns",
    "get_persistent_structures_weakening_live",
    "render_historical_live_comparison_markdown",
    "write_historical_live_comparison_outputs",
]
