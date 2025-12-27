"""Research Agent for deep investigation of selected topics.

This agent performs iterative research on a selected topic, gathering
facts, insights, and sources suitable for creating engaging tweets.
"""

from typing import Literal

from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langgraph.graph import END, START, StateGraph

from social_engager.prompts import COMPRESS_RESEARCH_PROMPT, RESEARCH_AGENT_SYSTEM_PROMPT
from social_engager.states.research_state import (
    CompressedResearch,
    ResearchInputState,
    ResearchOutputState,
    ResearchState,
)
from social_engager.tools import tavily_search, think_tool
from social_engager.utils import MAX_RESEARCH_ITERATIONS, get_smart_model, get_today_str

# Configuration
research_model = get_smart_model()
compress_model = get_smart_model()

tools = [tavily_search, think_tool]
tools_by_name = {tool.name: tool for tool in tools}
model_with_tools = research_model.bind_tools(tools)


async def research_llm_call(state: ResearchState) -> dict:
    """Analyze current state and decide on next research actions.

    The model analyzes the conversation state and decides whether to:
    1. Call search tools to gather more information
    2. Provide findings based on gathered information
    """
    system_prompt = RESEARCH_AGENT_SYSTEM_PROMPT.format(date=get_today_str())
    messages = [SystemMessage(content=system_prompt)] + list(
        state.get("researcher_messages", [])
    )

    # Add the research topic as initial message if starting fresh
    if len(state.get("researcher_messages", [])) == 0:
        topic = state.get("research_topic", "")
        category = state.get("topic_category", "")
        messages.append(
            HumanMessage(
                content=f"Research this topic for a tweet: {topic}\n\nCategory: {category}\n\nGather key facts, interesting insights, and sources."
            )
        )

    response = await model_with_tools.ainvoke(messages)

    return {"researcher_messages": [response]}


def research_tool_node(state: ResearchState) -> dict:
    """Execute all tool calls from the research agent."""
    messages = state.get("researcher_messages", [])
    last_message = messages[-1]

    tool_outputs = []
    raw_notes = []

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
            # Store raw notes from search results
            if tool_call["name"] == "tavily_search":
                raw_notes.append(result)

    return {
        "researcher_messages": tool_outputs,
        "raw_notes": raw_notes,
        "tool_call_iterations": state.get("tool_call_iterations", 0) + 1,
    }


async def compress_research(state: ResearchState) -> dict:
    """Compress research findings into key insights for tweet creation.

    Takes all research messages and creates a compressed summary
    suitable for generating an engaging tweet.
    """
    messages = state.get("researcher_messages", [])
    research_topic = state.get("research_topic", "")

    # Build compression prompt
    compress_prompt = COMPRESS_RESEARCH_PROMPT.format(research_topic=research_topic)

    # Use structured output for consistent format
    structured_model = compress_model.with_structured_output(CompressedResearch)

    try:
        # Include research messages as context
        context_messages = [
            SystemMessage(
                content="You are a research summarizer. Compress the research findings into key insights for tweet creation."
            )
        ]

        # Add research content
        research_content = []
        for msg in messages:
            if hasattr(msg, "content") and msg.content:
                research_content.append(str(msg.content)[:2000])

        context_messages.append(
            HumanMessage(
                content=f"{compress_prompt}\n\n<Research Content>\n{chr(10).join(research_content[-10:])}\n</Research Content>"
            )
        )

        compressed = await structured_model.ainvoke(context_messages)

        return {
            "compressed_research": compressed.summary,
            "key_insights": compressed.key_facts + compressed.tweet_angles,
        }

    except Exception as e:
        print(f"Compression failed: {e}")
        # Fallback: use raw notes
        raw_notes = state.get("raw_notes", [])
        return {
            "compressed_research": "\n".join(raw_notes)[:2000],
            "key_insights": ["Research completed but compression failed"],
        }


def should_continue_research(
    state: ResearchState,
) -> Literal["research_tool_node", "compress_research"]:
    """Determine whether to continue research or compress findings.

    Continues if:
    - The LLM made tool calls
    - We haven't exceeded max iterations

    Stops if:
    - No more tool calls
    - Max iterations reached
    """
    messages = state.get("researcher_messages", [])
    iterations = state.get("tool_call_iterations", 0)

    if not messages:
        return "compress_research"

    last_message = messages[-1]

    # Check iteration limit
    if iterations >= MAX_RESEARCH_ITERATIONS:
        return "compress_research"

    # Check for tool calls
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "research_tool_node"

    return "compress_research"


# Build the research agent graph
research_builder = StateGraph(
    ResearchState,
    input=ResearchInputState,
    output=ResearchOutputState,
)

research_builder.add_node("research_llm_call", research_llm_call)
research_builder.add_node("research_tool_node", research_tool_node)
research_builder.add_node("compress_research", compress_research)

research_builder.add_edge(START, "research_llm_call")
research_builder.add_conditional_edges(
    "research_llm_call",
    should_continue_research,
    {
        "research_tool_node": "research_tool_node",
        "compress_research": "compress_research",
    },
)
research_builder.add_edge("research_tool_node", "research_llm_call")
research_builder.add_edge("compress_research", END)

research_agent = research_builder.compile()

