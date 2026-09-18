#!/usr/bin/env python3
"""
build_promo.py -- render the portfolio promo spec to a pasteable .comp.

Thin wrapper: the engine is fusion_mcp/compbuilder.py and the design lives in
fusion_mcp/templates.py, so the MCP server and this CLI produce byte-identical
graphs from the same code path.
"""
import argparse, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "fusion_mcp"))
import compbuilder as cb          # noqa: E402
import templates as tpl           # noqa: E402


def smoke_spec(assets):
    return {
        "duration": 60, "transition": {"style": "none"},
        "scenes": [{"start": 0, "end": 60, "elements": [
            {"type": "text", "text": "TEST", "size": "mega", "y": 0.62, "at": 0},
            {"type": "rule", "y": 0.56, "width": 0.40, "at": 6},
            {"type": "image", "name": "WORK_01",
             "file": "%s/WORK_01.png" % str(assets).replace("\\", "/").rstrip("/"),
             "slot": [0.083, 0.16, 0.834, 0.30], "at": 2},
        ]}],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--assets", default=os.path.join(HERE, "out", "assets"))
    ap.add_argument("--font", default="Helvetica Neue")
    ap.add_argument("--style", default="Bold")
    ap.add_argument("--out", default=os.path.join(HERE, "out"))
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    assets = a.assets.replace("\\", "/").rstrip("/")

    txt, n = cb.render(tpl.portfolio_promo(assets=assets, font=a.font, style=a.style))
    p = os.path.join(a.out, "stelios_promo.comp")
    open(p, "w", encoding="utf-8").write(txt)
    print("wrote %s  (%d nodes, 720 frames, 1080x1920 @ 30fps)" % (p, n))

    txt, n = cb.render(smoke_spec(assets))
    p = os.path.join(a.out, "smoke_test.comp")
    open(p, "w", encoding="utf-8").write(txt)
    print("wrote %s  (%d nodes)" % (p, n))


if __name__ == "__main__":
    main()
