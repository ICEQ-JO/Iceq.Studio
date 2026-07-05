"""
CLI entry point for modules.verify.

Usage:
    python -m modules.verify --edl edit/edl.json --video edit/final.mp4 --out edit/verify
    python -m modules.verify --video edit/preview.mp4 --out edit/verify
"""

from __future__ import annotations

import argparse
import sys

from .report import verify_render


def main() -> int:
    parser = argparse.ArgumentParser(description="Render quality gate")
    parser.add_argument("--edl", help="Path to edl.json (optional)")
    parser.add_argument("--video", required=True, help="Path to rendered video")
    parser.add_argument("--out", default="edit/verify", help="Output directory for report")
    args = parser.parse_args()

    report = verify_render(edl_path=args.edl, video_path=args.video, output_dir=args.out)
    print(report.to_markdown())
    print(f"\n✅ Report saved to {args.out}/report.md")

    return 0 if report.overall != "fail" else 1


if __name__ == "__main__":
    sys.exit(main())
