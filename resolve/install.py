#!/usr/bin/env python3
"""
install.py -- set everything up in one command.

  python install.py

Creates the working folder, generates placeholder stills and a first promo,
validates it, copies the in-Resolve scripts into Resolve's Scripts folder, and
prints the exact `claude mcp add` line to paste.

Nothing here touches Resolve's sandbox, so it works on the Free edition.
"""
import argparse, os, platform, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "fusion_mcp"))
sys.path.insert(0, os.path.join(HERE, "promo"))

GREEN, RED, YEL, DIM, OFF = "\033[32m", "\033[31m", "\033[33m", "\033[2m", "\033[0m"
if platform.system() == "Windows" and not os.environ.get("WT_SESSION"):
    GREEN = RED = YEL = DIM = OFF = ""

steps = []


def step(ok, label, detail=""):
    steps.append(ok)
    mark = (GREEN + "  OK  " + OFF) if ok else (RED + " FAIL " + OFF)
    print("%s %-38s %s%s%s" % (mark, label, DIM, detail, OFF))


def note(s):
    print("       %s%s%s" % (DIM, s, OFF))


def resolve_scripts_dirs():
    s = platform.system()
    if s == "Windows":
        base = os.path.join(os.environ.get("APPDATA", ""), "Blackmagic Design",
                            "DaVinci Resolve", "Support", "Fusion", "Scripts")
    elif s == "Darwin":
        base = os.path.expanduser("~/Library/Application Support/Blackmagic Design/"
                                  "DaVinci Resolve/Fusion/Scripts")
    else:
        base = os.path.expanduser("~/.local/share/DaVinciResolve/Fusion/Scripts")
    return base


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workdir", default=None,
                    help="where comps and assets go (default C:/promo)")
    ap.add_argument("--font", default="Helvetica Neue")
    ap.add_argument("--fps", type=int, default=30,
                    help="match your timeline: 30 or 60 (TikTok is often 60)")
    ap.add_argument("--seconds-per-scene", type=float, default=3.0)
    ap.add_argument("--align", default="center", choices=["center", "left"],
                    help="left needs the Text+ enum confirmed via align_test")
    ap.add_argument("--skip-resolve", action="store_true",
                    help="do not copy scripts into Resolve's Scripts folder")
    a = ap.parse_args()

    print("\n%sFusion Motion Graphics MCP -- setup%s\n" % (YEL, OFF))

    work = a.workdir or ("C:/promo" if platform.system() == "Windows"
                         else os.path.join(os.path.expanduser("~"), "promo"))
    work = work.replace("\\", "/")
    os.environ["FUSION_MCP_DIR"] = work

    # 1 -- working folders
    try:
        os.makedirs(os.path.join(work, "assets"), exist_ok=True)
        step(True, "working folder", work)
    except OSError as e:
        step(False, "working folder", str(e))
        return 1

    # 2 -- placeholder stills
    try:
        import make_placeholders as mk
        for i in range(1, 6):
            mk.build(i, mk.SLOT_W, mk.SLOT_H).png(
                os.path.join(work, "assets", "WORK_%02d.png" % i))
        step(True, "placeholder stills", "WORK_01..05.png in %s/assets" % work)
    except Exception as e:
        step(False, "placeholder stills", str(e))

    # 3 -- generate + validate a first promo
    comp_path = None
    try:
        import compbuilder as cb, templates as tpl, validate as V
        text, n = cb.render(tpl.portfolio_promo(
            assets=os.path.join(work, "assets"), font=a.font, fps=a.fps,
            align=a.align,
            scene_frames=int(round(a.seconds_per_scene * a.fps))))
        rep = V.validate(text)
        comp_path = os.path.join(work, "promo.comp").replace("\\", "/")
        open(comp_path, "w", encoding="utf-8").write(text)
        step(rep["ok"], "generate + validate promo",
             "%d nodes, %d frames = %.1fs @ %dfps, %s"
             % (n, rep["stats"]["frames"], rep["stats"]["frames"] / float(a.fps),
                a.fps, "clean" if rep["ok"] else rep["errors"][:1]))
    except Exception as e:
        step(False, "generate + validate promo", str(e))

    # 3b -- the justification probe card
    try:
        import compbuilder as cb, templates as tpl
        txt, n = cb.render(tpl.align_test(font=a.font, fps=a.fps))
        ap_path = os.path.join(work, "align_test.comp").replace("\\", "/")
        open(ap_path, "w", encoding="utf-8").write(txt)
        step(True, "alignment probe card", ap_path)
    except Exception as e:
        step(False, "alignment probe card", str(e))

    # 4 -- in-Resolve scripts
    if not a.skip_resolve:
        base = resolve_scripts_dirs()
        if not os.path.isdir(base):
            step(False, "Resolve Scripts folder", "not found: %s" % base)
            note("Resolve may not be installed here, or has never been launched.")
            note("Everything except the live bridge still works.")
        else:
            copied = []
            for sub, src in (("Comp", os.path.join(HERE, "promo", "Paste_Promo.lua")),
                             ("Comp", os.path.join(HERE, "promo", "Fix_Output.lua")),
                             ("Utility", os.path.join(HERE, "probe", "fusion_api_probe.lua")),
                             ("Utility", os.path.join(HERE, "bridge", "resolve_bridge_free.lua"))):
                dst_dir = os.path.join(base, sub)
                try:
                    os.makedirs(dst_dir, exist_ok=True)
                    shutil.copy2(src, dst_dir)
                    copied.append("%s/%s" % (sub, os.path.basename(src)))
                except OSError as e:
                    note("could not copy %s: %s" % (os.path.basename(src), e))
            step(bool(copied), "Resolve scripts installed", ", ".join(copied))

            stale = os.path.join(base, "Edit", "MCP_Bridge.lua")
            if os.path.exists(stale):
                try:
                    os.replace(stale, stale + ".disabled")
                    step(True, "retired old MCP_Bridge.lua",
                         "it calls os.execute, which Resolve Free removed")
                except OSError as e:
                    note("please delete %s by hand (%s)" % (stale, e))

    # 5 -- point Paste_Promo at the real file
    if comp_path:
        try:
            base = resolve_scripts_dirs()
            tgt = os.path.join(base, "Comp", "Paste_Promo.lua")
            if os.path.exists(tgt):
                s = open(tgt, encoding="utf-8").read()
                s = s.replace('local COMP_FILE = "C:/promo/stelios_promo.comp"',
                              'local COMP_FILE = "%s"' % comp_path)
                open(tgt, "w", encoding="utf-8").write(s)
                step(True, "Paste_Promo.lua wired", comp_path)
        except OSError as e:
            note("could not rewrite Paste_Promo.lua: %s" % e)

    # 6 -- python dependency
    try:
        import fastmcp  # noqa: F401
        step(True, "fastmcp available", getattr(fastmcp, "__version__", "?"))
    except ImportError:
        try:
            import mcp.server.fastmcp  # noqa: F401
            step(True, "mcp SDK available", "official SDK layout")
        except ImportError:
            step(False, "fastmcp missing", "run:  pip install fastmcp")

    # ---- what to do next -------------------------------------------------
    server = os.path.join(HERE, "fusion_mcp", "server.py").replace("\\", "/")
    ok = all(steps)
    print("\n%s%s%s\n" % (GREEN if ok else YEL,
                          "Setup complete." if ok else "Setup finished with warnings.", OFF))
    print("1. Register the MCP server with Claude Code:\n")
    print('   claude mcp add fusion-mg --env FUSION_MCP_DIR=%s -- "%s" "%s"\n'
          % (work, sys.executable.replace("\\", "/"), server))
    print("2. Then just ask Claude, for example:\n")
    print('   "make me a 24 second vertical portfolio promo and put it on my clipboard"\n')
    print("3. In Resolve: open the Fusion page on a clip, click the node editor,")
    last = (rep["stats"]["frames"] - 1) if comp_path else 719
    print("   press Ctrl+V, connect FINAL_OUT to MediaOut1, set the range to 0-%d.\n" % last)
    if comp_path:
        print("   A promo is already waiting at: %s" % comp_path)
        print("   Replace %s/assets/WORK_01..05.png with your screenshots.\n" % work)
    return 0 if ok else 0


if __name__ == "__main__":
    sys.exit(main())
