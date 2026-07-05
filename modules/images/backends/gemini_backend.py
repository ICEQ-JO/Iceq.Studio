"""
modules/images/backends/gemini_backend.py

Google Gemini Imagen 3 image generation backend.

Model: imagen-3.0-generate-002  (Imagen 3)
SDK:   google-generativeai >= 0.8  (pip install google-generativeai)

Supported aspect ratios (mapped from canonical WxH strings):
  1:1   → 1024x1024  (square)
  16:9  → landscape (1344x768 internally, returned as PNG)
  9:16  → portrait  (768x1344)
  4:3   → 1024x768
  3:4   → 768x1024

Supported generation counts: 1–4 per API call.

Notes:
  - Imagen 3 does NOT support "quality" tiers — all output is the same fidelity.
  - Imagen 3 has built-in safety filters; overly graphic prompts will be rejected.
  - Requires a Gemini API key from: https://aistudio.google.com/app/apikey
  - Set GEMINI_API_KEY in .env
"""

from __future__ import annotations

import os
import time
from pathlib import Path

from dotenv import load_dotenv

from ..base import ImageBackend

load_dotenv(dotenv_path=Path(__file__).resolve().parents[4] / ".env")

# ── Aspect ratio mapping from canonical WxH ─────────────────────────────────

_ASPECT_RATIO_MAP: dict[str, str] = {
    "1024x1024": "1:1",
    "512x512":   "1:1",
    "256x256":   "1:1",
    # Landscape
    "1792x1024": "16:9",
    "1536x1024": "16:9",
    # Portrait
    "1024x1792": "9:16",
    "1024x1536": "9:16",
    # 4:3 / 3:4
    "1024x768":  "4:3",
    "768x1024":  "3:4",
}


class GeminiBackend(ImageBackend):
    """Google Gemini Imagen 3 image generation backend."""

    DEFAULT_MODEL = "imagen-3.0-generate-002"

    def name(self) -> str:
        return "gemini"

    def is_available(self) -> bool:
        if not os.getenv("GEMINI_API_KEY"):
            return False
        try:
            import google.generativeai  # noqa: F401
            return True
        except ImportError:
            return False

    def status(self) -> dict:
        key = os.getenv("GEMINI_API_KEY", "")
        available = self.is_available()
        info = {
            "name": self.name(),
            "available": available,
            "default_model": self.DEFAULT_MODEL,
            "key_hint": f"...{key[-6:]}" if len(key) > 10 else "(not set)",
        }
        if not os.getenv("GEMINI_API_KEY"):
            info["note"] = "Get a free key at https://aistudio.google.com/app/apikey"
        if os.getenv("GEMINI_API_KEY") and not available:
            info["note"] = "SDK not installed — run: pip install google-generativeai"
        return info

    def generate(
        self,
        prompt: str,
        output_dir: str | Path,
        size: str = "1024x1024",
        quality: str = "standard",  # ignored by Imagen 3
        n: int = 1,
        model: str | None = None,
    ) -> list[str]:
        """
        Generate images using Google Imagen 3 via the Gemini API.

        Args:
            prompt:     Image generation prompt.
            output_dir: Local directory for saved PNGs.
            size:       Canonical "WxH" string (mapped to nearest aspect ratio).
            quality:    Ignored — Imagen 3 has one quality level.
            n:          1–4 images per call.
            model:      Override model (default: imagen-3.0-generate-002).

        Returns:
            List of absolute paths to saved PNG files.
        """
        try:
            import google.generativeai as genai  # type: ignore[import]
        except ImportError:
            raise RuntimeError(
                "google-generativeai SDK not installed.\n"
                "Run: pip install google-generativeai"
            )

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError(
                "GEMINI_API_KEY is not set. Add it to .env:\n"
                "  GEMINI_API_KEY=AIza...\n"
                "  Get one at: https://aistudio.google.com/app/apikey"
            )

        genai.configure(api_key=api_key)

        chosen_model = model or self.DEFAULT_MODEL
        aspect_ratio = _ASPECT_RATIO_MAP.get(size, "1:1")
        n_clamped = max(1, min(n, 4))  # Imagen 3 limit

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        imagen = genai.ImageGenerationModel(chosen_model)
        response = imagen.generate_images(
            prompt=prompt,
            number_of_images=n_clamped,
            aspect_ratio=aspect_ratio,
            safety_filter_level="block_only_high",
            person_generation="allow_adult",
        )

        paths: list[str] = []
        for i, image in enumerate(response.images):
            slug = f"gemini_{int(time.time())}_{i:02d}.png"
            out = output_dir / slug
            # The SDK returns image bytes via .image.image_bytes or ._pil_image
            img_bytes: bytes | None = None
            try:
                img_bytes = image._pil_image.tobytes()  # type: ignore[attr-defined]
                # Use PIL to save as proper PNG
                pil_img = image._pil_image  # type: ignore[attr-defined]
                pil_img.save(str(out), "PNG")
            except AttributeError:
                try:
                    img_bytes = image.image.image_bytes  # type: ignore[attr-defined]
                    out.write_bytes(img_bytes)
                except AttributeError:
                    # Last-resort: try iterating raw bytes
                    raw = bytes(image)
                    if raw:
                        out.write_bytes(raw)
                    else:
                        continue
            paths.append(str(out))

        return paths
