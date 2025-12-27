"""State definitions for the trend discovery phase."""

import operator

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field
from typing_extensions import Annotated, TypedDict

from social_engager.utils import TopicCategory


class DiscoveryState(TypedDict):
    """State for the trend discovery agent.

    Tracks the discovery process including messages, discovered topics,
    and the selected topic for research.
    """

    messages: Annotated[list[BaseMessage], add_messages]
    discovered_topics: Annotated[list[str], operator.add]
    selected_topic: str
    topic_category: str
    topic_context: str


class DiscoveryInputState(TypedDict):
    """Input state for the discovery agent."""

    messages: Annotated[list[BaseMessage], add_messages]


class DiscoveryOutputState(TypedDict):
    """Output state from the discovery agent."""

    selected_topic: str
    topic_category: str
    topic_context: str


# Pydantic schemas for structured output


class DiscoveredTopic(BaseModel):
    """Schema for a discovered trending topic."""

    title: str = Field(description="The topic title or headline")
    category: TopicCategory = Field(
        description="The category this topic belongs to"
    )
    relevance_score: int = Field(
        description="How relevant/trending this topic is (1-10)", ge=1, le=10
    )
    summary: str = Field(description="Brief summary of why this topic is interesting")
    is_positive: bool = Field(
        description="Whether this topic has a positive/constructive angle"
    )


class TopicSelection(BaseModel):
    """Schema for the final topic selection."""

    selected_topic: str = Field(description="The selected topic to research and tweet about")
    topic_category: TopicCategory = Field(
        description="The category of the selected topic"
    )
    topic_context: str = Field(
        description="Context and key points about the topic for research"
    )
    selection_reasoning: str = Field(
        description="Why this topic was selected over others"
    )

