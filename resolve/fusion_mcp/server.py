#!/usr/bin/env python3
"""
Fusion Motion Graphics MCP server.

Exposes motion-design tools to Claude Code for DaVinci Resolve, including the
FREE edition, which blocks external scripting.

TWO PATHS, AND THE FIRST ONE ALWAYS WORKS
  offline  generate a Fusion node graph and put it on the clipboard; you press
           Ctrl+V in the Fusion node editor. Touches no sandboxed API, so it
           works on Resolve Free regardless of what its Lua environment allows.
  live     if bridge/resolve_bridge_free.lua is running inside Resolve, the
           graph can be pushed straight in, and the comp inspected/edited.

Every generate tool validates its own output before returning, so a malformed
graph is reported here rather than discovered after pasting.
"""
import os, subprocess, sys, json, platform

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "bridge"))
sys.path.insert(0, os.path.join(HERE, "..", "promo"))

import compbuilder as cb          # noqa: E402
import templates as tpl           # noqa: E402
import validate as V              # noqa: E402

try:
    from fastmcp import FastMCP
except ImportError:                                    # official MCP SDK layout
    from mcp.server.fastmcp import FastMCP

mcp = FastMCP("fusion-motion-graphics")


def workdir():
    d = os.environ.get("FUSION_MCP_DIR")
    if not d:
        d = "C:/promo" if platform.system() == "Windows" else \
            os.path.join(os.path.expanduser("~"), "promo")
    os.makedirs(d, exist_ok=True)
    os.makedirs(os.path.join(d, "assets"), exist_ok=True)
    return d.replace("\\", "/")


def _write(name, text):
    p = os.path.join(workdir(), name if name.endswith(".comp") else name + ".comp")
    with open(p, "w", encoding="utf-8") as f:
        f.write(text)
    return p.replace("\\", "/")


def _emit(spec, name):
    """Render, validate, write. Never returns an unvalidated graph."""
    try:
        text, n = cb.render(spec)
    except cb.SpecError as e:
        return {"ok": False, "error": "spec rejected: %s" % e}
    rep = V.validate(text)
    if not rep["ok"]:
        return {"ok": False, "error": "generated graph failed validation",
                "problems": rep["errors"], "stats": rep["stats"]}
    path = _write(name, text)
    return {"ok": True, "path": path, "nodes": n, "stats": rep["stats"],
            "warnings": rep["warnings"],
            "next": "call send_to_clipboard(%r), then press Ctrl+V in the "
                    "Fusion node editor; connect FINAL_OUT to MediaOut1 and "
                    "set the render range to 0-%d" % (path, rep["stats"]["frames"] - 1)}


def _bridge(timeout=15.0):
    from bridge_client_free import Bridge, BridgeError
    b = Bridge(os.environ.get("FUSION_BRIDGE_DIR"), timeout=timeout)
    b.handshake()
    return b, BridgeError


# ------------------------------------------------------------------ offline
@mcp.tool()
def describe_spec_format() -> str:
    """Return the motion-design spec schema accepted by make_composition.

    Read this before composing anything custom. Coordinates are 0-1 with y
    pointing up; timing is in frames and scene-relative.
    """
    return json.dumps({
        "top_level": {
            "width": 1080, "height": 1920, "fps": 30,
            "font": "Helvetica Neue", "style": "Bold",
            "margin": "left grid column, default 0.083",
            "palette": {"bg": "#0B0B0C", "fg": "#F2F2F4",
                        "accent": "#124DFF", "muted": "#6B6B73"},
            "type_scale": {"mega": 0.095, "h1": 0.072, "h2": 0.046,
                           "body": 0.024, "label": 0.017},
            "transition": {"style": "block-wipe | none",
                           "color": "accent", "frames": 12},
            "scenes": "[{start, end, elements:[...]}] -- frames, non-overlapping",
        },
        "elements": {
            "text": {"text": "STRING", "size": "mega|h1|h2|body|label or float",
                     "color": "palette key or #hex", "x": "default = margin",
                     "y": "0-1, required", "at": "frame within the scene",
                     "dur": 10, "ease": "expoOut|quintOut|quartOut|backOut|expoIn",
                     "align": "left|center", "tracking": 1.0},
            "rule": {"x": "default margin", "y": "required", "width": 0.3,
                     "at": 0, "dur": 11, "thickness": 0.0035, "color": "accent"},
            "image": {"name": "NODE NAME, e.g. WORK_01", "file": "absolute path",
                      "slot": "[x, y, w, h] in 0-1", "at": 0, "dur": 12,
                      "anchor": "bottom|top", "scale_from": 1.12, "scale_to": 1.02},
        },
        "notes": [
            "every motion channel is eased automatically; nothing is linear",
            "scene cuts are hidden under the transition block",
            "image elements become named Loader nodes you can repoint later",
        ],
    }, indent=2)


@mcp.tool()
def list_templates() -> str:
    """List the built-in motion-design templates and their parameters."""
    return json.dumps({
        "portfolio_promo": "vertical promo: hook, 5 replaceable work slots, "
                           "value proposition, end card (24s at 30fps)",
        "title_card": "single eased title card",
        "custom": "use make_composition with the schema from describe_spec_format",
    }, indent=2)


@mcp.tool()
def make_portfolio_promo(
    name_line_1: str = "STELIOS", name_line_2: str = "MITADIS",
    role: str = "GRAPHIC DESIGNER",
    cta_line_1: str = "LET'S BUILD", cta_line_2: str = "YOUR BRAND",
    hook_lines: str = "BRANDS|BUILT TO|BE SEEN",
    kicker: str = "PORTFOLIO / 2026",
    subline: str = "GRAPHIC DESIGN & ART DIRECTION",
    work_titles: str = "BRAND IDENTITY|EDITORIAL DESIGN|PACKAGING|DIGITAL PRODUCT|ART DIRECTION",
    work_tags: str = "",
    accent: str = "#124DFF", font: str = "Helvetica Neue", style: str = "Bold",
    seconds_per_scene: float = 3.0, fps: int = 30,
    width: int = 1080, height: int = 1920,
    filename: str = "promo.comp",
) -> str:
    """Generate the vertical portfolio promo as a pasteable Fusion graph.

    Pipe-separate multi-value fields. Produces five Loader nodes named
    WORK_01..WORK_05 that you repoint at real screenshots later. Call
    make_placeholders first so it renders before you have real images.
    """
    titles = [t.strip() for t in work_titles.split("|") if t.strip()]
    tags = [t.strip() for t in work_tags.split("|")] if work_tags else []
    works = [(titles[i] if i < len(titles) else tpl.DEFAULT_WORKS[i][0],
              tags[i] if i < len(tags) else tpl.DEFAULT_WORKS[i][1])
             for i in range(5)]
    spec = tpl.portfolio_promo(
        name_lines=(name_line_1, name_line_2), role=role,
        cta_lines=(cta_line_1, cta_line_2),
        hook_lines=tuple(h.strip() for h in hook_lines.split("|") if h.strip()),
        kicker=kicker, subline=subline, works=works,
        assets=os.path.join(workdir(), "assets"),
        font=font, style=style, palette={"accent": accent},
        scene_frames=max(30, int(round(seconds_per_scene * fps))),
        width=width, height=height, fps=fps)
    return json.dumps(_emit(spec, filename), indent=2)


@mcp.tool()
def make_composition(spec_json: str, filename: str = "composition.comp") -> str:
    """Generate an arbitrary motion graphic from a spec.

    spec_json is the JSON schema returned by describe_spec_format. Use this for
    anything that is not one of the built-in templates.
    """
    try:
        spec = json.loads(spec_json)
    except json.JSONDecodeError as e:
        return json.dumps({"ok": False, "error": "spec_json is not valid JSON: %s" % e})
    return json.dumps(_emit(spec, filename), indent=2)


@mcp.tool()
def make_title_card(lines: str, kicker: str = "", seconds: float = 3.0,
                    accent: str = "#124DFF", font: str = "Helvetica Neue",
                    fps: int = 30, filename: str = "title.comp") -> str:
    """Generate a single eased title card. Pipe-separate the lines."""
    spec = tpl.title_card([l.strip() for l in lines.split("|") if l.strip()],
                          kicker=kicker or None, font=font,
                          palette={"accent": accent},
                          frames=max(30, int(round(seconds * fps))), fps=fps)
    return json.dumps(_emit(spec, filename), indent=2)


@mcp.tool()
def make_placeholders(count: int = 5) -> str:
    """Generate numbered placeholder stills into the working assets folder.

    Run this before make_portfolio_promo so the graph renders immediately,
    before real screenshots exist.
    """
    sys.path.insert(0, os.path.join(HERE, "..", "promo"))
    import make_placeholders as mk
    out = os.path.join(workdir(), "assets")
    os.makedirs(out, exist_ok=True)
    made = []
    for i in range(1, max(1, min(int(count), 20)) + 1):
        p = os.path.join(out, "WORK_%02d.png" % i)
        mk.build(i, mk.SLOT_W, mk.SLOT_H).png(p)
        made.append(p.replace("\\", "/"))
    return json.dumps({"ok": True, "files": made, "folder": out.replace("\\", "/")},
                      indent=2)


@mcp.tool()
def validate_composition(path: str) -> str:
    """Re-check a generated .comp: dangling links, orphans, timeline invariants."""
    if not os.path.exists(path):
        return json.dumps({"ok": False, "error": "no such file: %s" % path})
    return json.dumps(V.validate(open(path, encoding="utf-8").read()), indent=2)


@mcp.tool()
def send_to_clipboard(path: str) -> str:
    """Copy a .comp onto the system clipboard for pasting into Fusion.

    This is the reliable delivery route on Resolve Free: it needs no bridge and
    no Resolve scripting. After calling it, click the Fusion node editor and
    press Ctrl+V.
    """
    if not os.path.exists(path):
        return json.dumps({"ok": False, "error": "no such file: %s" % path})
    data = open(path, "rb").read()
    sysname = platform.system()
    cmd = {"Windows": ["clip"], "Darwin": ["pbcopy"]}.get(
        sysname, ["xclip", "-selection", "clipboard"])
    try:
        r = subprocess.run(cmd, input=data, capture_output=True, timeout=30)
        if r.returncode != 0:
            raise OSError(r.stderr.decode("utf-8", "replace") or "exit %d" % r.returncode)
    except (OSError, subprocess.SubprocessError) as e:
        return json.dumps({
            "ok": False, "error": "clipboard copy failed: %s" % e,
            "fallback": ('run this in cmd:  type "%s" | clip' % os.path.normpath(path))
                        if platform.system() == "Windows" else
                        ("pipe it manually: cat %s | pbcopy" % path),
        }, indent=2)
    return json.dumps({
        "ok": True, "bytes": len(data), "via": cmd[0],
        "next": "click the Fusion node editor and press Ctrl+V, then connect "
                "FINAL_OUT to MediaOut1",
    }, indent=2)


# --------------------------------------------------------------------- live
@mcp.tool()
def bridge_status() -> str:
    """Check whether the in-Resolve bridge is running, and what it can do.

    Offline tools work regardless; this only affects the live ones.
    """
    try:
        b, _ = _bridge(timeout=8)
        env = b.call("env")
        return json.dumps({"ok": True, "dir": b.dir, "resolve": env}, indent=2)
    except Exception as e:
        return json.dumps({
            "ok": False, "error": str(e),
            "note": "Live tools need the bridge; generate + send_to_clipboard "
                    "does not. Start it in Resolve: Workspace > Console > Lua > "
                    'dofile("C:/brandres-resolve/resolve/bridge/resolve_bridge_free.lua")',
        }, indent=2)


@mcp.tool()
def resolve_info() -> str:
    """Report the open Resolve project, timeline and resolution. Needs the bridge."""
    try:
        b, _ = _bridge()
        return json.dumps({"ok": True, "result": b.call("project_info")}, indent=2)
    except Exception as e:
        return json.dumps({"ok": False, "error": str(e)}, indent=2)


@mcp.tool()
def fusion_comp_info() -> str:
    """Inspect the open Fusion composition: tool list and frame range. Needs the bridge."""
    try:
        b, _ = _bridge()
        return json.dumps({"ok": True, "result": b.call("comp_info")}, indent=2)
    except Exception as e:
        return json.dumps({"ok": False, "error": str(e)}, indent=2)


@mcp.tool()
def push_to_resolve(path: str) -> str:
    """Paste a generated .comp straight into the open Fusion composition.

    Needs the bridge. If it fails, fall back to send_to_clipboard, which always
    works.
    """
    if not os.path.exists(path):
        return json.dumps({"ok": False, "error": "no such file: %s" % path})
    try:
        b, _ = _bridge(timeout=60)
        return json.dumps({"ok": True,
                           "result": b.call("paste_comp", path=path.replace("\\", "/"))},
                          indent=2)
    except Exception as e:
        return json.dumps({"ok": False, "error": str(e),
                           "fallback": "use send_to_clipboard(%r) then Ctrl+V" % path},
                          indent=2)


@mcp.tool()
def probe_sandbox() -> str:
    """Report which Lua APIs Resolve's sandbox exposes. Needs the bridge."""
    try:
        b, _ = _bridge()
        return json.dumps({"ok": True, "result": b.call("env")}, indent=2)
    except Exception as e:
        return json.dumps({"ok": False, "error": str(e)}, indent=2)


if __name__ == "__main__":
    mcp.run()
