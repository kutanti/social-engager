"""Content moderation using Azure OpenAI.

This module uses Azure OpenAI to check for harmful content before posting.
"""

from dataclasses import dataclass

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from social_engager.utils import get_azure_chat_model


@dataclass
class ModerationResult:
    """Result from the moderation check."""

    is_safe: bool
    flagged_categories: list[str]
    reasoning: str


class ModerationCheck(BaseModel):
    """Schema for moderation check results."""

    is_safe: bool = Field(description="Whether the content is safe to post")
    flagged_categories: list[str] = Field(
        description="List of any problematic categories detected",
        default_factory=list,
    )
    reasoning: str = Field(description="Brief explanation of the assessment")


MODERATION_PROMPT = """You are a content moderation assistant. Analyze the following text and determine if it's safe to post on social media.

Check for:
- Hate speech or discriminatory content
- Harassment or bullying
- Violence or threats
- Sexual content
- Self-harm content
- Misinformation or dangerous advice
- Spam or scam content

Text to analyze:
{text}

Respond with whether the content is safe and list any concerns."""


def check_content_safety(text: str) -> tuple[bool, list[str]]:
    """Check content safety using Azure OpenAI.

    Args:
        text: The text content to check

    Returns:
        Tuple of (is_safe, list_of_flagged_categories)
    """
    if not text or not text.strip():
        return True, []

    try:
        model = get_azure_chat_model(temperature=0)
        structured_model = model.with_structured_output(ModerationCheck)

        result = structured_model.invoke(
            [
                SystemMessage(content="You are a content safety moderator."),
                HumanMessage(content=MODERATION_PROMPT.format(text=text)),
            ]
        )

        return result.is_safe, result.flagged_categories

    except Exception as e:
        print(f"Moderation check error: {e}")
        # On error, be conservative and flag for review
        return False, [f"moderation_error: {e}"]


def get_moderation_details(text: str) -> ModerationResult:
    """Get detailed moderation results.

    Args:
        text: The text content to check

    Returns:
        ModerationResult with detailed assessment
    """
    if not text or not text.strip():
        return ModerationResult(is_safe=True, flagged_categories=[], reasoning="Empty content")

    try:
        model = get_azure_chat_model(temperature=0)
        structured_model = model.with_structured_output(ModerationCheck)

        result = structured_model.invoke(
            [
                SystemMessage(content="You are a content safety moderator."),
                HumanMessage(content=MODERATION_PROMPT.format(text=text)),
            ]
        )

        return ModerationResult(
            is_safe=result.is_safe,
            flagged_categories=result.flagged_categories,
            reasoning=result.reasoning,
        )

    except Exception as e:
        print(f"Moderation check error: {e}")
        return ModerationResult(
            is_safe=False,
            flagged_categories=["error"],
            reasoning=str(e),
        )
