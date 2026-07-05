"""
modules/verify

Render quality gate for the video-use pipeline.

Runs after `render.py` to check that `final.mp4` (or any output) matches the
intent expressed in `edl.json`. Produces a structured `verify/report.md` with
pass/warn/fail status for each check.

Public API:
    from modules.verify import verify_render
    report = verify_render("edit/edl.json", "edit/final.mp4", "edit/verify")

CLI:
    python -m modules.verify --edl edit/edl.json --video edit/final.mp4 --out edit/verify
"""

from __future__ import annotations

from .report import VerifyReport, verify_render

__all__ = ["verify_render", "VerifyReport"]
