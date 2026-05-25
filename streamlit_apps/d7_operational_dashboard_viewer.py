from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st

from transmission_layers.expectation_failure.dashboard_operationalization.d7_streamlit_dashboard_viewer import (
    build_d7_dashboard_view_model,
    build_d7_debug_payload_sections,
    build_d7_evidence_highlights,
    build_d7_intelligence_cards,
    build_d7_narrative_sections,
    build_d7_runtime_diagnostics,
    build_d7_supervisor_summary,
    render_d7_debug_archive,
    render_d7_evidence_highlights,
    render_d7_finding_cards,
    render_d8_1_operational_insight_cards,
    render_d8_2_replay_evidence_density_summary,
    render_d7_integrity_overview,
    render_d7_intelligence_overview,
    render_d7_narrative_sections,
    render_d7_supervisor_interpretation,
    render_d15_historical_operational_intelligence,
    render_d16_historical_findings_operator_narrative,
    render_d17_historical_confidence_lineage,
    render_d18_cross_run_confidence_delta_operator_triage,
    render_d19_triage_explainability_continuity_taxonomy,
    render_h1_historical_density_expansion,
    render_h2_governed_replay_expansion_cycle,
    render_cd1_candidate_diversity_strengthening,
    render_h3_cross_replay_structural_transition_intelligence,
    render_cd2_replay_novelty_prioritization,
    render_cd3_governed_novelty_guided_replay_expansion_plan,
    render_e6_expectation_executive_summary,
    load_d7_dashboard_evidence_maps,
    load_d7_dashboard_findings,
    load_d7_dashboard_narratives,
    load_d7_dashboard_operational_integrity,
)
from transmission_layers.expectation_failure.dashboard_operationalization.dashboard_o7_streamlit_supabase_runtime import (
    build_streamlit_supabase_runtime_config,
    resolve_streamlit_supabase_client,
)


@st.cache_data(ttl=120)
def _load_view_model_cached(_client: object | None):
    findings = load_d7_dashboard_findings(_client)
    narratives = load_d7_dashboard_narratives(_client)
    evidence = load_d7_dashboard_evidence_maps(_client)
    integrity = load_d7_dashboard_operational_integrity(_client)
    return build_d7_dashboard_view_model(
        findings_payload=findings,
        narratives_payload=narratives,
        evidence_payload=evidence,
        integrity_payload=integrity,
    )


def main() -> None:
    st.set_page_config(page_title="D7 Operational Dashboard Viewer", layout="wide")
    st.title("SEFI D7 — Intelligence-First Operational Dashboard")

    secret_url = st.secrets.get("SUPABASE_URL") if hasattr(st, "secrets") else None
    secret_key = (
        st.secrets.get("SUPABASE_SERVICE_ROLE_KEY") if hasattr(st, "secrets") else None
    ) or (st.secrets.get("SUPABASE_ANON_KEY") if hasattr(st, "secrets") else None) or (st.secrets.get("SUPABASE_KEY") if hasattr(st, "secrets") else None)
    runtime_config = build_streamlit_supabase_runtime_config(supabase_url=secret_url, supabase_key=secret_key)
    client_resolution = resolve_streamlit_supabase_client(runtime_config)
    client = client_resolution.get("client")

    vm = _load_view_model_cached(client)
    findings_payload = vm["runtime_sections"]["findings_payload"]
    narratives_payload = vm["runtime_sections"]["narratives_payload"]
    evidence_payload = vm["runtime_sections"]["evidence_payload"]
    integrity_payload = vm["runtime_sections"]["integrity_payload"]

    table_payloads = {
        "dashboard_finding_records": findings_payload,
        "dashboard_narrative_records": narratives_payload,
        "dashboard_evidence_map_records": evidence_payload,
        "dashboard_export_manifests": integrity_payload.get("manifests", {}),
        "dashboard_persistence_audit_records": integrity_payload.get("audits", {}),
        "dashboard_replay_metadata_records": integrity_payload.get("replay", {}),
    }
    runtime_diagnostics = build_d7_runtime_diagnostics(
        runtime_config=runtime_config,
        client_resolution=client_resolution,
        table_payloads=table_payloads,
    )
    total_rows = sum(int(payload.get("row_count") or 0) for payload in table_payloads.values())

    if not client_resolution.get("client_resolved"):
        st.warning("Supabase client not configured")
    elif total_rows == 0:
        st.info("No persisted dashboard records found")
    else:
        st.success(f"Loaded {int(findings_payload.get('row_count') or 0)} findings from Supabase")

    intelligence_cards = build_d7_intelligence_cards(vm.get("findings", []), vm.get("evidence_maps", []))
    narrative_sections = build_d7_narrative_sections(vm.get("narratives", []))
    evidence_highlights = build_d7_evidence_highlights(vm.get("evidence_maps", []), vm.get("findings", []))
    supervisor_summary = build_d7_supervisor_summary(vm)
    integrity_overview = vm.get("integrity_overview", {})
    debug_archive = build_d7_debug_payload_sections(vm)
    if isinstance(debug_archive, dict):
        debug_archive.setdefault("runtime_diagnostics", runtime_diagnostics)

    render_e6_expectation_executive_summary(vm, st=st)
    render_d15_historical_operational_intelligence(vm, st=st)
    render_d16_historical_findings_operator_narrative(vm, st=st)
    render_d17_historical_confidence_lineage(vm, st=st)
    render_d18_cross_run_confidence_delta_operator_triage(vm, st=st)
    render_d19_triage_explainability_continuity_taxonomy(vm, st=st)
    render_h1_historical_density_expansion(vm, st=st)
    render_h2_governed_replay_expansion_cycle(vm, st=st)
    render_cd1_candidate_diversity_strengthening(vm, st=st)
    render_h3_cross_replay_structural_transition_intelligence(vm, st=st)
    render_cd2_replay_novelty_prioritization(vm, st=st)
    render_cd3_governed_novelty_guided_replay_expansion_plan(vm, st=st)
    render_d7_intelligence_overview(vm, st=st)

    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "Supervisor Interpretation",
        "Key Finding Cards",
        "Narrative Sections",
        "Evidence Highlights",
        "Operational Integrity",
        "Replay & Evidence Density",
        "Governance / Debug Archive",
    ])

    with tab1:
        render_d7_supervisor_interpretation(supervisor_summary, st=st)
    with tab2:
        render_d8_1_operational_insight_cards(vm, st=st)
        render_d7_finding_cards(intelligence_cards, st=st)
    with tab3:
        render_d7_narrative_sections(narrative_sections, st=st)
    with tab4:
        render_d7_evidence_highlights(evidence_highlights, st=st)
    with tab5:
        render_d7_integrity_overview(integrity_overview, st=st)
    with tab6:
        render_d8_2_replay_evidence_density_summary(vm, st=st)
    with tab7:
        render_d7_debug_archive(debug_archive, st=st)


if __name__ == "__main__":
    main()
