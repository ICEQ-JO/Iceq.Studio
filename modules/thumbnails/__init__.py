"""
modules/thumbnails — Video thumbnail generator.

Two rendering paths:
  1. Fast (PIL): extract a frame → composite text/overlays with Pillow → PNG
  2. High-quality (HyperFrames): render an HTML template to a 1280×720 PNG

Usage:
    python -m modules.thumbnails generate \\
        --video /path/to/final.mp4 \\
        --edit-dir /path/to/edit/

Module API:
    from modules.thumbnails import extractor, composer
    frames = extractor.extract_candidate_frames(video, timestamps=[5.0, 30.0, 60.0], output_dir=edit_dir)
    best   = extractor.pick_best_frame(frames)
    out    = composer.compose_thumbnail_pil(best, title="My Title", output_path="thumbnail.png")
"""

from .composer import (
    compose_thumbnail_ai_bg,
    compose_thumbnail_hyperframes,
    compose_thumbnail_pil,
    compose_thumbnail_variants,
)
from .extractor import extract_candidate_frames, pick_best_frame

__all__ = [
    "extract_candidate_frames",
    "pick_best_frame",
    "compose_thumbnail_pil",
    "compose_thumbnail_hyperframes",
    "compose_thumbnail_ai_bg",
    "compose_thumbnail_variants",
]
