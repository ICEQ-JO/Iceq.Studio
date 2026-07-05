"""
CLI entry point for modules.motion_graphics.

Usage:
    python -m modules.motion_graphics preview --template templates/editframe/lower-third.html
"""

from __future__ import annotations

import sys


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python -m modules.motion_graphics preview [options]")
        return 1

    subcommand = sys.argv[1]
    if subcommand == "preview":
        # Remove the subcommand so argparse in preview.py sees only its own args
        sys.argv = [sys.argv[0], *sys.argv[2:]]
        from .preview import main as preview_main
        return preview_main()

    print(f"Unknown subcommand: {subcommand}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
