"""modules/images/backends/__init__.py — backend registry"""
from .openai_backend import OpenAIBackend
from .gemini_backend import GeminiBackend

__all__ = ["OpenAIBackend", "GeminiBackend"]
