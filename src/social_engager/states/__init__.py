"""State definitions for the Social Engager workflow."""

from social_engager.states.discovery_state import (
    DiscoveredTopic,
    DiscoveryInputState,
    DiscoveryOutputState,
    DiscoveryState,
    TopicSelection,
)
from social_engager.states.research_state import (
    CompressedResearch,
    ResearchInputState,
    ResearchInsight,
    ResearchOutputState,
    ResearchState,
)
from social_engager.states.tweet_state import (
    TweetContent,
    TweetInputState,
    TweetOutputState,
    TweetState,
    TweetThread,
)
from social_engager.states.workflow_state import (
    PostResult,
    SafetyCheckResult,
    WorkflowInputState,
    WorkflowOutputState,
    WorkflowState,
)

__all__ = [
    # Discovery
    "DiscoveryState",
    "DiscoveryInputState",
    "DiscoveryOutputState",
    "DiscoveredTopic",
    "TopicSelection",
    # Research
    "ResearchState",
    "ResearchInputState",
    "ResearchOutputState",
    "ResearchInsight",
    "CompressedResearch",
    # Tweet
    "TweetState",
    "TweetInputState",
    "TweetOutputState",
    "TweetContent",
    "TweetThread",
    # Workflow
    "WorkflowState",
    "WorkflowInputState",
    "WorkflowOutputState",
    "SafetyCheckResult",
    "PostResult",
]

