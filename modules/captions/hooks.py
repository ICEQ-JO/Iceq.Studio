"""
modules/captions/hooks.py

Hook scoring for titles, descriptions, and thumbnails.

Reads the packed transcript and EDL to find high-impact quotes per chapter/beat.
A "hook" is a short transcript excerpt that is likely to stop a scroll:
- contains specifics (numbers, questions, strong verbs)
- is early in a chapter (prime retention window)
- is not too long (ideal YouTube title length)
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class HookCandidate:
    text: str
    beat: str
    output_offset_s: float
    score: float


def _clean_quote(text: str) -> str:
    """Remove filler words and normalize whitespace."""
    text = re.sub(r"\s+", " ", text).strip()
    # Trim to a reasonable title length
    if len(text) > 80:
        text = text[:80].rsplit(" ", 1)[0] + "..."
    return text


def _score_quote(text: str, position_in_chapter: float) -> float:
    """
    Score a quote excerpt for use as a title/hook.

    Higher is better. Factors:
      - length (penalize very short or very long)
      - contains number (boost)
      - contains question word or question mark (boost)
      - contains strong verbs (boost)
      - position in chapter (earlier is better, but not right at the start)
    """
    score = 0.0
    words = text.split()
    n = len(words)

    # Length sweet spot: 6-12 words
    if 6 <= n <= 12:
        score += 2.0
    elif 4 <= n <= 15:
        score += 1.0
    else:
        score -= 1.0

    # Numbers add specificity
    if re.search(r"\d", text):
        score += 1.5

    # Questions create curiosity gap
    if "?" in text or re.search(r"^(why|how|what|when|where|who|which)\b", text, re.IGNORECASE):
        score += 1.5

    # Strong verbs
    strong_verbs = {
        "built", "fixed", "solved", "crashed", "hacked", "designed", "shipped",
        "discovered", "proved", "destroyed", "transformed", "mastered", "escaped",
    }
    if any(w.lower().rstrip(".,!?") in strong_verbs for w in words):
        score += 1.0

    # Position: slightly prefer the first third of the chapter
    if position_in_chapter <= 0.33:
        score += 1.0
    elif position_in_chapter <= 0.66:
        score += 0.5

    return score


def extract_hooks(
    packed_transcript: str,
    edl_path: str | Path | None = None,
    top_n: int = 5,
) -> list[HookCandidate]:
    """
    Extract top hook candidates from a packed transcript, optionally guided by EDL beats.

    Args:
        packed_transcript: Plain transcript text (ideally from takes_packed.md).
        edl_path: Optional path to edl.json. If provided, beats are used to segment
                  the transcript and pick one hook per beat.
        top_n: Maximum number of candidates to return.

    Returns:
        List of HookCandidate, sorted by score descending.
    """
    edl: dict[str, Any] = {}
    if edl_path and Path(edl_path).exists():
        with Path(edl_path).open("r", encoding="utf-8") as f:
            edl = json.load(f)

    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", packed_transcript) if s.strip()]
    candidates: list[HookCandidate] = []

    ranges = edl.get("ranges", [])
    if ranges:
        # Segment sentences into beats based on proportional time.
        # We approximate by mapping sentence index to output timeline position.
        total_duration = float(edl.get("total_duration_s", 0)) or sum(
            float(seg["end"]) - float(seg["start"]) for seg in ranges
        )

        # Build a mapping from cumulative output time → beat
        beat_at_offset: list[tuple[float, str]] = []
        cumulative = 0.0
        for seg in ranges:
            beat = seg.get("beat", "SECTION").upper() or "SECTION"
            dur = float(seg["end"]) - float(seg["start"])
            beat_at_offset.append((cumulative, beat))
            cumulative += dur

        # Assign each sentence to a beat based on its relative position
        n = len(sentences)
        for i, sentence in enumerate(sentences):
            rel = i / max(n - 1, 1)
            offset = rel * total_duration
            # Find current beat
            current_beat = beat_at_offset[-1][1] if beat_at_offset else "SECTION"
            for j in range(len(beat_at_offset) - 1, -1, -1):
                if beat_at_offset[j][0] <= offset:
                    current_beat = beat_at_offset[j][1]
                    break

            # Estimate position within the beat (rough)
            position_in_chapter = 0.5
            if len(beat_at_offset) > 1:
                position_in_chapter = (offset % (total_duration / len(beat_at_offset))) / (
                    total_duration / len(beat_at_offset)
                )

            score = _score_quote(sentence, position_in_chapter)
            candidates.append(
                HookCandidate(
                    text=_clean_quote(sentence),
                    beat=current_beat,
                    output_offset_s=offset,
                    score=score,
                )
            )
    else:
        # No EDL: score all sentences as one chapter
        n = len(sentences)
        for i, sentence in enumerate(sentences):
            position = i / max(n - 1, 1)
            score = _score_quote(sentence, position)
            candidates.append(
                HookCandidate(
                    text=_clean_quote(sentence),
                    beat="SECTION",
                    output_offset_s=0.0,
                    score=score,
                )
            )

    # Deduplicate and sort
    seen: set[str] = set()
    unique: list[HookCandidate] = []
    for c in sorted(candidates, key=lambda x: x.score, reverse=True):
        if c.text not in seen:
            seen.add(c.text)
            unique.append(c)

    return unique[:top_n]


def top_hook_per_beat(
    packed_transcript: str,
    edl_path: str | Path,
) -> dict[str, HookCandidate | None]:
    """
    Return the best hook candidate for each beat label in the EDL.

    Useful for chapter titles or thumbnail copy.
    """
    edl_path = Path(edl_path)
    if not edl_path.exists():
        return {}

    all_hooks = extract_hooks(packed_transcript, edl_path, top_n=100)
    per_beat: dict[str, HookCandidate | None] = {}
    for hook in all_hooks:
        beat = hook.beat
        if beat not in per_beat or (per_beat[beat] and hook.score > per_beat[beat].score):
            per_beat[beat] = hook
    return per_beat
