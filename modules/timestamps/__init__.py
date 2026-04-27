"""
modules/timestamps — YouTube chapter timestamp generator.

Reads edit/edl.json + edit/takes_packed.md and produces
edit/timestamps.txt in standard YouTube format.

Usage:
    python -m modules.timestamps generate --edit-dir /path/to/edit/

Module API:
    from modules.timestamps import generator
    ts = generator.generate_timestamps(edit_dir="/path/to/edit/")
    print(ts)
"""

from .generator import generate_timestamps

__all__ = ["generate_timestamps"]
