"""Keyword blocklist filter for content safety.

This module provides a configurable blocklist of words and patterns
that should not appear in generated tweets.
"""

import re

# Blocked word patterns - topics to avoid
BLOCKED_PATTERNS = [
    # Politics
    r"\b(politic|politician|election|vote|voting|ballot|campaign|democrat|republican|liberal|conservative)\b",
    r"\b(congress|senate|parliament|president|prime minister|government policy)\b",
    r"\b(left-wing|right-wing|partisan|bipartisan)\b",
    # Religion
    r"\b(religious|religion|church|mosque|temple|synagogue|bible|quran|torah)\b",
    r"\b(christian|muslim|jewish|hindu|buddhist|atheist)\b",
    # Controversial/Negative
    r"\b(controversial|scandal|controversy|outrage|backlash)\b",
    r"\b(lawsuit|sued|suing|legal action|court case)\b",
    r"\b(fired|layoff|layoffs|downsizing|job cuts)\b",
    r"\b(bankrupt|bankruptcy|collapse|failure|crashed)\b",
    r"\b(hate|hating|hatred|racist|racism|sexist|sexism)\b",
    r"\b(war|warfare|military strike|bombing|attack)\b",
    # Profanity placeholder (expand as needed)
    r"\b(damn|hell|crap)\b",
    # Fear-mongering
    r"\b(dangerous|deadly|catastrophic|apocalyptic|doomsday)\b",
    r"\b(threat|threatening|menace|peril)\b",
]

# Compiled patterns for efficiency
COMPILED_PATTERNS = [re.compile(pattern, re.IGNORECASE) for pattern in BLOCKED_PATTERNS]

# Specific blocked phrases (exact match, case-insensitive)
BLOCKED_PHRASES = [
    "fake news",
    "deep state",
    "conspiracy theory",
    "culture war",
    "woke agenda",
    "cancel culture",
    "big tech censorship",
    "mainstream media",
    "political correctness",
]


def check_keyword_blocklist(text: str) -> tuple[bool, list[str]]:
    """Check if text contains any blocked words or patterns.

    Args:
        text: The text to check

    Returns:
        Tuple of (is_clean, list_of_matched_patterns)
    """
    if not text:
        return True, []

    matched_patterns = []
    text_lower = text.lower()

    # Check regex patterns
    for i, pattern in enumerate(COMPILED_PATTERNS):
        if pattern.search(text):
            # Get the original pattern for reporting
            matched_patterns.append(f"Pattern: {BLOCKED_PATTERNS[i]}")

    # Check exact phrases
    for phrase in BLOCKED_PHRASES:
        if phrase.lower() in text_lower:
            matched_patterns.append(f"Phrase: {phrase}")

    return len(matched_patterns) == 0, matched_patterns


def get_blocklist_summary() -> dict:
    """Get a summary of the blocklist configuration.

    Returns:
        Dictionary with blocklist statistics
    """
    return {
        "pattern_count": len(BLOCKED_PATTERNS),
        "phrase_count": len(BLOCKED_PHRASES),
        "categories": [
            "politics",
            "religion",
            "controversial",
            "negative",
            "fear-mongering",
        ],
    }


def add_blocked_pattern(pattern: str) -> None:
    """Add a new blocked pattern to the blocklist.

    Args:
        pattern: Regex pattern to add
    """
    BLOCKED_PATTERNS.append(pattern)
    COMPILED_PATTERNS.append(re.compile(pattern, re.IGNORECASE))


def add_blocked_phrase(phrase: str) -> None:
    """Add a new blocked phrase to the blocklist.

    Args:
        phrase: Exact phrase to block
    """
    BLOCKED_PHRASES.append(phrase)


def check_all_filters(text: str) -> tuple[bool, list[str]]:
    """Run all keyword-based filters on the text.

    This is a convenience function that runs all keyword checks.

    Args:
        text: The text to check

    Returns:
        Tuple of (is_clean, list_of_all_issues)
    """
    is_clean, issues = check_keyword_blocklist(text)
    return is_clean, issues

