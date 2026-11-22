from collections.abc import Callable
from llm import generate_structured
from schemas import CriticReview, ResearchBrief, ResearchState, SearchFinding
from tools import search_web

ProgressCallback = Callable[[str, ResearchState], None]


def build_search_queries(query: str) -> list[str]:
    """Build focused search queries from a company or industry topic."""
    cleaned = query.strip()
    return [
        cleaned,
        f"{cleaned} market overview competitors trends",
        f"{cleaned} key players challenges growth",
    ]


def run_researcher(state: ResearchState) -> ResearchState:
    """Search for relevant market information and store structured findings"""
    queries = build_search_queries(state.query)
    state.search_queries = queries

    collected: list[SearchFinding] = []
    seen_keys: set[str] = set()

    for q in queries:
        results = search_web(q, max_results=4)
        for item in results:
            dedup_key = item.url if item.url and item.url != "No URL provided" else item.title
            if dedup_key not in seen_keys:
                seen_keys.add(dedup_key)
                collected.append(item)

    if not collected:
        collected.append(
            SearchFinding(
                title="Sample Fallback Record",
                url="local://sample-fallback",
                snippet=(
                    f"Sample fallback data: no live web search results were returned for '{state.query}'. "
                    "Treat downstream observations as provisional until verified with primary sources."
                ),
                source_type="sample_fallback",
            )
        )

    state.findings = collected
    return state


def format_findings_for_prompt(findings: list[SearchFinding]) -> str:
    """Render findings as plain text blocks for LLM prompts."""
    if not findings:
        return "No research findings available."

    blocks: list[str] = []
    for idx, f in enumerate(findings, start=1):
        blocks.append(
            f"[{idx}] ({f.source_type}) {f.title}\n"
            f"Source: {f.url}\n"
            f"Snippet: {f.snippet}"
        )
    return "\n\n".join(blocks)


def run_analyst(state: ResearchState) -> ResearchState:
    """Synthesize research findings into a structured ResearchBrief."""
    evidence_text = format_findings_for_prompt(state.findings)

    revision_section = ""
    if state.revision_count > 0 and state.critic_feedback is not None:
        revision_section = (
            f"\nPrevious Critic Feedback (Revision #{state.revision_count}):\n"
            f"{state.critic_feedback.feedback}\n"
            "Address every point raised above while staying strictly grounded in the evidence.\n"
        )

    prompt = (
        f"Topic / Query: {state.query}\n"
        f"{revision_section}\n"
        f"Research Findings:\n{evidence_text}\n\n"
        "Instructions:\n"
        "- Synthesize a concise, factual market research brief using the provided findings.\n"
        "- Include up to 2 relevant competitors supported by or directly relevant to the findings.\n"
        "- List concrete key observations supported by the snippets.\n"
        "- List the source URLs (or sample fallback label) from the findings in `sources`.\n"
        "- Explicitly list gaps, missing statistics, or unverified metrics in `missing_information`."
    )

    system_instruction = (
        "You are a careful market research analyst. Never invent statistics, revenue numbers, "
        "or market shares that are not present in the research findings. Keep competitor mentions "
        "grounded in the gathered evidence, and mark uncertainties in missing_information."
    )

    brief = generate_structured(
        prompt=prompt,
        response_schema=ResearchBrief,
        system_instruction=system_instruction,
    )
    brief.competitors = brief.competitors[:2]

    real_sources = [
        f"{f.title} — {f.url}"
        for f in state.findings
        if f.source_type == "web_search" and f.url and f.url != "No URL provided"
    ]
    if real_sources:
        brief.sources = real_sources
    elif state.findings:
        brief.sources = [f"{f.title} ({f.url})" for f in state.findings]

    state.draft = brief
    return state


def run_critic(state:ResearchState) -> ResearchState:
    """Review the draft brief against the research findings and requirements."""
    if state.draft is None:
        state.critic_feedback = CriticReview(
            approved=False,
            feedback="Draft is missing. Generate a complete brief from the findings."
        )
        return state

    evidence_text = format_findings_for_prompt(state.findings)
    draft_json = state.draft.model_dump_json(indent=2)

    prompt = (
        f"Topic / Query: {state.query}\n"
        f"Current Revision Count: {state.revision_count} (Max allowed revisions: 1)\n\n"
        f"Draft Brief (JSON):\n{draft_json}\n\n"
        f"Available Research Findings:\n{evidence_text}\n\n"
        "Review Criteria:\n"
        "1. Does the brief answer the query with a clear summary, up to 2 competitors (if relevant), "
        "key observations, sources, and missing information?\n"
        "2. Are claims grounded in the research findings rather than fabricated?\n"
        "3. Are any gaps or limitations noted in missing_information?\n"
        "Set approved=True if acceptable; set approved=False only if concrete improvements are needed."
    )

    system_instruction = (
        "You are a strict research quality critic. Approve briefs that are accurate, well-structured, "
        "and honest about limitations; request targeted fixes only when material issues exist."
    )

    review = generate_structured(
        prompt=prompt,
        response_schema=CriticReview,
        system_instruction=system_instruction,
    )
    state.critic_feedback = review
    return state


def run_workflow(
        query: str,
        on_step: ProgressCallback | None = None,
) -> ResearchState:
    """Orchestrate Researcher -> Analyst -> Critic with at most one revision."""
    state = ResearchState(query=query.strip())

    def notify(stage: str) -> None:
        if on_step is not None:
            on_step(stage, state)

    notify("Orchestrator started workflow")

    run_researcher(state)
    notify("Researcher completed web search")

    run_analyst(state)
    notify("Analyst created initial draft")

    run_critic(state)
    notify("Critic reviewed initial draft")

    if state.critic_feedback and not state.critic_feedback.approved and state.revision_count < 1:
        state.revision_count += 1
        notify(f"Orchestrator triggered revision #{state.revision_count}")

        run_analyst(state)
        notify("Analyst revised draft using critic feedback")

        run_critic(state)
        notify("Critic completed final review")

    state.final_brief = state.draft
    notify("Workflow finished")
    return state