"""B1/B2 real-data deterministic adapters and certifications."""

from .b1_benchmark_registry import FIXED_BENCHMARK_ORDER, build_fixed_benchmark_registry
from .b1_fragility_payload_builder import build_deterministic_fragility_payload
from .b1_market_snapshot_builder import build_deterministic_market_snapshot
from .b1_real_entity_registry import FIXED_ENTITY_ORDER, build_fixed_real_entity_registry
from .b1_snapshot_certification import certify_b1_snapshot
from .b2_ingestion_certification import certify_b2_ingestion_candidate
from .b2_market_ingestion_adapter import build_b2_controlled_ingestion_adapter
from .b3_snapshot_assembler import assemble_b3_certified_snapshot_from_b2_candidate
from .b3_snapshot_assembly_certification import decide_b3_snapshot_assembly
from .b3_snapshot_assembly_validation import validate_b3_candidate_for_assembly
from .b3_snapshot_input_mapper import map_b2_candidate_to_b1_snapshot_inputs
from .b4_snapshot_persistence_certification import certify_b4_snapshot_persistence_readiness
from .b4_snapshot_persistence_contract import B4_APPROVED_TABLE_NAMES, B4_FORBIDDEN_CAPABILITY_CONTRACT, resolve_b4_table_names
from .b4_snapshot_persistence_orchestrator import orchestrate_b4_snapshot_persistence
from .b4_snapshot_persistence_validator import validate_b4_snapshot_persistence_input
from .b4_supabase_snapshot_repository import (
    build_snapshot_audit_record,
    build_snapshot_fragility_record,
    build_snapshot_persistence_record,
    persist_certified_market_snapshot,
)
from .t1_temporal_snapshot_sequencing import (
    build_t1_temporal_sequencing_report,
    build_temporal_checksum_chain,
    build_temporal_replay_window,
    build_temporal_snapshot_sequence,
    certify_temporal_snapshot_sequence,
    validate_temporal_snapshot_inputs,
)

from .t2_structural_delta_intelligence import (
    build_structural_delta_checksum_chain,
    build_structural_delta_records,
    build_structural_delta_summary,
    build_t2_structural_delta_report,
    certify_structural_delta_intelligence,
    validate_structural_delta_inputs,
)

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
    "map_b2_candidate_to_b1_snapshot_inputs",
    "validate_b3_candidate_for_assembly",
    "decide_b3_snapshot_assembly",
    "assemble_b3_certified_snapshot_from_b2_candidate",
    "B4_APPROVED_TABLE_NAMES",
    "B4_FORBIDDEN_CAPABILITY_CONTRACT",
    "resolve_b4_table_names",
    "validate_b4_snapshot_persistence_input",
    "build_snapshot_persistence_record",
    "build_snapshot_audit_record",
    "build_snapshot_fragility_record",
    "persist_certified_market_snapshot",
    "orchestrate_b4_snapshot_persistence",
    "certify_b4_snapshot_persistence_readiness",
    "build_temporal_snapshot_sequence",
    "validate_temporal_snapshot_inputs",
    "build_temporal_replay_window",
    "build_temporal_checksum_chain",
    "certify_temporal_snapshot_sequence",
    "build_t1_temporal_sequencing_report",
    "validate_structural_delta_inputs",
    "build_structural_delta_records",
    "build_structural_delta_summary",
    "build_structural_delta_checksum_chain",
    "certify_structural_delta_intelligence",
    "build_t2_structural_delta_report",
]
