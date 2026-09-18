#!/usr/bin/env python3
"""
selftest.py -- the incremental connection ladder, in order.

  1 ping/pong          2 sandbox report      3 Resolve project name
  4 Fusion comp state  5 create a Text+      6 animate a parameter
  7 paste the promo    (only with --paste)

Each rung prints PASS/FAIL and the ladder stops at the first failure, so the
output names exactly which capability is missing rather than a generic timeout.

  python selftest.py                       # auto-detect the bridge folder
  python selftest.py --dir "C:/..../resolve-mcp-v3free"
  python selftest.py --paste "C:/promo/stelios_promo.comp"
"""
import argparse, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bridge_client_free import Bridge, BridgeError

RUNGS = []


def rung(label):
    def deco(fn):
        RUNGS.append((label, fn))
        return fn
    return deco


@rung("1. ping / pong")
def _ping(b, a):
    r = b.call("ping", echo="hello")
    assert r.get("pong") is True, r
    return "writer=%s  tick=%s  dir=%s" % (r.get("writer"), r.get("tick"), r.get("dir"))


@rung("2. sandbox report")
def _env(b, a):
    r = b.call("env")
    return ("io=%s  os.execute=%s  bmd.writefile=%s  dofile=%s  resolve=%s  comp=%s"
            % (r.get("has_io"), r.get("has_os_execute"), r.get("has_writefile"),
               r.get("has_dofile"), r.get("has_resolve"), r.get("has_comp")))


@rung("3. Resolve project name")
def _proj(b, a):
    r = b.call("project_info")
    assert r.get("project"), r
    return ("%s %s  project=%r  timeline=%r  %sx%s @ %s"
            % (r.get("product"), r.get("version"), r.get("project"), r.get("timeline"),
               r.get("width"), r.get("height"), r.get("fps")))


@rung("4. Fusion composition")
def _comp(b, a):
    r = b.call("comp_info")
    tools = r.get("tools") or []
    if isinstance(tools, dict):
        tools = [tools[k] for k in sorted(tools)]
    return ("tools=%s  range=%s..%s  first=%s"
            % (r.get("tool_count"), r.get("render_start"), r.get("render_end"),
               ", ".join(map(str, tools[:4])) or "-"))


@rung("5. create Text+ 'TEST'")
def _text(b, a):
    r = b.call("add_text", text="TEST", size=0.09, name="MCP_TEST")
    assert r.get("name"), r
    a["tool"] = r["name"]
    return "created %s (%s)" % (r.get("name"), r.get("regid"))


@rung("6. animate a parameter")
def _anim(b, a):
    tool = a.get("tool")
    assert tool, "rung 5 did not create a tool"
    r = b.call("animate", tool=tool, input="Size",
               keys=[{"frame": 0, "value": 0.02}, {"frame": 12, "value": 0.09}])
    assert r.get("keys") == 2, r
    return "%s.%s got %s keys" % (r.get("tool"), r.get("input"), r.get("keys"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=None)
    ap.add_argument("--timeout", type=float, default=15.0)
    ap.add_argument("--paste", default=None, metavar="COMP",
                    help="after the ladder passes, paste this .comp into the open comp")
    args = ap.parse_args()

    b = Bridge(args.dir, timeout=args.timeout)
    print("bridge dir : %s" % b.dir)
    try:
        h = b.handshake()
        print("handshake  : proto=%s writer=%s" % (h.get("proto"), h.get("writer")))
    except BridgeError as e:
        print("\nFAIL before rung 1:\n%s" % e)
        return 1

    state, failed = {}, False
    for label, fn in RUNGS:
        try:
            detail = fn(b, state)
            print("  PASS  %-26s %s" % (label, detail))
        except Exception as e:
            print("  FAIL  %-26s %s: %s" % (label, type(e).__name__, e))
            failed = True
            break

    if not failed and args.paste:
        try:
            r = b.call("paste_comp", path=args.paste.replace("\\", "/"))
            print("  PASS  %-26s pasted=%s connected=%s last_frame=%s"
                  % ("7. paste promo comp", r.get("pasted"),
                     r.get("connected"), r.get("last_frame")))
        except Exception as e:
            print("  FAIL  %-26s %s" % ("7. paste promo comp", e))
            failed = True

    print("\n%s" % ("LADDER FAILED" if failed else "LADDER PASSED"))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
