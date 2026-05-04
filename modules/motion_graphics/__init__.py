"""
modules/motion_graphics — Motion graphics bridges.

Two backends are available:
  - editframe   (default) — Editframe <ef-*> web-component DSL.
                            Works reliably with all major LLMs.
                            Templates: templates/editframe/*.html
  - hyperframes           — HyperFrames HTML→MP4 (GSAP-powered).
                            Best for complex, bespoke GSAP animations.
                            Templates: templates/*.html

Backend is selected by the MOTION_GRAPHICS_BACKEND env variable.
Default is "editframe".

Usage (recommended — auto-selects backend from env):
    from modules.motion_graphics import bridge
    out = bridge.add_lower_third(
        name="Khalid Al-Mansouri",
        title="Product Designer",
        output_dir="/footage/edit",
    )

Usage (explicit backend):
    from modules.motion_graphics import editframe_bridge as ef
    from modules.motion_graphics import bridge as hf  # HyperFrames

Module API (both backends expose the same surface):
    render_template(template_path, vars, output_mp4, duration) → str
    add_lower_third(name, title, output_dir, ...)              → str
    add_chapter_intro(chapter_name, output_dir, ...)           → str
    add_title_card(title, output_dir, ...)                     → str
    add_subscribe_bump(output_dir, ...)                        → str
    add_end_screen(channel_name, output_dir, ...)              → str  (Editframe only)
    render_template_with_ai_bg(...)                            → str
"""

from __future__ import annotations

import os

# ── re-export the raw bridges so callers can import them explicitly ────────
from .editframe_bridge import (  # noqa: F401
    render_template         as ef_render_template,
    add_lower_third         as ef_add_lower_third,
    add_chapter_intro       as ef_add_chapter_intro,
    add_title_card          as ef_add_title_card,
    add_subscribe_bump      as ef_add_subscribe_bump,
    add_end_screen          as ef_add_end_screen,
    render_template_with_ai_bg as ef_render_template_with_ai_bg,
)

from .bridge import (  # noqa: F401  (HyperFrames)
    render_template         as hf_render_template,
    add_lower_third         as hf_add_lower_third,
    add_chapter_intro       as hf_add_chapter_intro,
    add_title_card          as hf_add_title_card,
    add_subscribe_bump      as hf_add_subscribe_bump,
    render_template_with_ai_bg as hf_render_template_with_ai_bg,
)


# ── auto-routing via MOTION_GRAPHICS_BACKEND env variable ─────────────────
_BACKEND = os.getenv("MOTION_GRAPHICS_BACKEND", "editframe").lower().strip()

if _BACKEND == "hyperframes":
    from .bridge import (
        render_template,
        add_lower_third,
        add_chapter_intro,
        add_title_card,
        add_subscribe_bump,
        render_template_with_ai_bg,
    )
    # add_end_screen not available in HyperFrames bridge — stub it
    def add_end_screen(*args, **kwargs):  # type: ignore[override]
        raise NotImplementedError(
            "add_end_screen is only available with the Editframe backend.\n"
            "Set MOTION_GRAPHICS_BACKEND=editframe in your .env file."
        )
else:
    # Default: Editframe
    from .editframe_bridge import (
        render_template,
        add_lower_third,
        add_chapter_intro,
        add_title_card,
        add_subscribe_bump,
        add_end_screen,
        render_template_with_ai_bg,
    )


__all__ = [
    # Auto-routed (respects MOTION_GRAPHICS_BACKEND)
    "render_template",
    "add_lower_third",
    "add_chapter_intro",
    "add_title_card",
    "add_subscribe_bump",
    "add_end_screen",
    "render_template_with_ai_bg",
    # Explicit Editframe
    "ef_render_template",
    "ef_add_lower_third",
    "ef_add_chapter_intro",
    "ef_add_title_card",
    "ef_add_subscribe_bump",
    "ef_add_end_screen",
    "ef_render_template_with_ai_bg",
    # Explicit HyperFrames
    "hf_render_template",
    "hf_add_lower_third",
    "hf_add_chapter_intro",
    "hf_add_title_card",
    "hf_add_subscribe_bump",
    "hf_render_template_with_ai_bg",
]
