"""Trend Discovery Agent for finding positive trending news.

This agent searches for trending topics in AI and Technology,
filtering for positive and constructive content suitable for social media.
"""

from typing import Literal

from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command

from social_engager.prompts import TOPIC_SELECTION_PROMPT, TREND_DISCOVERY_SYSTEM_PROMPT
from social_engager.states.discovery_state import (
    DiscoveryInputState,
    DiscoveryOutputState,
    DiscoveryState,
    TopicSelection,
)
from social_engager.tools import tavily_news_search, think_tool
from social_engager.utils import FALLBACK_TOPICS, get_smart_model, get_today_str, get_topic_names_display

# Configuration
discovery_model = get_smart_model()
tools = [tavily_news_search, think_tool]
tools_by_name = {tool.name: tool for tool in tools}
model_with_tools = discovery_model.bind_tools(tools)


async def discover_trends(state: DiscoveryState) -> Command[Literal["process_tools", "select_topic"]]:
    """Search for trending news in target categories.

    Uses Tavily news search to find current trending topics
    with a focus on positive developments.
    """
    system_prompt = TREND_DISCOVERY_SYSTEM_PROMPT.format(date=get_today_str())
    messages = [SystemMessage(content=system_prompt)] + list(state.get("messages", []))

    # Add initial search request if this is the first iteration
    if not state.get("discovered_topics"):
        messages.append(
            HumanMessage(
                content=f"Search for the most interesting trending news today in {get_topic_names_display()}. Focus on positive developments and breakthroughs."
            )
        )

    response = await model_with_tools.ainvoke(messages)

    if response.tool_calls:
        return Command(
            goto="process_tools",
            update={"messages": [response]},
        )
    else:
        return Command(
            goto="select_topic",
            update={"messages": [response]},
        )


async def process_tools(state: DiscoveryState) -> Command[Literal["discover_trends"]]:
    """Execute tool calls from the discovery agent."""
    messages = state.get("messages", [])
    last_message = messages[-1]

    tool_outputs = []
    discovered = []

    for tool_call in last_message.tool_calls:
        tool = tools_by_name.get(tool_call["name"])
        if tool:
            result = tool.invoke(tool_call["args"])
            tool_outputs.append(
                ToolMessage(
                    content=result,
                    name=tool_call["name"],
                    tool_call_id=tool_call["id"],
                )
            )
            # Track discovered topics from search results
            if tool_call["name"] == "tavily_news_search":
                discovered.append(result[:500])  # Store summary of results

    return Command(
        goto="discover_trends",
        update={
            "messages": tool_outputs,
            "discovered_topics": discovered,
        },
    )


async def select_topic(state: DiscoveryState) -> dict:
    """Select the best topic from discovered trends.

    Uses structured output to ensure consistent topic selection format.
    Falls back to thought leadership topics if no strong trends found.
    """
    messages = state.get("messages", [])
    discovered_topics = state.get("discovered_topics", [])

    # If no topics discovered, use fallback
    if not discovered_topics:
        import random

        fallback = random.choice(FALLBACK_TOPICS)
        return {
            "selected_topic": fallback["topic"],
            "topic_category": fallback["category"],
            "topic_context": fallback["context"],
        }

    # Use structured output for topic selection
    selection_model = discovery_model.with_structured_output(TopicSelection)

    search_results = "\n\n".join(discovered_topics)
    selection_prompt = TOPIC_SELECTION_PROMPT.format(search_results=search_results)

    try:
        selection = await selection_model.ainvoke(
            [
                SystemMessage(content=TREND_DISCOVERY_SYSTEM_PROMPT.format(date=get_today_str())),
                HumanMessage(content=selection_prompt),
            ]
        )

        return {
            "selected_topic": selection.selected_topic,
            "topic_category": selection.topic_category,
            "topic_context": selection.topic_context,
        }
    except Exception as e:
        # Fallback on error
        print(f"Topic selection failed: {e}")
        import random

        fallback = random.choice(FALLBACK_TOPICS)
        return {
            "selected_topic": fallback["topic"],
            "topic_category": fallback["category"],
            "topic_context": fallback["context"],
        }


# Build the trend discovery graph
discovery_builder = StateGraph(
    DiscoveryState,
    input=DiscoveryInputState,
    output=DiscoveryOutputState,
)

discovery_builder.add_node("discover_trends", discover_trends)
discovery_builder.add_node("process_tools", process_tools)
discovery_builder.add_node("select_topic", select_topic)

discovery_builder.add_edge(START, "discover_trends")
discovery_builder.add_edge("select_topic", END)

trend_discovery_agent = discovery_builder.compile()

