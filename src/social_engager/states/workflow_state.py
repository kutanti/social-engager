"""Main workflow state that combines all phases."""

import operator
from typing import Literal

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field
from typing_extensions import Annotated, TypedDict


class WorkflowState(TypedDict):
    """Main state for the complete Social Engager workflow.

    This state flows through all phases:
    Discovery → Research → Tweet Generation → Posting
    """

    # Discovery phase
    messages: Annotated[list[BaseMessage], add_messages]
    selected_topic: str
    topic_category: str
    topic_context: str

    # Research phase
    research_summary: str
    key_insights: Annotated[list[str], operator.add]
    sources: Annotated[list[str], operator.add]

    # Tweet generation phase
    generated_tweet: str
    tweet_style: str
    hashtags: list[str]

    # Safety validation phase
    is_safe: bool
    safety_checks: dict[str, bool]
    validation_errors: Annotated[list[str], operator.add]

    # Posting phase
    is_posted: bool
    post_result: str
    tweet_id: str


class WorkflowInputState(TypedDict):
    """Input state for the workflow - just needs to be triggered."""

    messages: Annotated[list[BaseMessage], add_messages]


class WorkflowOutputState(TypedDict):
    """Output state from the complete workflow."""

    selected_topic: str
    topic_category: str
    generated_tweet: str
    is_posted: bool
    post_result: str
    tweet_id: str


class SafetyCheckResult(BaseModel):
    """Schema for safety check results."""

    is_safe: bool = Field(description="Whether the content passed all safety checks")
    topic_validation: bool = Field(description="Passed topic validation check")
    moderation_check: bool = Field(description="Passed OpenAI moderation check")
    keyword_filter: bool = Field(description="Passed keyword blocklist check")
    errors: list[str] = Field(
        description="List of any validation errors encountered",
        default_factory=list,
    )


class PostResult(BaseModel):
    """Schema for the posting result."""

    success: bool = Field(description="Whether the tweet was successfully posted")
    tweet_id: str = Field(description="The ID of the posted tweet, if successful")
    message: str = Field(description="Status message about the posting result")
    was_dry_run: bool = Field(description="Whether this was a dry run (not actually posted)")

