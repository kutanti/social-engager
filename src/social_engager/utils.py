"""Utility functions and configuration for Social Engager."""

import os
from datetime import datetime
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI

# Load environment variables
load_dotenv()


# =============================================================================
# TOPIC CONFIGURATION - Edit this section to change allowed topics
# =============================================================================

# Define the topic categories and their details
# To add/remove topics, update this dictionary and TOPIC_CATEGORY_TYPE below
TOPIC_CONFIG = {
    "ai": {
        "name": "AI",
        "description": "Artificial Intelligence, Machine Learning, LLMs, AI applications, AI research",
        "keywords": ["ai", "artificial intelligence", "machine learning", "ml", "llm", "gpt", "model", "neural", "agent", "chatbot"],
    },
    "technology": {
        "name": "Technology",
        "description": "Tech innovations, gadgets, software, internet trends, digital transformation",
        "keywords": ["tech", "technology", "software", "hardware", "digital", "innovation", "app", "platform", "startup", "developer"],
    },
    "positive_news": {
        "name": "Positive News",
        "description": "Uplifting stories about AI/tech making the world better",
        "keywords": ["progress", "success", "breakthrough", "achievement", "advance", "improve", "benefit", "innovation"],
    },
}

# Type for topic categories - UPDATE THIS when changing TOPIC_CONFIG keys
TopicCategory = Literal["ai", "technology", "positive_news"]

# Fallback topics for thought leadership when no trending news is found
FALLBACK_TOPICS = [
    {
        "topic": "The future of AI agents in everyday applications",
        "category": "ai",
        "context": "AI agents are becoming more capable and integrated into daily workflows. Explore recent developments and their implications.",
    },
    {
        "topic": "The democratization of AI tools for creators",
        "category": "ai",
        "context": "AI tools are becoming accessible to more people. Discuss how this is enabling new forms of creativity.",
    },
    {
        "topic": "Emerging trends in edge computing and AI",
        "category": "technology",
        "context": "AI is increasingly running on edge devices. Explore how this is changing tech applications.",
    },
    {
        "topic": "The evolution of large language models",
        "category": "ai",
        "context": "LLMs continue to evolve rapidly. Discuss recent improvements and new capabilities.",
    },
]


# =============================================================================
# DERIVED VALUES - Automatically computed from TOPIC_CONFIG
# =============================================================================

def get_allowed_topics() -> list[str]:
    """Get list of allowed topic keys."""
    return list(TOPIC_CONFIG.keys())


def get_topic_keywords() -> dict[str, list[str]]:
    """Get keywords for each topic category."""
    return {key: config["keywords"] for key, config in TOPIC_CONFIG.items()}


def get_topic_names_display() -> str:
    """Get a human-readable string of topic names (e.g., 'AI and Technology')."""
    names = [config["name"] for config in TOPIC_CONFIG.values() if config["name"] != "Positive News"]
    return " and ".join(names)


def get_topic_categories_prompt() -> str:
    """Generate the topic categories section for prompts."""
    lines = []
    for key, config in TOPIC_CONFIG.items():
        lines.append(f"- **{key}**: {config['description']}")
    return "\n".join(lines)


def get_topic_keys_display() -> str:
    """Get topic keys formatted for display (e.g., 'ai/technology/positive_news')."""
    return "/".join(TOPIC_CONFIG.keys())


# Legacy constant for backwards compatibility
ALLOWED_TOPICS = get_allowed_topics()
ALLOWED_SENTIMENTS = ["positive", "neutral", "informative"]


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def get_today_str() -> str:
    """Get current date in a human-readable format."""
    return datetime.now().strftime("%a %b %-d, %Y")


def get_current_dir() -> Path:
    """Get the current directory of the module."""
    try:
        return Path(__file__).resolve().parent
    except NameError:
        return Path.cwd()


def is_dry_run() -> bool:
    """Check if the agent is running in dry run mode."""
    return os.getenv("DRY_RUN", "true").lower() == "true"


def is_debug() -> bool:
    """Check if debug mode is enabled."""
    return os.getenv("DEBUG", "false").lower() == "true"

# Azure OpenAI configuration
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY", "")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")

# Single model deployment
AZURE_GPT41_DEPLOYMENT = os.getenv("AZURE_GPT41_DEPLOYMENT", "gpt-41")

# Search configuration
MAX_SEARCH_RESULTS = 5
MAX_RESEARCH_ITERATIONS = 5


def get_azure_chat_model(
    temperature: float = 0.7,
    max_tokens: int | None = None,
) -> AzureChatOpenAI:
    """Get an Azure OpenAI chat model instance.

    Args:
        temperature: Sampling temperature (0-1).
        max_tokens: Maximum tokens in response.

    Returns:
        Configured AzureChatOpenAI instance.
    """
    kwargs = {
        "azure_deployment": AZURE_GPT41_DEPLOYMENT,
        "azure_endpoint": AZURE_OPENAI_ENDPOINT,
        "api_key": AZURE_OPENAI_API_KEY,
        "api_version": AZURE_OPENAI_API_VERSION,
        "temperature": temperature,
    }

    if max_tokens:
        kwargs["max_tokens"] = max_tokens

    return AzureChatOpenAI(**kwargs)


def get_fast_model() -> AzureChatOpenAI:
    """Get the model for quick operations."""
    return get_azure_chat_model()


def get_smart_model() -> AzureChatOpenAI:
    """Get the model for complex reasoning."""
    return get_azure_chat_model()
