from modules.motion_graphics import bridge

edit_dir = "/home/khalid/editing-workspace/Iceq Studio/video testing/edit"

# Render the glassy title card
path = bridge.render_template(
    template_path="/home/khalid/editing-workspace/templates/ios-glassy-title.html",
    vars={},
    output_mp4=f"{edit_dir}/animations/slot_glassy1/render.mp4",
    duration=6.0,
    fps=24,
    width=1920,
    height=1080
)

print(f"Motion graphic rendered to: {path}")
