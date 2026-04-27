"""
modules/captions/style_profile.py

Stores and loads a user's writing style profile so the caption generator
can match tone, vocabulary, sentence length, emoji usage, and CTA patterns.

The profile is persisted at <edit_dir>/style_profile.json.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path


@dataclass
class StyleProfile:
    """
    Encodes a user's writing style for use by the caption generator.

    Fields can be filled manually, learned from sample texts via analyze_style(),
    or loaded from a cached JSON file.
    """

    # Qualitative tone descriptor — drives the LLM system prompt
    tone: str = "conversational"  # e.g. "conversational", "formal", "hype", "educational"

    # Rough average words per sentence (used in generation prompt)
    avg_sentence_len: int = 15

    # Recurring phrases / words the user commonly uses
    common_phrases: list[str] = field(default_factory=list)

    # Whether the user typically uses emoji in captions
    emoji_usage: bool = False

    # How the user typically ends captions (call to action style)
    cta_style: str = ""  # e.g. "Subscribe below 👇", "Drop a comment!", "Link in bio."

    # Favourite hashtag groups per platform
    hashtags: dict[str, list[str]] = field(default_factory=dict)
    # e.g. {"youtube": [], "instagram": ["#contentcreator", "#videopro"]}

    # Raw sample texts used to derive this profile (stored for re-analysis)
    sample_texts: list[str] = field(default_factory=list)

    # Optional: creator name / brand for personalised output
    creator_name: str = ""

    # Optional: niche / topic area for contextual generation
    niche: str = ""  # e.g. "tech", "travel", "education", "gaming"


def load_style_profile(edit_dir: str | Path) -> StyleProfile | None:
    """
    Load a StyleProfile from <edit_dir>/style_profile.json.
    Returns None if the file does not exist.
    """
    path = Path(edit_dir) / "style_profile.json"
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return StyleProfile(**{k: v for k, v in data.items() if k in StyleProfile.__dataclass_fields__})


def save_style_profile(profile: StyleProfile, edit_dir: str | Path) -> Path:
    """
    Save a StyleProfile to <edit_dir>/style_profile.json.
    Creates the directory if it doesn't exist.
    """
    path = Path(edit_dir) / "style_profile.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(asdict(profile), f, indent=2, ensure_ascii=False)
    return path


def default_profile() -> StyleProfile:
    """Return a safe neutral fallback profile for use when no profile exists."""
    return StyleProfile(
        tone="conversational",
        avg_sentence_len=15,
        emoji_usage=False,
        cta_style="",
    )
