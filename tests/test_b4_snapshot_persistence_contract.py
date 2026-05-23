from transmission_layers.expectation_failure.real_data import (
    B4_APPROVED_TABLE_NAMES,
    B4_FORBIDDEN_CAPABILITY_CONTRACT,
    resolve_b4_table_names,
)


def test_b4_contract_table_resolution_deterministic_and_override():
    base = resolve_b4_table_names()
    assert base == B4_APPROVED_TABLE_NAMES
    override = resolve_b4_table_names({"snapshots": "x_snapshots"})
    assert override["snapshots"] == "x_snapshots"
    assert override["audit"] == B4_APPROVED_TABLE_NAMES["audit"]
    assert B4_FORBIDDEN_CAPABILITY_CONTRACT["supabase_client_creation"] == "disallowed"
