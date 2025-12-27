"""Tweet Generator Agent for creating engaging social media content.

This agent takes research findings and generates engaging tweets
with adaptive styling based on the content type.
"""

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph

from social_engager.prompts import TWEET_GENERATION_PROMPT, TWEET_GENERATOR_SYSTEM_PROMPT
from social_engager.states.tweet_state import (
    TweetContent,
    TweetInputState,
    TweetOutputState,
    TweetState,
)
from social_engager.utils import get_smart_model, get_today_str

# Configuration
tweet_model = get_smart_model()


async def generate_tweet(state: TweetState) -> dict:
    """Generate an engaging tweet based on research findings.

    Uses structured output to ensure consistent tweet format
    with built-in validation fields.
    """
    research_summary = state.get("research_summary", "")
    key_insights = state.get("key_insights", [])
    topic_category = state.get("topic_category", "ai")

    # Format key insights
    insights_text = "\n".join([f"- {insight}" for insight in key_insights])

    # Build generation prompt
    generation_prompt = TWEET_GENERATION_PROMPT.format(
        topic_category=topic_category,
        research_summary=research_summary,
        key_insights=insights_text,
    )

    # Use structured output for consistent format
    structured_model = tweet_model.with_structured_output(TweetContent)

    try:
        system_prompt = TWEET_GENERATOR_SYSTEM_PROMPT.format(date=get_today_str())

        tweet_content = await structured_model.ainvoke(
            [
                SystemMessage(content=system_prompt),
                HumanMessage(content=generation_prompt),
            ]
        )

        # Format the final tweet with hashtags
        hashtags_str = " ".join([f"#{tag}" for tag in tweet_content.hashtags[:3]])
        final_tweet = tweet_content.tweet_text

        # Only add hashtags if there's room
        if len(final_tweet) + len(hashtags_str) + 1 <= 280:
            final_tweet = f"{final_tweet} {hashtags_str}".strip()

        return {
            "generated_tweet": final_tweet,
            "tweet_style": tweet_content.tweet_style,
            "hashtags": tweet_content.hashtags,
            "is_validated": tweet_content.is_on_topic,
            "validation_errors": []
            if tweet_content.is_on_topic
            else ["Self-validation failed: tweet may be off-topic"],
        }

    except Exception as e:
        print(f"Tweet generation failed: {e}")
        # Fallback: generate a simple tweet
        return await generate_fallback_tweet(state)


async def generate_fallback_tweet(state: TweetState) -> dict:
    """Generate a simple fallback tweet if structured generation fails."""
    research_summary = state.get("research_summary", "")
    topic_category = state.get("topic_category", "ai")

    # Simple prompt for fallback
    fallback_prompt = f"""Create a simple, engaging tweet about this topic:

{research_summary[:500]}

Requirements:
- Maximum 250 characters (to leave room for hashtags)
- Positive and informative tone
- Focus on the most interesting aspect
- No controversial content

Return ONLY the tweet text, nothing else."""

    try:
        response = await tweet_model.ainvoke(
            [HumanMessage(content=fallback_prompt)]
        )

        tweet_text = response.content.strip()[:250]

        # Add default hashtags based on category
        category_hashtags = {
            "ai": ["AI", "ArtificialIntelligence"],
            "science": ["Science", "Research"],
            "technology": ["Tech", "Innovation"],
            "positive_news": ["GoodNews", "Progress"],
        }

        hashtags = category_hashtags.get(topic_category, ["Tech"])
        hashtags_str = " ".join([f"#{tag}" for tag in hashtags[:2]])

        if len(tweet_text) + len(hashtags_str) + 1 <= 280:
            final_tweet = f"{tweet_text} {hashtags_str}"
        else:
            final_tweet = tweet_text

        return {
            "generated_tweet": final_tweet,
            "tweet_style": "informative",
            "hashtags": hashtags,
            "is_validated": True,
            "validation_errors": [],
        }

    except Exception as e:
        print(f"Fallback tweet generation failed: {e}")
        return {
            "generated_tweet": "",
            "tweet_style": "error",
            "hashtags": [],
            "is_validated": False,
            "validation_errors": [f"Tweet generation failed: {e}"],
        }


async def validate_tweet(state: TweetState) -> dict:
    """Perform initial validation on the generated tweet.

    This is a preliminary check before the full guardrails pipeline.
    """
    tweet = state.get("generated_tweet", "")
    validation_errors = list(state.get("validation_errors", []))

    # Check length
    if len(tweet) > 280:
        validation_errors.append(f"Tweet too long: {len(tweet)} characters")

    # Check if empty
    if not tweet.strip():
        validation_errors.append("Tweet is empty")

    # Basic content checks
    if not tweet:
        is_validated = False
    else:
        is_validated = len(validation_errors) == 0

    return {
        "is_validated": is_validated,
        "validation_errors": validation_errors,
    }


# Build the tweet generator graph
tweet_builder = StateGraph(
    TweetState,
    input=TweetInputState,
    output=TweetOutputState,
)

tweet_builder.add_node("generate_tweet", generate_tweet)
tweet_builder.add_node("validate_tweet", validate_tweet)

tweet_builder.add_edge(START, "generate_tweet")
tweet_builder.add_edge("generate_tweet", "validate_tweet")
tweet_builder.add_edge("validate_tweet", END)

tweet_generator_agent = tweet_builder.compile()

