"""
modules/captions/generator.py

Style-aware caption, title, and description generator.

Supports two LLM backends:
  - openai  (GPT-4o by default)
  - anthropic (claude-3-5-sonnet by default)

Backend is selected from the CAPTION_LLM_BACKEND env var (default: openai).

All functions work without an LLM key — they fall back to a rule-based
heuristic generator so the pipeline is never fully blocked.

CLI usage:
    python -m modules.captions generate \\
        --edit-dir /path/to/edit/ \\
        --platform youtube

    python -m modules.captions analyze-style \\
        --edit-dir /path/to/edit/ \\
        --samples "sample text 1" "sample text 2"
"""

from __future__ import annotations

import json
import os
import re
import textwrap
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv

from .style_profile import StyleProfile, default_profile, load_style_profile, save_style_profile

load_dotenv(dotenv_path=Path(__file__).resolve().parents[2] / ".env")

Platform = Literal["youtube", "instagram", "linkedin", "twitter", "tiktok"]
LLMBackend = Literal["openai", "anthropic", "none"]

# ─────────────────────────────────────────────────────────────────────────────
# LLM helpers
# ─────────────────────────────────────────────────────────────────────────────

def _active_backend() -> LLMBackend:
    backend = os.getenv("CAPTION_LLM_BACKEND", "").lower()
    if backend in ("openai", "anthropic"):
        return backend  # type: ignore[return-value]
    if os.getenv("OPENAI_API_KEY"):
        return "openai"
    if os.getenv("ANTHROPIC_API_KEY"):
        return "anthropic"
    return "none"


def _llm_call(system: str, user: str) -> str:
    """Call the configured LLM backend. Returns the assistant reply as a string."""
    backend = _active_backend()

    if backend == "openai":
        from openai import OpenAI  # type: ignore[import]
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        resp = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            max_tokens=2048,
            temperature=0.7,
        )
        return resp.choices[0].message.content or ""

    if backend == "anthropic":
        import anthropic as ant  # type: ignore[import]
        client = ant.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        resp = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=2048,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return resp.content[0].text  # type: ignore[index]

    # Fallback: return empty so callers use rule-based path
    return ""


# ─────────────────────────────────────────────────────────────────────────────
# Style analysis
# ─────────────────────────────────────────────────────────────────────────────

def analyze_style(sample_texts: list[str]) -> StyleProfile:
    """
    Derive a StyleProfile from a list of sample texts written by the user.

    With an LLM key: uses the model to infer tone, emoji usage, CTA style,
    and common phrases from the samples.

    Without a key: applies simple heuristics (sentence length, emoji regex, etc.)
    """
    if not sample_texts:
        return default_profile()

    combined = "\n\n---\n\n".join(sample_texts)

    system = textwrap.dedent("""
        You are a writing-style analyst. Analyze the provided texts and return
        a JSON object with these fields:
          tone          (string: conversational|formal|hype|educational|storytelling)
          avg_sentence_len (int: average words per sentence)
          emoji_usage   (bool: does the author use emoji?)
          cta_style     (string: their typical call-to-action phrase, or "")
          common_phrases (list[str]: 3-5 recurring expressions or vocabulary choices)
          niche         (string: best guess at topic area, or "")

        Return ONLY valid JSON, no prose, no markdown fences.
    """).strip()

    raw = _llm_call(system, f"Sample texts from this creator:\n\n{combined}")

    profile = default_profile()
    profile.sample_texts = sample_texts

    if raw:
        try:
            data = json.loads(raw)
            if isinstance(data.get("tone"), str):
                profile.tone = data["tone"]
            if isinstance(data.get("avg_sentence_len"), int):
                profile.avg_sentence_len = data["avg_sentence_len"]
            if isinstance(data.get("emoji_usage"), bool):
                profile.emoji_usage = data["emoji_usage"]
            if isinstance(data.get("cta_style"), str):
                profile.cta_style = data["cta_style"]
            if isinstance(data.get("common_phrases"), list):
                profile.common_phrases = data["common_phrases"]
            if isinstance(data.get("niche"), str):
                profile.niche = data["niche"]
        except (json.JSONDecodeError, KeyError):
            pass  # Fall through to heuristics below
    else:
        # Rule-based heuristics
        words = combined.split()
        sentences = re.split(r"[.!?]+", combined)
        sentences = [s.strip() for s in sentences if s.strip()]
        profile.avg_sentence_len = len(words) // max(len(sentences), 1)
        profile.emoji_usage = bool(re.search(r"[\U0001F300-\U0001FAFF]", combined))
        profile.niche = ""  # cannot infer without LLM

    return profile


# ─────────────────────────────────────────────────────────────────────────────
# Generation functions
# ─────────────────────────────────────────────────────────────────────────────

def _style_directive(profile: StyleProfile) -> str:
    """Build a concise style instruction string for use in LLM prompts."""
    parts = [f"Tone: {profile.tone}."]
    parts.append(f"Target sentence length: ~{profile.avg_sentence_len} words.")
    if profile.emoji_usage:
        parts.append("Use emoji naturally, matching the creator's style.")
    else:
        parts.append("Do NOT use emoji.")
    if profile.common_phrases:
        parts.append(f"Occasionally use phrases like: {', '.join(profile.common_phrases[:3])}.")
    if profile.cta_style:
        parts.append(f"End with CTA: {profile.cta_style}")
    if profile.creator_name:
        parts.append(f"Creator name: {profile.creator_name}.")
    if profile.niche:
        parts.append(f"Niche: {profile.niche}.")
    return " ".join(parts)


def generate_title_options(
    transcript: str,
    style: StyleProfile | None = None,
    n: int = 5,
) -> list[str]:
    """
    Generate n YouTube-style title options for a video.

    Returns a list of plain-string titles (no numbering).
    Falls back to extracting the first sentence of the transcript if no LLM.
    """
    profile = style or default_profile()
    style_dir = _style_directive(profile)

    system = textwrap.dedent(f"""
        You generate YouTube video titles. {style_dir}
        Rules:
        - 50-70 characters max
        - Curiosity gap, specificity, or clear benefit in every title
        - No clickbait that under-delivers
        - Vary the structure across the {n} options (question, number, "how to", bold claim, etc.)
        Return ONLY a JSON array of {n} strings. No prose, no markdown.
    """).strip()

    raw = _llm_call(system, f"Video transcript:\n\n{transcript[:4000]}")

    if raw:
        try:
            titles = json.loads(raw)
            if isinstance(titles, list) and all(isinstance(t, str) for t in titles):
                return titles[:n]
        except json.JSONDecodeError:
            # Try extracting quoted strings
            titles = re.findall(r'"([^"]{10,80})"', raw)
            if titles:
                return titles[:n]

    # Rule-based fallback — extract first sentence + variants
    first_sentence = re.split(r"[.!?]", transcript)[0].strip()[:70]
    return [first_sentence] + [f"How I {first_sentence.lower()[:60]}"] * min(n - 1, 4)


def generate_description(
    transcript: str,
    style: StyleProfile | None = None,
    include_timestamps: str | None = None,
) -> str:
    """
    Generate a YouTube video description in the user's writing style.

    Args:
        transcript: Full or packed transcript text.
        style: Style profile to match.
        include_timestamps: Pre-generated timestamps string to append.

    Returns:
        Description as a plain string (not markdown).
    """
    profile = style or default_profile()
    style_dir = _style_directive(profile)

    system = textwrap.dedent(f"""
        You write YouTube video descriptions. {style_dir}
        Structure:
        1. Hook paragraph (2-3 sentences): what the video is about and why it matters.
        2. What viewers will learn (3-5 bullet points starting with "—").
        3. CTA paragraph.
        4. Leave a blank line, then add: "TIMESTAMPS_PLACEHOLDER" if timestamps should go here.
        5. Two blank lines, then relevant hashtags (5-10).

        Write in plain text, no markdown formatting. Match the creator's voice exactly.
    """).strip()

    raw = _llm_call(system, f"Video transcript:\n\n{transcript[:6000]}")

    if not raw:
        # Rule-based fallback
        raw = (
            f"{transcript[:200].strip()}...\n\n"
            "— Key insight 1\n— Key insight 2\n— Key insight 3\n\n"
            f"{profile.cta_style or 'Let me know your thoughts in the comments!'}\n\n"
            "#video #content"
        )

    if include_timestamps and "TIMESTAMPS_PLACEHOLDER" in raw:
        raw = raw.replace("TIMESTAMPS_PLACEHOLDER", include_timestamps)
    elif include_timestamps:
        raw = raw + "\n\n" + include_timestamps

    return raw.strip()


def generate_caption(
    transcript: str,
    style: StyleProfile | None = None,
    platform: Platform = "youtube",
) -> str:
    """
    Generate a platform-specific caption/post in the user's writing style.

    Platform limits:
        youtube    — short hook for community post or pinned comment
        instagram  — 2200 chars max, hashtag-heavy
        linkedin   — professional, story-driven, no hashtag spam
        twitter    — 280 chars max
        tiktok     — hype, punchy, emoji-heavy regardless of profile
    """
    profile = style or default_profile()
    style_dir = _style_directive(profile)

    platform_rules = {
        "youtube": "Write a YouTube community post (3-4 sentences, engaging question at the end, no hashtags).",
        "instagram": "Write an Instagram caption. Hook in the first line. 150-300 words. 15-25 relevant hashtags at the end, separated by line break.",
        "linkedin": "Write a LinkedIn post. Professional but personal tone. Story structure. 200-400 words. 3-5 hashtags max.",
        "twitter": "Write a tweet. Max 280 characters. Punchy. No hashtags unless they fit naturally.",
        "tiktok": "Write a TikTok caption. Max 150 characters. Energy, hooks, lots of emoji.",
    }

    system = textwrap.dedent(f"""
        You write social media captions. {style_dir}
        Platform-specific rules: {platform_rules.get(platform, platform_rules['instagram'])}
        Return ONLY the caption text, no extra explanation.
    """).strip()

    raw = _llm_call(system, f"Video content (transcript excerpt):\n\n{transcript[:3000]}")

    if not raw:
        # Rule-based fallback
        hook = transcript[:100].strip()
        hashtags = " ".join((profile.hashtags or {}).get(platform, []) or ["#video"])
        raw = f"{hook}... {profile.cta_style or ''} {hashtags}".strip()

    return raw.strip()


# ─────────────────────────────────────────────────────────────────────────────
# CLI entry point
# ─────────────────────────────────────────────────────────────────────────────

def _read_transcript(edit_dir: Path) -> str:
    """Read takes_packed.md or fall back to any .txt in the edit dir."""
    packed = edit_dir / "takes_packed.md"
    if packed.exists():
        return packed.read_text(encoding="utf-8")
    txts = list(edit_dir.glob("*.txt"))
    if txts:
        return txts[0].read_text(encoding="utf-8")
    return ""


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Caption / description generator CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)

    gen = sub.add_parser("generate", help="Generate titles, description, and platform captions")
    gen.add_argument("--edit-dir", required=True, help="Path to <footage>/edit/")
    gen.add_argument("--platform", default="youtube", choices=["youtube", "instagram", "linkedin", "twitter", "tiktok"])
    gen.add_argument("--n-titles", type=int, default=5)

    style_cmd = sub.add_parser("analyze-style", help="Analyze sample texts and save style profile")
    style_cmd.add_argument("--edit-dir", required=True)
    style_cmd.add_argument("--samples", nargs="+", required=True, help="Sample text strings from the creator")

    args = parser.parse_args()

    if args.cmd == "analyze-style":
        profile = analyze_style(args.samples)
        path = save_style_profile(profile, args.edit_dir)
        print(f"✅ Style profile saved → {path}")
        return

    # generate command
    edit_dir = Path(args.edit_dir)
    profile = load_style_profile(edit_dir) or default_profile()
    transcript = _read_transcript(edit_dir)

    if not transcript:
        print("⚠️  No transcript found in edit dir. Add takes_packed.md or any .txt file.")

    print("\n─── Titles ─────────────────────────────────")
    titles = generate_title_options(transcript, profile, args.n_titles)
    title_output = "\n".join(f"{i+1}. {t}" for i, t in enumerate(titles))
    print(title_output)
    (edit_dir / "title_options.md").write_text(title_output, encoding="utf-8")

    print("\n─── Description ────────────────────────────")
    desc = generate_description(transcript, profile)
    print(desc[:300] + "..." if len(desc) > 300 else desc)
    (edit_dir / "description.md").write_text(desc, encoding="utf-8")

    print(f"\n─── Caption ({args.platform}) ──────────────────")
    cap = generate_caption(transcript, profile, platform=args.platform)  # type: ignore[arg-type]
    print(cap)
    (edit_dir / f"caption_{args.platform}.md").write_text(cap, encoding="utf-8")

    print(f"\n✅ Outputs saved to {edit_dir}")


if __name__ == "__main__":
    main()
