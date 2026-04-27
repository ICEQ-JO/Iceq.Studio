"""
modules/images/generator.py

Unified image generation interface.

Public API:
    generate_image(prompt, backend, size, quality, output_dir, n, style_hint) → list[str]
    list_backends() → list[dict]   — status of all backends
    get_backend(name) → ImageBackend

Style presets (composable with any prompt):
    STYLE_PRESETS = {
        "cinematic":   "Epic cinematic photography, dramatic lighting, 8K, film grain —",
        "flat_dark":   "Flat design, dark background #0A0A0A, minimal, geometric —",
        "thumbnail":   "Eye-catching YouTube thumbnail style, bold colours, high contrast —",
        "realistic":   "Photorealistic, high detail, professional photography —",
        "motion_bg":   "Abstract motion graphic background, dark, subtle texture, no text —",
        "illustration":"Digital illustration, vibrant colours, clean lines —",
        "neon":        "Neon glow aesthetic, dark background, cyberpunk, bokeh —",
    }

Usage:
    from modules.images.generator import generate_image
    paths = generate_image(
        prompt="A futuristic keyboard glowing in the dark",
        backend="openai",
        size="1792x1024",
        quality="hd",
        style_hint="cinematic",
        output_dir="edit/assets/",
    )
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

from .base import ImageBackend
from .backends.openai_backend import OpenAIBackend
from .backends.gemini_backend import GeminiBackend

load_dotenv(dotenv_path=Path(__file__).resolve().parents[2] / ".env")

# ── Style presets ─────────────────────────────────────────────────────────────

STYLE_PRESETS: dict[str, str] = {
    "cinematic":    "Epic cinematic photography, dramatic lighting, 8K resolution, subtle film grain —",
    "flat_dark":    "Flat design illustration, very dark background #0A0A0A, minimal, clean geometric shapes —",
    "thumbnail":    "Eye-catching YouTube thumbnail style, bold vibrant colours, high contrast, dramatic —",
    "realistic":    "Ultra-photorealistic, high detail, professional photography, studio lighting —",
    "motion_bg":    "Abstract motion graphic background, very dark background, subtle texture, no text, no UI —",
    "illustration": "Clean digital illustration, vibrant colours, bold outlines, editorial style —",
    "neon":         "Neon glow aesthetic, dark background, cyberpunk vibes, light streaks, bokeh —",
    "clean_studio": "Clean white studio background, professional product photography, soft shadows —",
}

# ── Backend registry ──────────────────────────────────────────────────────────

_BACKENDS: dict[str, ImageBackend] = {
    "openai": OpenAIBackend(),
    "gemini": GeminiBackend(),
}


def get_backend(name: str) -> ImageBackend:
    """
    Return a backend by name.

    Args:
        name: "openai" | "gemini"

    Raises:
        ValueError: If the backend name is unknown.
        RuntimeError: If the backend is not available (missing key / SDK).
    """
    if name not in _BACKENDS:
        raise ValueError(
            f"Unknown backend '{name}'. Available: {list(_BACKENDS.keys())}"
        )
    backend = _BACKENDS[name]
    if not backend.is_available():
        status = backend.status()
        note = status.get("note", "Check API key and SDK installation.")
        raise RuntimeError(
            f"Backend '{name}' is not available.\n{note}"
        )
    return backend


def _auto_backend() -> ImageBackend:
    """
    Pick the best available backend automatically.
    Priority: env var IMAGE_GENERATOR_BACKEND → openai → gemini.
    Raises RuntimeError if no backend is available.
    """
    preferred = os.getenv("IMAGE_GENERATOR_BACKEND", "").lower()
    if preferred and preferred in _BACKENDS:
        if _BACKENDS[preferred].is_available():
            return _BACKENDS[preferred]

    # Try in priority order
    for name in ["openai", "gemini"]:
        if _BACKENDS[name].is_available():
            return _BACKENDS[name]

    raise RuntimeError(
        "No image generation backend is available.\n"
        "Set OPENAI_API_KEY (for gpt-image-1 / dall-e-3) or\n"
        "GEMINI_API_KEY + pip install google-generativeai (for Imagen 3) in .env."
    )


def list_backends() -> list[dict]:
    """Return status dicts for all registered backends."""
    return [b.status() for b in _BACKENDS.values()]


def generate_image(
    prompt: str,
    backend: str = "auto",
    size: str = "1024x1024",
    quality: str = "standard",
    output_dir: str | Path = ".",
    n: int = 1,
    style_hint: str = "",
    model: str | None = None,
) -> list[str]:
    """
    Generate one or more images from a text prompt.

    Args:
        prompt:     What to generate.
        backend:    "openai" | "gemini" | "auto" (auto picks the first available).
        size:       Canonical "WxH" string.
                      Common values: "1024x1024" (square), "1792x1024" (landscape),
                                     "1024x1792" (portrait)
        quality:    "standard" | "hd" (OpenAI) — ignored by Gemini.
        output_dir: Directory where PNG files are saved.
        n:          Number of images to generate (1–10 for OpenAI, 1–4 for Gemini).
        style_hint: Key from STYLE_PRESETS or any custom prefix string.
                    Prepended to the prompt automatically.
        model:      Force a specific model (e.g. "dall-e-3", "gpt-image-1").

    Returns:
        List of absolute local PNG file paths.

    Example:
        paths = generate_image(
            "A developer typing on a glowing keyboard at night",
            backend="openai",
            size="1792x1024",
            quality="hd",
            style_hint="cinematic",
            output_dir="edit/assets/",
        )
    """
    # Build full prompt with style prefix
    style_prefix = STYLE_PRESETS.get(style_hint, style_hint)
    full_prompt = f"{style_prefix} {prompt}".strip() if style_prefix else prompt

    # Select backend
    if backend == "auto":
        b = _auto_backend()
    else:
        b = get_backend(backend)

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    return b.generate(
        prompt=full_prompt,
        output_dir=output_dir,
        size=size,
        quality=quality,
        n=n,
        model=model,
    )
