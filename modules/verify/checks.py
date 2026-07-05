"""
modules/verify/checks.py

Individual quality checks for a rendered video against its EDL.
All checks are read-only: they inspect files but never modify them.
"""

from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class CheckResult:
    name: str
    status: str  # "pass", "warn", "fail"
    message: str
    details: dict[str, Any] | None = None


def _ffprobe_duration(video_path: Path) -> float:
    """Return video duration in seconds via ffprobe."""
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(video_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return float(result.stdout.strip())


def _ffmpeg_loudness(video_path: Path) -> dict[str, float]:
    """Run the loudnorm filter in analysis mode and return LUFS stats."""
    cmd = [
        "ffmpeg", "-i", str(video_path),
        "-af", "loudnorm=print_format=json",
        "-f", "null", "-",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    # The JSON is printed to stderr after the "[Parsed_loudnorm_0" line.
    match = re.search(r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", result.stderr)
    if not match:
        raise RuntimeError("Could not parse loudnorm output")
    data = json.loads(match.group(0))
    return {
        "input_i": float(data.get("input_i", -70)),
        "input_tp": float(data.get("input_tp", 0)),
        "input_lra": float(data.get("input_lra", 0)),
        "input_thresh": float(data.get("input_thresh", -70)),
        "target_offset": float(data.get("target_offset", 0)),
    }


def _detect_black_frames(video_path: Path, duration: float) -> list[dict[str, float]]:
    """Return list of black-frame intervals using blackdetect."""
    cmd = [
        "ffmpeg", "-i", str(video_path),
        "-vf", "blackdetect=d=0.5:pix_th=0.10",
        "-an", "-f", "null", "-",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    intervals = []
    for line in result.stderr.splitlines():
        if "blackdetect" in line and "black_start:" in line:
            start_match = re.search(r"black_start:([\d.]+)", line)
            end_match = re.search(r"black_end:([\d.]+)", line)
            if start_match and end_match:
                start = float(start_match.group(1))
                end = float(end_match.group(1))
                intervals.append({"start": start, "end": end, "duration": end - start})
    return intervals


def _detect_silence(video_path: Path, duration: float) -> list[dict[str, float]]:
    """Return list of silent intervals using silencedetect."""
    cmd = [
        "ffmpeg", "-i", str(video_path),
        "-af", "silencedetect=noise=-50dB:d=0.5",
        "-f", "null", "-",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    intervals = []
    starts: list[float] = []
    ends: list[float] = []
    for line in result.stderr.splitlines():
        if "silence_start:" in line:
            m = re.search(r"silence_start:([\d.]+)", line)
            if m:
                starts.append(float(m.group(1)))
        elif "silence_end:" in line:
            m = re.search(r"silence_end:([\d.]+)", line)
            if m:
                ends.append(float(m.group(1)))
    for s, e in zip(starts, ends):
        intervals.append({"start": s, "end": e, "duration": e - s})
    return intervals


def _detect_subtitle_burnin(video_path: Path) -> bool:
    """
    Heuristic: check if the video has more than one subtitle stream or if
    a typical subtitle filter was applied. We cannot detect burned-in text
    visually without OCR, so we report this as a manual check hint.
    """
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "stream=codec_name",
        "-of", "default=noprint_wrappers=1",
        str(video_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return "subrip" in result.stdout or "mov_text" in result.stdout


def check_file_exists(video_path: Path) -> CheckResult:
    if video_path.exists() and video_path.stat().st_size > 0:
        return CheckResult("file_exists", "pass", f"{video_path.name} exists ({video_path.stat().st_size} bytes)")
    return CheckResult("file_exists", "fail", f"{video_path} is missing or empty")


def check_duration(edl: dict[str, Any], video_path: Path) -> CheckResult:
    expected = float(edl.get("total_duration_s", 0))
    actual = _ffprobe_duration(video_path)
    diff = abs(actual - expected)
    details = {"expected_s": expected, "actual_s": actual, "diff_s": diff}

    if expected <= 0:
        return CheckResult("duration", "warn", "EDL has no total_duration_s; cannot verify", details)
    if diff < 0.5:
        return CheckResult("duration", "pass", f"Duration matches EDL within {diff:.2f}s", details)
    if diff < 2.0:
        return CheckResult("duration", "warn", f"Duration differs by {diff:.2f}s", details)
    return CheckResult("duration", "fail", f"Duration differs by {diff:.2f}s", details)


def check_black_frames(video_path: Path) -> CheckResult:
    duration = _ffprobe_duration(video_path)
    black = _detect_black_frames(video_path, duration)
    total_black = sum(i["duration"] for i in black)
    details = {"black_intervals": black, "total_black_s": total_black}

    if not black:
        return CheckResult("black_frames", "pass", "No black frames detected", details)
    if total_black < 1.0:
        return CheckResult("black_frames", "warn", f"{total_black:.2f}s of black frames detected", details)
    return CheckResult("black_frames", "fail", f"{total_black:.2f}s of black frames detected", details)


def check_silence(video_path: Path) -> CheckResult:
    duration = _ffprobe_duration(video_path)
    silent = _detect_silence(video_path, duration)
    total_silent = sum(i["duration"] for i in silent)
    details = {"silent_intervals": silent, "total_silent_s": total_silent}

    if not silent:
        return CheckResult("silence", "pass", "No long silent stretches detected", details)
    if total_silent < 1.0:
        return CheckResult("silence", "warn", f"{total_silent:.2f}s of silence detected", details)
    return CheckResult("silence", "fail", f"{total_silent:.2f}s of silence detected", details)


def check_loudness(video_path: Path) -> CheckResult:
    stats = _ffmpeg_loudness(video_path)
    lufs = stats["input_i"]
    peak = stats["input_tp"]
    details = {"integrated_lufs": lufs, "true_peak_db": peak}

    # YouTube normalizes to -14 LUFS; final export should be close.
    if lufs < -20:
        return CheckResult("loudness", "warn", f"Quiet audio ({lufs:.1f} LUFS)", details)
    if peak > 0:
        return CheckResult("loudness", "fail", f"Audio clipping detected ({peak:.1f} dBTP)", details)
    if lufs > -12:
        return CheckResult("loudness", "warn", f"Very loud audio ({lufs:.1f} LUFS)", details)
    return CheckResult("loudness", "pass", f"Loudness {lufs:.1f} LUFS, peak {peak:.1f} dBTP", details)


def check_subtitles(video_path: Path, edl: dict[str, Any]) -> CheckResult:
    expected = bool(edl.get("subtitles"))
    has_stream = _detect_subtitle_burnin(video_path)
    details = {"edl_expects_subtitles": expected, "has_subtitle_stream": has_stream}

    if expected and not has_stream:
        return CheckResult(
            "subtitles",
            "warn",
            "EDL expects subtitles but none detected (may be burned-in; visual check recommended)",
            details,
        )
    if expected:
        return CheckResult("subtitles", "pass", "Subtitle stream detected", details)
    return CheckResult("subtitles", "pass", "EDL does not expect subtitles", details)
