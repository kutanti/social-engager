"""Command-line interface for the Social Engager agent.

This module provides CLI commands for running the social engager
in various modes and configurations.
"""

import argparse
import asyncio
import os
import sys

from dotenv import load_dotenv
from rich.console import Console

# Load environment variables
load_dotenv()

console = Console()


def check_environment() -> bool:
    """Check that required environment variables are set.

    Returns:
        True if all required variables are set, False otherwise
    """
    # Azure OpenAI is required for the main LLM
    azure_vars = [
        ("AZURE_OPENAI_ENDPOINT", "Azure OpenAI endpoint URL"),
        ("AZURE_OPENAI_API_KEY", "Azure OpenAI API key"),
        ("AZURE_GPT41_DEPLOYMENT", "Azure GPT-4.1 deployment name"),
    ]

    required_vars = [
        ("TAVILY_API_KEY", "Tavily API key for news search"),
    ]

    # X API keys are optional if in dry run mode
    x_vars = [
        ("X_API_KEY", "X API key"),
        ("X_API_SECRET", "X API secret"),
        ("X_ACCESS_TOKEN", "X access token"),
        ("X_ACCESS_TOKEN_SECRET", "X access token secret"),
    ]

    missing = []

    # Check Azure OpenAI vars
    for var, description in azure_vars:
        if not os.getenv(var):
            missing.append(f"  - {var}: {description}")

    # Check other required vars
    for var, description in required_vars:
        if not os.getenv(var):
            missing.append(f"  - {var}: {description}")

    dry_run = os.getenv("DRY_RUN", "true").lower() == "true"

    if not dry_run:
        for var, description in x_vars:
            if not os.getenv(var):
                missing.append(f"  - {var}: {description}")

    if missing:
        console.print("[red]Missing required environment variables:[/red]")
        for m in missing:
            console.print(m)
        console.print("\nCopy env.example to .env and fill in your API keys.")
        return False

    return True


async def run_once() -> int:
    """Run the social engager workflow once.

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    from social_engager.graph import run_social_engager

    try:
        result = await run_social_engager()

        if result.get("is_posted") or "DRY RUN" in result.get("post_result", ""):
            return 0
        else:
            console.print("[red]Workflow completed but posting failed[/red]")
            return 1

    except Exception as e:
        console.print(f"[red]Error running workflow: {e}[/red]")
        return 1


def main() -> int:
    """Main entry point for the CLI.

    Returns:
        Exit code
    """
    parser = argparse.ArgumentParser(
        description="Social Engager - AI-powered tweet generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  social-engager                    Run in dry-run mode (default)
  social-engager --live             Run with live posting to X
  social-engager --dry-run          Explicitly run in dry-run mode

Environment Variables:
  DRY_RUN=true/false    Control posting behavior
  DEBUG=true/false      Enable verbose logging
        """,
    )

    parser.add_argument(
        "--live",
        action="store_true",
        help="Enable live posting to X (overrides DRY_RUN env var)",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run in dry-run mode without posting (default)",
    )

    parser.add_argument(
        "--check",
        action="store_true",
        help="Check environment configuration and exit",
    )

    args = parser.parse_args()

    # Handle --live and --dry-run flags
    if args.live:
        os.environ["DRY_RUN"] = "false"
    elif args.dry_run:
        os.environ["DRY_RUN"] = "true"

    # Check environment
    if not check_environment():
        return 1

    if args.check:
        console.print("[green]Environment configuration is valid![/green]")
        dry_run = os.getenv("DRY_RUN", "true").lower() == "true"
        console.print(f"Mode: {'DRY RUN' if dry_run else 'LIVE POSTING'}")
        return 0

    # Run the workflow
    return asyncio.run(run_once())


if __name__ == "__main__":
    sys.exit(main())
