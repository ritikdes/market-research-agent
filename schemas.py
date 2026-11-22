from pydantic import BaseModel, Field

class SearchFinding(BaseModel):
    title: str
    url: str
    snippet: str
    source_type: str = Field(
        default="web_search",
        description="Whether this came from 'web_search' or 'sample_feedback'.",
    )


class CompetitorInfo(BaseModel):
    name: str
    overview: str = Field(description="Brief summary of what the competitor does and its market position.")


class ResearchBrief(BaseModel):
    topic_summary: str = Field(description="Concise summary of the company or industry.")
    competitors: list[CompetitorInfo] = Field(
        default_factory=list,
        max_length=2,
        description="Up to two relevant competitors based on available evidence.",
    )
    key_observation: list[str] = Field(
        description="Key market trends, dynamics, or findings supported by the research."
    )
    sources: list[str] = Field(
        description="List of source URLs or labeled sample references used in the brief."
    )
    missing_information: list[str] = Field(
        description="Gaps, uncertainities or data not found in the gathered evidence."
    )


class CriticReview(BaseModel):
    approved: bool = Field(
        description="True if the brief is accurate, grounded in findings and meets all sections; False if 1 revision is needed."
    )
    feedback: str = Field(
        description="Specific, actionable notes for the Analyst if revision is needed, or brief approval note."
    )


class ResearchState(BaseModel):
    query: str
    search_queries: list[str] = Field(default_factory=list)
    findings: list[SearchFinding] = Field(default_factory=list)
    draft: ResearchBrief | None = None
    critic_feedback: CriticReview | None = None
    revision_count: int = 0
    final_brief: ResearchBrief | None = None