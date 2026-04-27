"""
modules/images — AI image generation for the editing workspace.

Supports OpenAI (gpt-image-1, dall-e-3) and Google Gemini (Imagen 3).

Quick API:
    from modules.images import generate_image, STYLE_PRESETS, list_backends

    # Check what's available
    for b in list_backends():
        print(b["name"], "available" if b["available"] else "NOT available")

    # Generate a thumbnail background
    paths = generate_image(
        prompt="A developer at a glowing workstation, dark room",
        backend="openai",        # or "gemini" or "auto"
        size="1792x1024",        # landscape — perfect for thumbnails
        quality="hd",
        style_hint="cinematic",  # prepends cinematic style prefix
        output_dir="edit/assets/",
        n=1,
    )

    # Generate a dark abstract background for a motion graphic
    paths = generate_image(
        prompt="swirling dark particles, deep blue and orange tones",
        style_hint="motion_bg",
        output_dir="edit/assets/",
    )

CLI:
    python -m modules.images status
    python -m modules.images generate --prompt "..." --backend openai --style cinematic
    python -m modules.images thumbnail-bg --prompt "..." --edit-dir edit/

Style presets:
    cinematic | flat_dark | thumbnail | realistic | motion_bg | illustration | neon | clean_studio
"""

from .generator import generate_image, list_backends, get_backend, STYLE_PRESETS
from .base import ImageBackend

__all__ = [
    "generate_image",
    "list_backends",
    "get_backend",
    "STYLE_PRESETS",
    "ImageBackend",
]
