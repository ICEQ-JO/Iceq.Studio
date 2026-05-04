#!/usr/bin/env python3
import sys, os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.motion_graphics.bridge import render_template, _templates_dir

edit_dir = "/home/khalid/editing-workspace/Iceq Studio/Video Projects/Testing 2/edit"
slot = sys.argv[1]
title = sys.argv[2]
subtitle = sys.argv[3]
layout = sys.argv[4]
duration = float(sys.argv[5])

output_mp4 = f"{edit_dir}/animations/slot_{slot}/render.mp4"

path = render_template(
    template_path=_templates_dir() / "glassy-overlay.html",
    vars={
        "title": title,
        "subtitle": subtitle,
        "layout": layout,
    },
    output_mp4=output_mp4,
    duration=duration,
)
print(f"RENDERED: {path}")
