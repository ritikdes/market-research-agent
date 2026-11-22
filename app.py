import streamlit as st

from agents import run_workflow
from schemas import ResearchState, ResearchBrief

st.set_page_config(
    page_title="Market Research Multi-Agent App",
    layout="wide",
)


def brief_to_markdown(query: str, state: ResearchState) -> str:
    """Format the final research brief and metadata into a Markdown report."""
    brief = state.final_brief
    if brief is None:
        return f"# Market Research Brief: {query}\n\nNo Brief generated"

    lines: list[str] = [
        f"# Market Research Brief: {query}",
        "",
        "## Topic Summary",
        brief.topic_summary,
        "",
        "## Competitors (Up to 2)",
    ]

    if brief.competitors:
        for comp in brief.competitors[:2]:
            lines.append(f"- **{comp.name}**: {comp.overview}")
    else:
        lines.append("- No specific competitors highlighted from available findings.")

    lines.extend(["", "## Key Observations"])
    if brief.key_observation:
        for obs in brief.key_observation:
            lines.append(f"- {obs}")
    else:
        lines.append("- None recorded.")

    lines.extend(["", "## Sources"])
    if brief.sources:
        for src in brief.sources:
            lines.append(f"- {src}")
    else:
        lines.append("- None recorded.")

    lines.extend(["", "## Missing Information"])
    if brief.missing_information:
        for gap in brief.missing_information:
            lines.append(f"- {gap}")
    else:
        lines.append("- No major gaps noted.")

    lines.extend(
        [
            "",
            "---",
            f"Revisions used: {state.revision_count} / 1",
        ]
    )
    if state.critic_feedback:
        lines.append(
            f"Critic status: {'Approved' if state.critic_feedback.approved else 'Revision requested'} — "
            f"{state.critic_feedback.feedback}"
        )

    return "\n".join(lines)


def render_brief(brief: ResearchBrief) -> None:
    """Render the four required brief sections in Streamlit"""
    st.subheader("Topic Summary")
    st.write(brief.topic_summary)

    st.subheader("Competitors (Up to 2)")
    if brief.competitors:
        for comp in brief.competitors[:2]:
            st.markdown(f"**{comp.name}** - {comp.overview}")
    else:
        st.caption("No specific competitors identified as relevant from the current findings.")

    st.subheader("Key Observations")
    for item in brief.key_observation:
        st.markdown(f"- {item}")

    col_sources, col_gaps = st.columns(2)
    with col_sources:
        st.subheader("Sources")
        if brief.sources:
            for src in brief.sources:
                st.markdown(f"- {src}")
        else:
            st.caption("No sources listed.")

    with col_gaps:
        st.subheader("Missing Information")
        if brief.missing_information:
            for gap in brief.missing_information:
                st.markdown(f"- {gap}")
        else:
            st.caption("No missing information noted.")


def main() -> None:
    st.title("Multi-Agent Market Research")
    st.write(
        "Enter a company or industry to run a sequential workflow across "
        "**Orchestrator**, **Researcher**, **Analyst** and **Critic**."
    )

    query = st.text_input(
        "Company or Industry Query",
        value="Analyze the food delivery market in Nepal.",
        placeholder="e.g., Analyze the food delivery market in Nepal.",
    )

    run_clicked = st.button("Run Research", type="primary")

    if "research_state" not in st.session_state:
        st.session_state.research_state = None
        st.session_state.step_logs = []

    if run_clicked:
        cleaned_query = query.strip()
        if not cleaned_query:
            st.warning("Please enter a company or industry before starting.")
            return

        logs: list[str] = []
        status_box = st.status("Running multi-agent workflow...", expanded=True)

        def handle_step(stage: str, current_state: ResearchState) -> None:
            logs.append(stage)
            status_box.write(f"- {stage}")

        try:
            final_state = run_workflow(cleaned_query, on_step=handle_step)
            status_box.update(label="Workflow complete", state="complete", expanded=False)
            st.session_state.research_state = final_state
            st.session_state.step_logs = logs
        except Exception as e:
            status_box.update(label="Workflow failed", state="error", expanded=True)
            st.error(f"Error during workflow execution: {e}")
            return

    state: ResearchState | None = st.session_state.research_state
    if state and state.final_brief:
        st.divider()
        render_brief(state.final_brief)

        md_report = brief_to_markdown(state.query, state)
        st.download_button(
            label="Download Brief (.md)",
            data=md_report,
            file_name="sample_output.md",
            mime="text/markdown",
        )

        with st.expander("Agent Workflow & Evidence Details"):
            st.markdown("**Execution Steps**")
            for step in st.session_state.step_logs:
                st.markdown(f"- {step}")

            st.markdown(f"**Revisions completed:** '{state.revision_count}' (max 1)")
            if state.critic_feedback:
                st.markdown(
                    f"**Critic Decision:** '{'Approved' if state.critic_feedback.approved else 'Not Approved'}'"
                )
                st.write(state.critic_feedback.feedback)

            st.markdown("**Search Queries Used**")
            for q in state.search_queries:
                st.markdown(f"- {q}")

            st.markdown("**Gathered Findings**")
            for idx, f in enumerate(state.findings, start=1):
                st.markdown(f"{idx}. **[{f.source_type}] {f.title}** ({f.url})")
                st.caption(f.snippet)


if __name__ == "__main__":
    main()