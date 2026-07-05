"""
modules/motion_graphics/editframe_bridge.py

Python bridge between the video-use editing pipeline and the Editframe
HTML web-component → MP4 renderer.

Why Editframe?
  HyperFrames requires free-form HTML + GSAP code, which only Claude-class
  models generate reliably.  Editframe's <ef-*> web-component DSL is
  declarative, schema-driven, and well within the training distribution of
  every major model — making motion graphics model-agnostic.

How it works:
  1. Load an HTML composition from templates/editframe/*.html
  2. Run `npx editframe render --url <file:///...> --data '<json>' -o out.mp4`
     Render data is injected via --data and exposed as window.__EF_DATA__
     inside the composition.
  3. Return the output path for inclusion in the EDL's "overlays" key.

The rendered clip goes into <edit_dir>/animations/slot_<id>/render.mp4,
which is the standard path expected by tools/video-use/helpers/render.py.

Requirements:
    - Node >= 18  (16 minimum for @editframe/cli)
    - npx on PATH
    - ffmpeg on PATH  (used by Editframe's local renderer)
    - Internet access on first run (CDN fetch for ef-* components is cached)

Environment variables:
    EDITFRAME_TOKEN  — Optional. Required only for cloud rendering
                       (npx editframe cloud-render). Local rendering is free.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

# ─────────────────────────────────────────────────────────────────────────────
# Internal helpers
# ─────────────────────────────────────────────────────────────────────────────

def _workspace_root() -> Path:
    """Return the absolute path to the editing-workspace root."""
    return Path(__file__).resolve().parents[2]


def _ef_templates_dir() -> Path:
    return _workspace_root() / "templates" / "editframe"


def _camel_case(name: str) -> str:
    """Convert kebab-case token names to camelCase for Editframe data keys."""
    parts = name.split("-")
    return parts[0] + "".join(p.capitalize() for p in parts[1:])


def _load_design_tokens() -> dict[str, str]:
    """Load shared design tokens from templates/design-system.json (camelCase keys)."""
    path = _workspace_root() / "templates" / "design-system.json"
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return {_camel_case(k): str(v) for k, v in data.items() if not k.startswith("_")}
    except (json.JSONDecodeError, OSError):
        return {}


def _check_requirements() -> None:
    """Raise if npx is not available."""
    if not shutil.which("npx"):
        raise RuntimeError(
            "npx not found on PATH.\n"
            "Install Node.js >= 18 from https://nodejs.org/ and retry."
        )


def _slot_path(output_dir: str | Path, slot_id: str) -> Path:
    """Return <output_dir>/animations/slot_<id>/render.mp4"""
    return Path(output_dir) / "animations" / f"slot_{slot_id}" / "render.mp4"


def _run_editframe(
    html_path: Path,
    output_path: Path,
    data: dict,
    duration: float,
    fps: int = 30,
    width: int = 1920,
    height: int = 1080,
) -> None:
    """
    Call `npx editframe render` on the given HTML file.

    Editframe CLI reference:
        npx editframe render
            --url <file://...>          HTML composition to render
            --data '<json>'             Render-time data (window.__EF_DATA__)
            --duration <seconds>        Total clip length
            --fps <n>                   Frames per second
            --width <px>                Output width
            --height <px>               Output height
            -o <path>                   Output MP4 path
    """
    _check_requirements()
    ws = _workspace_root()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Merge design tokens (base) + user data (override) + duration
    render_data: dict[str, Any] = {"duration": duration, **_load_design_tokens(), **data}

    cmd = [
        "npx", "--yes", "@editframe/cli", "render",
        "--url", html_path.as_uri(),
        "--data", json.dumps(render_data),
        "--duration", str(duration),
        "--fps", str(fps),
        "--width", str(width),
        "--height", str(height),
        "-o", str(output_path),
    ]

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=str(ws),
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"Editframe render failed for {html_path.name}:\n"
            f"CMD:    {' '.join(cmd)}\n"
            f"STDOUT: {result.stdout}\n"
            f"STDERR: {result.stderr}"
        )


# ─────────────────────────────────────────────────────────────────────────────
# Cache helpers (mirror HyperFrames bridge)
# ─────────────────────────────────────────────────────────────────────────────

def _render_hash(
    template_path: Path,
    vars: dict[str, str],
    duration: float,
    fps: int,
    width: int,
    height: int,
) -> str:
    """Return a stable hash string for a render job."""
    payload = {
        "template": str(template_path.resolve()),
        "vars": vars,
        "duration": duration,
        "fps": fps,
        "width": width,
        "height": height,
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:16]


def _hash_path(output_mp4: Path) -> Path:
    return output_mp4.with_suffix(output_mp4.suffix + ".renderhash")


def _is_cached(output_mp4: Path, expected_hash: str) -> bool:
    mp4 = Path(output_mp4)
    hash_file = _hash_path(mp4)
    return mp4.exists() and hash_file.exists() and hash_file.read_text(encoding="utf-8").strip() == expected_hash


def _write_cache_hash(output_mp4: Path, render_hash: str) -> None:
    _hash_path(output_mp4).write_text(render_hash, encoding="utf-8")


# ─────────────────────────────────────────────────────────────────────────────
# Public API  (mirrors the HyperFrames bridge.py surface exactly)
# ─────────────────────────────────────────────────────────────────────────────

def render_template(
    template_path: str | Path,
    vars: dict[str, str],
    output_mp4: str | Path,
    duration: float = 5.0,
    fps: int = 30,
    width: int = 1920,
    height: int = 1080,
    dry_run: bool = False,
) -> str:
    """
    Render any Editframe HTML composition to an MP4 clip.

    This is the generic render call — identical signature to the HyperFrames
    bridge so callers can swap backends without changing calling code.

    Args:
        template_path: Path to a templates/editframe/*.html file.
        vars:          Render-data dictionary.  Keys map to window.__EF_DATA__
                       inside the composition.  Common keys:
                         title, subtitle, accentColor, bgColor, font
        output_mp4:    Destination for the rendered clip.
        duration:      Clip length in seconds.
        fps:           Frames per second (default 30).
        width, height: Output resolution (default 1920 × 1080).
        dry_run:       If True, print the render plan and return the output path
                       without running Editframe.

    Returns:
        Absolute path to the rendered MP4.

    Example::

        from modules.motion_graphics import editframe_bridge as ef

        path = ef.render_template(
            template_path="templates/editframe/lower-third.html",
            vars={"title": "Khalid Al-Mansouri", "subtitle": "Founder",
                  "accentColor": "#FF5A00"},
            output_mp4="footage/edit/animations/slot_lt1/render.mp4",
            duration=4.0,
        )
    """
    tpl = Path(template_path).resolve()
    if not tpl.exists():
        raise FileNotFoundError(
            f"Editframe template not found: {tpl}\n"
            f"Available templates: {list(_ef_templates_dir().glob('*.html'))}"
        )

    out = Path(output_mp4).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    render_hash = _render_hash(tpl, vars, duration, fps, width, height)

    if _is_cached(out, render_hash):
        print(f"[motion_graphics] cached: {out.name}")
        return str(out)

    if dry_run:
        print(f"[motion_graphics] dry-run: would render {tpl.name} -> {out}")
        print(f"[motion_graphics] dry-run: hash={render_hash} vars={json.dumps(vars, sort_keys=True)}")
        return str(out)

    from ..observability import PipelineLogger

    edit_dir = out.parent
    while edit_dir.name != "edit" and edit_dir.parent != edit_dir:
        edit_dir = edit_dir.parent
    logger = PipelineLogger(edit_dir if edit_dir.name == "edit" else out.parent)

    with logger.timed("motion_graphics.render", {"template": tpl.name, "output": out.name, "hash": render_hash}):
        _run_editframe(tpl, out, data=vars, duration=duration, fps=fps,
                       width=width, height=height)
    _write_cache_hash(out, render_hash)
    return str(out)


def add_lower_third(
    name: str,
    title: str,
    output_dir: str | Path,
    slot_id: str = "lt1",
    duration: float = 4.0,
    accent_color: str = "#FF5A00",
    bg_color: str = "rgba(10,10,10,0.88)",
    font: str = "Inter",
) -> str:
    """
    Render a lower-third overlay (name + role, slide in from left).

    Args:
        name:         Large text — the person's name.
        title:        Small text below — their role or title.
        output_dir:   The edit/ directory.  Clip saved to
                      animations/slot_<id>/render.mp4.
        slot_id:      Unique slot identifier.  Use different IDs if rendering
                      multiple lower-thirds in the same session.
        duration:     Clip length in seconds (default 4 s).
        accent_color: Hex accent for bar + role text.
        bg_color:     Background panel color.
        font:         Font family name.

    Returns:
        Absolute path to render.mp4 — add to EDL overlays.

    Example::

        path = add_lower_third(
            name="Khalid Al-Mansouri",
            title="Product Designer",
            output_dir="/footage/edit",
            slot_id="lt1",
            accent_color="#FF5A00",
        )
    """
    return render_template(
        template_path=_ef_templates_dir() / "lower-third.html",
        vars={
            "title":       name,
            "subtitle":    title,
            "accentColor": accent_color,
            "bgColor":     bg_color,
            "font":        font,
        },
        output_mp4=_slot_path(output_dir, slot_id),
        duration=duration,
    )


def add_lower_third_vertical(
    name: str,
    title: str,
    output_dir: str | Path,
    slot_id: str = "ltv1",
    duration: float = 4.0,
    accent_color: str = "#FF5A00",
    bg_color: str = "rgba(10,10,10,0.88)",
    font: str = "Inter",
) -> str:
    """
    Render a 9:16 vertical lower-third overlay for Shorts/Reels.

    Args: same as add_lower_third.
    Returns: Absolute path to render.mp4.
    """
    return render_template(
        template_path=_ef_templates_dir() / "lower-third-vertical.html",
        vars={
            "title":       name,
            "subtitle":    title,
            "accentColor": accent_color,
            "bgColor":     bg_color,
            "font":        font,
        },
        output_mp4=_slot_path(output_dir, slot_id),
        duration=duration,
        width=1080,
        height=1920,
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
    Render a chapter intro transition (chapter name, letter-spacing reveal).

    Args:
        chapter_name:   The chapter label (e.g. "The Problem").
        output_dir:     The edit/ directory.
        slot_id:        Unique slot identifier.
        chapter_number: Optional prefix ("01", "Chapter 1", etc.).
        duration:       Clip length in seconds (default 3 s).
        accent_color:   Highlight color.
        bg_color:       Background color.

    Returns:
        Absolute path to render.mp4 — add to EDL overlays.
    """
    return render_template(
        template_path=_ef_templates_dir() / "chapter-intro.html",
        vars={
            "title":       chapter_name,
            "subtitle":    chapter_number,
            "accentColor": accent_color,
            "bgColor":     bg_color,
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
    Render a full-screen title card with staggered word reveal.

    Args:
        title:        Main title text.
        output_dir:   The edit/ directory.
        slot_id:      Unique slot identifier.
        subtitle:     Optional subtitle below the main title.
        duration:     Clip length in seconds.
        accent_color, bg_color, font: Visual style.

    Returns:
        Absolute path to render.mp4 — add to EDL overlays.
    """
    return render_template(
        template_path=_ef_templates_dir() / "title-card.html",
        vars={
            "title":       title,
            "subtitle":    subtitle,
            "accentColor": accent_color,
            "bgColor":     bg_color,
            "font":        font,
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
    Render a subscribe bump (bell icon + Subscribe pill, bottom-right corner).

    Args:
        output_dir:   The edit/ directory.
        slot_id:      Unique slot identifier.
        duration:     Clip length in seconds.
        accent_color: Subscribe button color (default YouTube red).
        label:        Button label text.

    Returns:
        Absolute path to render.mp4 — add to EDL overlays.
    """
    return render_template(
        template_path=_ef_templates_dir() / "subscribe-bump.html",
        vars={
            "title":       label,
            "accentColor": accent_color,
        },
        output_mp4=_slot_path(output_dir, slot_id),
        duration=duration,
    )


def add_end_screen(
    channel_name: str,
    output_dir: str | Path,
    slot_id: str = "end1",
    tagline: str = "New videos every week",
    duration: float = 15.0,
    accent_color: str = "#FF0000",
    bg_color: str = "#0A0A0A",
    font: str = "Inter",
) -> str:
    """
    Render a full-screen end screen with subscribe button and channel name.

    Args:
        channel_name: Channel/creator name displayed below the button.
        output_dir:   The edit/ directory.
        slot_id:      Unique slot identifier.
        tagline:      Short line below the channel name.
        duration:     Clip length (default 15 s).
        accent_color: Subscribe button + pulse ring color.
        bg_color:     Background color.
        font:         Font family.

    Returns:
        Absolute path to render.mp4 — add to EDL overlays.
    """
    return render_template(
        template_path=_ef_templates_dir() / "end-screen.html",
        vars={
            "title":       channel_name,
            "subtitle":    tagline,
            "accentColor": accent_color,
            "bgColor":     bg_color,
            "font":        font,
        },
        output_mp4=_slot_path(output_dir, slot_id),
        duration=duration,
    )


# ─────────────────────────────────────────────────────────────────────────────
# AI Background Integration  (mirrors bridge.py's render_template_with_ai_bg)
# ─────────────────────────────────────────────────────────────────────────────

def render_template_with_ai_bg(
    template_path: str | Path,
    vars: dict[str, str],
    output_mp4: str | Path,
    duration: float,
    bg_prompt: str,
    bg_backend: str = "auto",
    bg_style: str = "motion_bg",
    bg_quality: str = "standard",
    fps: int = 30,
    width: int = 1920,
    height: int = 1080,
    assets_dir: str | Path | None = None,
) -> str:
    """
    Generate an AI background image, inject it into an Editframe template,
    and render to MP4.

    Identical signature to HyperFrames bridge.render_template_with_ai_bg so
    callers can swap backends without code changes.

    Args:
        template_path: Path to a templates/editframe/*.html file.
        vars:          Render-data dict (title, subtitle, etc.).
                       Do NOT include bgImage — set automatically.
        output_mp4:    Destination for the rendered clip.
        duration:      Clip length in seconds.
        bg_prompt:     Text prompt for the AI background image.
        bg_backend:    "openai" | "gemini" | "auto".
        bg_style:      Style preset key (default "motion_bg").
        bg_quality:    Image quality ("standard" | "hd").
        fps, width, height: Render parameters.
        assets_dir:    Where to save the generated background PNG.

    Returns:
        Absolute path to the rendered MP4.
    """
    from ..images.generator import generate_image

    out = Path(output_mp4).resolve()
    bg_dir = Path(assets_dir) if assets_dir else out.parent / "assets"
    bg_dir.mkdir(parents=True, exist_ok=True)

    bg_paths = generate_image(
        prompt=bg_prompt,
        backend=bg_backend,
        size="1024x1024",
        quality=bg_quality,
        output_dir=bg_dir,
        n=1,
        style_hint=bg_style,
    )

    if not bg_paths:
        raise RuntimeError("AI background generation returned no results.")

    merged_vars = {"bgImage": bg_paths[0], **vars}

    return render_template(
        template_path=template_path,
        vars=merged_vars,
        output_mp4=output_mp4,
        duration=duration,
        fps=fps,
        width=width,
        height=height,
    )
