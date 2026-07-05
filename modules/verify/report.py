"""
modules/verify/report.py

Orchestrates quality checks and writes a structured markdown report.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from .checks import (
    CheckResult,
    check_black_frames,
    check_duration,
    check_file_exists,
    check_loudness,
    check_silence,
    check_subtitles,
)


@dataclass
class VerifyReport:
    video_path: Path
    edl_path: Path | None
    results: list[CheckResult] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    @property
    def overall(self) -> str:
        statuses = {r.status for r in self.results}
        if "fail" in statuses:
            return "fail"
        if "warn" in statuses:
            return "warn"
        return "pass"

    def to_markdown(self) -> str:
        lines = [
            "---",
            "type: verify_report",
            f"status: {self.overall}",
            f"date: {self.created_at}",
            f"video: {self.video_path}",
            f"edl: {self.edl_path or 'none'}",
            "tags: [video/verify]",
            "---",
            "# Render Quality Report",
            "",
            f"**Overall:** {self.overall.upper()}",
            f"**Video:** `{self.video_path}`",
            f"**EDL:** `{self.edl_path or 'none'}`",
            "",
            "| Check | Status | Message |",
            "|-------|--------|---------|",
        ]
        for r in self.results:
            icon = {"pass": "✅", "warn": "⚠️", "fail": "❌"}.get(r.status, "")
            lines.append(f"| {r.name} | {icon} {r.status.upper()} | {r.message} |")

        lines += ["", "## Details", ""]
        for r in self.results:
            lines.append(f"### {r.name}")
            lines.append(f"- **Status:** {r.status}")
            lines.append(f"- **Message:** {r.message}")
            if r.details:
                lines.append("- **Details:**")
                for key, value in r.details.items():
                    lines.append(f"  - `{key}`: `{json.dumps(value, default=str)}`")
            lines.append("")

        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        return {
            "created_at": self.created_at,
            "video_path": str(self.video_path),
            "edl_path": str(self.edl_path) if self.edl_path else None,
            "overall": self.overall,
            "results": [
                {"name": r.name, "status": r.status, "message": r.message, "details": r.details}
                for r in self.results
            ],
        }


def verify_render(
    edl_path: str | Path | None,
    video_path: str | Path,
    output_dir: str | Path,
) -> VerifyReport:
    """
    Run the full quality gate against a rendered video.

    Args:
        edl_path: Path to the EDL JSON. If None, only file-level checks run.
        video_path: Path to the rendered MP4.
        output_dir: Directory where verify/report.md and verify/report.json are saved.

    Returns:
        VerifyReport with all check results.
    """
    video_path = Path(video_path).resolve()
    output_dir = Path(output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    edl: dict[str, Any] = {}
    if edl_path:
        edl_path = Path(edl_path).resolve()
        if edl_path.exists():
            with edl_path.open("r", encoding="utf-8") as f:
                edl = json.load(f)

    report = VerifyReport(video_path=video_path, edl_path=edl_path)

    # Always run file existence first; skip downstream checks if missing.
    report.results.append(check_file_exists(video_path))
    if report.results[-1].status == "fail":
        report.results.extend([
            CheckResult("duration", "skip", "Video file missing"),
            CheckResult("black_frames", "skip", "Video file missing"),
            CheckResult("silence", "skip", "Video file missing"),
            CheckResult("loudness", "skip", "Video file missing"),
            CheckResult("subtitles", "skip", "Video file missing"),
        ])
    else:
        report.results.append(check_duration(edl, video_path))
        report.results.append(check_black_frames(video_path))
        report.results.append(check_silence(video_path))
        report.results.append(check_loudness(video_path))
        report.results.append(check_subtitles(video_path, edl))

    # Write outputs
    (output_dir / "report.md").write_text(report.to_markdown(), encoding="utf-8")
    (output_dir / "report.json").write_text(json.dumps(report.to_dict(), indent=2), encoding="utf-8")

    return report
