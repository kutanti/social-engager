"""Utility functions and configuration for Social Engager."""

import os
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI

# Load environment variables
load_dotenv()


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


# Configuration constants
ALLOWED_TOPICS = ["ai", "science", "technology", "positive_news"]
ALLOWED_SENTIMENTS = ["positive", "neutral", "informative"]

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
