"""
modules/motion_graphics — Python bridge to the HyperFrames CLI.

Usage:
    from modules.motion_graphics import bridge
    out = bridge.render_template(
        template_path="templates/lower-third.html",
        vars={"title": "Khalid Al-Mansouri", "subtitle": "Product Designer"},
        output_mp4="path/to/edit/animations/slot_1/render.mp4",
        duration=4.0,
    )

Module API:
    bridge.render_template(template_path, vars, output_mp4, duration) → str
    bridge.add_lower_third(name, title, start, duration, output_dir) → str
    bridge.add_chapter_intro(chapter_name, duration, output_dir) → str
    bridge.add_title_card(title, subtitle, duration, output_dir) → str
"""

from .bridge import (
    render_template,
    add_lower_third,
    add_chapter_intro,
    add_title_card,
    add_subscribe_bump,
)

__all__ = [
    "render_template",
    "add_lower_third",
    "add_chapter_intro",
    "add_title_card",
    "add_subscribe_bump",
]
