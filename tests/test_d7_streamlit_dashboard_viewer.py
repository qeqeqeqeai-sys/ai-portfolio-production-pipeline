from transmission_layers.expectation_failure.dashboard_operationalization.d7_streamlit_dashboard_viewer import (
    D7_RENDER_SECTION_ORDER,
    D7_PHYSICAL_COLUMNS_BY_TABLE,
    build_e6_executive_summary_render_plan,
    build_d7_dashboard_view_model,
    build_d7_render_plan,
    build_d15_historical_operational_intelligence_render_plan,
    build_d7_debug_payload_sections,
    build_d7_evidence_highlights,
    build_d7_intelligence_cards,
    build_d7_narrative_sections,
    build_d7_runtime_diagnostics,
    build_d7_supervisor_summary,
    render_d7_debug_archive,
    render_d7_evidence_highlights,
    render_d7_finding_cards,
    render_d7_intelligence_overview,
    render_d7_integrity_overview,
    render_d8_2_replay_evidence_density_summary,
    render_d15_historical_operational_intelligence,
    render_d16_historical_findings_operator_narrative,
    render_e6_expectation_executive_summary,
    render_d7_narrative_sections,
    render_d7_supervisor_interpretation,
    render_cd2_replay_novelty_prioritization,
    load_d7_dashboard_evidence_maps,
    load_d7_dashboard_findings,
    load_d7_dashboard_narratives,
    load_d7_dashboard_operational_integrity,
)
class _Ctx:
    def __enter__(self): return self
    def __exit__(self, exc_type, exc, tb): return False

class FakeStreamlit:
    def __init__(self):
        self.metrics = []
        self.markdowns = []
        self.captions = []
        self.json_calls = []
    def markdown(self, text): self.markdowns.append(str(text))
    def caption(self, text): self.captions.append(str(text))
    def metric(self, label, value): self.metrics.append((label, value))
    def json(self, data): self.json_calls.append(data)
    def divider(self): return None
    def container(self): return _Ctx()
    def expander(self, _): return _Ctx()
    def columns(self, n): return [self for _ in range(n)]


class _Resp:
    def __init__(self, data):
        self.data = data


class _Query:
    def __init__(self, rows, client, table):
        self.rows = list(rows)
        self.client = client
        self.table = table

    def select(self, cols):
        self.client.selections.append((self.table, cols))
        return self

    def order(self, key, desc=True):
        self.rows = sorted(self.rows, key=lambda x: str(x.get(key) or ""), reverse=desc)
        return self

    def limit(self, n):
        self.rows = self.rows[:n]
        return self

    def execute(self):
        return _Resp(self.rows)


class FakeReadOnlyClient:
    def __init__(self, tables):
        self.tables = tables
        self.write_calls = []
        self.selections = []

    def table(self, name):
        return _Query(self.tables.get(name, []), self, name)

    def insert(self, *args, **kwargs):
        self.write_calls.append((args, kwargs))


def _build_client():
    return FakeReadOnlyClient({
        "dashboard_finding_records": [
            {"record_id": "FR2", "finding_id": "F2", "created_at": "2026-05-24T01:00:00Z", "finding_title": "Elevated spread", "finding_type": "credit", "finding_severity": "high", "finding_direction": "worsening", "confidence_label": "high", "evidence_refs": ["EV2"], "lineage_refs": ["O5"], "source_payload_checksum": "abcdef1234567890", "payload": {"replay_id": "replay-2", "finding_summary": "spread widening"}, "replay_metadata": {}},
        ],
        "dashboard_narrative_records": [
            {"record_id": "N1", "created_at": "2026-05-24T01:00:00Z", "narrative_section": "expectation_fragility", "related_finding_ids": ["F2"], "payload": {"narrative_text": "Fragility concentrated in AI semis."}, "replay_metadata": {"replay_id": "replay-2"}}
        ],
        "dashboard_evidence_map_records": [
            {"record_id": "E1", "created_at": "2026-05-24T01:00:00Z", "finding_id": "F2", "evidence_ref": "EV2", "payload": {"evidence_metadata": {"metric": "credit_spread"}}, "replay_metadata": {}}
        ],
        "dashboard_export_manifests": [
            {"record_id": "MREC1", "manifest_id": "M1", "created_at": "2026-05-24T01:00:00Z", "manifest_checksum": "chk-export", "payload": {"record_counts": {"findings": 1}}, "replay_metadata": {}}
        ],
        "dashboard_persistence_audit_records": [
            {"record_id": "A1", "audit_id": "A1", "created_at": "2026-05-24T01:00:00Z", "write_status": "EXECUTED", "target_table": "dashboard_finding_records", "payload": {}, "replay_metadata": {}}
        ],
        "dashboard_replay_metadata_records": [
            {"record_id": "R1", "replay_id": "R1", "created_at": "2026-05-24T01:00:00Z", "replay_checksum": "chk-replay", "payload": {"continuity_status": "VERIFIED", "readback_verification_status": "CERTIFIED_REAL_READBACK_VERIFIED", "cycle_checksum": "cycle-123"}, "replay_metadata": {}}
        ],
    })


def test_d7_no_invalid_column_references_in_selects():
    client = _build_client()
    _ = load_d7_dashboard_findings(client)
    _ = load_d7_dashboard_narratives(client)
    _ = load_d7_dashboard_evidence_maps(client)
    _ = load_d7_dashboard_operational_integrity(client)
    invalid = {"severity", "narrative_text", "evidence_metadata", "export_manifest_checksum", "audit_status", "continuity_status"}
    selected_cols = set()
    for _, cols in client.selections:
        selected_cols.update(cols.split(","))
    assert selected_cols.isdisjoint(invalid)


def test_d7_view_model_uses_d2_mappings_and_payload_fallbacks():
    client = _build_client()
    vm = build_d7_dashboard_view_model(
        findings_payload=load_d7_dashboard_findings(client),
        narratives_payload=load_d7_dashboard_narratives(client),
        evidence_payload=load_d7_dashboard_evidence_maps(client),
        integrity_payload=load_d7_dashboard_operational_integrity(client),
    )
    assert vm["findings"][0]["severity"] == "high"
    assert vm["narratives"][0]["narrative_text"] == "Fragility concentrated in AI semis."
    assert vm["evidence_maps"][0]["evidence_metadata"]["metric"] == "credit_spread"
    assert vm["integrity"]["latest_export_manifest_checksum"] == "chk-export"
    assert vm["integrity"]["latest_persistence_audit_status"] == "EXECUTED"
    assert vm["integrity"]["verification_continuity"] == "VERIFIED"
    assert vm["integrity"]["normalized"]["persistence_status"] == "EXECUTED"
    assert vm["integrity"]["normalized"]["readback_status"] == "CERTIFIED_REAL_READBACK_VERIFIED"
    assert vm["integrity"]["normalized"]["checksum_continuity"] == "partial"


def test_d7_derives_persistence_from_payload_fallbacks():
    client = _build_client()
    client.tables["dashboard_persistence_audit_records"] = [
        {"record_id": "A2", "audit_id": "A2", "created_at": "2026-05-24T03:00:00Z", "write_status": None, "target_table": "dashboard_finding_records", "payload": {"result_summary": {"persistence_status": "EXECUTED"}}, "replay_metadata": {}}
    ]
    vm = build_d7_dashboard_view_model(
        findings_payload=load_d7_dashboard_findings(client),
        narratives_payload=load_d7_dashboard_narratives(client),
        evidence_payload=load_d7_dashboard_evidence_maps(client),
        integrity_payload=load_d7_dashboard_operational_integrity(client),
    )
    assert vm["integrity"]["normalized"]["persistence_status"] == "EXECUTED"


def test_d7_checksum_continuity_yes_with_full_chain():
    client = _build_client()
    client.tables["dashboard_export_manifests"][0]["source_payload_checksum"] = "src-1"
    client.tables["dashboard_export_manifests"][0]["export_checksum"] = "exp-1"
    client.tables["dashboard_export_manifests"][0]["manifest_checksum"] = "man-1"
    client.tables["dashboard_replay_metadata_records"][0]["replay_checksum"] = "rep-1"
    client.tables["dashboard_replay_metadata_records"][0]["source_payload_checksum"] = "src-1"
    client.tables["dashboard_replay_metadata_records"][0]["export_checksum"] = "exp-1"
    vm = build_d7_dashboard_view_model(
        findings_payload=load_d7_dashboard_findings(client),
        narratives_payload=load_d7_dashboard_narratives(client),
        evidence_payload=load_d7_dashboard_evidence_maps(client),
        integrity_payload=load_d7_dashboard_operational_integrity(client),
    )
    assert vm["integrity"]["normalized"]["checksum_continuity"] == "yes"


def test_d7_fallbacks_when_fields_missing():
    client = _build_client()
    client.tables["dashboard_replay_metadata_records"] = [{"record_id": "R2", "created_at": "2026-05-24T04:00:00Z", "payload": {}, "replay_metadata": {}}]
    client.tables["dashboard_persistence_audit_records"] = [{"record_id": "A3", "created_at": "2026-05-24T04:00:00Z", "payload": {}, "replay_metadata": {}}]
    vm = build_d7_dashboard_view_model(
        findings_payload=load_d7_dashboard_findings(client),
        narratives_payload=load_d7_dashboard_narratives(client),
        evidence_payload=load_d7_dashboard_evidence_maps(client),
        integrity_payload=load_d7_dashboard_operational_integrity(client),
    )
    assert vm["integrity"]["normalized"]["persistence_status"] == "PLANNED"
    assert vm["integrity"]["normalized"]["readback_status"] == "unknown"


def test_d7_diagnostics_counts_work_without_invalid_columns():
    client = _build_client()
    findings = load_d7_dashboard_findings(client)
    narratives = load_d7_dashboard_narratives(client)
    evidence = load_d7_dashboard_evidence_maps(client)
    integrity = load_d7_dashboard_operational_integrity(client)
    out = build_d7_runtime_diagnostics(
        runtime_config={"supabase_url": "https://abc123.supabase.co", "supabase_key": "anon", "credentials_present": True},
        client_resolution={"client_resolved": True, "client_factory_source": "supabase_package"},
        table_payloads={
            "dashboard_finding_records": findings,
            "dashboard_narrative_records": narratives,
            "dashboard_evidence_map_records": evidence,
            "dashboard_export_manifests": integrity["manifests"],
            "dashboard_persistence_audit_records": integrity["audits"],
            "dashboard_replay_metadata_records": integrity["replay"],
        },
    )
    assert out["table_diagnostics"]["dashboard_finding_records"]["row_count"] == 1


def test_d7_schema_map_has_only_allowed_keys_subset():
    assert "dashboard_finding_records" in D7_PHYSICAL_COLUMNS_BY_TABLE
    assert "severity" not in D7_PHYSICAL_COLUMNS_BY_TABLE["dashboard_finding_records"]


def test_d8_2_summary_renderer_keeps_raw_ids_outside_primary_surface():
    st = FakeStreamlit()
    vm = {
        "d8_2_dashboard": {
            "semantic_persistence_summary": {"persistence_status": "persistent"},
            "evidence_density_indicators": {"evidence_density_classification": "dense", "replay_linked_evidence_refs": ["EV-1"]},
            "replay_continuity_summary": {"continuity_status": "CONTINUOUS"},
            "regime_transition_history": {"transition_count": 2},
            "persistent_contradiction_tracking": {"persistent_contradiction_themes": ["margin_pressure"]},
            "thematic_evolution_summary": {"evolution_interpretation": "Themes stable with minor drift."},
        },
        "d8_2_replay_density_expansion": {"d8_2_checksum": "secret_checksum", "replay_density_inventory": {"run_ids": ["internal-run-1"]}},
    }
    render_d8_2_replay_evidence_density_summary(vm, st=st)
    primary_text = " ".join(st.markdowns + st.captions)
    assert "secret_checksum" not in primary_text
    assert "internal-run-1" not in primary_text
    assert st.json_calls


def test_d15_operational_intelligence_sections_render_when_payload_exists():
    st = FakeStreamlit()
    vm = {
        "d15_historical_backfill_execution_enrichment": {
            "historical_replay_depth": "SUFFICIENT",
            "historical_expectation_regime": "STABLE",
            "regime_evolution_timeline_cards": ["W1 stable", "W2 stable"],
            "strongest_recurring_constraints": ["constraint_a"],
            "strongest_historical_patterns": ["pattern_a"],
            "historical_continuity_status": "CONTINUOUS",
            "supervisory_operational_summary": "Operational continuity preserved.",
            "supervisory_risk_band": "LOW",
            "operational_recommendation": "Continue controlled read-only monitoring.",
            "governance_debug_details": {"audit_visibility": "secondary"},
            "payload_checksum": "chk-d15",
        },
        "d15_historical_execution_timeline": [{"phase": "D11"}],
        "d15_dashboard_enrichment_certification": {"certification_status": "CERTIFIED_DASHBOARD_ENRICHMENT"},
    }
    render_d15_historical_operational_intelligence(vm, st=st)
    joined = " ".join(st.markdowns + st.captions + [label for label, _ in st.metrics])
    assert "Historical Replay Depth" in joined
    assert "Historical Expectation Regime" in joined
    assert "Operational Recommendation" in joined
    assert st.json_calls


def test_d15_operational_intelligence_handles_missing_or_degraded_payload():
    st = FakeStreamlit()
    render_d15_historical_operational_intelligence({}, st=st)
    assert any("unavailable" in text.lower() for text in st.captions)


def test_d15_governance_debug_details_are_secondary_and_collapsible():
    plan = build_d15_historical_operational_intelligence_render_plan({
        "d15_historical_backfill_execution_enrichment": {"historical_replay_depth": "SUFFICIENT", "governance_debug_details": {"audit": "visible"}, "payload_checksum": "abc"},
        "d15_historical_execution_timeline": [],
        "d15_dashboard_enrichment_certification": {"certification_status": "CERTIFIED_DASHBOARD_ENRICHMENT"},
    })
    assert plan["available"] is True
    assert "governance_debug_details" in plan
    assert "primary_sections" in plan

def test_d7_ignores_stale_planned_when_newer_executed_exists():
    client = _build_client()
    client.tables["dashboard_persistence_audit_records"] = [
        {"record_id": "A-old", "created_at": "2026-05-24T01:00:00Z", "write_status": "PLANNED", "payload": {}, "replay_metadata": {}},
        {"record_id": "A-new", "created_at": "2026-05-24T02:00:00Z", "write_status": "EXECUTED", "payload": {}, "replay_metadata": {}},
    ]
    vm = build_d7_dashboard_view_model(
        findings_payload=load_d7_dashboard_findings(client),
        narratives_payload=load_d7_dashboard_narratives(client),
        evidence_payload=load_d7_dashboard_evidence_maps(client),
        integrity_payload=load_d7_dashboard_operational_integrity(client),
    )
    assert vm["integrity"]["normalized"]["persistence_status"] == "EXECUTED"
    assert vm["integrity"]["normalized"]["integrity_sources"]["selected_persistence_record_id"] == "A-new"


def test_d7_prefers_latest_row_by_created_at_for_ties():
    client = _build_client()
    client.tables["dashboard_persistence_audit_records"] = [
        {"record_id": "A1", "created_at": "2026-05-24T01:00:00Z", "write_status": "PERSISTED", "payload": {}, "replay_metadata": {}},
        {"record_id": "A2", "created_at": "2026-05-24T03:00:00Z", "write_status": "PERSISTED", "payload": {}, "replay_metadata": {}},
    ]
    vm = build_d7_dashboard_view_model(
        findings_payload=load_d7_dashboard_findings(client),
        narratives_payload=load_d7_dashboard_narratives(client),
        evidence_payload=load_d7_dashboard_evidence_maps(client),
        integrity_payload=load_d7_dashboard_operational_integrity(client),
    )
    assert vm["integrity"]["normalized"]["integrity_sources"]["selected_persistence_record_id"] == "A2"


def test_d7_derives_certified_readback_from_replay_payload_priority():
    client = _build_client()
    client.tables["dashboard_replay_metadata_records"] = [
        {"record_id": "R-old", "created_at": "2026-05-24T01:00:00Z", "payload": {"readback_verification_status": "PENDING"}, "replay_metadata": {}},
        {"record_id": "R-new", "created_at": "2026-05-24T02:00:00Z", "payload": {"effective_readback_verification_status": "CERTIFIED_REAL_READBACK_VERIFIED"}, "replay_metadata": {}},
    ]
    vm = build_d7_dashboard_view_model(
        findings_payload=load_d7_dashboard_findings(client),
        narratives_payload=load_d7_dashboard_narratives(client),
        evidence_payload=load_d7_dashboard_evidence_maps(client),
        integrity_payload=load_d7_dashboard_operational_integrity(client),
    )
    assert vm["integrity"]["normalized"]["readback_status"] == "CERTIFIED_REAL_READBACK_VERIFIED"
    assert vm["integrity"]["normalized"]["integrity_sources"]["selected_readback_record_id"] == "R-new"


def test_d7_selects_full_checksum_chain_when_available():
    client = _build_client()
    client.tables["dashboard_export_manifests"] = [
        {"record_id": "M-new", "created_at": "2026-05-24T03:00:00Z", "source_payload_checksum": "s1", "export_checksum": "e1", "payload": {}, "replay_metadata": {}},
        {"record_id": "M-full", "created_at": "2026-05-24T02:00:00Z", "source_payload_checksum": "s0", "export_checksum": "e0", "manifest_checksum": "m0", "payload": {"o5_checksum": "o5", "o6_checksum": "o6", "d3_summary_checksum": "d3", "d4_verification_checksum": "d4", "cycle_checksum": "cyc"}, "replay_metadata": {}},
    ]
    vm = build_d7_dashboard_view_model(
        findings_payload=load_d7_dashboard_findings(client),
        narratives_payload=load_d7_dashboard_narratives(client),
        evidence_payload=load_d7_dashboard_evidence_maps(client),
        integrity_payload=load_d7_dashboard_operational_integrity(client),
    )
    assert vm["integrity"]["normalized"]["checksum_chain"]["o6_checksum"] == "o6"
    assert vm["integrity"]["normalized"]["integrity_sources"]["selected_integrity_strategy"] in {"latest_full_checksum_chain", "latest_successful"}


def test_d7_deterministic_tie_breaker_for_equal_created_at_rows():
    client = _build_client()
    client.tables["dashboard_persistence_audit_records"] = [
        {"record_id": "Aaa", "created_at": "2026-05-24T04:00:00Z", "write_status": "EXECUTED", "payload": {}, "replay_metadata": {}},
        {"record_id": "Abb", "created_at": "2026-05-24T04:00:00Z", "write_status": "EXECUTED", "payload": {}, "replay_metadata": {}},
    ]
    vm1 = build_d7_dashboard_view_model(
        findings_payload=load_d7_dashboard_findings(client),
        narratives_payload=load_d7_dashboard_narratives(client),
        evidence_payload=load_d7_dashboard_evidence_maps(client),
        integrity_payload=load_d7_dashboard_operational_integrity(client),
    )
    vm2 = build_d7_dashboard_view_model(
        findings_payload=load_d7_dashboard_findings(client),
        narratives_payload=load_d7_dashboard_narratives(client),
        evidence_payload=load_d7_dashboard_evidence_maps(client),
        integrity_payload=load_d7_dashboard_operational_integrity(client),
    )
    assert vm1["integrity"]["normalized"]["integrity_sources"]["selected_persistence_record_id"] == vm2["integrity"]["normalized"]["integrity_sources"]["selected_persistence_record_id"]


def test_d7_prefers_post_execution_audit_record_over_planned_row():
    client = _build_client()
    client.tables["dashboard_persistence_audit_records"] = [
        {"record_id": "A-plan", "record_type": "persistence_audit_record", "created_at": "2026-05-24T05:00:00Z", "write_status": "PLANNED", "payload": {}, "replay_metadata": {}},
        {"record_id": "A-exec", "record_type": "d3_execution_summary_record", "created_at": "2026-05-24T04:00:00Z", "write_status": "EXECUTED", "payload": {}, "replay_metadata": {}},
    ]
    vm = build_d7_dashboard_view_model(
        findings_payload=load_d7_dashboard_findings(client),
        narratives_payload=load_d7_dashboard_narratives(client),
        evidence_payload=load_d7_dashboard_evidence_maps(client),
        integrity_payload=load_d7_dashboard_operational_integrity(client),
    )
    assert vm["integrity"]["normalized"]["persistence_status"] == "EXECUTED"
    assert vm["integrity"]["normalized"]["integrity_sources"]["selected_persistence_record_id"] == "A-exec"


def test_d7_renderer_helper_api_presence_and_ordering_constant():
    assert D7_RENDER_SECTION_ORDER == (
        "e6_expectation_executive_summary", "d15_historical_operational_intelligence", "d16_historical_findings_operator_narrative", "d17_historical_confidence_lineage", "d18_cross_run_confidence_delta_operator_triage",
            "d19_triage_explainability_continuity_taxonomy", "h1_historical_density_expansion", "h2_governed_replay_expansion_cycle", "cd1_candidate_diversity_strengthening", "h3_cross_replay_structural_transition_intelligence", "cd2_replay_novelty_prioritization", "cd3_governed_novelty_guided_replay_expansion_plan", "cd4_expectation_drift_and_replay_saturation_intelligence", "cd5_operator_adjudication_assist", "ix1_structural_insight_extraction", "ix2_evidence_linked_insight_attribution", "ix3_structural_narrative_compression", "ix4_interpretability_hardening", "intelligence_overview", "supervisor_interpretation", "key_finding_cards", "narrative_sections", "evidence_highlights", "operational_integrity_overview", "replay_evidence_density_summary", "governance_debug_archive"
    )
    assert callable(render_e6_expectation_executive_summary)
    assert callable(render_d15_historical_operational_intelligence)
    assert callable(render_d16_historical_findings_operator_narrative)
    assert callable(render_cd2_replay_novelty_prioritization)
    assert callable(render_d7_intelligence_overview)
    assert callable(render_d7_supervisor_interpretation)
    assert callable(render_d7_finding_cards)
    assert callable(render_d7_narrative_sections)
    assert callable(render_d7_evidence_highlights)
    assert callable(render_d7_integrity_overview)
    assert callable(render_d7_debug_archive)


def test_d7_render_plan_deterministic_contract_and_no_debug_leakage_in_primary_fields():
    client = _build_client()
    vm = build_d7_dashboard_view_model(
        findings_payload=load_d7_dashboard_findings(client),
        narratives_payload=load_d7_dashboard_narratives(client),
        evidence_payload=load_d7_dashboard_evidence_maps(client),
        integrity_payload=load_d7_dashboard_operational_integrity(client),
    )
    plan = build_d7_render_plan(vm)
    assert plan["section_order"] == list(D7_RENDER_SECTION_ORDER)
    assert "checksum" not in "".join(plan["overview_metrics"].keys()).lower()
    assert "raw_payload_json" not in str(plan)


def test_d7_renderer_tolerates_missing_sections_and_empty_lists():
    st = FakeStreamlit()
    render_e6_expectation_executive_summary({}, st=st)
    render_d7_intelligence_overview({}, st=st)
    render_d7_supervisor_interpretation({}, st=st)
    render_d7_finding_cards([], st=st)
    render_d7_narrative_sections({}, st=st)
    render_d7_evidence_highlights([], st=st)
    render_d7_integrity_overview({}, st=st)
    render_d7_debug_archive({}, st=st)
    assert any("No intelligence finding cards" in x for x in st.captions)
    assert any("No narrative sections" in x for x in st.captions)
    assert any("No evidence highlights" in x for x in st.captions)
    assert any("E5 supervisor closeout is unavailable" in x for x in st.captions)


def test_e6_render_plan_deterministic_and_field_extraction():
    client = _build_client()
    vm = build_d7_dashboard_view_model(
        findings_payload=load_d7_dashboard_findings(client),
        narratives_payload=load_d7_dashboard_narratives(client),
        evidence_payload=load_d7_dashboard_evidence_maps(client),
        integrity_payload=load_d7_dashboard_operational_integrity(client),
    )
    p1 = build_e6_executive_summary_render_plan(vm)
    p2 = build_e6_executive_summary_render_plan(vm)
    assert p1 == p2
    assert p1["available"] is True
    assert "dominant_expectation_regime" in p1["panels"]["executive_summary"]
    assert "e5_operational_status" in p1["panels"]["operational_usefulness"]
    assert "most_important_contradictions" in p1["panels"]["contradiction_priority"]
    assert "strongest_supporting_evidence_refs" in p1["panels"]["strongest_evidence"]
    assert "persistent_themes" in p1["panels"]["temporal_semantic_change"]
    assert "confidence_constraints" in p1["panels"]["caveat_inventory"]


def test_e6_debug_only_contains_raw_e5_payload_and_primary_plan_excludes_debug_tokens():
    client = _build_client()
    vm = build_d7_dashboard_view_model(
        findings_payload=load_d7_dashboard_findings(client),
        narratives_payload=load_d7_dashboard_narratives(client),
        evidence_payload=load_d7_dashboard_evidence_maps(client),
        integrity_payload=load_d7_dashboard_operational_integrity(client),
    )
    plan = build_e6_executive_summary_render_plan(vm)
    primary_text = str(plan["panels"])
    assert "raw_e5_envelope" not in primary_text
    assert "governance_flags" not in primary_text
    assert "checksum" not in primary_text.lower()
    assert "raw_e5_envelope" in plan["debug"]


def test_d7_primary_render_sections_do_not_emit_raw_payload_or_internal_ids():
    st = FakeStreamlit()
    card = {
        "finding_title": "Test", "finding_type": "credit", "severity": "high", "confidence": "high",
        "summary": "sum", "expectation_fragility_interpretation": "interp", "why_this_matters": "matters",
        "evidence_highlights": ["e1"], "internal_id": "i1", "checksum_ref": "c1", "raw_payload": {"k": "v"},
    }
    render_d7_finding_cards([card], st=st)
    combined = " ".join(st.markdowns + st.captions)
    assert "internal_id" not in combined
    assert "raw_payload" not in combined
    assert len(st.json_calls) >= 1


def test_d7_derives_full_checksum_continuity_from_d6_replay_record():
    client = _build_client()
    client.tables["dashboard_replay_metadata_records"] = [
        {
            "record_id": "R-d6",
            "record_type": "d6_operational_cycle_replay_record",
            "created_at": "2026-05-24T06:00:00Z",
            "source_payload_checksum": "src",
            "export_checksum": "exp",
            "payload": {"o5_checksum": "o5", "o6_checksum": "o6", "d3_summary_checksum": "d3", "d4_verification_checksum": "d4", "cycle_checksum": "cyc", "effective_readback_verification_status": "CERTIFIED_REAL_READBACK_VERIFIED"},
            "replay_metadata": {},
        }
    ]
    vm = build_d7_dashboard_view_model(
        findings_payload=load_d7_dashboard_findings(client),
        narratives_payload=load_d7_dashboard_narratives(client),
        evidence_payload=load_d7_dashboard_evidence_maps(client),
        integrity_payload=load_d7_dashboard_operational_integrity(client),
    )
    assert vm["integrity"]["normalized"]["checksum_continuity"] == "yes"


def test_d7_intelligence_cards_deterministic_and_contradiction_fallback():
    client = _build_client()
    vm = build_d7_dashboard_view_model(
        findings_payload=load_d7_dashboard_findings(client),
        narratives_payload=load_d7_dashboard_narratives(client),
        evidence_payload=load_d7_dashboard_evidence_maps(client),
        integrity_payload=load_d7_dashboard_operational_integrity(client),
    )
    cards1 = build_d7_intelligence_cards(vm["findings"], vm["evidence_maps"])
    cards2 = build_d7_intelligence_cards(vm["findings"], vm["evidence_maps"])
    assert cards1 == cards2
    assert "No explicit contradiction/divergence notes" in cards1[0]["contradiction_or_divergence_notes"]


def test_d7_narrative_grouping_and_missing_sections_stable():
    rows = [{"narrative_section": "semantic_pressure", "payload": {"narrative_text": "x"}}, {"narrative_section": "unknown", "payload": {"narrative_text": "y"}}]
    out = build_d7_narrative_sections(rows)
    keys = [x["section_key"] for x in out]
    assert keys == ["market_context", "semantic_pressure"]


def test_d7_evidence_highlight_generation_and_payload_extraction_stability():
    findings = [{"finding_id": "F2", "finding_title": "Elevated spread"}]
    evidence = [{"finding_id": "F2", "evidence_ref": "EV2", "payload": {"semantic_drivers": ["credit"], "kpi_references": ["spread_z"]}}]
    out = build_d7_evidence_highlights(evidence, findings)
    assert out[0]["linked_finding"] == "Elevated spread"
    assert out[0]["semantic_drivers"] == ["credit"]


def test_d7_integrity_debug_separation_and_input_immutability():
    client = _build_client()
    findings_payload = load_d7_dashboard_findings(client)
    before = findings_payload["rows"][0]["finding_title"]
    vm = build_d7_dashboard_view_model(
        findings_payload=findings_payload,
        narratives_payload=load_d7_dashboard_narratives(client),
        evidence_payload=load_d7_dashboard_evidence_maps(client),
        integrity_payload=load_d7_dashboard_operational_integrity(client),
    )
    debug = build_d7_debug_payload_sections(vm)
    summary = build_d7_supervisor_summary(vm)
    assert "checksum_chain" in debug and "raw_payload_json" in debug
    assert "what_sefi_currently_believes" in summary
    assert findings_payload["rows"][0]["finding_title"] == before


def test_d7_d8_6_enrichment_surface_and_strongest_evidence_override():
    client = _build_client()
    vm = build_d7_dashboard_view_model(
        findings_payload=load_d7_dashboard_findings(client),
        narratives_payload=load_d7_dashboard_narratives(client),
        evidence_payload=load_d7_dashboard_evidence_maps(client),
        integrity_payload=load_d7_dashboard_operational_integrity(client),
    )
    assert "d8_6_evidence_graph_enrichment" in vm
    assert "d8_6_dashboard" in vm
    assert vm["d8_dashboard"]["strongest_supporting_evidence_panel"].get("evidence_ref")
