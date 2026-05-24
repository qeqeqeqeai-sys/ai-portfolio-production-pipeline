from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st

from transmission_layers.expectation_failure.dashboard_operationalization.d7_streamlit_dashboard_viewer import (
    build_d7_dashboard_view_model,
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

    runtime_config = build_streamlit_supabase_runtime_config()
    client_resolution = resolve_streamlit_supabase_client(runtime_config)
    client = client_resolution.get("client")

    if not client_resolution.get("client_resolved"):
        st.status("Supabase client unavailable; rendering degraded read-only shell.")

    vm = _load_view_model_cached(client)
    overview = vm["overview"]

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
