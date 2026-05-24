from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st

from transmission_layers.expectation_failure.dashboard_operationalization.d7_streamlit_dashboard_viewer import (
    build_d7_dashboard_view_model,
    build_d7_runtime_diagnostics,
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
    st.title("SEFI D7 — Thin Operational Dashboard Viewer")

    secret_url = st.secrets.get("SUPABASE_URL") if hasattr(st, "secrets") else None
    secret_key = (
        st.secrets.get("SUPABASE_SERVICE_ROLE_KEY") if hasattr(st, "secrets") else None
    ) or (st.secrets.get("SUPABASE_ANON_KEY") if hasattr(st, "secrets") else None) or (st.secrets.get("SUPABASE_KEY") if hasattr(st, "secrets") else None)
    runtime_config = build_streamlit_supabase_runtime_config(supabase_url=secret_url, supabase_key=secret_key)
    client_resolution = resolve_streamlit_supabase_client(runtime_config)
    client = client_resolution.get("client")

    vm = _load_view_model_cached(client)
    overview = vm["overview"]
    findings_payload = vm["runtime_sections"]["findings_payload"]
    narratives_payload = vm["runtime_sections"]["narratives_payload"]
    evidence_payload = vm["runtime_sections"]["evidence_payload"]
    integrity_payload = vm["runtime_sections"]["integrity_payload"]
    table_row_counts = {
        "dashboard_finding_records": int(findings_payload.get("row_count") or 0),
        "dashboard_narrative_records": int(narratives_payload.get("row_count") or 0),
        "dashboard_evidence_map_records": int(evidence_payload.get("row_count") or 0),
        "dashboard_export_manifests": int(integrity_payload.get("manifests", {}).get("row_count") or 0),
        "dashboard_persistence_audit_records": int(integrity_payload.get("audits", {}).get("row_count") or 0),
        "dashboard_replay_metadata_records": int(integrity_payload.get("replay", {}).get("row_count") or 0),
    }
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
    total_rows = sum(table_row_counts.values())

    if not client_resolution.get("client_resolved"):
        st.warning("Supabase client not configured")
    elif total_rows == 0:
        st.info("No persisted dashboard records found")
    else:
        st.success(f"Loaded {table_row_counts['dashboard_finding_records']} findings from Supabase")

    with st.expander("Supabase table row counts", expanded=False):
        st.json(table_row_counts)
    with st.expander("D7 runtime diagnostics", expanded=False):
        st.json(runtime_diagnostics)

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Latest Run", overview.get("latest_operational_run") or "n/a")
    c2.metric("Certification", overview.get("certification_status") or "n/a")
    c3.metric("Persistence", overview.get("persistence_execution_status") or "n/a")
    c4.metric("Readback", overview.get("readback_verification_status") or "n/a")
    c5.metric("Checksum Continuity", "yes" if overview.get("replay_checksum_continuity") else "no")

    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Findings", "Narratives", "Evidence", "Integrity", "Supervisor"])
    with tab1:
        findings = vm["findings"]
        severities = sorted({str(x.get("severity") or "") for x in findings if x.get("severity")})
        types = sorted({str(x.get("finding_type") or "") for x in findings if x.get("finding_type")})
        sev_filter = st.multiselect("Severity", severities, default=severities)
        type_filter = st.multiselect("Finding Type", types, default=types)
        filtered = [r for r in findings if (not sev_filter or r.get("severity") in sev_filter) and (not type_filter or r.get("finding_type") in type_filter)]
        st.dataframe(filtered, use_container_width=True)

    with tab2:
        st.dataframe(vm["narratives"], use_container_width=True)

    with tab3:
        st.dataframe(vm["evidence_maps"], use_container_width=True)

    with tab4:
        st.json(vm["integrity"])
        with st.expander("Raw integrity payload"):
            st.json(vm["runtime_sections"]["integrity_payload"])

    with tab5:
        interp = vm["runtime_sections"]
        st.subheader("Supervisor Interpretation")
        st.json(vm["invariant_flags"])
        st.write("Operational usefulness interpretation:", vm.get("overview", {}).get("certification_status"))
        st.write("Limitations and next step")
        st.json(build_d7_dashboard_view_model(
            findings_payload=vm["runtime_sections"]["findings_payload"],
            narratives_payload=vm["runtime_sections"]["narratives_payload"],
            evidence_payload=vm["runtime_sections"]["evidence_payload"],
            integrity_payload=vm["runtime_sections"]["integrity_payload"],
        )["integrity"])


if __name__ == "__main__":
    main()
