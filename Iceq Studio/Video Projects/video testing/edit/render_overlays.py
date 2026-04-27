from modules.motion_graphics import bridge
from pathlib import Path

edit_dir = "/home/khalid/editing-workspace/Iceq Studio/Video Projects/video testing/edit"
template = "templates/ios-glassy-dynamic.html"

# 1. Lower Third Intro
bridge.render_template(
    template_path=template,
    vars={
        "title": "Iceq Studio Demo",
        "subtitle": "AI Video Workspace",
        "layout": "lower-third"
    },
    output_mp4=f"{edit_dir}/animations/slot_lt1/render.mp4",
    duration=4.0
)

# 2. Gemma 4 Info Card
bridge.render_template(
    template_path=template,
    vars={
        "title": "Gemma 4 Architecture",
        "subtitle": "Latest AI Model by Google",
        "layout": "center"
    },
    output_mp4=f"{edit_dir}/animations/slot_tc1/render.mp4",
    duration=5.0
)

# 3. Outro Badge
bridge.render_template(
    template_path=template,
    vars={
        "title": "Edited with i6 Studio",
        "subtitle": "Fast & Intelligent",
        "layout": "center"
    },
    output_mp4=f"{edit_dir}/animations/slot_end1/render.mp4",
    duration=4.0
)
