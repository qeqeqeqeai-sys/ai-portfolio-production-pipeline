"""Streamlit Daily Briefing MVP for existing SEFI intelligence outputs."""

from __future__ import annotations

from datetime import date
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st

from transmission_layers.daily_briefing import DEFAULT_ARTIFACT_PATHS, load_daily_briefing

APP_ENTRYPOINT = "apps/sefi_daily_briefing.py"
APP_TITLE = "SEFI Daily Briefing"


def _init_session_state() -> None:
    st.session_state.setdefault("selected_briefing_date", date.today())
    st.session_state.setdefault("selected_investigation", None)
    st.session_state.setdefault("selected_story", None)
    st.session_state.setdefault("active_drill_down", None)


def _confidence_badge(value: str | None) -> str:
    return f"Confidence: {value or 'not available'}"


def _lifecycle_badge(item: dict) -> str:
    lifecycle = item.get("lifecycle_state") or "not available"
    archetype = item.get("narrative_archetype") or "not available"
    return f"Lifecycle: {lifecycle} · Archetype: {archetype}"


def _render_empty_state(load_result) -> None:
    st.warning("No daily briefing data available for selected date")
    st.write("Suggested next action: run existing OPS-LIVE / OBS-QUERY pipeline.")
    with st.expander("Available artifact/report paths inspected", expanded=True):
        for path in load_result.inspected_paths:
            status = "loaded" if path in load_result.loaded_paths else "not found"
            st.write(f"- {path} — {status}")
    if load_result.warnings:
        with st.expander("Adapter warnings"):
            for warning in load_result.warnings:
                st.write(f"- {warning}")


def _render_summary_card(item: dict) -> None:
    st.markdown(f"**{item.get('title', 'Untitled item')}**")
    st.write(f"What changed: {item.get('what_changed', 'Not available')}")
    st.write(f"Why it matters: {item.get('why_it_matters', 'Not available')}")
    st.caption(
        f"{_lifecycle_badge(item)} · {_confidence_badge(item.get('confidence'))} · Historical/live deviation: "
        f"{item.get('historical_live_deviation') if item.get('historical_live_deviation') is not None else 'not available'}"
    )


def _render_item_list(items: list[dict], empty_text: str) -> None:
    if not items:
        st.info(empty_text)
        return
    for item in items:
        with st.container(border=True):
            _render_summary_card(item)


def render_daily_briefing(briefing: dict) -> None:
    st.header("Daily Briefing")
    cols = st.columns(3)
    cols[0].metric("Briefing date", briefing.get("briefing_date", "not selected"))
    cols[1].metric("Attention level", briefing.get("attention_level", "not available"))
    cols[2].metric("Confidence labels", ", ".join(briefing.get("confidence_labels") or ["not available"]))

    st.subheader("Top major developments")
    _render_item_list(briefing.get("major_developments") or [], "No major developments in the loaded briefing artifact.")

    st.subheader("Top investigation candidates")
    candidates = briefing.get("investigation_candidates") or []
    if not candidates:
        st.info("No investigation candidates in the loaded briefing artifact.")
    for item in candidates:
        with st.container(border=True):
            st.markdown(f"**#{item.get('rank')} {item.get('title')}**")
            st.write(f"Why it appears: {item.get('why_it_appears')}")
            st.write(f"Analyst value: {item.get('analyst_value')}")
            st.caption(
                f"{_lifecycle_badge(item)} · Type: {item.get('investigation_type')} · Priority: {item.get('priority')} · "
                f"{_confidence_badge(item.get('confidence'))}"
            )
            if st.button("Open detail", key=f"briefing-open-{item.get('id')}"):
                st.session_state.selected_investigation = item.get("id")
                st.session_state.selected_story = item.get("id")

    st.subheader("Historical vs live deviation highlights")
    _render_item_list(briefing.get("historical_live_deviation_highlights") or [], "No historical/live deviations in the loaded briefing artifact.")

    st.subheader("Emerging themes")
    _render_item_list(briefing.get("emerging_themes") or [], "No emerging themes in the loaded briefing artifact.")

    st.subheader("Persistence watchlist")
    _render_item_list(briefing.get("persistence_watchlist") or [], "No persistence watchlist items in the loaded briefing artifact.")


def render_investigation_queue(briefing: dict) -> None:
    st.header("Investigation Queue")
    items = briefing.get("investigation_candidates") or []
    if not items:
        st.info("No ranked investigation items available.")
        return
    labels = [f"#{item['rank']} {item['title']} ({item['priority']})" for item in items]
    selected_label = st.radio("Select investigation", labels, index=0, key="investigation_queue_radio")
    selected = items[labels.index(selected_label)]
    st.session_state.selected_investigation = selected.get("id")
    st.session_state.selected_story = selected.get("id")

    for item in items:
        with st.container(border=True):
            st.markdown(f"**#{item.get('rank')} {item.get('title')}**")
            st.write(f"Investigation type: {item.get('investigation_type')}")
            st.write(f"Lifecycle: {item.get('lifecycle_state', 'not available')}")
            st.write(f"Narrative archetype: {item.get('narrative_archetype', 'not available')}")
            st.write(f"Priority: {item.get('priority')}")
            st.write(f"Why it appears: {item.get('why_it_appears')}")
            st.write(f"Analyst value: {item.get('analyst_value')}")
            st.write("Recommended questions:")
            for question in item.get("recommended_questions") or []:
                st.write(f"- {question}")
            if st.button("View story detail", key=f"queue-open-{item.get('id')}"):
                st.session_state.selected_investigation = item.get("id")
                st.session_state.selected_story = item.get("id")


def _selected_story(briefing: dict) -> dict | None:
    stories = briefing.get("stories") or []
    selected_id = st.session_state.get("selected_story") or st.session_state.get("selected_investigation")
    if selected_id:
        for story in stories:
            if story.get("id") == selected_id:
                return story
    return stories[0] if stories else None


def render_story_detail(briefing: dict) -> None:
    st.header("Story Detail")
    story = _selected_story(briefing)
    if not story:
        st.info("Select an investigation item to view story detail.")
        return
    st.subheader(story.get("title", "Selected story"))
    st.write(f"Current state: {story.get('current_state')}")
    st.write(f"Lifecycle: {story.get('lifecycle_state', 'not available')}")
    st.write(f"Narrative archetype: {story.get('narrative_archetype', 'not available')}")
    st.write(f"Continuity explanation: {story.get('continuity_explanation', 'Not available')}")
    st.write(f"Historical context: {story.get('historical_context')}")
    st.write(f"Similarities: {story.get('similarities')}")
    st.write(f"Differences: {story.get('differences')}")
    st.write(f"Analyst significance: {story.get('analyst_significance')}")
    st.caption(
        f"Priority: {story.get('priority')} · Type: {story.get('investigation_type')} · "
        f"{_confidence_badge(story.get('confidence'))}"
    )

    st.write("Recommended next questions:")
    for question in story.get("next_questions") or []:
        st.write(f"- {question}")

    evidence = story.get("evidence") or {}
    with st.expander("Evidence drill-down: supporting fact and evidence IDs"):
        st.session_state.active_drill_down = story.get("id")
        st.write("Supporting fact IDs:")
        st.write(", ".join(evidence.get("supporting_fact_ids") or []) or "None supplied")
        st.write("Supporting evidence IDs:")
        st.write(", ".join(evidence.get("supporting_evidence_ids") or []) or "None supplied")
        st.write("Historical supporting fact IDs:")
        st.write(", ".join(evidence.get("historical_supporting_fact_ids") or []) or "None supplied")
        st.write("Live supporting fact IDs:")
        st.write(", ".join(evidence.get("live_supporting_fact_ids") or []) or "None supplied")
        st.write("Source phases:")
        st.write(", ".join(evidence.get("source_phases") or []) or "None supplied")


def main() -> None:
    st.set_page_config(page_title=APP_TITLE, layout="wide")
    _init_session_state()
    st.title(APP_TITLE)
    st.caption("Read-only MVP over existing SEFI intelligence artifacts; no schema changes, writes, or new intelligence generation.")

    selected_date = st.sidebar.date_input("Briefing date", value=st.session_state.selected_briefing_date, key="briefing_date_input")
    st.session_state.selected_briefing_date = selected_date
    page = st.sidebar.radio("Workflow", ["Daily Briefing", "Investigation Queue", "Story Detail"], key="daily_briefing_page")

    load_result = load_daily_briefing(
        selected_date=selected_date,
        artifact_paths=DEFAULT_ARTIFACT_PATHS,
        project_root=PROJECT_ROOT,
    )
    briefing = load_result.briefing
    if briefing.get("empty"):
        _render_empty_state(load_result)
        return

    with st.sidebar.expander("Loaded sources"):
        for path in load_result.loaded_paths:
            st.write(f"- {path}")

    if page == "Daily Briefing":
        render_daily_briefing(briefing)
    elif page == "Investigation Queue":
        render_investigation_queue(briefing)
    else:
        render_story_detail(briefing)


if __name__ == "__main__":
    main()
