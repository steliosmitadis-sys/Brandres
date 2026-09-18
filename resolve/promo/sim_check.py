#!/usr/bin/env python3
"""
sim_check.py -- evaluate the generated comp's Bezier splines frame by frame.

Structural validation proves the graph loads. This proves it *behaves*: it
solves each cubic segment for every integer frame and asserts the timeline
invariants that a wrong keyframe would silently break -- exactly one scene
visible at a time, and the wipe block fully hidden outside its own windows.
"""
import re, sys, os

def parse_splines(text):
    """-> {name: [(frame, value, LH|None, RH|None), ...]}"""
    out = {}
    for m in re.finditer(r"(\w+) = BezierSpline \{(.*?)\n\t\t\},", text, re.S):
        name, body = m.group(1), m.group(2)
        kf = re.search(r"KeyFrames = \{(.*?)\n\t\t\t\},", body, re.S)
        if not kf:
            continue
        keys = []
        for km in re.finditer(
                r"\[(-?\d+)\] = \{ ([-\d.]+)(?:, LH = \{ ([-\d.]+), ([-\d.]+) \})?"
                r"(?:, RH = \{ ([-\d.]+), ([-\d.]+) \})? \}", kf.group(1)):
            f, v, lx, ly, rx, ry = km.groups()
            keys.append((int(f), float(v),
                         (float(lx), float(ly)) if lx else None,
                         (float(rx), float(ry)) if rx else None))
        out[name] = keys
    return out


def bez_at(keys, frame):
    """Value of the spline at `frame`, solving x(t)=frame per cubic segment."""
    if not keys:
        return 0.0
    if frame <= keys[0][0]:
        return keys[0][1]
    if frame >= keys[-1][0]:
        return keys[-1][1]
    for i in range(len(keys) - 1):
        f0, v0, _, rh = keys[i]
        f1, v1, lh, _ = keys[i + 1]
        if not (f0 <= frame <= f1):
            continue
        p1 = rh or (f0 + (f1 - f0) / 3.0, v0 + (v1 - v0) / 3.0)
        p2 = lh or (f0 + 2 * (f1 - f0) / 3.0, v0 + 2 * (v1 - v0) / 3.0)
        lo, hi = 0.0, 1.0
        for _ in range(60):                      # bisect on x(t)
            t = (lo + hi) / 2.0
            u = 1 - t
            x = u**3 * f0 + 3 * u*u*t * p1[0] + 3 * u*t*t * p2[0] + t**3 * f1
            if x < frame:
                lo = t
            else:
                hi = t
        t = (lo + hi) / 2.0
        u = 1 - t
        return u**3 * v0 + 3 * u*u*t * p1[1] + 3 * u*t*t * p2[1] + t**3 * v1
    return keys[-1][1]


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else \
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "out", "stelios_promo.comp")
    text = open(path, encoding="utf-8").read()
    sp = parse_splines(text)
    fails = []

    # --- 1. keyframes strictly ascending, no duplicates -------------------
    for name, keys in sp.items():
        fs = [k[0] for k in keys]
        if fs != sorted(fs):
            fails.append("%s: keyframes not ascending" % name)
        if len(set(fs)) != len(fs):
            fails.append("%s: duplicate keyframes %s"
                         % (name, sorted({f for f in fs if fs.count(f) > 1})))

    # --- 2. no linear motion on any motion channel ------------------------
    linear = []
    for name, keys in sp.items():
        if name.startswith("MRG_S") or "Blend" in name:
            continue                              # visibility cuts are meant to be hard
        for i in range(len(keys) - 1):
            f0, v0, _, rh = keys[i]
            f1, v1, lh, _ = keys[i + 1]
            if abs(v1 - v0) < 1e-9:
                continue
            if rh is None and lh is None:
                linear.append(name)
                break
    if linear:
        fails.append("motion channels with no easing handles: %s" % linear[:8])

    # --- 3. exactly one scene visible on every frame ----------------------
    blends = {n: k for n, k in sp.items() if re.fullmatch(r"MRG_S\dBlend", n)}
    if len(blends) != 8:
        fails.append("expected 8 scene Blend splines, found %d" % len(blends))
    bad = []
    for f in range(720):
        vis = [n for n, k in blends.items() if bez_at(k, f) > 0.5]
        if len(vis) != 1:
            bad.append((f, sorted(vis)))
    if bad:
        fails.append("frames without exactly one visible scene: %s%s"
                     % (bad[:6], " ..." if len(bad) > 6 else ""))

    # --- 4. wipe block hidden outside its 12-frame windows ----------------
    wW, wH = sp.get("WIPE_MWidth"), sp.get("WIPE_MHeight")
    if not (wW and wH):
        fails.append("wipe splines missing")
    else:
        windows = [range(b - 8, b + 7) for b in range(90, 631, 90)]
        leaks = []
        for f in range(720):
            if any(f in w for w in windows):
                continue
            if min(bez_at(wW, f), bez_at(wH, f)) > 0.002:
                leaks.append(f)
        if leaks:
            fails.append("blue wipe block visible outside its windows on %d frames: %s"
                         % (len(leaks), leaks[:12]))

    # --- 5. every wipe fully covers frame at the cut ----------------------
    weak = [b for b in range(90, 631, 90)
            if min(bez_at(wW, b), bez_at(wH, b)) < 0.999] if (wW and wH) else []
    if weak:
        fails.append("wipe does not fully cover at boundaries %s" % weak)

    print("sim_check: %s" % path)
    print("  splines evaluated : %d" % len(sp))
    print("  frames simulated  : 720")
    print("  scene Blend rig   : %d scenes" % len(blends))
    if wW and wH:
        print("  wipe coverage     : %s"
              % ", ".join("f%d=%.3f" % (b, min(bez_at(wW, b), bez_at(wH, b)))
                          for b in range(90, 631, 90)))
    if fails:
        print("  FAILURES: %d" % len(fails))
        for f in fails:
            print("    - " + f)
        sys.exit(1)
    print("  all timeline invariants hold")


if __name__ == "__main__":
    main()
