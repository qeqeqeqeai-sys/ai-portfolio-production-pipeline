import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from transmission_layers.asset_discovery.tier3h5.canonical_propagation_memory import consolidate_canonical_propagation_memory


def test_canonical_graph_edge_identity_preferred() -> None:
    out = consolidate_canonical_propagation_memory([
        {
            "legacy_memory_id": "m1",
            "legacy_source_asset_id": "a",
            "legacy_target_asset_id": "b",
            "canonical_graph_source_id": "CANONICAL_SECURITY::sa",
            "canonical_graph_target_id": "CANONICAL_SECURITY::sb",
            "canonical_graph_edge_id": "CANONICAL_SECURITY::sa-->CANONICAL_SECURITY::sb",
        }
    ])
    row = out["memory"][0]
    assert row["memory_identity_mode"] == "canonical_graph_edge"


def test_canonical_graph_node_identity_when_edge_unavailable() -> None:
    out = consolidate_canonical_propagation_memory([
        {
            "legacy_memory_id": "m1",
            "legacy_source_asset_id": "a",
            "legacy_target_asset_id": "b",
            "canonical_graph_source_id": "CANONICAL_SECURITY::sa",
            "canonical_graph_target_id": "CANONICAL_SECURITY::sb",
        }
    ])
    assert out["memory"][0]["memory_identity_mode"] == "canonical_mixed"


def test_legacy_preserved_when_canonical_unavailable() -> None:
    out = consolidate_canonical_propagation_memory([
        {"legacy_memory_id": "m1", "legacy_source_asset_id": "a", "legacy_target_asset_id": "b"}
    ])
    assert out["memory"][0]["memory_consolidation_status"] == "legacy_memory_preserved"


def test_canonical_memory_edge_id_deterministic() -> None:
    rows = [{"legacy_memory_id": "m1", "legacy_source_asset_id": "a", "legacy_target_asset_id": "b", "canonical_graph_edge_id": "CANONICAL_SECURITY::sa-->CANONICAL_SECURITY::sb"}]
    assert consolidate_canonical_propagation_memory(rows) == consolidate_canonical_propagation_memory(rows)


def test_duplicate_legacy_memory_rows_collapsed_deterministically() -> None:
    rows = [
        {"legacy_memory_id": "m1", "legacy_source_asset_id": "a1", "legacy_target_asset_id": "b", "canonical_graph_edge_id": "X-->Y"},
        {"legacy_memory_id": "m2", "legacy_source_asset_id": "a2", "legacy_target_asset_id": "b", "canonical_graph_edge_id": "X-->Y"},
    ]
    out = consolidate_canonical_propagation_memory(rows, collapse_duplicates=True)
    assert len(out["memory"]) == 1
    assert out["diagnostics"]["duplicate_legacy_memory_collapsed"] == 1


def test_canonicalization_created_self_loop_prevented() -> None:
    out = consolidate_canonical_propagation_memory([
        {"legacy_memory_id": "m1", "legacy_source_asset_id": "a1", "legacy_target_asset_id": "a2", "canonical_graph_source_id": "CANONICAL_ISSUER::ia", "canonical_graph_target_id": "CANONICAL_ISSUER::ia"}
    ])
    assert out["memory"][0]["memory_consolidation_status"] == "canonical_self_loop_prevented"


def test_conflict_status_preserves_legacy_memory() -> None:
    out = consolidate_canonical_propagation_memory([
        {"legacy_memory_id": "m1", "legacy_source_asset_id": "a", "legacy_target_asset_id": "b", "memory_conflict_status": "conflict"}
    ])
    assert out["memory"][0]["memory_identity_mode"] == "conflict_preserved_legacy"


def test_invalid_input_preserves_legacy_memory() -> None:
    out = consolidate_canonical_propagation_memory([
        {"legacy_memory_id": "m1", "legacy_source_asset_id": "", "legacy_target_asset_id": "b"}
    ])
    assert out["memory"][0]["memory_identity_mode"] == "invalid_input_preserved_legacy"


def test_unresolved_input_preserves_legacy_memory() -> None:
    out = consolidate_canonical_propagation_memory([
        {"legacy_memory_id": "m1", "legacy_source_asset_id": "a", "legacy_target_asset_id": "b", "memory_conflict_status": "no_match"}
    ])
    assert out["memory"][0]["memory_identity_mode"] == "unresolved_preserved_legacy"


def test_diagnostics_counters_deterministic() -> None:
    rows = [{"legacy_memory_id": "m1", "legacy_source_asset_id": "a", "legacy_target_asset_id": "b", "canonical_graph_edge_id": "X-->Y"}]
    a = consolidate_canonical_propagation_memory(rows)
    b = consolidate_canonical_propagation_memory(rows)
    assert a["diagnostics"] == b["diagnostics"]


def test_continuity_lineage_consolidation_deterministic() -> None:
    rows = [{"legacy_memory_id": "m1", "legacy_source_asset_id": "a", "legacy_target_asset_id": "b", "canonical_graph_edge_id": "X-->Y"}]
    out = consolidate_canonical_propagation_memory(rows)
    assert out["memory"][0]["continuity_lineage_status"] == "consolidated"


def test_no_scoring_fields_mutated() -> None:
    row = {
        "legacy_memory_id": "m1",
        "legacy_source_asset_id": "a",
        "legacy_target_asset_id": "b",
        "canonical_graph_edge_id": "X-->Y",
        "transmission_score": 0.42,
        "decay_rate": 0.15,
    }
    out = consolidate_canonical_propagation_memory([row])
    assert out["memory"][0]["transmission_score"] == 0.42
    assert out["memory"][0]["decay_rate"] == 0.15
