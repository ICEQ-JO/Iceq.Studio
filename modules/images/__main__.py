"""
modules/images/__main__.py — CLI entry point

Commands:
    python -m modules.images status
    python -m modules.images generate --prompt "..." [options]
    python -m modules.images thumbnail-bg --prompt "..." --edit-dir "..."
    python -m modules.images styles
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def cmd_status(args: argparse.Namespace) -> None:
    """Show availability of all backends."""
    from .generator import list_backends

    backends = list_backends()
    if args.json:
        print(json.dumps(backends, indent=2))
        return

    print("\n🎨  Image Generation Backends\n")
    for b in backends:
        icon = "✅" if b["available"] else "❌"
        name = b["name"].upper()
        print(f"  {icon}  {name}")
        for k, v in b.items():
            if k in ("name", "available"):
                continue
            print(f"       {k}: {v}")
        print()


def cmd_styles(args: argparse.Namespace) -> None:
    """List all style presets."""
    from .generator import STYLE_PRESETS

    print("\n🎨  Style Presets\n")
    max_key = max(len(k) for k in STYLE_PRESETS)
    for key, prefix in STYLE_PRESETS.items():
        print(f"  {key:<{max_key}}  →  {prefix[:70]}...")
    print()


def cmd_generate(args: argparse.Namespace) -> None:
    """Generate one or more images from a prompt."""
    from .generator import generate_image

    output_dir = Path(args.output_dir)

    print(f"\n🎨  Generating {args.n} image(s) with [{args.backend}] backend…")
    if args.style:
        print(f"    Style: {args.style}")
    print(f"    Prompt: {args.prompt[:80]}{'…' if len(args.prompt) > 80 else ''}")
    print(f"    Size: {args.size}  Quality: {args.quality}")
    print()

    try:
        paths = generate_image(
            prompt=args.prompt,
            backend=args.backend,
            size=args.size,
            quality=args.quality,
            output_dir=output_dir,
            n=args.n,
            style_hint=args.style or "",
            model=args.model or None,
        )
        print(f"✅  Generated {len(paths)} image(s):")
        for p in paths:
            print(f"    {p}")
        print()
    except RuntimeError as e:
        print(f"❌  {e}", file=sys.stderr)
        sys.exit(1)


def cmd_thumbnail_bg(args: argparse.Namespace) -> None:
    """Generate a thumbnail background image and save to edit/assets/."""
    from .generator import generate_image

    edit_dir = Path(args.edit_dir)
    output_dir = edit_dir / "assets"
    output_dir.mkdir(parents=True, exist_ok=True)

    print("\n🖼   Generating thumbnail background…")
    print(f"    Prompt: {args.prompt[:80]}")
    print(f"    Backend: {args.backend}  Style: {args.style or 'thumbnail'}")
    print()

    try:
        paths = generate_image(
            prompt=args.prompt,
            backend=args.backend,
            size=args.size,
            quality=args.quality,
            output_dir=output_dir,
            n=args.n,
            style_hint=args.style or "thumbnail",
        )

        # Compose thumbnail with PIL if --title is provided
        if args.title and paths:
            from ..thumbnails.composer import compose_thumbnail_pil
            out_path = edit_dir / "thumbnail.png"
            result = compose_thumbnail_pil(
                base_frame=paths[0],
                title=args.title,
                subtitle=args.subtitle or None,
                output_path=out_path,
            )
            print(f"✅  Thumbnail composed → {result}")
        else:
            print("✅  Background images saved:")
            for p in paths:
                print(f"    {p}")
            if paths:
                print("\n💡  Tip: use --title 'My Title' to auto-composite text on the image.")
        print()

    except RuntimeError as e:
        print(f"❌  {e}", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="python -m modules.images",
        description="AI image generation for the editing workspace",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    # ── status ────────────────────────────────────────────────────────────────
    p_status = sub.add_parser("status", help="Show backend availability")
    p_status.add_argument("--json", action="store_true", help="Output as JSON")

    # ── styles ────────────────────────────────────────────────────────────────
    sub.add_parser("styles", help="List all style presets")

    # ── generate ──────────────────────────────────────────────────────────────
    p_gen = sub.add_parser("generate", help="Generate images from a prompt")
    p_gen.add_argument("--prompt", "-p", required=True, help="Image generation prompt")
    p_gen.add_argument("--backend", "-b", default="auto",
                       choices=["auto", "openai", "gemini"],
                       help="Backend to use (default: auto)")
    p_gen.add_argument("--size", "-s", default="1024x1024",
                       help="Image size: 1024x1024, 1792x1024, 1024x1792, etc.")
    p_gen.add_argument("--quality", "-q", default="standard",
                       choices=["standard", "hd", "low", "medium", "high"],
                       help="Image quality (default: standard)")
    p_gen.add_argument("--style", help="Style preset key (see: python -m modules.images styles)")
    p_gen.add_argument("--n", type=int, default=1, help="Number of images to generate")
    p_gen.add_argument("--output-dir", "-o", default=".", help="Output directory")
    p_gen.add_argument("--model", help="Force a specific model (e.g. dall-e-3, gpt-image-1)")

    # ── thumbnail-bg ──────────────────────────────────────────────────────────
    p_tbg = sub.add_parser("thumbnail-bg",
                            help="Generate an AI thumbnail background (optionally composite text)")
    p_tbg.add_argument("--prompt", "-p", required=True, help="Background image prompt")
    p_tbg.add_argument("--edit-dir", required=True, help="Project edit/ directory")
    p_tbg.add_argument("--title", help="Title text to composite on the thumbnail")
    p_tbg.add_argument("--subtitle", help="Subtitle text below the title")
    p_tbg.add_argument("--backend", "-b", default="auto",
                       choices=["auto", "openai", "gemini"])
    p_tbg.add_argument("--size", default="1792x1024",
                       help="Background image size (default: 1792x1024 — landscape)")
    p_tbg.add_argument("--quality", default="standard",
                       choices=["standard", "hd", "low", "medium", "high"])
    p_tbg.add_argument("--style", default="thumbnail",
                       help="Style preset (default: thumbnail)")
    p_tbg.add_argument("--n", type=int, default=1,
                       help="Number of background variants to generate")

    args = parser.parse_args()

    dispatch = {
        "status":       cmd_status,
        "styles":       cmd_styles,
        "generate":     cmd_generate,
        "thumbnail-bg": cmd_thumbnail_bg,
    }
    dispatch[args.cmd](args)


if __name__ == "__main__":
    main()
