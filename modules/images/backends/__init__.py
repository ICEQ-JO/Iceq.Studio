"""modules/images/backends/__init__.py — backend registry"""
from .gemini_backend import GeminiBackend
from .openai_backend import OpenAIBackend

__all__ = ["OpenAIBackend", "GeminiBackend"]
