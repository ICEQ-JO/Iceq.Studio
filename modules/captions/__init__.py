"""
modules/captions — Style-aware caption, title, and description generator.

Usage:
    python -m modules.captions generate \\
        --edit-dir /path/to/footage/edit/ \\
        --platform youtube

Module API:
    from modules.captions import generator
    titles = generator.generate_title_options(transcript, style)
    desc   = generator.generate_description(transcript, style)
    cap    = generator.generate_caption(transcript, style, platform="instagram")
"""

from .generator import generate_title_options, generate_description, generate_caption, analyze_style
from .style_profile import StyleProfile, load_style_profile, save_style_profile

__all__ = [
    "generate_title_options",
    "generate_description",
    "generate_caption",
    "analyze_style",
    "StyleProfile",
    "load_style_profile",
    "save_style_profile",
]
