from transmission_layers.expectation_failure.replay_ecology import lr6_live7_deterministic_shared_wave_id_remediation as live7
from transmission_layers.expectation_failure.replay_ecology.persistence.adapters import replay_richness_wave0_shadow_append_only_adapter as adapter


class _Resp:
    def __init__(self, rows):
        self.count = len(rows)


class _Table:
    def __init__(self):
        self.rows = []

    def insert(self, rows):
        self.rows = rows
        return self

    def execute(self):
        return _Resp(self.rows)


class _Client:
    def __init__(self):
        self.t = _Table()

    def table(self, _name):
        return self.t


def _metadata():
    return {
        "metric_target": "replay_richness",
        "target_name": "replay_richness_wave0_shadow",
        "append_only": True,
        "mode": "append_only_insert",
        "schema_confirmed": True,
    }


def _intent(i):
    return {
        "duplicate_prevention_key": f"LR6_LIVE5_WAVE_001|LIVE5_E{i}|replay_richness|W0",
        "lineage_metadata": {"run": "x"},
        "rollback_metadata": {"ticket": "r"},
        "payload": {"entity_id": f"LIVE5_E{i}", "source_artifact_refs": ["a.json"], "execution_mode": "append_only_insert"},
    }


def test_shared_wave_id_deterministic_semantics_and_adapter_inheritance():
    intents = [_intent(1), _intent(2), _intent(3)]
    c = live7.build_lr6_live7_shared_wave_context(insert_intents=intents, metadata=_metadata())
    c2 = live7.build_lr6_live7_shared_wave_context(insert_intents=intents, metadata=_metadata())
    w1 = live7.build_lr6_live7_shared_wave_id(c)
    w2 = live7.build_lr6_live7_shared_wave_id(c2)
    assert w1 == w2

    c3 = live7.build_lr6_live7_shared_wave_context(insert_intents=[_intent(4)], metadata=_metadata())
    assert live7.build_lr6_live7_shared_wave_id(c3) != w1

    client = _Client()
    out = adapter.execute_append_only_insert(insert_intents=intents, metadata=_metadata(), client=client)
    assert out["attempted"] is True
    wave_ids = {r["wave_id"] for r in client.t.rows}
    assert len(wave_ids) == 1
    assert next(iter(wave_ids)).startswith("LR6_LIVE7_WAVE_")


def test_reviews_certification_and_report_completeness():
    rows = [{"wave_id": "LR6_LIVE7_WAVE_A", "duplicate_prevention_key": "k1", "lineage_metadata": {"a": 1}, "rollback_metadata": {"b": 1}, "source_artifact_refs": ["x"], "adapter_name": adapter.APPROVED_ADAPTER_NAME, "execution_mode": "append_only_insert"}]
    hist = [{"wave_id": "LR6_LIVE5_WAVE_1FB274FE8C0A"}]
    review = live7.build_lr6_live7_supervisor_review(inserted_rows=rows, historical_rows=hist)
    assert review["historical_compatibility_review"]["automatic_migration_performed"] is False
    assert review["append_only_findings"]["duplicate_prevention_key_uniqueness_preserved"] is True
    assert review["governance_findings"]["scaling_enabled"] is False
    assert review["governance_findings"]["topology_expansion_enabled"] is False
    assert review["governance_findings"]["prediction_enabled"] is False
    assert review["governance_findings"]["trading_enabled"] is False

    md = live7.build_lr6_live7_markdown_report(review)
    for section in (
        "## shared_wave_remediation_summary",
        "## deterministic_derivation_explanation",
        "## replay_cohort_semantics_explanation",
        "## historical_compatibility_review",
        "## append_only_findings",
        "## governance_findings",
        "## residual_risks",
        "## live8_recommendation",
    ):
        assert section in md
