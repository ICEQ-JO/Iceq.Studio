"""
modules/timestamps/generator.py

Generates a YouTube-style chapter timestamp structure from the video-use EDL.

The EDL's "ranges" array has a "beat" field per segment that names the chapter
(e.g. "HOOK", "PROBLEM", "SOLUTION"). This module:
  1. Reads edl.json
  2. Calculates cumulative output-timeline offsets from segment durations
  3. Groups consecutive segments with the same beat into one chapter
  4. Formats as YouTube timestamps (0:00 Introduction, 1:23 Problem, ...)
  5. Saves to <edit_dir>/timestamps.txt

CLI:
    python -m modules.timestamps generate --edit-dir /path/to/edit/

Module API:
    from modules.timestamps import generate_timestamps
    text = generate_timestamps(edit_dir="/path/to/edit/")
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal


# Beat label → human-readable chapter name mappings
# Add your own or override with the --label-map flag
DEFAULT_BEAT_LABELS: dict[str, str] = {
    "HOOK": "Introduction",
    "PROBLEM": "The Problem",
    "SOLUTION": "The Solution",
    "BENEFIT": "Key Benefits",
    "EXAMPLE": "Live Example",
    "DEMO": "Demo",
    "CTA": "Outro",
    "INTRO": "Introduction",
    "SETUP": "Setup",
    "STEPS": "Step-by-Step",
    "GOTCHAS": "Common Mistakes",
    "RECAP": "Recap",
    "QUESTION": "Question",
    "ANSWER": "Answer",
    "ARRIVAL": "Arrival",
    "HIGHLIGHTS": "Highlights",
    "QUIET": "Quiet Moments",
    "DEPARTURE": "Departure",
    "THESIS": "Thesis",
    "EVIDENCE": "Evidence",
    "COUNTERPOINT": "Counterpoint",
    "CONCLUSION": "Conclusion",
    "VERSE": "Verse",
    "CHORUS": "Chorus",
    "BRIDGE": "Bridge",
    "OUTRO": "Outro",
}


def _seconds_to_timestamp(seconds: float) -> str:
    """Convert float seconds to M:SS or H:MM:SS format."""
    total = int(round(seconds))
    h = total // 3600
    m = (total % 3600) // 60
    s = total % 60
    if h > 0:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


def _humanise_beat(beat: str, label_map: dict[str, str]) -> str:
    """Convert a raw beat label ('HOOK') to a display name ('Introduction')."""
    if beat in label_map:
        return label_map[beat]
    # Title-case the raw label as a fallback
    return beat.replace("_", " ").title()


def generate_timestamps(
    edit_dir: str | Path,
    style: Literal["youtube", "chapters", "minimal"] = "youtube",
    label_map: dict[str, str] | None = None,
    include_first_zero: bool = True,
) -> str:
    """
    Generate a chapter timestamp string from the EDL in <edit_dir>/edl.json.

    Args:
        edit_dir: Path to the edit directory containing edl.json.
        style: Output format.
            "youtube"  — Standard YouTube format: "0:00 Introduction\\n1:23 Problem\\n..."
            "chapters" — Same but with "Chapters:" header line prepended.
            "minimal"  — Just the time → label, no decoration.
        label_map: Override the default beat-label → display-name mapping.
        include_first_zero: If True, ensures the first chapter always starts at 0:00.

    Returns:
        Formatted timestamp string ready to paste into a YouTube description.

    Side effects:
        Writes the result to <edit_dir>/timestamps.txt.
    """
    edit_dir = Path(edit_dir)
    edl_path = edit_dir / "edl.json"

    if not edl_path.exists():
        raise FileNotFoundError(
            f"edl.json not found at {edl_path}. "
            "Run the video-use editing pipeline first to produce an EDL."
        )

    with edl_path.open("r", encoding="utf-8") as f:
        edl = json.load(f)

    ranges = edl.get("ranges", [])
    if not ranges:
        return "# No segments found in EDL."

    lmap = {**DEFAULT_BEAT_LABELS, **(label_map or {})}

    # ── Calculate output-timeline offset for each segment ────────────────────
    # Segments are ordered; each segment's duration = end - start in source time.
    chapters: list[tuple[float, str]] = []  # (output_offset_seconds, chapter_name)
    cumulative: float = 0.0
    last_beat: str | None = None

    for seg in ranges:
        beat = seg.get("beat", "").upper() or "SECTION"
        dur = float(seg["end"]) - float(seg["start"])

        # New chapter whenever beat changes
        if beat != last_beat:
            chapters.append((cumulative, _humanise_beat(beat, lmap)))
            last_beat = beat

        cumulative += dur

    # ── Force first chapter at 0:00 if requested ─────────────────────────────
    if include_first_zero and chapters and chapters[0][0] > 0:
        chapters.insert(0, (0.0, chapters[0][1]))

    # ── Format ────────────────────────────────────────────────────────────────
    lines = [f"{_seconds_to_timestamp(t)} {name}" for t, name in chapters]

    if style == "chapters":
        output = "Chapters:\n" + "\n".join(lines)
    elif style == "minimal":
        output = "\n".join(lines)
    else:  # youtube (default)
        output = "\n".join(lines)

    # Save to file
    out_path = edit_dir / "timestamps.txt"
    out_path.write_text(output, encoding="utf-8")

    return output


# ─────────────────────────────────────────────────────────────────────────────
# CLI entry point
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="YouTube timestamp generator")
    sub = parser.add_subparsers(dest="cmd", required=True)

    gen = sub.add_parser("generate", help="Generate timestamps from edit/edl.json")
    gen.add_argument("--edit-dir", required=True, help="Path to <footage>/edit/")
    gen.add_argument(
        "--style",
        default="youtube",
        choices=["youtube", "chapters", "minimal"],
        help="Output format style",
    )
    gen.add_argument(
        "--no-first-zero",
        action="store_true",
        help="Don't force first chapter to 0:00",
    )

    args = parser.parse_args()

    result = generate_timestamps(
        edit_dir=args.edit_dir,
        style=args.style,
        include_first_zero=not args.no_first_zero,
    )
    print(result)
    print(f"\n✅ Saved to {Path(args.edit_dir) / 'timestamps.txt'}")


if __name__ == "__main__":
    main()
