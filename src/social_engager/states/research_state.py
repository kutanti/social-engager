"""State definitions for the research phase."""

import operator
from typing import Sequence

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field
from typing_extensions import Annotated, TypedDict


class ResearchState(TypedDict):
    """State for the research agent.

    Tracks the research process including messages, iterations,
    and accumulated findings.
    """

    researcher_messages: Annotated[Sequence[BaseMessage], add_messages]
    tool_call_iterations: int
    research_topic: str
    topic_category: str
    compressed_research: str
    raw_notes: Annotated[list[str], operator.add]
    key_insights: Annotated[list[str], operator.add]


class ResearchInputState(TypedDict):
    """Input state for the research agent."""

    research_topic: str
    topic_category: str


class ResearchOutputState(TypedDict):
    """Output state from the research agent."""

    compressed_research: str
    key_insights: Annotated[list[str], operator.add]
    raw_notes: Annotated[list[str], operator.add]


# Pydantic schemas for structured output


class ResearchInsight(BaseModel):
    """Schema for a key research insight."""

    insight: str = Field(description="A key insight or fact from the research")
    source_url: str = Field(description="URL of the source for this insight")
    source_title: str = Field(description="Title of the source")
    relevance: str = Field(description="Why this insight is relevant to the topic")


class CompressedResearch(BaseModel):
    """Schema for compressed research findings."""

    summary: str = Field(
        description="Comprehensive summary of all research findings"
    )
    key_facts: list[str] = Field(
        description="List of key facts discovered during research"
    )
    notable_quotes: list[str] = Field(
        description="Notable quotes or excerpts from sources"
    )
    sources: list[str] = Field(
        description="List of source URLs used in research"
    )
    tweet_angles: list[str] = Field(
        description="Potential angles for crafting a tweet"
    )

