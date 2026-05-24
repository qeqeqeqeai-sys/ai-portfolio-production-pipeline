from streamlit_apps.d7_operational_dashboard_viewer import _load_view_model_cached
from transmission_layers.expectation_failure.dashboard_operationalization.d7_streamlit_dashboard_viewer import build_d7_dashboard_view_model, build_e6_executive_summary_render_plan


class _Resp:
    def __init__(self, data):
        self.data = data


class _Query:
    def __init__(self, rows):
        self.rows = list(rows)

    def select(self, _cols):
        return self

    def order(self, key, desc=True):
        self.rows = sorted(self.rows, key=lambda x: str(x.get(key) or ""), reverse=desc)
        return self

    def limit(self, n):
        self.rows = self.rows[:n]
        return self

    def execute(self):
        return _Resp(self.rows)


class _Client:
    def __init__(self, tables):
        self.tables = tables

    def table(self, name):
        return _Query(self.tables.get(name, []))


def _payloads():
    return {
        "dashboard_finding_records": [
            {"record_id": "F1", "finding_id": "F-1", "finding_title": "Liquidity stress", "finding_type": "liquidity", "finding_severity": "high", "finding_direction": "worsening", "confidence_label": "high", "created_at": "2026-05-24T01:00:00Z", "payload": {"finding_summary": "Liquidity stress is rising.", "confidence": "high"}, "replay_metadata": {}},
        ],
        "dashboard_narrative_records": [
            {"record_id": "N1", "created_at": "2026-05-24T01:01:00Z", "narrative_section": "supervisor_interpretation", "related_finding_ids": ["F-1"], "payload": {"narrative_text": "Supervisor notes elevated fragility pressure."}, "replay_metadata": {}},
        ],
        "dashboard_evidence_map_records": [
            {"record_id": "E1", "finding_id": "F-1", "evidence_ref": "EV-1", "created_at": "2026-05-24T01:02:00Z", "payload": {"evidence_summary": "Spread widening + elevated drawdown tails."}, "replay_metadata": {}},
        ],
        "dashboard_export_manifests": [],
        "dashboard_persistence_audit_records": [],
        "dashboard_replay_metadata_records": [],
        "dashboard_governance_records": [],
        "dashboard_supervisor_panel_records": [],
    }


def test_e6_populates_from_existing_e5_envelope_shape():
    vm = _load_view_model_cached(_Client(_payloads()))
    plan = build_e6_executive_summary_render_plan(vm)
    summary = plan["panels"]["executive_summary"]
    assert summary["dominant_expectation_regime"] != "Unavailable"
    assert summary["regime_confidence_band"] != "Unavailable"
    assert summary["key_contradiction_summary"] != "Unavailable"
    assert summary["temporal_semantic_change_summary"] != "Unavailable"
    assert summary["caveat_summary"] != "Unavailable"
    assert summary["supervisor_closeout_interpretation"] != "Unavailable"


def test_missing_optional_payloads_degrade_gracefully_without_fake_defaults():
    vm = build_d7_dashboard_view_model(
        findings_payload={"rows": [], "row_count": 0},
        narratives_payload={"rows": [], "row_count": 0},
        evidence_payload={"rows": [], "row_count": 0},
        integrity_payload={"manifests": {"rows": [], "row_count": 0}, "audits": {"rows": [], "row_count": 0}, "replay": {"rows": [], "row_count": 0}},
    )
    plan = build_e6_executive_summary_render_plan(vm)
    summary = plan["panels"]["executive_summary"]
    assert summary["key_contradiction_summary"] != ""


def test_operational_and_streamlit_paths_share_same_populated_view_model_semantics():
    client = _Client(_payloads())
    vm_operational = _load_view_model_cached(client)
    vm_direct = build_d7_dashboard_view_model(
        findings_payload={"rows": _payloads()["dashboard_finding_records"], "row_count": 1},
        narratives_payload={"rows": _payloads()["dashboard_narrative_records"], "row_count": 1},
        evidence_payload={"rows": _payloads()["dashboard_evidence_map_records"], "row_count": 1},
        integrity_payload={"manifests": {"rows": [], "row_count": 0}, "audits": {"rows": [], "row_count": 0}, "replay": {"rows": [], "row_count": 0}},
    )
    op = build_e6_executive_summary_render_plan(vm_operational)["panels"]["executive_summary"]
    dr = build_e6_executive_summary_render_plan(vm_direct)["panels"]["executive_summary"]
    assert op["dominant_expectation_regime"] == dr["dominant_expectation_regime"]
