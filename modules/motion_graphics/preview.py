"""
modules/motion_graphics/preview.py

Quick local preview for motion-graphics templates.

Renders a template with sample data into a standalone HTML file that can be
opened in a browser. This is much faster than rendering to MP4 when iterating
on design.

Usage:
    python -m modules.motion_graphics preview \
        --template templates/editframe/lower-third.html \
        --output /tmp/preview.html

    python -m modules.motion_graphics preview \
        --template templates/lower-third.html \
        --serve 8000
"""

from __future__ import annotations

import argparse
import re
import subprocess
import tempfile
import webbrowser
from pathlib import Path


def _workspace_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _load_design_tokens() -> dict[str, str]:
    path = _workspace_root() / "templates" / "design-system.json"
    if not path.exists():
        return {}
    try:
        import json
        data = json.loads(path.read_text(encoding="utf-8"))
        return {k: str(v) for k, v in data.items() if not k.startswith("_")}
    except (Exception):
        return {}


def _inject_for_hyperframes(html: str, vars: dict[str, str]) -> str:
    """Inject vars as data-* attributes on #stage."""
    all_vars = {**_load_design_tokens(), **vars}

    def inject(m: re.Match) -> str:
        tag = m.group(0)
        for k, v in all_vars.items():
            attr = f"data-{k}"
            if attr not in tag:
                tag = tag[:-1] + f' {attr}="{v}">'
        return tag

    return re.sub(r'<div[^>]*id=["\']stage["\'][^>]*>', inject, html, count=1)


def _inject_for_editframe(html: str, vars: dict[str, str]) -> str:
    """
    For Editframe templates we inject window.__EF_DATA__ before the closing
    </head> or first <script> so the composition sees sample values locally.
    """
    import json

    all_vars = {**_load_design_tokens(), **vars}
    # Convert kebab-case design tokens to camelCase to match existing JS usage
    camel_vars: dict[str, str] = {}
    for k, v in all_vars.items():
        parts = k.split("-")
        camel = parts[0] + "".join(p.capitalize() for p in parts[1:])
        camel_vars[camel] = v

    data_script = (
        "<script>\n"
        "  window.__EF_DATA__ = "
        + json.dumps(camel_vars, indent=2)
        + ";\n"
        "</script>\n"
    )

    head_match = re.search(r"</head>", html, re.IGNORECASE)
    if head_match:
        return html[: head_match.start()] + data_script + html[head_match.start() :]
    # Fallback: prepend before first <script>
    script_match = re.search(r"<script", html, re.IGNORECASE)
    if script_match:
        return html[: script_match.start()] + data_script + html[script_match.start() :]
    return html + data_script


def build_preview(
    template_path: str | Path,
    vars: dict[str, str] | None = None,
    output_path: str | Path | None = None,
) -> Path:
    """
    Build a standalone preview HTML for a template.

    Auto-detects HyperFrames (#stage with data-*) vs Editframe (ef-configuration).
    """
    tpl = Path(template_path).resolve()
    if not tpl.exists():
        raise FileNotFoundError(f"Template not found: {tpl}")

    html = tpl.read_text(encoding="utf-8")
    user_vars = vars or {}

    if "ef-configuration" in html:
        html = _inject_for_editframe(html, user_vars)
    elif 'id="stage"' in html or "id='stage'" in html:
        html = _inject_for_hyperframes(html, user_vars)
    else:
        raise RuntimeError("Could not detect template engine (Editframe or HyperFrames).")

    out = Path(output_path) if output_path else Path(tempfile.gettempdir()) / f"preview_{tpl.name}"
    out = out.resolve()
    out.write_text(html, encoding="utf-8")
    return out


def serve_preview(preview_path: Path, port: int = 8000) -> None:
    """Open the preview in a browser via a temporary HTTP server."""
    url = f"http://127.0.0.1:{port}/{preview_path.name}"
    print(f"Serving preview at {url}")
    webbrowser.open(url)
    subprocess.run(
        ["python3", "-m", "http.server", str(port), "--directory", str(preview_path.parent)],
        check=True,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Preview motion-graphics templates")
    parser.add_argument("--template", required=True, help="Path to HTML template")
    parser.add_argument("--output", help="Where to write preview HTML")
    parser.add_argument("--var", action="append", default=[], help="Variable key=value")
    parser.add_argument("--serve", type=int, help="Start HTTP server on port")
    args = parser.parse_args()

    vars_dict: dict[str, str] = {}
    for item in args.var:
        if "=" not in item:
            raise ValueError(f"--var must be key=value, got: {item}")
        k, v = item.split("=", 1)
        vars_dict[k] = v

    # Sensible defaults for lower-third previews
    defaults = {
        "title": "Khalid Al-Mansouri",
        "subtitle": "Product Designer",
        "accentColor": "#FF5A00",
        "accent-color": "#FF5A00",
        "bgColor": "rgba(10,10,10,0.88)",
        "bg-color": "rgba(10,10,10,0.88)",
        "font": "Inter",
        "duration": "4",
    }
    for k, v in defaults.items():
        vars_dict.setdefault(k, v)

    out = build_preview(args.template, vars_dict, args.output)
    print(f"✅ Preview written to {out}")

    if args.serve:
        serve_preview(out, port=args.serve)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
