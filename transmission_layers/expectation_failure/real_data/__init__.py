"""B1/B2 real-data deterministic adapters and certifications."""

from .b1_benchmark_registry import FIXED_BENCHMARK_ORDER, build_fixed_benchmark_registry
from .b1_fragility_payload_builder import build_deterministic_fragility_payload
from .b1_market_snapshot_builder import build_deterministic_market_snapshot
from .b1_real_entity_registry import FIXED_ENTITY_ORDER, build_fixed_real_entity_registry
from .b1_snapshot_certification import certify_b1_snapshot
from .b2_ingestion_certification import certify_b2_ingestion_candidate
from .b2_market_ingestion_adapter import build_b2_controlled_ingestion_adapter

__all__ = [
    "FIXED_ENTITY_ORDER",
    "FIXED_BENCHMARK_ORDER",
    "build_fixed_real_entity_registry",
    "build_fixed_benchmark_registry",
    "build_deterministic_market_snapshot",
    "build_deterministic_fragility_payload",
    "certify_b1_snapshot",
    "build_b2_controlled_ingestion_adapter",
    "certify_b2_ingestion_candidate",
]
