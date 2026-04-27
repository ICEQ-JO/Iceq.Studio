"""
modules/motion_graphics/bridge.py

Python bridge between the video-use editing pipeline and the HyperFrames
HTML → MP4 renderer.

HyperFrames takes an HTML composition file and renders it to MP4.
This bridge:
  1. Loads a template from templates/*.html
  2. Injects template variables as data-* attributes on the #stage element
  3. Calls `npx hyperframes render` to produce a video clip
  4. Returns the output path for inclusion in the EDL's "overlays" key

The rendered clip goes into <edit_dir>/animations/slot_<id>/render.mp4
which is the standard path expected by tools/video-use/helpers/render.py.

Requirements:
    - Node >= 22
    - `npm install` run in the workspace root (installs hyperframes CLI)
    - ffmpeg on PATH (used by HyperFrames internally)
"""

from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
from pathlib import Path


# ─────────────────────────────────────────────────────────────────────────────
# Internal helpers
# ─────────────────────────────────────────────────────────────────────────────

def _workspace_root() -> Path:
    """Return the absolute path to the editing-workspace root."""
    return Path(__file__).resolve().parents[2]


def _templates_dir() -> Path:
    return _workspace_root() / "templates"


def _check_requirements() -> None:
    """Raise if Node/npx is not available."""
    if not shutil.which("npx"):
        raise RuntimeError(
            "npx not found on PATH.\n"
            "Install Node.js >= 22 from https://nodejs.org/ then run:\n"
            f"  cd {_workspace_root()} && npm install"
        )


def _inject_vars(html: str, vars: dict[str, str], duration: float | None = None) -> str:
    """
    Inject vars as data-* attributes on the first #stage element.
    Also sets data-duration if provided and not already present.
    """
    all_vars = dict(vars)
    if duration is not None and "duration" not in all_vars:
        all_vars["duration"] = str(duration)

    def inject(m: re.Match) -> str:
        tag = m.group(0)
        for k, v in all_vars.items():
            attr_name = f"data-{k}"
            if attr_name not in tag:
                # Insert before closing >
                tag = tag[:-1] + f' {attr_name}="{v}">'
        return tag

    return re.sub(r'<div[^>]*id=["\']stage["\'][^>]*>', inject, html, count=1)


def _run_hyperframes(
    html_path: Path,
    output_path: Path,
    duration: float,
    fps: int = 30,
    width: int = 1920,
    height: int = 1080,
) -> None:
    """Call `npx hyperframes render` on the given HTML file."""
    _check_requirements()
    ws = _workspace_root()

    cmd = [
        "npx", "hyperframes", "render",
        str(html_path),
        "--output", str(output_path),
        "--width", str(width),
        "--height", str(height),
        "--fps", str(fps),
        "--duration", str(duration),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(ws))
    if result.returncode != 0:
        raise RuntimeError(
            f"HyperFrames render failed for {html_path.name}:\n"
            f"STDOUT: {result.stdout}\n"
            f"STDERR: {result.stderr}"
        )


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def render_template(
    template_path: str | Path,
    vars: dict[str, str],
    output_mp4: str | Path,
    duration: float = 5.0,
    fps: int = 30,
    width: int = 1920,
    height: int = 1080,
) -> str:
    """
    Render any HyperFrames HTML template to an MP4 clip.

    Args:
        template_path: Path to a templates/*.html file.
        vars: Template variables injected as data-* attributes on #stage.
              Common vars: title, subtitle, accent-color, bg-color, font.
        output_mp4: Destination for the rendered clip.
        duration: Clip length in seconds.
        fps: Frames per second.
        width, height: Output resolution.

    Returns:
        Absolute path to the rendered MP4.
    """
    tpl = Path(template_path).resolve()
    if not tpl.exists():
        raise FileNotFoundError(f"Template not found: {tpl}")

    html = tpl.read_text(encoding="utf-8")
    html = _inject_vars(html, vars, duration)

    out = Path(output_mp4).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="w", encoding="utf-8") as f:
        f.write(html)
        tmp_html = Path(f.name)

    try:
        _run_hyperframes(tmp_html, out, duration=duration, fps=fps, width=width, height=height)
    finally:
        tmp_html.unlink(missing_ok=True)

    return str(out)


def _slot_path(output_dir: str | Path, slot_id: str) -> Path:
    """Return <output_dir>/animations/slot_<id>/render.mp4"""
    return Path(output_dir) / "animations" / f"slot_{slot_id}" / "render.mp4"


def add_lower_third(
    name: str,
    title: str,
    output_dir: str | Path,
    slot_id: str = "lt1",
    duration: float = 4.0,
    accent_color: str = "#FF5A00",
    bg_color: str = "#0A0A0A",
    font: str = "Inter",
) -> str:
    """
    Render a lower-third overlay (name + title bar, slide in from left).

    Args:
        name: Large text (e.g. "Khalid Al-Mansouri").
        title: Small text below name (e.g. "Product Designer").
        output_dir: The edit/ directory. Clip saved to animations/slot_<id>/render.mp4.
        slot_id: Unique identifier for this animation slot. Use different IDs
                 if rendering multiple lower-thirds in one session.
        duration: Clip length in seconds (default 4s).
        accent_color: Hex accent color for the animated bar.
        bg_color: Hex background color.
        font: Font family name (must be installed or available to Chrome).

    Returns:
        Absolute path to render.mp4 — add to EDL overlays.
    """
    return render_template(
        template_path=_templates_dir() / "lower-third.html",
        vars={
            "title": name,
            "subtitle": title,
            "accent-color": accent_color,
            "bg-color": bg_color,
            "font": font,
        },
        output_mp4=_slot_path(output_dir, slot_id),
        duration=duration,
    )


def add_chapter_intro(
    chapter_name: str,
    output_dir: str | Path,
    slot_id: str = "ch1",
    chapter_number: str = "",
    duration: float = 3.0,
    accent_color: str = "#FF5A00",
    bg_color: str = "#0A0A0A",
) -> str:
    """
    Render a chapter intro transition (chapter name centered, fade in/out).

    Args:
        chapter_name: The chapter label (e.g. "The Problem").
        output_dir: The edit/ directory.
        slot_id: Unique identifier for this slot.
        chapter_number: Optional prefix like "01" or "Chapter 1".
        duration: Clip length in seconds (default 3s).
        accent_color: Highlight color.
        bg_color: Background color.

    Returns:
        Absolute path to render.mp4 — add to EDL overlays.
    """
    return render_template(
        template_path=_templates_dir() / "chapter-intro.html",
        vars={
            "title": chapter_name,
            "subtitle": chapter_number,
            "accent-color": accent_color,
            "bg-color": bg_color,
        },
        output_mp4=_slot_path(output_dir, slot_id),
        duration=duration,
    )


def add_title_card(
    title: str,
    output_dir: str | Path,
    slot_id: str = "tc1",
    subtitle: str = "",
    duration: float = 5.0,
    accent_color: str = "#FF5A00",
    bg_color: str = "#0A0A0A",
    font: str = "Inter",
) -> str:
    """
    Render a full-screen title card with animated reveal.

    Args:
        title: Main title text.
        output_dir: The edit/ directory.
        slot_id: Unique identifier for this slot.
        subtitle: Optional subtitle below the main title.
        duration: Clip length in seconds.
        accent_color, bg_color, font: Visual style.

    Returns:
        Absolute path to render.mp4 — add to EDL overlays.
    """
    return render_template(
        template_path=_templates_dir() / "title-card.html",
        vars={
            "title": title,
            "subtitle": subtitle,
            "accent-color": accent_color,
            "bg-color": bg_color,
            "font": font,
        },
        output_mp4=_slot_path(output_dir, slot_id),
        duration=duration,
    )


def add_subscribe_bump(
    output_dir: str | Path,
    slot_id: str = "sub1",
    duration: float = 3.0,
    accent_color: str = "#FF0000",
    label: str = "Subscribe",
) -> str:
    """
    Render a subscribe bump animation (bell icon + Subscribe label).

    Designed to appear in a corner overlay for 3 seconds.

    Args:
        output_dir: The edit/ directory.
        slot_id: Unique slot identifier.
        duration: Clip length in seconds.
        accent_color: Subscribe button color (default YouTube red).
        label: Button label text.

    Returns:
        Absolute path to render.mp4 — add to EDL overlays.
    """
    return render_template(
        template_path=_templates_dir() / "subscribe-bump.html",
        vars={
            "title": label,
            "accent-color": accent_color,
        },
        output_mp4=_slot_path(output_dir, slot_id),
        duration=duration,
    )
