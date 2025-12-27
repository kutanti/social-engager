"""Tavily search tool for web research."""

import os
from typing import Literal

from langchain_core.messages import HumanMessage
from langchain_core.tools import InjectedToolArg, tool
from pydantic import BaseModel, Field
from tavily import TavilyClient
from typing_extensions import Annotated

from social_engager.utils import get_fast_model, get_today_str

# Initialize Tavily client
tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

# Summarization model for compressing search results (using fast model)
summarization_model = get_fast_model()


class Summary(BaseModel):
    """Schema for webpage content summarization."""

    summary: str = Field(description="Concise summary of the webpage content")
    key_excerpts: str = Field(
        description="Important quotes and excerpts from the content"
    )


SUMMARIZE_WEBPAGE_PROMPT = """Summarize this webpage content for social media research.

<webpage_content>
{webpage_content}
</webpage_content>

Focus on:
1. The main topic or announcement
2. Key facts and statistics
3. Notable quotes
4. Why this is newsworthy

Today's date is {date}.
"""


def summarize_webpage_content(webpage_content: str) -> str:
    """Summarize webpage content using the summarization model."""
    try:
        structured_model = summarization_model.with_structured_output(Summary)
        summary = structured_model.invoke(
            [
                HumanMessage(
                    content=SUMMARIZE_WEBPAGE_PROMPT.format(
                        webpage_content=webpage_content, date=get_today_str()
                    )
                )
            ]
        )
        return (
            f"<summary>\n{summary.summary}\n</summary>\n\n"
            f"<key_excerpts>\n{summary.key_excerpts}\n</key_excerpts>"
        )
    except Exception as e:
        print(f"Failed to summarize webpage: {e}")
        return (
            webpage_content[:1000] + "..."
            if len(webpage_content) > 1000
            else webpage_content
        )


def deduplicate_search_results(search_results: list[dict]) -> dict:
    """Deduplicate search results by URL."""
    unique_results = {}
    for response in search_results:
        for result in response.get("results", []):
            url = result.get("url")
            if url and url not in unique_results:
                unique_results[url] = result
    return unique_results


def process_search_results(unique_results: dict) -> dict:
    """Process search results by summarizing content where available."""
    summarized_results = {}
    for url, result in unique_results.items():
        if not result.get("raw_content"):
            content = result.get("content", "")
        else:
            content = summarize_webpage_content(result["raw_content"])

        summarized_results[url] = {
            "title": result.get("title", ""),
            "content": content,
        }
    return summarized_results


def format_search_output(summarized_results: dict) -> str:
    """Format search results into a well-structured string output."""
    if not summarized_results:
        return "No valid search results found. Please try different search queries."

    formatted_output = "Search results:\n\n"
    for i, (url, result) in enumerate(summarized_results.items(), 1):
        formatted_output += f"\n--- SOURCE {i}: {result['title']} ---\n"
        formatted_output += f"URL: {url}\n\n"
        formatted_output += f"SUMMARY:\n{result['content']}\n\n"
        formatted_output += "-" * 80 + "\n"

    return formatted_output


@tool(parse_docstring=True)
def tavily_search(
    query: str,
    max_results: Annotated[int, InjectedToolArg] = 5,
    topic: Annotated[
        Literal["general", "news", "finance"], InjectedToolArg
    ] = "news",
) -> str:
    """Search the web for information using Tavily API.

    This tool searches for current news and information about a given topic.
    Best for finding trending news, recent developments, and factual information.

    Args:
        query: The search query to execute
        max_results: Maximum number of results to return (default: 5)
        topic: Topic filter - 'general', 'news', or 'finance' (default: 'news')

    Returns:
        Formatted string of search results with summaries
    """
    try:
        # Execute search
        search_result = tavily_client.search(
            query,
            max_results=max_results,
            include_raw_content=True,
            topic=topic,
        )

        # Process results
        unique_results = deduplicate_search_results([search_result])
        summarized_results = process_search_results(unique_results)

        return format_search_output(summarized_results)

    except Exception as e:
        return f"Search failed: {e}. Please try a different query."


@tool(parse_docstring=True)
def tavily_news_search(
    query: str,
    days: int = 3,
) -> str:
    """Search for recent news articles using Tavily API.

    This tool specifically searches for news articles from the past few days.
    Best for finding trending and breaking news stories.

    Args:
        query: The search query for news articles
        days: How many days back to search (default: 3)

    Returns:
        Formatted string of news search results
    """
    try:
        # Execute news search
        search_result = tavily_client.search(
            query,
            max_results=5,
            include_raw_content=True,
            topic="news",
            days=days,
        )

        # Process results
        unique_results = deduplicate_search_results([search_result])
        summarized_results = process_search_results(unique_results)

        return format_search_output(summarized_results)

    except Exception as e:
        return f"News search failed: {e}. Please try a different query."

