"""
modules/images/base.py

Abstract base class for all image generation backends.

Every backend must implement:
  - name()         → str   (e.g. "openai", "gemini")
  - is_available() → bool  (checks API key is present and SDK is installed)
  - generate(...)  → list[str]  (local PNG paths, downloaded from API)

Size strings use the canonical format "WxH" (e.g. "1024x1024", "1792x1024").
Backends that don't support arbitrary sizes should map to their nearest supported value.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path


class ImageBackend(ABC):
    """Abstract interface for an image generation backend."""

    @abstractmethod
    def name(self) -> str:
        """Short lowercase identifier: 'openai', 'gemini', etc."""
        ...

    @abstractmethod
    def is_available(self) -> bool:
        """
        Return True if this backend can be used right now.
        Checks: API key in environment AND Python SDK installed.
        Should NOT make a network call.
        """
        ...

    @abstractmethod
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
        Generate n images from the prompt.

        Args:
            prompt:     The image prompt.
            output_dir: Directory where downloaded PNGs are saved.
            size:       Canonical "WxH" string. Backend maps to nearest supported size.
            quality:    "standard" | "hd" (backends that don't support this ignore it).
            n:          Number of images to generate (some backends limit to 1).
            model:      Override the default model for this backend (optional).

        Returns:
            List of absolute local PNG file paths.
        """
        ...

    def status(self) -> dict:
        """
        Return a status dict for display in `python -m modules.images status`.
        Override to add backend-specific info (model, max sizes, etc.).
        """
        return {
            "name": self.name(),
            "available": self.is_available(),
        }
