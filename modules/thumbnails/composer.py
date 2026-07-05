"""
modules/thumbnails/composer.py

Two thumbnail composition paths:

1. PIL path (fast, fully local):
   - Load the best extracted frame
   - Draw title text, optional gradient bar, optional icon
   - Save as PNG

2. HyperFrames path (high-quality):
   - Inject variables into a HTML template
   - Render via `npx hyperframes render` → PNG
   - Requires Node >= 22 and hyperframes installed

Both paths output a 1280×720 PNG by default.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
from pathlib import Path

# ─────────────────────────────────────────────────────────────────────────────
# PIL Compositor
# ─────────────────────────────────────────────────────────────────────────────

def _find_font(preferred: list[str]) -> str | None:
    """Return the first available font path from a list of candidates."""
    candidates = preferred + [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "C:/Windows/Fonts/arial.ttf",
    ]
    for c in candidates:
        if Path(c).exists():
            return c
    return None


def compose_thumbnail_pil(
    base_frame: str | Path,
    title: str,
    subtitle: str | None = None,
    output_path: str | Path | None = None,
    style: dict | None = None,
) -> str:
    """
    Composite a thumbnail using Pillow.

    Args:
        base_frame: Path to the source PNG/JPEG frame (extract with extractor.py).
        title: Main title text drawn on the thumbnail.
        subtitle: Optional secondary line below the title.
        output_path: Where to save the output PNG. Defaults to base_frame + '.thumb.png'.
        style: Optional dict with style overrides:
            {
                "bg_gradient": bool,       # dark gradient behind text (default True)
                "text_color": (R,G,B),     # default (255, 255, 255)
                "accent_color": (R,G,B),   # bar accent, default (255, 90, 0) — orange
                "font_path": str,          # explicit font path
                "title_size": int,         # pt, default 72
                "subtitle_size": int,      # pt, default 42
                "margin": int,             # px from edges, default 60
            }

    Returns:
        Absolute path to the saved thumbnail PNG.
    """
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        raise RuntimeError("Pillow is not installed. Run: pip install pillow")

    sty = style or {}
    bg_gradient: bool = sty.get("bg_gradient", True)
    text_color: tuple = sty.get("text_color", (255, 255, 255))
    accent_color: tuple = sty.get("accent_color", (255, 90, 0))
    title_size: int = sty.get("title_size", 72)
    subtitle_size: int = sty.get("subtitle_size", 42)
    margin: int = sty.get("margin", 60)

    font_path = sty.get("font_path") or _find_font([])
    title_font = ImageFont.truetype(font_path, title_size) if font_path else ImageFont.load_default()
    sub_font = ImageFont.truetype(font_path, subtitle_size) if font_path else ImageFont.load_default()

    # Load frame at 1280×720
    img = Image.open(base_frame).convert("RGBA").resize((1280, 720), Image.LANCZOS)

    # Optional dark gradient at bottom
    if bg_gradient:
        grad = Image.new("RGBA", (1280, 720), (0, 0, 0, 0))
        for y in range(720):
            alpha = int(220 * max(0, (y - 300) / 420))  # gradient from y=300 down
            for x in range(1280):
                grad.putpixel((x, y), (0, 0, 0, alpha))
        img = Image.alpha_composite(img, grad)

    draw = ImageDraw.Draw(img)

    # Accent bar
    bar_y = 720 - margin - title_size - (subtitle_size + 10 if subtitle else 0) - 12
    draw.rectangle([(margin, bar_y), (margin + 6, bar_y + title_size + (subtitle_size + 10 if subtitle else 0))],
                   fill=accent_color)

    # Title text (with soft drop shadow)
    tx, ty = margin + 20, bar_y
    # Shadow
    draw.text((tx + 2, ty + 2), title, font=title_font, fill=(0, 0, 0, 180))
    draw.text((tx, ty), title, font=title_font, fill=text_color)

    # Subtitle
    if subtitle:
        sy = ty + title_size + 10
        draw.text((tx + 2, sy + 2), subtitle, font=sub_font, fill=(0, 0, 0, 180))
        draw.text((tx, sy), subtitle, font=sub_font, fill=(200, 200, 200))

    # Save
    if output_path is None:
        output_path = Path(base_frame).with_suffix(".thumb.png")
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    img.convert("RGB").save(str(out), "PNG", optimize=True)
    return str(out)


# ─────────────────────────────────────────────────────────────────────────────
# HyperFrames Compositor
# ─────────────────────────────────────────────────────────────────────────────

def compose_thumbnail_hyperframes(
    base_frame: str | Path,
    template: str | Path,
    vars: dict[str, str],
    output_path: str | Path | None = None,
    workspace_root: str | Path | None = None,
) -> str:
    """
    Render a thumbnail using a HyperFrames HTML template.

    The template HTML is copied to a temp dir, the base_frame path and all
    `vars` are injected as data attributes on the #stage element, and then
    `npx hyperframes render` is run to produce a PNG.

    Args:
        base_frame: Path to the source PNG frame (will be set as --bg or data-bg).
        template: Path to a templates/*.html file in the workspace.
        vars: Dict of HyperFrames data-attribute variables, e.g.:
              {"title": "My Video Title", "accent-color": "#FF5A00"}
        output_path: Where to save the final PNG. Defaults next to base_frame.
        workspace_root: Path to the editing-workspace root. Auto-detected if not set.

    Returns:
        Absolute path to the rendered PNG.

    Raises:
        RuntimeError: If Node/npx/hyperframes is not installed.
    """
    if not shutil.which("npx"):
        raise RuntimeError(
            "npx not found. Install Node.js >= 22: https://nodejs.org/\n"
            "Then run: npm install (in the editing-workspace root)"
        )

    base_frame = Path(base_frame).resolve()
    template = Path(template).resolve()

    if not template.exists():
        raise FileNotFoundError(f"Template not found: {template}")
    if not base_frame.exists():
        raise FileNotFoundError(f"Base frame not found: {base_frame}")

    # Read template HTML
    html = template.read_text(encoding="utf-8")

    # Inject base_frame as a bg variable
    vars_with_bg = {"bg-image": str(base_frame), **vars}

    # Inject all vars as data-* attributes on the #stage element
    def inject_attrs(m: re.Match) -> str:
        tag = m.group(0)
        for k, v in vars_with_bg.items():
            attr = f'data-{k}="{v}"'
            if f"data-{k}" not in tag:
                tag = tag.rstrip(">") + f" {attr}>"
        return tag

    html = re.sub(r'<div[^>]*id=["\']stage["\'][^>]*>', inject_attrs, html, count=1)

    # Write modified HTML to a temp dir and render
    with tempfile.TemporaryDirectory() as tmp:
        tmp_html = Path(tmp) / "thumbnail.html"
        tmp_html.write_text(html, encoding="utf-8")

        if output_path is None:
            output_path = base_frame.with_suffix(".hf_thumb.png")
        out = Path(output_path).resolve()
        out.parent.mkdir(parents=True, exist_ok=True)

        # Determine workspace root for npx
        ws_root = Path(workspace_root).resolve() if workspace_root else Path(__file__).parents[2].resolve()

        cmd = [
            "npx", "hyperframes", "render",
            str(tmp_html),
            "--output", str(out),
            "--width", "1280",
            "--height", "720",
            "--format", "png",
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(ws_root))
        if result.returncode != 0:
            raise RuntimeError(
                f"HyperFrames render failed:\n{result.stderr}\n\n"
                "Make sure hyperframes is installed: npm install (in workspace root)"
            )

    return str(out)



# ─────────────────────────────────────────────────────────────────────────────
# AI Background Compositor
# ─────────────────────────────────────────────────────────────────────────────

def compose_thumbnail_ai_bg(
    prompt: str,
    title: str,
    subtitle: str | None = None,
    output_path: str | Path | None = None,
    backend: str = "auto",
    style: str = "thumbnail",
    size: str = "1792x1024",
    quality: str = "standard",
    pil_style: dict | None = None,
    assets_dir: str | Path | None = None,
) -> str:
    """
    Generate an AI background image, then composite title text on top with PIL.

    This is the fully AI-driven thumbnail path — no video frame extraction needed.
    The generated background is saved to assets_dir alongside the final thumbnail.

    Args:
        prompt:      Text prompt for the AI background (e.g. "dark studio with neon lights").
        title:       Main title text to composite on the thumbnail.
        subtitle:    Optional subtitle below the title.
        output_path: Where to save the final thumbnail PNG.
                     Defaults to <assets_dir>/thumbnail.png.
        backend:     Image generation backend: "openai" | "gemini" | "auto".
        style:       Style preset from STYLE_PRESETS (default: "thumbnail").
                     This prefix is prepended to the prompt automatically.
        size:        Image size for the background (default: "1792x1024" — landscape).
        quality:     Quality tier for the backend (default: "standard").
        pil_style:   Optional PIL compositor style overrides (see compose_thumbnail_pil).
        assets_dir:  Directory for intermediate generated images.
                     Defaults to output_path's parent / "assets".

    Returns:
        Absolute path to the saved thumbnail PNG.

    Example:
        path = compose_thumbnail_ai_bg(
            prompt="A developer at a glowing keyboard in a dark room",
            title="How I Edit Videos with AI",
            subtitle="Full Pipeline Explained",
            backend="openai",
            style="cinematic",
            output_path="edit/thumbnail.png",
        )
    """
    from ..images.generator import generate_image

    if output_path is None:
        if assets_dir:
            output_path = Path(assets_dir) / "thumbnail.png"
        else:
            output_path = Path(".") / "thumbnail.png"

    output_path = Path(output_path)
    bg_dir = Path(assets_dir) if assets_dir else output_path.parent / "assets"
    bg_dir.mkdir(parents=True, exist_ok=True)

    # Generate background with AI
    bg_paths = generate_image(
        prompt=prompt,
        backend=backend,
        size=size,
        quality=quality,
        output_dir=bg_dir,
        n=1,
        style_hint=style,
    )

    if not bg_paths:
        raise RuntimeError("Image generation returned no results.")

    bg_path = bg_paths[0]

    # Composite title text on the AI-generated background
    return compose_thumbnail_pil(
        base_frame=bg_path,
        title=title,
        subtitle=subtitle,
        output_path=output_path,
        style=pil_style,
    )


def compose_thumbnail_variants(
    base_frame: str | Path,
    titles: list[str],
    subtitle: str | None = None,
    output_dir: str | Path | None = None,
    accent_colors: list[tuple[int, int, int]] | None = None,
) -> list[str]:
    """
    Generate A/B thumbnail variants from the same base frame with different titles.

    Args:
        base_frame: Path to the source frame.
        titles: List of title texts (one per variant).
        subtitle: Optional subtitle shared across variants.
        output_dir: Directory for output PNGs. Defaults to base_frame's parent.
        accent_colors: Optional list of RGB tuples, one per variant.

    Returns:
        List of saved PNG paths, one per variant.
    """
    base_frame = Path(base_frame)
    out_dir = Path(output_dir) if output_dir else base_frame.parent
    out_dir.mkdir(parents=True, exist_ok=True)

    default_colors = [
        (255, 90, 0),    # orange
        (0, 150, 255),   # blue
        (255, 220, 0),   # yellow
    ]
    colors = accent_colors or default_colors

    paths: list[str] = []
    for i, title in enumerate(titles):
        color = colors[i % len(colors)]
        out_path = out_dir / f"thumbnail_variant_{i + 1}.png"
        path = compose_thumbnail_pil(
            base_frame=base_frame,
            title=title,
            subtitle=subtitle,
            output_path=out_path,
            style={"accent_color": color},
        )
        paths.append(path)

    return paths


# ─────────────────────────────────────────────────────────────────────────────
# CLI entry point
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    import argparse

    from .extractor import extract_candidate_frames, frames_from_edl, pick_best_frame

    parser = argparse.ArgumentParser(description="Thumbnail generator CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)

    gen = sub.add_parser("generate", help="Extract + compose a thumbnail from a video")
    gen.add_argument("--video", required=True, help="Path to input video (final.mp4 or source)")
    gen.add_argument("--edit-dir", required=True, help="Path to <footage>/edit/")
    gen.add_argument("--title", default="", help="Title text for the thumbnail")
    gen.add_argument("--subtitle", default="", help="Subtitle text")
    gen.add_argument("--method", default="pil", choices=["pil", "hyperframes"])
    gen.add_argument("--template", default="", help="Path to HyperFrames template (for --method hyperframes)")
    gen.add_argument("--timestamps", nargs="*", type=float, help="Specific timestamps to sample (seconds)")
    gen.add_argument("--variants", nargs="+", help="Generate A/B variants with these title texts")

    args = parser.parse_args()

    edit_dir = Path(args.edit_dir)
    edit_dir.mkdir(parents=True, exist_ok=True)

    # Extract frames
    edl_path = edit_dir / "edl.json"
    if args.timestamps:
        frames = extract_candidate_frames(args.video, args.timestamps, edit_dir / "verify")
    elif edl_path.exists():
        frames = frames_from_edl(args.video, edl_path, edit_dir / "verify")
    else:
        # Sample every 10 seconds up to 5 candidates
        import subprocess
        result = subprocess.run(
            ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
             "-of", "csv=p=0", args.video],
            capture_output=True, text=True
        )
        try:
            duration = float(result.stdout.strip())
        except ValueError:
            duration = 60.0
        ts = [duration * i / 5 for i in range(1, 5)]
        frames = extract_candidate_frames(args.video, ts, edit_dir / "verify")

    if not frames:
        print("❌ No frames could be extracted. Check the video path and ffmpeg installation.")
        return

    best = pick_best_frame(frames, criteria="sharpness")
    print(f"🎞  Best frame: {best}")

    if args.variants:
        variant_paths = compose_thumbnail_variants(
            base_frame=best,
            titles=args.variants,
            subtitle=args.subtitle or None,
            output_dir=edit_dir,
        )
        for path in variant_paths:
            print(f"✅ Thumbnail variant saved → {path}")
        # Also save the first variant as the default thumbnail.png
        import shutil as _shutil
        _shutil.copy(variant_paths[0], edit_dir / "thumbnail.png")
        return

    out_path = edit_dir / "thumbnail.png"

    if args.method == "hyperframes" and args.template:
        result_path = compose_thumbnail_hyperframes(
            base_frame=best,
            template=args.template,
            vars={"title": args.title or "My Video", "subtitle": args.subtitle},
            output_path=out_path,
        )
    else:
        result_path = compose_thumbnail_pil(
            base_frame=best,
            title=args.title or "My Video",
            subtitle=args.subtitle or None,
            output_path=out_path,
        )

    print(f"✅ Thumbnail saved → {result_path}")


if __name__ == "__main__":
    main()
