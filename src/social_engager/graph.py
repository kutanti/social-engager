"""Main workflow graph for the Social Engager.

This module composes the complete workflow connecting:
1. Trend Discovery Agent
2. Research Agent
3. Tweet Generator Agent
4. Content Safety Guardrails
5. X Posting Tool
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Literal

from langchain_core.messages import HumanMessage
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command
from rich.console import Console
from rich.panel import Panel

from social_engager.agents.research_agent import research_agent
from social_engager.agents.trend_discovery import trend_discovery_agent
from social_engager.agents.tweet_generator import tweet_generator_agent
from social_engager.guardrails import (
    check_content_safety,
    check_keyword_blocklist,
    validate_tweet_content,
)
from social_engager.states.workflow_state import (
    WorkflowInputState,
    WorkflowOutputState,
    WorkflowState,
)
from social_engager.tools.x_poster import post_tweet
from social_engager.utils import get_current_dir, is_dry_run

console = Console()

# Maximum regeneration attempts for failed content
MAX_REGENERATION_ATTEMPTS = 3


def log_workflow_step(step: str, data: dict) -> None:
    """Log a workflow step for audit purposes."""
    log_dir = get_current_dir() / "logs"
    log_dir.mkdir(exist_ok=True)

    log_file = log_dir / "workflow_log.jsonl"

    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "step": step,
        "data": data,
    }

    with open(log_file, "a") as f:
        f.write(json.dumps(log_entry, default=str) + "\n")


async def discover_topic(state: WorkflowState) -> dict:
    """Run the trend discovery agent to find a topic.

    This node invokes the trend discovery subgraph to search for
    trending news and select the best topic for tweeting.
    """
    console.print(Panel("🔍 Discovering trending topics...", style="cyan"))

    try:
        result = await trend_discovery_agent.ainvoke(
            {"messages": [HumanMessage(content="Find trending positive news")]}
        )

        selected_topic = result.get("selected_topic", "")
        topic_category = result.get("topic_category", "ai")
        topic_context = result.get("topic_context", "")

        console.print(f"✅ Selected topic: [bold]{selected_topic}[/bold]")
        console.print(f"   Category: {topic_category}")

        log_workflow_step(
            "discover_topic",
            {
                "selected_topic": selected_topic,
                "topic_category": topic_category,
                "topic_context": topic_context,
            },
        )

        return {
            "selected_topic": selected_topic,
            "topic_category": topic_category,
            "topic_context": topic_context,
        }

    except Exception as e:
        console.print(f"[red]Error in topic discovery: {e}[/red]")
        log_workflow_step("discover_topic_error", {"error": str(e)})
        # Fallback topic
        return {
            "selected_topic": "The latest developments in AI agents",
            "topic_category": "ai",
            "topic_context": "Explore recent advances in AI agent technology",
        }


async def research_topic(state: WorkflowState) -> dict:
    """Run the research agent to investigate the selected topic.

    This node invokes the research subgraph to gather facts,
    insights, and sources about the selected topic.
    """
    console.print(Panel("📚 Researching topic...", style="blue"))

    topic = state.get("selected_topic", "")
    category = state.get("topic_category", "ai")

    try:
        result = await research_agent.ainvoke(
            {
                "research_topic": topic,
                "topic_category": category,
            }
        )

        research_summary = result.get("compressed_research", "")
        key_insights = result.get("key_insights", [])

        console.print(f"✅ Research complete: {len(key_insights)} insights gathered")

        log_workflow_step(
            "research_topic",
            {
                "topic": topic,
                "summary_length": len(research_summary),
                "insight_count": len(key_insights),
            },
        )

        return {
            "research_summary": research_summary,
            "key_insights": key_insights,
        }

    except Exception as e:
        console.print(f"[red]Error in research: {e}[/red]")
        log_workflow_step("research_topic_error", {"error": str(e)})
        return {
            "research_summary": f"Topic: {topic}. Unable to complete full research.",
            "key_insights": [topic],
        }


async def generate_tweet(state: WorkflowState) -> dict:
    """Run the tweet generator to create content.

    This node invokes the tweet generator subgraph to create
    an engaging tweet based on the research findings.
    """
    console.print(Panel("✍️ Generating tweet...", style="green"))

    try:
        result = await tweet_generator_agent.ainvoke(
            {
                "research_summary": state.get("research_summary", ""),
                "key_insights": state.get("key_insights", []),
                "topic_category": state.get("topic_category", "ai"),
            }
        )

        tweet = result.get("generated_tweet", "")
        style = result.get("tweet_style", "informative")

        console.print(f"✅ Tweet generated ({len(tweet)} chars)")
        console.print(Panel(tweet, title="Generated Tweet", style="yellow"))

        log_workflow_step(
            "generate_tweet",
            {
                "tweet": tweet,
                "style": style,
                "length": len(tweet),
            },
        )

        return {
            "generated_tweet": tweet,
            "tweet_style": style,
            "hashtags": result.get("hashtags", []),
        }

    except Exception as e:
        console.print(f"[red]Error generating tweet: {e}[/red]")
        log_workflow_step("generate_tweet_error", {"error": str(e)})
        return {
            "generated_tweet": "",
            "tweet_style": "error",
            "hashtags": [],
            "validation_errors": [f"Tweet generation failed: {e}"],
        }


async def validate_content(state: WorkflowState) -> dict:
    """Run all content safety guardrails.

    This node performs multi-layered safety validation:
    1. Topic validation
    2. OpenAI moderation
    3. Keyword blocklist
    """
    console.print(Panel("🛡️ Running safety checks...", style="magenta"))

    tweet = state.get("generated_tweet", "")
    topic_category = state.get("topic_category", "ai")
    errors = list(state.get("validation_errors", []))
    safety_checks = {}

    # Layer 1: Topic Validation
    console.print("  → Checking topic relevance...")
    topic_valid, topic_errors = await validate_tweet_content(tweet, topic_category)
    safety_checks["topic_validation"] = topic_valid
    if not topic_valid:
        errors.extend(topic_errors)

    # Layer 2: OpenAI Moderation
    console.print("  → Running moderation check...")
    mod_safe, mod_flags = check_content_safety(tweet)
    safety_checks["moderation_check"] = mod_safe
    if not mod_safe:
        errors.append(f"Moderation flags: {mod_flags}")

    # Layer 3: Keyword Blocklist
    console.print("  → Checking keyword blocklist...")
    keyword_clean, keyword_matches = check_keyword_blocklist(tweet)
    safety_checks["keyword_filter"] = keyword_clean
    if not keyword_clean:
        errors.extend(keyword_matches)

    is_safe = all(safety_checks.values())

    if is_safe:
        console.print("✅ All safety checks passed!")
    else:
        console.print(f"[red]⚠️ Safety issues found: {len(errors)}[/red]")
        for error in errors:
            console.print(f"   - {error}")

    log_workflow_step(
        "validate_content",
        {
            "is_safe": is_safe,
            "safety_checks": safety_checks,
            "errors": errors,
        },
    )

    return {
        "is_safe": is_safe,
        "safety_checks": safety_checks,
        "validation_errors": errors,
    }


def should_post_or_regenerate(
    state: WorkflowState,
) -> Literal["post_content", "regenerate_tweet", "__end__"]:
    """Decide whether to post, regenerate, or abort.

    Routes based on:
    - Safety validation results
    - Number of regeneration attempts
    """
    is_safe = state.get("is_safe", False)
    errors = state.get("validation_errors", [])

    # Count regeneration attempts from errors
    regen_count = sum(1 for e in errors if "Regeneration attempt" in str(e))

    if is_safe:
        return "post_content"

    if regen_count < MAX_REGENERATION_ATTEMPTS:
        return "regenerate_tweet"

    # Max attempts reached, abort
    console.print("[red]Max regeneration attempts reached. Aborting.[/red]")
    return END


async def regenerate_tweet(state: WorkflowState) -> dict:
    """Regenerate the tweet after failed validation.

    Attempts to generate a new tweet with guidance
    about what to avoid based on previous errors.
    """
    console.print(Panel("🔄 Regenerating tweet...", style="yellow"))

    errors = state.get("validation_errors", [])
    error_count = sum(1 for e in errors if "Regeneration attempt" in str(e))

    # Clear errors and add regeneration marker
    new_errors = [f"Regeneration attempt {error_count + 1}"]

    log_workflow_step(
        "regenerate_tweet",
        {
            "attempt": error_count + 1,
            "previous_errors": errors,
        },
    )

    return {
        "validation_errors": new_errors,
        "is_safe": False,  # Reset for new validation
    }


async def post_content(state: WorkflowState) -> dict:
    """Post the validated tweet to X.

    In dry run mode, logs the tweet without posting.
    """
    tweet = state.get("generated_tweet", "")
    topic = state.get("selected_topic", "")

    if is_dry_run():
        console.print(Panel("📝 DRY RUN - Tweet logged but not posted", style="yellow"))
    else:
        console.print(Panel("🚀 Posting to X...", style="green"))

    try:
        result = post_tweet.invoke({"tweet_text": tweet, "topic": topic})

        is_posted = "successfully" in result.lower() or "DRY RUN" in result
        tweet_id = ""

        if "Tweet ID:" in result:
            tweet_id = result.split("Tweet ID:")[-1].strip()

        console.print(f"✅ {result}")

        log_workflow_step(
            "post_content",
            {
                "tweet": tweet,
                "result": result,
                "is_posted": is_posted,
                "tweet_id": tweet_id,
                "dry_run": is_dry_run(),
            },
        )

        return {
            "is_posted": is_posted,
            "post_result": result,
            "tweet_id": tweet_id,
        }

    except Exception as e:
        console.print(f"[red]Error posting tweet: {e}[/red]")
        log_workflow_step("post_content_error", {"error": str(e)})
        return {
            "is_posted": False,
            "post_result": f"Error: {e}",
            "tweet_id": "",
        }


# Build the main workflow graph
workflow_builder = StateGraph(
    WorkflowState,
    input=WorkflowInputState,
    output=WorkflowOutputState,
)

# Add nodes
workflow_builder.add_node("discover_topic", discover_topic)
workflow_builder.add_node("research_topic", research_topic)
workflow_builder.add_node("generate_tweet", generate_tweet)
workflow_builder.add_node("validate_content", validate_content)
workflow_builder.add_node("regenerate_tweet", regenerate_tweet)
workflow_builder.add_node("post_content", post_content)

# Add edges
workflow_builder.add_edge(START, "discover_topic")
workflow_builder.add_edge("discover_topic", "research_topic")
workflow_builder.add_edge("research_topic", "generate_tweet")
workflow_builder.add_edge("generate_tweet", "validate_content")
workflow_builder.add_conditional_edges(
    "validate_content",
    should_post_or_regenerate,
    {
        "post_content": "post_content",
        "regenerate_tweet": "regenerate_tweet",
        END: END,
    },
)
workflow_builder.add_edge("regenerate_tweet", "generate_tweet")
workflow_builder.add_edge("post_content", END)

# Compile the workflow
social_engager_agent = workflow_builder.compile()


async def run_social_engager() -> dict:
    """Run the complete social engager workflow.

    Returns:
        Dictionary with workflow results
    """
    console.print(Panel.fit("🐦 Social Engager Agent", style="bold blue"))
    console.print(f"Mode: {'DRY RUN' if is_dry_run() else 'LIVE POSTING'}")
    console.print("")

    result = await social_engager_agent.ainvoke(
        {"messages": [HumanMessage(content="Start daily tweet generation")]}
    )

    console.print("")
    console.print(Panel.fit("✨ Workflow Complete", style="bold green"))

    return result

