"""SEFI history Supabase read-model helpers."""

from .loader import (
    ArtifactLoadError,
    build_read_model_rows,
    build_rows_from_artifact,
    deterministic_duplicate_key,
    load_rows_to_supabase,
)
from .queries import (
    get_latest_completed_phase,
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
    "get_window_metrics",
]
