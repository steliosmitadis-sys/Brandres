#!/usr/bin/env python3
"""
compbuilder.py -- turn a declarative motion-design spec into a Fusion node graph.

A Fusion composition is plain text in Lua syntax, so this module is the whole
rendering engine: no Resolve, no bridge, no sandboxed API. Give it a spec and
it returns pasteable clipboard text.

The spec is the interface an LLM designs against:

    {
      "width": 1080, "height": 1920, "fps": 30, "duration": 720,
      "font": "Helvetica Neue", "style": "Bold", "margin": 0.083,
      "palette": {"bg": "#0B0B0C", "fg": "#F2F2F4", "accent": "#124DFF"},
      "transition": {"style": "block-wipe", "color": "accent", "frames": 12},
      "scenes": [
        {"start": 0, "end": 90, "elements": [
          {"type": "text",  "text": "BRANDS", "size": "mega", "y": 0.60, "at": 6},
          {"type": "rule",  "y": 0.355, "width": 0.36, "at": 24},
          {"type": "image", "name": "WORK_01", "file": "C:/a/w1.png",
           "slot": [0.083, 0.435, 0.834, 0.44], "at": 2}
        ]}
      ]
    }

Every motion channel is eased; nothing animates linearly.
"""
import copy

# ------------------------------------------------------------------ defaults
DEFAULTS = {
    "width": 1080, "height": 1920, "fps": 30, "duration": 720,
    "font": "Helvetica Neue", "style": "Bold", "margin": 0.083,
    "align": "center",
    "palette": {"bg": "#0B0B0C", "fg": "#F2F2F4",
                "accent": "#124DFF", "muted": "#6B6B73"},
    "type_scale": {"mega": 0.095, "h1": 0.072, "h2": 0.046,
                   "body": 0.024, "label": 0.017},
    "transition": {"style": "block-wipe", "color": "accent", "frames": 12},
    "drift": 0.014,
    "scenes": [],
}

# Text+ HorizontalJustificationNew. If generated text lands centred when it
# should be left-aligned, flip H_LEFT to 1 -- this is the only uncertain enum.
H_LEFT, H_CENTER, V_CENTER = 0, 3, 3

EASE = {
    "expoOut":    (0.16, 1.00, 0.30, 1.00),
    "quintOut":   (0.22, 1.00, 0.36, 1.00),
    "quartOut":   (0.25, 1.00, 0.50, 1.00),
    "backOut":    (0.34, 1.28, 0.64, 1.00),
    "expoIn":     (0.70, 0.00, 0.84, 0.00),
    "quintInOut": (0.83, 0.00, 0.17, 1.00),
    "STEP":       (0.33, 0.33, 0.67, 0.67),
}


class SpecError(ValueError):
    pass


def hex_rgb(v):
    if isinstance(v, (list, tuple)):
        return tuple(float(x) for x in v[:3])
    s = str(v).lstrip("#")
    if len(s) == 3:
        s = "".join(ch * 2 for ch in s)
    if len(s) != 6:
        raise SpecError("bad colour %r -- want #RRGGBB" % v)
    return tuple(int(s[i:i + 2], 16) / 255.0 for i in (0, 2, 4))


# ------------------------------------------------------------------ emitter
class Link:
    def __init__(self, op, source="Output"):
        self.op, self.source = op, source


class FuID:
    def __init__(self, v):
        self.v = v


def fmt(x):
    if isinstance(x, float):
        s = ("%.6f" % x).rstrip("0").rstrip(".")
        return s if s not in ("", "-") else "0"
    return str(x)


def enc(v):
    if isinstance(v, Link):
        return 'Input {\n\t\t\t\tSourceOp = "%s",\n\t\t\t\tSource = "%s",\n\t\t\t}' % (v.op, v.source)
    if isinstance(v, FuID):
        return 'Input { Value = FuID { "%s" }, }' % v.v
    if isinstance(v, bool):
        return "Input { Value = %d, }" % (1 if v else 0)
    if isinstance(v, (tuple, list)):
        return "Input { Value = { %s }, }" % ", ".join(fmt(x) for x in v)
    if isinstance(v, str):
        return 'Input { Value = "%s", }' % v.replace("\\", "\\\\").replace('"', '\\"')
    return "Input { Value = %s, }" % fmt(v)


class Comp:
    def __init__(self, cfg):
        self.cfg = cfg
        self.W, self.H = cfg["width"], cfg["height"]
        self.DUR = cfg["duration"]
        self.tools, self.names = [], set()

    def _name(self, n):
        n = "".join(ch if (ch.isalnum() or ch == "_") else "_" for ch in n)
        if n and n[0].isdigit():
            n = "T" + n
        if n in self.names:
            i = 2
            while "%s_%d" % (n, i) in self.names:
                i += 1
            n = "%s_%d" % (n, i)
        self.names.add(n)
        return n

    def add(self, name, kind, inputs=None, pos=None, extra=None, modifier=False):
        name = self._name(name)
        self.tools.append(dict(name=name, kind=kind, inputs=inputs or {},
                               pos=pos, extra=extra, modifier=modifier))
        return name

    def _set(self, tool, inp, val):
        for t in self.tools:
            if t["name"] == tool:
                t["inputs"][inp] = val
                return
        raise KeyError(tool)

    def render(self, active=None):
        out = ["{", "\tTools = ordered() {"]
        for t in self.tools:
            out.append("\t\t%s = %s {" % (t["name"], t["kind"]))
            if t["extra"]:
                out.append(t["extra"])
            if t["inputs"]:
                out.append("\t\t\tInputs = {")
                for k, v in t["inputs"].items():
                    key = k if k.replace("_", "").isalnum() and not k[0].isdigit() else '["%s"]' % k
                    out.append("\t\t\t\t%s = %s," % (key, enc(v)))
                out.append("\t\t\t},")
            if not t["modifier"] and t["pos"]:
                out.append("\t\t\tViewInfo = OperatorInfo { Pos = { %s, %s } },"
                           % (fmt(float(t["pos"][0])), fmt(float(t["pos"][1]))))
            out.append("\t\t},")
        out.append("\t},")
        if active:
            out.append('\tActiveTool = "%s",' % active)
        out.append("}")
        return "\n".join(out)

    # -------------------------------------------------------------- splines
    def _spline(self, name, keys, color=(255, 0, 0)):
        keys = sorted(keys, key=lambda k: k[0])
        frames = [k[0] for k in keys]
        if len(set(frames)) != len(frames):
            dup = sorted({f for f in frames if frames.count(f) > 1})
            raise SpecError("%s: duplicate keyframes at %s" % (name, dup))
        LH, RH = {}, {}
        for i in range(len(keys) - 1):
            f0, v0, e = keys[i]
            f1, v1 = keys[i + 1][0], keys[i + 1][1]
            x1, y1, x2, y2 = EASE.get(e) or EASE["expoOut"]
            dt, dv = float(f1 - f0), float(v1 - v0)
            RH[i] = (f0 + x1 * dt, v0 + y1 * dv)
            LH[i + 1] = (f0 + x2 * dt, v0 + y2 * dv)
        rows = []
        for i, (f, v, _) in enumerate(keys):
            parts = [fmt(float(v))]
            if i in LH:
                parts.append("LH = { %s, %s }" % (fmt(LH[i][0]), fmt(LH[i][1])))
            if i in RH:
                parts.append("RH = { %s, %s }" % (fmt(RH[i][0]), fmt(RH[i][1])))
            rows.append("\t\t\t\t[%d] = { %s }" % (f, ", ".join(parts)))
        extra = ("\t\t\tSplineColor = { Red = %d, Green = %d, Blue = %d },\n"
                 "\t\t\tNameSet = true,\n"
                 "\t\t\tKeyFrames = {\n%s\n\t\t\t},") % (color + (",\n".join(rows),))
        return self.add(name, "BezierSpline", extra=extra, modifier=True)

    def anim(self, tool, inp, keys, color=(255, 0, 0)):
        self._set(tool, inp, Link(self._spline("%s%s" % (tool, inp), keys, color), "Value"))

    def anim_xy(self, tool, inp, keys, color=(0, 160, 255)):
        xs = [(f, p[0], e) for f, p, e in keys]
        ys = [(f, p[1], e) for f, p, e in keys]
        base = "%s%s" % (tool, inp)
        ins = {
            "X": (Link(self._spline(base + "X", xs, color), "Value")
                  if len({round(v, 6) for _, v, _ in xs}) > 1 else xs[0][1]),
            "Y": (Link(self._spline(base + "Y", ys, color), "Value")
                  if len({round(v, 6) for _, v, _ in ys}) > 1 else ys[0][1]),
        }
        path = self.add(base, "XYPath", inputs=ins,
                        extra='\t\t\tDrawMode = "ModifyOnly",', modifier=True)
        self._set(tool, inp, Link(path, "Value"))

    # ------------------------------------------------------------ factories
    def bg(self, name, color, pos, alpha=1.0, mask=None):
        i = {"Width": self.W, "Height": self.H, "UseFrameFormatSettings": 0,
             "TopLeftRed": color[0], "TopLeftGreen": color[1],
             "TopLeftBlue": color[2], "TopLeftAlpha": alpha,
             "GlobalIn": 0, "GlobalOut": self.DUR - 1}
        if mask:
            i["EffectMask"] = Link(mask, "Mask")
        return self.add(name, "Background", i, pos)

    def text(self, name, s, size, color, pos, align=H_LEFT, tracking=1.0):
        i = {"Width": self.W, "Height": self.H, "UseFrameFormatSettings": 0,
             "GlobalIn": 0, "GlobalOut": self.DUR - 1,
             "StyledText": s, "Font": self.cfg["font"], "Style": self.cfg["style"],
             "Size": size, "Tracking": tracking, "LineSpacing": 1.0,
             "Red1": color[0], "Green1": color[1], "Blue1": color[2], "Alpha1": 1.0,
             "HorizontalJustificationNew": align, "VerticalJustificationNew": V_CENTER}
        return self.add(name, "TextPlus", i, pos)

    def rect(self, name, w, h, center, pos, soft=0.0):
        i = {"MaskWidth": self.W, "MaskHeight": self.H, "Width": w, "Height": h,
             "Center": center, "SoftEdge": soft, "CornerRadius": 0.0,
             "Invert": 0, "MaskClipMode": FuID("None")}
        return self.add(name, "RectangleMask", i, pos)

    def xf(self, name, inp, pos, center=(0.5, 0.5), size=1.0, mask=None):
        i = {"Input": Link(inp), "Center": center, "Size": size, "Angle": 0.0}
        if mask:
            i["EffectMask"] = Link(mask, "Mask")
        return self.add(name, "Transform", i, pos)

    def merge(self, name, bg, fg, pos, center=None, blend=None, mask=None):
        i = {"Background": Link(bg), "Foreground": Link(fg), "PerformDepthMerge": 0}
        if center is not None:
            i["Center"] = center
        if blend is not None:
            i["Blend"] = blend
        if mask:
            i["EffectMask"] = Link(mask, "Mask")
        return self.add(name, "Merge", i, pos)

    def loader(self, name, filename, pos):
        clip = ('\t\t\tClips = {\n\t\t\t\tClip {\n'
                '\t\t\t\t\tID = "Clip1",\n'
                '\t\t\t\t\tFilename = "%s",\n'
                '\t\t\t\t\tFormatID = "PNGFormat",\n'
                '\t\t\t\t\tStartFrame = -1,\n'
                '\t\t\t\t\tLengthSetManually = true,\n'
                '\t\t\t\t\tTrimIn = 0,\n\t\t\t\t\tTrimOut = 0,\n'
                '\t\t\t\t\tExtendFirst = 0,\n\t\t\t\t\tExtendLast = 0,\n'
                '\t\t\t\t\tLoop = 1,\n\t\t\t\t\tAspectMode = 0,\n'
                '\t\t\t\t\tDepth = 0,\n\t\t\t\t\tGlobalStart = 0,\n'
                '\t\t\t\t\tGlobalEnd = %d\n'
                '\t\t\t\t}\n\t\t\t},') % (str(filename).replace("\\", "/"), self.DUR - 1)
        i = {"Loop": 1, "GlobalIn": 0, "GlobalOut": self.DUR - 1,
             "HoldLastFrame": self.DUR, "Depth": 0}
        return self.add(name, "Loader", i, pos, extra=clip)


# ------------------------------------------------------------------ patterns
def el_text(c, cfg, base, el, pos):
    """Typography rising into a fixed crop slot."""
    size = el.get("size", "h2")
    size = cfg["type_scale"].get(size, size) if isinstance(size, str) else float(size)
    color = hex_rgb(cfg["palette"].get(el.get("color", "fg"), el.get("color", "fg")))
    just = el.get("justify")
    if isinstance(just, int):
        align = just                                   # raw enum, for probing
    else:
        align = H_CENTER if el.get("align", cfg["align"]) == "center" else H_LEFT
    x = el.get("x", 0.5 if align != H_LEFT else cfg["margin"])
    y = float(el["y"])
    ts = cfg["time_scale"]
    at = int(el.get("at", 0))
    dur = max(2, int(round(float(el.get("dur", 10)) * ts)))
    ease = el.get("ease", "expoOut")

    t = c.text(base + "_T", str(el["text"]), size, color, pos,
               align=align, tracking=float(el.get("tracking", 1.0)))
    m = c.rect(base + "_M", 1.4, size * 1.75, (0.5, y), (pos[0], pos[1] + 40))
    xf = c.xf(base, t, (pos[0] + 110, pos[1]), mask=m)
    rise = float(el.get("rise", size * 1.05))
    c.anim_xy(xf, "Center", [(at, (x, y - rise), ease), (at + dur, (x, y), ease)])
    return xf


def el_rule(c, cfg, base, el, pos):
    """A hairline growing from its left edge."""
    color = hex_rgb(cfg["palette"].get(el.get("color", "accent"), el.get("color", "accent")))
    x = float(el.get("x", cfg["margin"]))
    y, w = float(el["y"]), float(el.get("width", 0.3))
    ts = cfg["time_scale"]
    at = int(el.get("at", 0))
    dur = max(2, int(round(float(el.get("dur", 11)) * ts)))
    thick = float(el.get("thickness", 0.0035))
    ease = el.get("ease", "expoOut")
    r = c.rect(base + "_M", w, thick, (x + w / 2.0, y), pos)
    c.anim(r, "Width", [(at, 0.0, ease), (at + dur, w, ease)])
    c.anim_xy(r, "Center", [(at, (x, y), ease), (at + dur, (x + w / 2.0, y), ease)])
    return c.bg(base, color, (pos[0] + 110, pos[1]), mask=r)


def el_image(c, cfg, base, el, pos, scene_end):
    """A replaceable still, crop-revealed into a slot with a slow scale drift."""
    slot = el.get("slot") or [cfg["margin"], 0.3, 1 - 2 * cfg["margin"], 0.4]
    sx, sy, sw, sh = (float(v) for v in slot)
    scy = sy + sh / 2.0
    ts = cfg["time_scale"]
    at = int(el.get("at", 0))
    dur = max(2, int(round(float(el.get("dur", 12)) * ts)))
    anchor = el.get("anchor", "bottom")
    ease = el.get("ease", "expoOut")

    name = el.get("name") or (base + "_IMG")
    ld = c.loader(name, el.get("file", ""), pos)
    xf = c.xf(name + "_XF", ld, (pos[0] + 110, pos[1]))
    c.anim(xf, "Size", [(at, float(el.get("scale_from", 1.12)), "quintOut"),
                        (max(at + 1, scene_end - 2), float(el.get("scale_to", 1.02)), "quintOut")])

    m = c.rect(name + "_SLOT", sw, sh, (sx + sw / 2.0, scy), (pos[0] + 110, pos[1] + 60))
    edge = sy if anchor == "bottom" else sy + sh
    c.anim(m, "Height", [(at, 0.0, ease), (at + dur, sh, ease)])
    c.anim_xy(m, "Center", [(at, (sx + sw / 2.0, edge), ease),
                            (at + dur, (sx + sw / 2.0, scy), ease)])

    base_fld = c.bg(name + "_FIELD", (0, 0, 0), (pos[0] + 220, pos[1]), alpha=0.0)
    return c.merge(name + "_MRG", base_fld, xf, (pos[0] + 330, pos[1]),
                   center=(sx + sw / 2.0, scy), mask=m)


ELEMENTS = {"text": el_text, "rule": el_rule, "image": el_image}


def build_wipe(c, cfg, bounds, row):
    """One hard-edge block covering each cut, alternating direction."""
    if not bounds or cfg["transition"].get("style") == "none":
        return None
    half = max(2, int(round(int(cfg["transition"].get("frames", 12))
                            * cfg["time_scale"])) // 2)
    col = cfg["transition"].get("color", "accent")
    color = hex_rgb(cfg["palette"].get(col, col))
    hk = [(0, 0.0, "STEP")]
    wk = [(0, 1.0, "STEP")]
    ck = [(0, (0.5, 0.0), "STEP")]
    for n, b in enumerate(bounds):
        a, z = b - half, b + half
        if n == len(bounds) - 1 and len(bounds) > 1:          # final cut: horizontal
            hk += [(a - 2, 0.0, "STEP"), (a - 1, 1.0, "STEP"), (z, 1.0, "STEP")]
            wk += [(a - 2, 0.0, "STEP"), (a, 0.0, "quartOut"),
                   (b, 1.0, "expoIn"), (z, 0.0, "STEP")]
            ck += [(a - 2, (0.0, 0.5), "STEP"), (a, (0.0, 0.5), "quartOut"),
                   (b, (0.5, 0.5), "expoIn"), (z, (1.0, 0.5), "STEP")]
        else:
            c0, c2 = ((0.0, 1.0) if n % 2 == 0 else (1.0, 0.0))
            wk += [(a, 1.0, "STEP"), (z, 1.0, "STEP")]
            hk += [(a, 0.0, "quartOut"), (b, 1.0, "expoIn"), (z, 0.0, "STEP")]
            ck += [(a, (0.5, c0), "quartOut"), (b, (0.5, 0.5), "expoIn"),
                   (z, (0.5, c2), "STEP")]
    r = c.rect("WIPE_M", 1.0, 0.0, (0.5, 0.5), (0, row))
    c.anim(r, "Height", hk)
    c.anim(r, "Width", wk)
    c.anim_xy(r, "Center", ck)
    return c.bg("WIPE", color, (110, row), mask=r)


# ------------------------------------------------------------------ assembly
def normalize(spec):
    cfg = copy.deepcopy(DEFAULTS)
    for k, v in (spec or {}).items():
        if isinstance(v, dict) and isinstance(cfg.get(k), dict):
            cfg[k].update(v)
        else:
            cfg[k] = v
    if not cfg["scenes"]:
        raise SpecError("spec has no scenes")
    for n, sc in enumerate(cfg["scenes"]):
        if "start" not in sc or "end" not in sc:
            raise SpecError("scene %d needs start and end (frames)" % n)
        if int(sc["end"]) <= int(sc["start"]):
            raise SpecError("scene %d: end must be after start" % n)
    if not cfg.get("time_scale"):
        # Element timings are authored in 30fps units. At 60fps a 10-frame move
        # must become 20 frames to look the same, so scale everything by fps/30.
        cfg["time_scale"] = float(cfg["fps"]) / 30.0
    cfg["scenes"].sort(key=lambda s: int(s["start"]))
    last = cfg["scenes"][-1]
    cfg["duration"] = max(int(cfg["duration"]), int(last["end"]))
    return cfg


def build(spec):
    """spec -> (Comp, final_tool_name)"""
    cfg = normalize(spec)
    c = Comp(cfg)
    scenes = cfg["scenes"]
    outs = []

    for i, sc in enumerate(scenes):
        row = i * 700
        start, end = int(sc["start"]), int(sc["end"])
        layers = []
        for j, el in enumerate(sc.get("elements", [])):
            kind = el.get("type", "text")
            fn = ELEMENTS.get(kind)
            if not fn:
                raise SpecError("scene %d element %d: unknown type %r "
                                "(want one of %s)" % (i, j, kind, sorted(ELEMENTS)))
            el = dict(el)
            el["at"] = start + int(round(int(el.get("at", 0)) * cfg["time_scale"]))
            base = "S%d_E%d" % (i + 1, j + 1)
            pos = (0, row + j * 120)
            layers.append(fn(c, cfg, base, el, pos, end) if kind == "image"
                          else fn(c, cfg, base, el, pos))

        cur = c.bg("S%d_BASE" % (i + 1), (0, 0, 0), (500, row), alpha=0.0)
        for n, layer in enumerate(layers):
            cur = c.merge("S%d_MRG%d" % (i + 1, n + 1), cur, layer, (610 + n * 110, row))

        d = c.xf("S%d_DRIFT" % (i + 1), cur, (900, row))
        dr = float(cfg["drift"])
        c.anim_xy(d, "Center", [(start, (0.5, 0.5 - dr / 2), "quintOut"),
                                (end - 1, (0.5, 0.5 + dr / 2), "quintOut")])
        outs.append(d)

    y = len(scenes) * 700 + 200
    cur = c.bg("MASTER_BG", hex_rgb(cfg["palette"]["bg"]), (0, y))
    for i, d in enumerate(outs):
        start, end = int(scenes[i]["start"]), int(scenes[i]["end"])
        m = c.merge("MRG_S%d" % (i + 1), cur, d, (150 + i * 110, y))
        k = []
        if start > 0:
            k.append((start - 1, 0.0, "STEP"))
        k.append((start, 1.0, "STEP"))
        if end < cfg["duration"]:
            k += [(end - 1, 1.0, "STEP"), (end, 0.0, "STEP")]
        if len(k) >= 2:
            c.anim(m, "Blend", k, color=(120, 120, 120))
        cur = m

    wipe = build_wipe(c, cfg, [int(s["start"]) for s in scenes[1:]], y + 200)
    if wipe:
        cur = c.merge("MRG_WIPE", cur, wipe, (150 + len(outs) * 110, y))
    final = c.xf("FINAL_OUT", cur, (280 + len(outs) * 110, y))
    return c, final


def render(spec):
    c, final = build(spec)
    return c.render(active=final), len(c.tools)
