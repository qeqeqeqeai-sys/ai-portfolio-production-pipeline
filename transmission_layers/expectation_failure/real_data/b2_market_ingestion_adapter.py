"""B2 controlled deterministic market data ingestion adapter."""

from __future__ import annotations

from copy import deepcopy
from typing import Iterable

from .b1_benchmark_registry import FIXED_BENCHMARK_ORDER
from .b1_real_entity_registry import FIXED_ENTITY_ORDER
from .b2_ingestion_candidate_builder import build_ingestion_candidate
from .b2_ingestion_certification import certify_b2_ingestion_candidate
from .b2_market_input_normalizer import normalize_market_input_records
from .b2_market_input_validation import validate_normalized_records


def build_b2_controlled_ingestion_adapter(raw_records: Iterable[dict], as_of_date: str) -> dict:
    """Build and certify deterministic B2 ingestion candidate from raw records."""
    raw_projection = deepcopy(list(raw_records))
    allowed_symbols = set(FIXED_ENTITY_ORDER) | set(FIXED_BENCHMARK_ORDER)
    normalized = normalize_market_input_records(raw_projection)
    accepted, quarantined = validate_normalized_records(normalized, allowed_symbols=allowed_symbols, as_of_date=as_of_date)
    candidate = build_ingestion_candidate(
        accepted_records=accepted,
        quarantined_records=quarantined,
        entity_symbols=FIXED_ENTITY_ORDER,
        benchmark_symbols=FIXED_BENCHMARK_ORDER,
        as_of_date=as_of_date,
    )
    return certify_b2_ingestion_candidate(candidate)
