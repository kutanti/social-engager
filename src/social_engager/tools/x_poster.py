"""X (Twitter) posting tool using Tweepy."""

import json
import os
from datetime import datetime
from pathlib import Path

import tweepy
from langchain_core.tools import tool

from social_engager.utils import get_current_dir, is_dry_run


def get_x_client() -> tweepy.Client:
    """Get an authenticated Tweepy client for X API v2."""
    return tweepy.Client(
        consumer_key=os.getenv("X_API_KEY"),
        consumer_secret=os.getenv("X_API_SECRET"),
        access_token=os.getenv("X_ACCESS_TOKEN"),
        access_token_secret=os.getenv("X_ACCESS_TOKEN_SECRET"),
        bearer_token=os.getenv("X_BEARER_TOKEN"),
    )


def log_tweet(
    tweet_text: str,
    tweet_id: str | None,
    status: str,
    topic: str = "",
    metadata: dict | None = None,
) -> None:
    """Log a tweet to the audit log file."""
    log_dir = get_current_dir() / "logs"
    log_dir.mkdir(exist_ok=True)

    log_file = log_dir / "tweet_log.jsonl"

    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "tweet_text": tweet_text,
        "tweet_id": tweet_id,
        "status": status,
        "topic": topic,
        "metadata": metadata or {},
    }

    with open(log_file, "a") as f:
        f.write(json.dumps(log_entry) + "\n")


@tool(parse_docstring=True)
def post_tweet(
    tweet_text: str,
    topic: str = "",
) -> str:
    """Post a tweet to X (Twitter).

    This tool posts a tweet using the X API v2. In dry run mode,
    it will only log the tweet without actually posting.

    Args:
        tweet_text: The text of the tweet to post (max 280 characters)
        topic: The topic category for logging purposes

    Returns:
        Status message indicating success or failure
    """
    # Validate tweet length
    if len(tweet_text) > 280:
        error_msg = f"Tweet too long: {len(tweet_text)} characters (max 280)"
        log_tweet(tweet_text, None, "rejected", topic, {"error": error_msg})
        return error_msg

    # Check for dry run mode
    if is_dry_run():
        log_tweet(tweet_text, "DRY_RUN", "dry_run", topic)
        return f"[DRY RUN] Tweet logged but not posted:\n\n{tweet_text}"

    try:
        # Post the tweet
        client = get_x_client()
        response = client.create_tweet(text=tweet_text)

        tweet_id = response.data.get("id") if response.data else None

        log_tweet(
            tweet_text,
            tweet_id,
            "posted",
            topic,
            {"response": str(response.data)},
        )

        return f"Tweet posted successfully! Tweet ID: {tweet_id}"

    except tweepy.TweepyException as e:
        error_msg = f"Failed to post tweet: {e}"
        log_tweet(tweet_text, None, "failed", topic, {"error": str(e)})
        return error_msg


def post_thread(tweets: list[str], topic: str = "") -> str:
    """Post a thread of tweets to X.

    Args:
        tweets: List of tweet texts to post as a thread
        topic: The topic category for logging purposes

    Returns:
        Status message indicating success or failure
    """
    if is_dry_run():
        for i, tweet in enumerate(tweets):
            log_tweet(tweet, f"DRY_RUN_THREAD_{i}", "dry_run", topic)
        return f"[DRY RUN] Thread of {len(tweets)} tweets logged but not posted"

    try:
        client = get_x_client()
        tweet_ids = []
        reply_to_id = None

        for i, tweet_text in enumerate(tweets):
            if len(tweet_text) > 280:
                return f"Tweet {i+1} too long: {len(tweet_text)} characters"

            response = client.create_tweet(
                text=tweet_text,
                in_reply_to_tweet_id=reply_to_id,
            )

            tweet_id = response.data.get("id") if response.data else None
            tweet_ids.append(tweet_id)
            reply_to_id = tweet_id

            log_tweet(
                tweet_text,
                tweet_id,
                "posted",
                topic,
                {"thread_position": i + 1, "reply_to": reply_to_id},
            )

        return f"Thread posted successfully! Tweet IDs: {tweet_ids}"

    except tweepy.TweepyException as e:
        error_msg = f"Failed to post thread: {e}"
        log_tweet(str(tweets), None, "failed", topic, {"error": str(e)})
        return error_msg

