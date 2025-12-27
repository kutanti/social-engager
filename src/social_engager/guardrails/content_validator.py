"""Content validation guardrails for topic and sentiment checking.

This module validates that generated tweets stay within allowed topics
and maintain appropriate sentiment.
"""

from typing import Literal

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from social_engager.prompts import CONTENT_VALIDATION_PROMPT
from social_engager.utils import ALLOWED_SENTIMENTS, ALLOWED_TOPICS, get_fast_model

# Configuration
validation_model = get_fast_model()


class ContentValidationResult(BaseModel):
    """Schema for content validation results."""

    is_on_topic: bool = Field(
        description="Whether the content is on-topic for allowed categories"
    )
    detected_category: str = Field(
        description="The detected topic category of the content"
    )
    detected_sentiment: str = Field(
        description="The detected sentiment of the content"
    )
    is_appropriate: bool = Field(
        description="Whether the content is appropriate for posting"
    )
    concerns: list[str] = Field(
        description="List of any concerns about the content",
        default_factory=list,
    )
    confidence: int = Field(
        description="Confidence score for the validation (1-10)",
        ge=1,
        le=10,
    )


def validate_topic_category(category: str) -> tuple[bool, str]:
    """Validate that a topic category is allowed.

    Args:
        category: The topic category to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if category.lower() in ALLOWED_TOPICS:
        return True, ""
    return False, f"Invalid topic category: {category}. Allowed: {ALLOWED_TOPICS}"


def validate_sentiment(sentiment: str) -> tuple[bool, str]:
    """Validate that a sentiment is allowed.

    Args:
        sentiment: The sentiment to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if sentiment.lower() in ALLOWED_SENTIMENTS:
        return True, ""
    return False, f"Invalid sentiment: {sentiment}. Allowed: {ALLOWED_SENTIMENTS}"


async def validate_tweet_content(
    tweet: str,
    topic_category: str,
) -> tuple[bool, list[str]]:
    """Validate tweet content using LLM-based analysis.

    This function uses an LLM to verify that the tweet:
    1. Is on-topic for the specified category
    2. Has appropriate sentiment
    3. Doesn't contain controversial content
    4. Is suitable for posting

    Args:
        tweet: The tweet text to validate
        topic_category: The expected topic category

    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []

    # Basic validation
    if not tweet or not tweet.strip():
        return False, ["Tweet is empty"]

    if len(tweet) > 280:
        errors.append(f"Tweet exceeds 280 characters: {len(tweet)}")

    # LLM-based content validation
    try:
        structured_model = validation_model.with_structured_output(
            ContentValidationResult
        )

        validation_prompt = CONTENT_VALIDATION_PROMPT.format(
            tweet=tweet,
            topic_category=topic_category,
        )

        result = await structured_model.ainvoke(
            [
                SystemMessage(
                    content="You are a content validator. Check if this tweet is appropriate for posting on social media."
                ),
                HumanMessage(content=validation_prompt),
            ]
        )

        # Check validation results
        if not result.is_on_topic:
            errors.append(
                f"Content is off-topic. Detected: {result.detected_category}, Expected: {topic_category}"
            )

        if not result.is_appropriate:
            errors.append("Content flagged as inappropriate")

        if result.concerns:
            errors.extend(result.concerns)

        if result.confidence < 5:
            errors.append(f"Low confidence in content quality: {result.confidence}/10")

        return len(errors) == 0, errors

    except Exception as e:
        # On error, be conservative and flag for review
        print(f"Content validation error: {e}")
        return False, [f"Validation error: {e}"]


def quick_topic_check(tweet: str, topic_category: str) -> tuple[bool, list[str]]:
    """Perform quick keyword-based topic validation.

    This is a fast, synchronous check that doesn't require LLM calls.
    Use for preliminary filtering before full validation.

    Args:
        tweet: The tweet text to check
        topic_category: The expected topic category

    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    tweet_lower = tweet.lower()

    # Category-specific keywords that should be present
    category_keywords = {
        "ai": ["ai", "artificial intelligence", "machine learning", "ml", "llm", "gpt", "model", "neural"],
        "science": ["science", "research", "study", "discovery", "experiment", "scientist", "breakthrough"],
        "technology": ["tech", "technology", "software", "hardware", "digital", "innovation", "app", "platform"],
        "positive_news": ["progress", "success", "breakthrough", "achievement", "advance", "improve", "benefit"],
    }

    # Check if any category keywords are present
    keywords = category_keywords.get(topic_category.lower(), [])
    has_keyword = any(keyword in tweet_lower for keyword in keywords)

    if not has_keyword:
        errors.append(
            f"Tweet may not be on-topic for {topic_category}. No category keywords found."
        )

    return len(errors) == 0, errors

