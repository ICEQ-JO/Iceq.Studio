"""
modules/transcription

Hash-based transcription cache wrapper around tools/video-use/helpers/transcribe.py.

video-use already caches by filename, which is fast but fragile: renaming or moving
a source file causes a re-transcription. This module caches by file content hash so
identical footage never gets transcribed twice, even across projects.

Public API:
    from modules.transcription import transcribe_video
    path = transcribe_video("/path/to/footage/video.mp4", edit_dir="/path/to/edit")

CLI:
    python -m modules.transcription /path/to/video.mp4 --edit-dir /path/to/edit
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path


def _file_hash(path: Path) -> str:
    """Return a fast sha256 hash of the first and last 8 MB of a file."""
    h = hashlib.sha256()
    size = path.stat().st_size
    with path.open("rb") as f:
        h.update(f.read(8192 * 1024))
        if size > 16 * 1024 * 1024:
            f.seek(-8192 * 1024, 2)
            h.update(f.read(8192 * 1024))
        else:
            h.update(f.read())
    return h.hexdigest()[:16]


def _hash_metadata_path(transcripts_dir: Path, file_hash: str) -> Path:
    return transcripts_dir / f"{file_hash}.source.json"


def _find_cached_transcript(transcripts_dir: Path, file_hash: str) -> Path | None:
    """Return the cached transcript path if a source with this hash was already transcribed."""
    meta = _hash_metadata_path(transcripts_dir, file_hash)
    if not meta.exists():
        return None
    try:
        data = json.loads(meta.read_text(encoding="utf-8"))
        cached = Path(data["transcript_path"])
        if cached.exists():
            return cached
    except (json.JSONDecodeError, KeyError, OSError):
        pass
    return None


def transcribe_video(
    video_path: str | Path,
    edit_dir: str | Path,
    language: str | None = None,
    num_speakers: int | None = None,
) -> Path:
    """
    Transcribe a video with content-hash caching.

    Args:
        video_path: Path to the video file.
        edit_dir: The edit/ directory where transcripts/ will be created.
        language: Optional language code passed to Scribe.
        num_speakers: Optional speaker count passed to Scribe.

    Returns:
        Path to the transcript JSON.
    """
    from ..observability import PipelineLogger

    video = Path(video_path).resolve()
    edit = Path(edit_dir).resolve()
    logger = PipelineLogger(edit)
    transcripts_dir = edit / "transcripts"
    transcripts_dir.mkdir(parents=True, exist_ok=True)

    file_hash = _file_hash(video)
    cached = _find_cached_transcript(transcripts_dir, file_hash)
    if cached:
        print(f"[transcription] cached by hash: {cached.name}")
        logger.log("transcription.hit", {"video": video.name, "hash": file_hash, "path": str(cached)})
        return cached

    logger.log("transcription.miss", {"video": video.name, "hash": file_hash})

    # video-use transcribe.py caches by stem; call it and then record the hash mapping.
    cmd = [
        "python3",
        str(Path(__file__).resolve().parents[2] / "tools" / "video-use" / "helpers" / "transcribe.py"),
        str(video),
        "--edit-dir", str(edit),
    ]
    if language:
        cmd.extend(["--language", language])
    if num_speakers:
        cmd.extend(["--num-speakers", str(num_speakers)])

    with logger.timed("transcription.scribe", {"video": video.name, "hash": file_hash}):
        result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"Transcription failed for {video.name}:\n"
            f"STDOUT: {result.stdout}\nSTDERR: {result.stderr}"
        )

    # video-use writes to <video_stem>.json
    transcript_path = transcripts_dir / f"{video.stem}.json"
    if not transcript_path.exists():
        raise RuntimeError(
            f"Expected transcript at {transcript_path} after transcription, but it is missing."
        )

    # Record the hash mapping for future lookups
    meta = _hash_metadata_path(transcripts_dir, file_hash)
    meta.write_text(
        json.dumps({
            "video_hash": file_hash,
            "video_path": str(video),
            "transcript_path": str(transcript_path),
        }, indent=2),
        encoding="utf-8",
    )

    print(f"[transcription] transcribed: {transcript_path.name}")
    logger.log("transcription.done", {"video": video.name, "hash": file_hash, "path": str(transcript_path)})
    return transcript_path


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Hash-cached video transcription wrapper")
    parser.add_argument("video", help="Path to video file")
    parser.add_argument("--edit-dir", required=True, help="Path to <footage>/edit/")
    parser.add_argument("--language", help="Language code for Scribe")
    parser.add_argument("--num-speakers", type=int, help="Number of speakers")
    args = parser.parse_args()

    path = transcribe_video(
        args.video,
        args.edit_dir,
        language=args.language,
        num_speakers=args.num_speakers,
    )
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
