"""
modules/images/backends/openai_backend.py

OpenAI image generation backend.

Supported models:
  - gpt-image-1   (default) — latest, best instruction following, supports transparency
  - dall-e-3      — widely available, slightly less capable

Supported sizes (gpt-image-1):
  1024x1024  (square)
  1536x1024  (landscape)
  1024x1536  (portrait)

Supported sizes (dall-e-3):
  1024x1024  (square)
  1792x1024  (landscape)
  1024x1792  (portrait)

Quality:
  standard  (default)
  hd        (dall-e-3 only — doubles rendering time and cost)
  high      (gpt-image-1 equivalent of hd)

Pricing (approximate, April 2026):
  gpt-image-1   low:    $0.011/image (1024x1024)
  gpt-image-1   medium: $0.042/image
  gpt-image-1   high:   $0.167/image
  dall-e-3      standard: $0.040/image
  dall-e-3      hd:       $0.080/image
"""

from __future__ import annotations

import base64
import os
import time
from pathlib import Path

from dotenv import load_dotenv

from ..base import ImageBackend

load_dotenv(dotenv_path=Path(__file__).resolve().parents[4] / ".env")

# ── Size mapping: canonical "WxH" → model-specific strings ──────────────────

_GPT_IMAGE_SIZES = {
    "1024x1024": "1024x1024",
    "1536x1024": "1536x1024",
    "1024x1536": "1024x1536",
    # landscape aliases
    "1792x1024": "1536x1024",
    "1024x1792": "1024x1536",
    # square aliases
    "512x512":  "1024x1024",
    "256x256":  "1024x1024",
}

_DALLE3_SIZES = {
    "1024x1024": "1024x1024",
    "1792x1024": "1792x1024",
    "1024x1792": "1024x1792",
    # square aliases
    "512x512":  "1024x1024",
    "256x256":  "1024x1024",
    # landscape aliases
    "1536x1024": "1792x1024",
    "1024x1536": "1024x1792",
}

_QUALITY_MAP_GPT = {
    "standard": "medium",
    "hd":       "high",
    "low":      "low",
    "medium":   "medium",
    "high":     "high",
}


class OpenAIBackend(ImageBackend):
    """OpenAI image generation: gpt-image-1 (default) or dall-e-3."""

    DEFAULT_MODEL = "gpt-image-1"

    def name(self) -> str:
        return "openai"

    def is_available(self) -> bool:
        if not os.getenv("OPENAI_API_KEY"):
            return False
        try:
            import openai  # noqa: F401
            return True
        except ImportError:
            return False

    def status(self) -> dict:
        key = os.getenv("OPENAI_API_KEY", "")
        return {
            "name": self.name(),
            "available": self.is_available(),
            "default_model": self.DEFAULT_MODEL,
            "key_hint": f"...{key[-6:]}" if len(key) > 10 else "(not set)",
            "supported_models": ["gpt-image-1", "dall-e-3"],
            "sizes": {
                "gpt-image-1": list(_GPT_IMAGE_SIZES.keys()),
                "dall-e-3": list(_DALLE3_SIZES.keys()),
            },
        }

    def generate(
        self,
        prompt: str,
        output_dir: str | Path,
        size: str = "1024x1024",
        quality: str = "standard",
        n: int = 1,
        model: str | None = None,
    ) -> list[str]:
        """
        Generate images using OpenAI's image API.

        For gpt-image-1: quality maps to "low" | "medium" | "high".
        For dall-e-3:    quality maps to "standard" | "hd".
        dall-e-3 is limited to n=1 per API call.

        Returns list of absolute paths to saved PNG files.
        """
        from openai import OpenAI  # type: ignore[import]

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError(
                "OPENAI_API_KEY is not set. Add it to .env:\n"
                "  OPENAI_API_KEY=sk-proj-..."
            )

        client = OpenAI(api_key=api_key)
        chosen_model = model or self.DEFAULT_MODEL
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        paths: list[str] = []

        if chosen_model == "dall-e-3":
            mapped_size = _DALLE3_SIZES.get(size, "1024x1024")
            mapped_quality = "hd" if quality in ("hd", "high") else "standard"

            # DALL-E 3 only supports n=1 per call; loop for n>1
            for i in range(n):
                response = client.images.generate(
                    model="dall-e-3",
                    prompt=prompt,
                    size=mapped_size,  # type: ignore[arg-type]
                    quality=mapped_quality,  # type: ignore[arg-type]
                    response_format="b64_json",
                    n=1,
                )
                img_data = response.data[0].b64_json
                path = self._save_b64(img_data, output_dir, i)
                paths.append(path)

        else:
            # gpt-image-1
            mapped_size = _GPT_IMAGE_SIZES.get(size, "1024x1024")
            mapped_quality = _QUALITY_MAP_GPT.get(quality, "medium")

            response = client.images.generate(
                model="gpt-image-1",
                prompt=prompt,
                size=mapped_size,  # type: ignore[arg-type]
                quality=mapped_quality,  # type: ignore[arg-type]
                n=min(n, 10),  # gpt-image-1 supports up to 10
            )
            for i, item in enumerate(response.data):
                b64 = getattr(item, "b64_json", None)
                if b64:
                    path = self._save_b64(b64, output_dir, i)
                elif getattr(item, "url", None):
                    path = self._download_url(item.url, output_dir, i)
                else:
                    continue
                paths.append(path)

        return paths

    # ── Internal helpers ─────────────────────────────────────────────────────

    @staticmethod
    def _slug(idx: int) -> str:
        return f"openai_{int(time.time())}_{idx:02d}"

    def _save_b64(self, b64_data: str, output_dir: Path, idx: int) -> str:
        img_bytes = base64.b64decode(b64_data)
        out = output_dir / f"{self._slug(idx)}.png"
        out.write_bytes(img_bytes)
        return str(out)

    def _download_url(self, url: str, output_dir: Path, idx: int) -> str:
        import urllib.request
        out = output_dir / f"{self._slug(idx)}.png"
        urllib.request.urlretrieve(url, str(out))
        return str(out)
