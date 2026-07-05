"""
modules/thumbnails/extractor.py

Extracts candidate frames from a video at specified timestamps
and picks the sharpest / most usable one.

All extraction uses ffmpeg — no extra Python video libraries needed.

Functions:
    extract_candidate_frames(video, timestamps, output_dir) → list[str]
    pick_best_frame(frames, criteria) → str
    frames_from_edl(video, edl_path, output_dir, n_per_beat) → list[str]
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path


def _run(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, check=check)


def extract_candidate_frames(
    video_path: str | Path,
    timestamps: list[float],
    output_dir: str | Path,
    width: int = 1280,
    height: int = 720,
) -> list[str]:
    """
    Extract one frame per timestamp from video_path using ffmpeg.

    Args:
        video_path: Absolute path to the video file.
        timestamps: List of float seconds at which to extract frames.
        output_dir: Directory where extracted PNGs are saved.
        width, height: Output frame dimensions (default 1280×720 — YouTube thumbnail size).

    Returns:
        List of absolute paths to extracted PNG files (existing frames only).
    """
    video_path = Path(video_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if not shutil.which("ffmpeg"):
        raise RuntimeError("ffmpeg not found on PATH. Install it first: https://ffmpeg.org/download.html")

    if not video_path.exists():
        raise FileNotFoundError(f"Video not found: {video_path}")

    extracted: list[str] = []

    for ts in timestamps:
        out_path = output_dir / f"candidate_{ts:.2f}s.png"
        cmd = [
            "ffmpeg", "-y",
            "-ss", str(ts),
            "-i", str(video_path),
            "-vframes", "1",
            "-vf", f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
                   f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:black",
            "-q:v", "2",
            str(out_path),
        ]
        result = _run(cmd, check=False)
        if result.returncode == 0 and out_path.exists():
            extracted.append(str(out_path))

    return extracted


def _sharpness_score(frame_path: str) -> float:
    """
    Compute a sharpness score for a PNG using the Laplacian variance method via PIL.
    Higher score = sharper image.
    """
    try:
        import numpy as np
        from PIL import Image, ImageFilter

        img = Image.open(frame_path).convert("L")  # grayscale
        laplacian = np.array(img.filter(ImageFilter.FIND_EDGES), dtype=np.float32)
        return float(np.var(laplacian))
    except Exception:
        return 0.0


def pick_best_frame(
    frames: list[str],
    criteria: str = "sharpness",
) -> str:
    """
    Pick the best frame from a list of candidate frame paths.

    Args:
        frames: List of paths returned by extract_candidate_frames.
        criteria: Scoring method. Currently only "sharpness" is supported
                  (Laplacian variance — high = sharp). Falls back to first
                  frame if PIL or numpy are unavailable.

    Returns:
        Path to the best frame. Returns frames[0] as fallback.
    """
    if not frames:
        raise ValueError("No candidate frames provided.")

    if len(frames) == 1:
        return frames[0]

    if criteria == "sharpness":
        scores = [(f, _sharpness_score(f)) for f in frames]
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[0][0]

    return frames[0]


def frames_from_edl(
    video_path: str | Path,
    edl_path: str | Path,
    output_dir: str | Path,
    n_per_beat: int = 1,
) -> list[str]:
    """
    Extract frames at the midpoint of each EDL segment.

    Args:
        video_path: Path to the edited final.mp4 (or any rendered output).
        edl_path: Path to edl.json.
        output_dir: Output directory for PNG frames.
        n_per_beat: How many frames to sample per segment (evenly spaced).

    Returns:
        List of extracted PNG paths.
    """
    edl_path = Path(edl_path)
    with edl_path.open("r", encoding="utf-8") as f:
        edl = json.load(f)

    timestamps: list[float] = []
    for seg in edl.get("ranges", []):
        start = float(seg["start"])
        end = float(seg["end"])
        if n_per_beat == 1:
            timestamps.append((start + end) / 2)
        else:
            step = (end - start) / (n_per_beat + 1)
            timestamps.extend(start + step * (i + 1) for i in range(n_per_beat))

    return extract_candidate_frames(video_path, timestamps, output_dir)
