#!/usr/bin/env python3
"""
validate.py -- check a generated .comp without Resolve and without Lua.

Two layers:
  structure -- every SourceOp resolves, nothing is orphaned from ActiveTool
  behaviour -- every Bezier segment solved at every frame, so timeline
               invariants (one scene visible, wipe hidden outside its windows)
               are checked numerically rather than assumed
"""
import re


def parse_tools(text):
    return dict(re.findall(r"^\t\t(\w+) = (\w+) \{", text, re.M))


def parse_edges(text):
    edges, cur = {}, None
    for line in text.splitlines():
        m = re.match(r"^\t\t(\w+) = (\w+) \{", line)
        if m:
            cur = m.group(1)
            edges.setdefault(cur, [])
        elif cur:
            s = re.search(r'SourceOp = "(\w+)"', line)
            if s:
                edges[cur].append(s.group(1))
    return edges


def parse_splines(text):
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
        for _ in range(50):
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


def validate(text, duration=None):
    """-> {'ok': bool, 'errors': [...], 'warnings': [...], 'stats': {...}}"""
    errors, warnings = [], []
    tools = parse_tools(text)
    edges = parse_edges(text)
    splines = parse_splines(text)

    active = re.search(r'ActiveTool = "(\w+)"', text)
    active = active.group(1) if active else None

    for owner, deps in edges.items():
        for d in deps:
            if d not in tools:
                errors.append("%s links to missing tool %r" % (owner, d))

    if not active or active not in tools:
        errors.append("ActiveTool missing or unknown: %r" % active)
    else:
        seen, stack = {active}, [active]
        while stack:
            for dep in edges.get(stack.pop(), []):
                if dep not in seen:
                    seen.add(dep)
                    stack.append(dep)
        orphans = sorted(set(tools) - seen)
        if orphans:
            errors.append("%d tool(s) unreachable from %s: %s"
                          % (len(orphans), active, ", ".join(orphans[:10])))

    for name, keys in splines.items():
        fs = [k[0] for k in keys]
        if fs != sorted(fs):
            errors.append("%s: keyframes not ascending" % name)
        if len(set(fs)) != len(fs):
            errors.append("%s: duplicate keyframes %s"
                          % (name, sorted({f for f in fs if fs.count(f) > 1})))
        if len(keys) < 2:
            warnings.append("%s has %d keyframe(s)" % (name, len(keys)))

    linear = []
    for name, keys in splines.items():
        if name.startswith("MRG_S"):
            continue
        for i in range(len(keys) - 1):
            if abs(keys[i + 1][1] - keys[i][1]) < 1e-9:
                continue
            if keys[i][3] is None and keys[i + 1][2] is None:
                linear.append(name)
                break
    if linear:
        warnings.append("un-eased motion on: %s" % ", ".join(linear[:6]))

    if duration is None:
        m = re.search(r"GlobalOut = Input \{ Value = (\d+)", text)
        duration = int(m.group(1)) + 1 if m else 0

    blends = {n: k for n, k in splines.items() if re.fullmatch(r"MRG_S\d+Blend", n)}
    if blends and duration:
        bad = [f for f in range(duration)
               if len([1 for k in blends.values() if bez_at(k, f) > 0.5]) != 1]
        if bad:
            errors.append("frames without exactly one visible scene: %s%s"
                          % (bad[:6], " ..." if len(bad) > 6 else ""))

    wW, wH = splines.get("WIPE_MWidth"), splines.get("WIPE_MHeight")
    if wW and wH and duration and blends:
        # Derive the cuts from the scene rig itself, then check the property
        # that actually matters: the block shows only in short runs, each one
        # centred on a real cut, and fully covering the frame at that cut.
        cuts = set()
        for keys in blends.values():
            for i in range(len(keys) - 1):
                if keys[i][1] < 0.5 <= keys[i + 1][1]:
                    cuts.add(keys[i + 1][0])
        cuts.discard(0)

        vis = [f for f in range(duration)
               if min(bez_at(wW, f), bez_at(wH, f)) > 0.002]
        runs = []
        for f in vis:
            if runs and f == runs[-1][-1] + 1:
                runs[-1].append(f)
            else:
                runs.append([f])

        for r in runs:
            centre = (r[0] + r[-1]) // 2
            if not any(abs(centre - c) <= 3 for c in cuts):
                errors.append("transition block visible at frames %d-%d, "
                              "which is not a scene cut" % (r[0], r[-1]))
            elif len(r) > 30:
                errors.append("transition block lingers %d frames at %d-%d"
                              % (len(r), r[0], r[-1]))
        if len(runs) != len(cuts):
            errors.append("%d transition(s) for %d cut(s)" % (len(runs), len(cuts)))
        weak = [c for c in sorted(cuts)
                if min(bez_at(wW, c), bez_at(wH, c)) < 0.999]
        if weak:
            errors.append("transition does not fully cover at cut(s) %s" % weak)

    return {
        "ok": not errors,
        "errors": errors,
        "warnings": warnings,
        "stats": {
            "tools": len(tools),
            "splines": len(splines),
            "frames": duration,
            "scenes": len(blends) or None,
            "active_tool": active,
            "kinds": {k: sum(1 for v in tools.values() if v == k)
                      for k in sorted(set(tools.values()))},
        },
    }
