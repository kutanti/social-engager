"""State definitions for the tweet generation phase."""

from typing import Literal

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field
from typing_extensions import Annotated, TypedDict


class TweetState(TypedDict):
    """State for the tweet generator agent.

    Tracks the tweet generation process including research context,
    generated content, and safety validation results.
    """

    messages: Annotated[list[BaseMessage], add_messages]
    research_summary: str
    key_insights: list[str]
    topic_category: str
    generated_tweet: str
    tweet_style: str
    hashtags: list[str]
    is_validated: bool
    validation_errors: list[str]


class TweetInputState(TypedDict):
    """Input state for the tweet generator."""

    research_summary: str
    key_insights: list[str]
    topic_category: str


class TweetOutputState(TypedDict):
    """Output state from the tweet generator."""

    generated_tweet: str
    tweet_style: str
    hashtags: list[str]
    is_validated: bool


# Pydantic schemas for structured output


class TweetContent(BaseModel):
    """Schema for generated tweet content with validation fields."""

    topic_category: Literal["ai", "science", "technology", "positive_news"] = Field(
        description="The category this tweet belongs to"
    )
    tweet_text: str = Field(
        description="The tweet text (max 280 characters)",
        max_length=280,
    )
    sentiment: Literal["positive", "neutral", "informative"] = Field(
        description="The sentiment/tone of the tweet"
    )
    tweet_style: Literal[
        "breaking_news", "educational", "thought_leadership", "conversation_starter"
    ] = Field(description="The style of the tweet")
    hashtags: list[str] = Field(
        description="Relevant hashtags for the tweet (without # symbol)",
        max_length=5,
    )
    source_attribution: str = Field(
        description="Brief source attribution or link to include"
    )
    is_on_topic: bool = Field(
        description="Self-validation: Is this tweet on-topic for the allowed categories?"
    )
    confidence_score: int = Field(
        description="Confidence that this tweet is appropriate and engaging (1-10)",
        ge=1,
        le=10,
    )


class TweetThread(BaseModel):
    """Schema for a tweet thread (multiple connected tweets)."""

    tweets: list[str] = Field(
        description="List of tweets in the thread (each max 280 chars)"
    )
    topic_category: Literal["ai", "science", "technology", "positive_news"] = Field(
        description="The category this thread belongs to"
    )
    hashtags: list[str] = Field(description="Hashtags for the thread")
    is_on_topic: bool = Field(description="Self-validation for topic relevance")

