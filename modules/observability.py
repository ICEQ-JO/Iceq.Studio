"""
modules/observability.py

Lightweight structured logging for the editing pipeline.

Writes JSON Lines to <edit_dir>/logs/pipeline.jsonl so each run is inspectable
and diffable. Each log entry has a timestamp, event name, duration_ms, and
arbitrary payload.

Usage:
    from modules.observability import PipelineLogger

    logger = PipelineLogger("/path/to/edit")
    with logger.timed("transcribe"):
        transcribe_video(...)
    logger.log("render", {"output": "final.mp4", "duration_s": 87.4})
"""

from __future__ import annotations

import json
import time
from collections.abc import Generator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


class PipelineLogger:
    """Append-only JSONL logger scoped to an edit directory."""

    def __init__(self, edit_dir: str | Path, run_id: str | None = None):
        self.edit_dir = Path(edit_dir).resolve()
        self.log_dir = self.edit_dir / "logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.log_dir / "pipeline.jsonl"
        self.run_id = run_id or datetime.now(UTC).strftime("%Y%m%d-%H%M%S")

    def log(self, event: str, payload: dict[str, Any] | None = None) -> None:
        """Write a single structured log entry."""
        entry = {
            "ts": datetime.now(UTC).isoformat(),
            "run_id": self.run_id,
            "event": event,
            "payload": payload or {},
        }
        with self.log_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, default=str) + "\n")

    @contextmanager
    def timed(self, event: str, payload: dict[str, Any] | None = None) -> Generator[None, None, None]:
        """Context manager that logs start and end with duration_ms."""
        merged = dict(payload or {})
        self.log(f"{event}.start", merged)
        t0 = time.perf_counter()
        try:
            yield
        except Exception as e:
            duration_ms = int((time.perf_counter() - t0) * 1000)
            self.log(f"{event}.error", {**merged, "duration_ms": duration_ms, "error": str(e)})
            raise
        duration_ms = int((time.perf_counter() - t0) * 1000)
        self.log(f"{event}.end", {**merged, "duration_ms": duration_ms})

    def read(self, limit: int = 1000) -> list[dict[str, Any]]:
        """Read the most recent log entries (newest last)."""
        if not self.log_file.exists():
            return []
        lines = self.log_file.read_text(encoding="utf-8").splitlines()
        return [json.loads(line) for line in lines[-limit:]]
