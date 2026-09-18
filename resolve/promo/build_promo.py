#!/usr/bin/env python3
"""
build_promo.py -- generate the Fusion node graph for a 1080x1920 / 30fps / 24s
motion-design portfolio promo, as pasteable Fusion clipboard text.

WHY A GENERATOR AND NOT A LIVE BRIDGE
  A Fusion composition is plain text. Resolve's Fusion page accepts that text
  straight from the clipboard (Ctrl+V into the node editor) and from
  comp:Paste() inside a Workspace > Scripts macro. Neither route needs `io`,
  `os.execute`, Py3, or an MCP round-trip -- so this works on Resolve 21.1 Free
  today, regardless of what the API probe finds.

OUTPUT
  out/stelios_promo.comp  -- the full 24s piece (~230 nodes)
  out/smoke_test.comp     -- one of each construct used, for a 10-second sanity
                             check before you paste the big one

USAGE
  python build_promo.py --assets "C:/promo/assets"
  python build_promo.py --font "Helvetica Neue" --style Bold
"""
import argparse, os

# ----------------------------------------------------------------- constants
W, H, FPS = 1080, 1920, 30
DUR = 720                                   # 24s @ 30fps -> frames 0..719

BLACK = (0.043, 0.043, 0.047)
WHITE = (0.949, 0.949, 0.957)
BLUE  = (0.071, 0.302, 1.000)               # electric blue accent
GREY  = (0.420, 0.420, 0.450)

MARGIN = 0.083                              # ~90px -> the grid's left column

MEGA, H1, H2, BODY, LABEL = 0.095, 0.072, 0.046, 0.024, 0.017

# Text+ justification enum. If your text lands centred instead of left-aligned,
# flip H_LEFT to 1 and regenerate -- this is the single value to tune.
H_LEFT, H_CENTER = 0, 3
V_CENTER = 3

# cubic-bezier control points; nothing here is linear except STEP (visibility).
EASE = {
    "expoOut":   (0.16, 1.00, 0.30, 1.00),
    "quintOut":  (0.22, 1.00, 0.36, 1.00),
    "quartOut":  (0.25, 1.00, 0.50, 1.00),
    "backOut":   (0.34, 1.28, 0.64, 1.00),
    "expoIn":    (0.70, 0.00, 0.84, 0.00),
    "quintInOut":(0.83, 0.00, 0.17, 1.00),
    "STEP":      (0.33, 0.33, 0.67, 0.67),
}

SCENES = [(i * 90, i * 90 + 90) for i in range(8)]
BOUNDS = [s for s, _ in SCENES[1:]]         # 90,180,...,630


# ----------------------------------------------------------------- emitter
class Link:
    def __init__(self, op, source="Output"):
        self.op, self.source = op, source


class FuID:
    def __init__(self, v):
        self.v = v


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


def fmt(x):
    if isinstance(x, float):
        s = ("%.6f" % x).rstrip("0").rstrip(".")
        return s if s not in ("", "-") else "0"
    return str(x)


class Comp:
    def __init__(self):
        self.tools, self.names = [], set()

    def _name(self, n):
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

    # ------------------------------------------------------------ animation
    def _spline(self, name, keys, color=(255, 0, 0)):
        """keys: [(frame, value, ease_for_segment_starting_here), ...]"""
        keys = sorted(keys, key=lambda k: k[0])
        frames = [k[0] for k in keys]
        if len(set(frames)) != len(frames):
            dup = sorted({f for f in frames if frames.count(f) > 1})
            raise ValueError("%s: duplicate keyframes at %s -- two key lists "
                             "were merged onto one channel" % (name, dup))
        LH, RH = {}, {}
        for i in range(len(keys) - 1):
            f0, v0, e = keys[i]
            f1, v1 = keys[i + 1][0], keys[i + 1][1]
            x1, y1, x2, y2 = EASE[e]
            dt, dv = float(f1 - f0), float(v1 - v0)
            RH[i]     = (f0 + x1 * dt, v0 + y1 * dv)
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
        sp = self._spline("%s%s" % (tool, inp), keys, color)
        self._set(tool, inp, Link(sp, "Value"))

    def anim_xy(self, tool, inp, keys, color=(0, 160, 255)):
        """keys: [(frame, (x, y), ease), ...] -- constant axes stay static."""
        xs = [(f, p[0], e) for f, p, e in keys]
        ys = [(f, p[1], e) for f, p, e in keys]
        base = "%s%s" % (tool, inp)
        ins = {}
        ins["X"] = (Link(self._spline(base + "X", xs, color), "Value")
                    if len({round(v, 6) for _, v, _ in xs}) > 1 else xs[0][1])
        ins["Y"] = (Link(self._spline(base + "Y", ys, color), "Value")
                    if len({round(v, 6) for _, v, _ in ys}) > 1 else ys[0][1])
        path = self.add(base, "XYPath", inputs=ins,
                        extra='\t\t\tDrawMode = "ModifyOnly",', modifier=True)
        self._set(tool, inp, Link(path, "Value"))

    def _set(self, tool, inp, val):
        for t in self.tools:
            if t["name"] == tool:
                t["inputs"][inp] = val
                return
        raise KeyError(tool)

    # ------------------------------------------------------------ factories
    def bg(self, name, color, pos, alpha=1.0, mask=None):
        i = {"Width": W, "Height": H, "UseFrameFormatSettings": 0,
             "TopLeftRed": color[0], "TopLeftGreen": color[1],
             "TopLeftBlue": color[2], "TopLeftAlpha": alpha,
             "GlobalIn": 0, "GlobalOut": DUR - 1}
        if mask:
            i["EffectMask"] = Link(mask, "Mask")
        return self.add(name, "Background", i, pos)

    def text(self, name, s, size, color, pos, align=H_LEFT, tracking=1.0, font=None, style=None):
        i = {"Width": W, "Height": H, "UseFrameFormatSettings": 0,
             "GlobalIn": 0, "GlobalOut": DUR - 1,
             "StyledText": s, "Font": font or FONT, "Style": style or STYLE,
             "Size": size, "Tracking": tracking, "LineSpacing": 1.0,
             "Red1": color[0], "Green1": color[1], "Blue1": color[2], "Alpha1": 1.0,
             "HorizontalJustificationNew": align, "VerticalJustificationNew": V_CENTER}
        return self.add(name, "TextPlus", i, pos)

    def rect(self, name, w, h, center, pos, soft=0.0):
        i = {"MaskWidth": W, "MaskHeight": H, "Width": w, "Height": h,
             "Center": center, "SoftEdge": soft, "CornerRadius": 0.0,
             "Invert": 0, "MaskClipMode": FuID("None")}
        return self.add(name, "RectangleMask", i, pos)

    def xf(self, name, inp, pos, center=(0.5, 0.5), size=1.0, mask=None, angle=0.0):
        i = {"Input": Link(inp), "Center": center, "Size": size, "Angle": angle}
        if mask:
            i["EffectMask"] = Link(mask, "Mask")
        return self.add(name, "Transform", i, pos)

    def merge(self, name, bg, fg, pos, center=None, blend=None, mask=None, size=None):
        i = {"Background": Link(bg), "Foreground": Link(fg), "PerformDepthMerge": 0}
        if center is not None:
            i["Center"] = center
        if size is not None:
            i["Size"] = size
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
                '\t\t\t\t}\n\t\t\t},') % (filename.replace("\\", "/"), DUR - 1)
        i = {"Loop": 1, "GlobalIn": 0, "GlobalOut": DUR - 1,
             "HoldLastFrame": DUR, "Depth": 0}
        return self.add(name, "Loader", i, pos, extra=clip)


# ----------------------------------------------------------------- patterns
def reveal_text(c, base, s, size, color, x, y, f0, pos, dur=10,
                ease="expoOut", align=H_LEFT, rise=None, tracking=1.0):
    """Typography rising into a fixed crop slot -- the signature move."""
    t = c.text(base + "_T", s, size, color, pos, align=align, tracking=tracking)
    m = c.rect(base + "_M", 1.4, size * 1.75, (0.5, y), (pos[0], pos[1] + 40))
    xf = c.xf(base, t, (pos[0] + 110, pos[1]), mask=m)
    dy = rise if rise is not None else size * 1.05
    c.anim_xy(xf, "Center", [(f0, (x, y - dy), ease), (f0 + dur, (x, y), ease)])
    return xf


def rule(c, base, x, y, width, f0, pos, dur=11, thick=0.0035, color=BLUE, ease="expoOut"):
    """A hairline that grows from its left edge."""
    r = c.rect(base + "_M", width, thick, (x + width / 2.0, y), pos)
    c.anim(r, "Width", [(f0, 0.0, ease), (f0 + dur, width, ease)])
    c.anim_xy(r, "Center", [(f0, (x, y), ease), (f0 + dur, (x + width / 2.0, y), ease)])
    return c.bg(base, color, (pos[0] + 110, pos[1]), mask=r)


def stack(c, base, layers, pos):
    """Merge a list of tools bottom-up onto a transparent field."""
    cur = c.bg(base + "_BASE", BLACK, pos, alpha=0.0)
    for n, layer in enumerate(layers):
        cur = c.merge("%s_MRG%d" % (base, n + 1), cur, layer,
                      (pos[0] + 110 * (n + 1), pos[1]))
    return cur


# ----------------------------------------------------------------- scenes
WORKS = [
    ("BRAND IDENTITY",  "VISUAL SYSTEM / LOGOTYPE / GUIDELINES"),
    ("EDITORIAL DESIGN","LAYOUT SYSTEMS / TYPOGRAPHY / PRINT"),
    ("PACKAGING",       "STRUCTURE / DIELINES / SHELF PRESENCE"),
    ("DIGITAL PRODUCT", "INTERFACE SYSTEMS / DESIGN TOKENS"),
    ("ART DIRECTION",   "CAMPAIGN / IMAGE / TONE OF VOICE"),
]


def scene_hook(c, row):
    f = 0
    L = []
    L.append(reveal_text(c, "S1_LBL", "PORTFOLIO / 2026", LABEL, BLUE,
                         MARGIN, 0.845, f + 2, (0, row), tracking=1.35))
    L.append(reveal_text(c, "S1_A", "BRANDS",   MEGA, WHITE, MARGIN, 0.600, f + 6,  (0, row + 120)))
    L.append(reveal_text(c, "S1_B", "BUILT TO", MEGA, WHITE, MARGIN, 0.505, f + 11, (0, row + 240)))
    L.append(reveal_text(c, "S1_C", "BE SEEN",  MEGA, BLUE,  MARGIN, 0.410, f + 16, (0, row + 360)))
    L.append(rule(c, "S1_R", MARGIN, 0.355, 0.36, f + 24, (0, row + 480)))
    L.append(reveal_text(c, "S1_D", "GRAPHIC DESIGN & ART DIRECTION", BODY, GREY,
                         MARGIN, 0.310, f + 30, (0, row + 560), tracking=1.15))
    return stack(c, "S1", L, (500, row))


def scene_work(c, idx, row, assets):
    f = idx * 90                                  # 90,180,...,450
    title, tag = WORKS[idx - 1]
    top = idx % 2 == 1                            # alternate the grid
    sw, sh = 0.834, 0.44
    scy = 0.655 if top else 0.345
    y0 = scy - sh / 2.0
    cap = 0.375 if top else 0.720

    # --- image slot: loader -> scale drift -> merge positioned + crop-revealed
    ld = c.loader("WORK_%02d" % idx, os.path.join(assets, "WORK_%02d.png" % idx), (0, row))
    xf = c.xf("W%02d_XF" % idx, ld, (110, row))
    c.anim(xf, "Size", [(f, 1.12, "quintOut"), (f + 88, 1.02, "quintOut")])

    slot = c.rect("W%02d_SLOT" % idx, sw, sh, (0.5, scy), (110, row + 60))
    anchor = y0 if top else y0 + sh                # grow up from the bottom edge / down from the top
    c.anim(slot, "Height", [(f + 2, 0.0, "expoOut"), (f + 14, sh, "expoOut")])
    c.anim_xy(slot, "Center",
              [(f + 2, (0.5, anchor), "expoOut"), (f + 14, (0.5, scy), "expoOut")])

    L = []
    base = c.bg("W%02d_FIELD" % idx, BLACK, (220, row), alpha=0.0)
    img = c.merge("W%02d_IMG" % idx, base, xf, (330, row), center=(0.5, scy), mask=slot)
    L.append(img)

    L.append(reveal_text(c, "W%02d_N" % idx, "%02d" % idx, LABEL * 1.7, BLUE,
                         MARGIN, cap, f + 10, (0, row + 140), tracking=1.2))
    L.append(reveal_text(c, "W%02d_T" % idx, title, H2, WHITE,
                         MARGIN, cap - 0.050, f + 14, (0, row + 260)))
    L.append(rule(c, "W%02d_R" % idx, MARGIN, cap - 0.090, 0.28, f + 19, (0, row + 380)))
    L.append(reveal_text(c, "W%02d_G" % idx, tag, BODY * 0.85, GREY,
                         MARGIN, cap - 0.120, f + 23, (0, row + 460), tracking=1.3))
    return stack(c, "W%02d" % idx, L, (500, row))


def scene_value(c, row):
    f = 540
    rows = [("01", "STRATEGY FIRST"), ("02", "SYSTEMS, NOT ASSETS"), ("03", "BUILT TO SCALE")]
    L = [reveal_text(c, "S7_LBL", "HOW I WORK", LABEL, BLUE, MARGIN, 0.845, f + 2,
                     (0, row), tracking=1.35)]
    for n, (num, txt) in enumerate(rows):
        y = 0.640 - n * 0.125
        L.append(reveal_text(c, "S7_N%d" % n, num, LABEL * 1.5, BLUE,
                             MARGIN, y, f + 8 + n * 7, (0, row + 120 + n * 240), tracking=1.2))
        L.append(reveal_text(c, "S7_T%d" % n, txt, H2, WHITE,
                             MARGIN + 0.115, y, f + 11 + n * 7, (0, row + 200 + n * 240)))
    L.append(rule(c, "S7_R", MARGIN, 0.255, 0.42, f + 36, (0, row + 860)))
    return stack(c, "S7", L, (500, row))


def scene_cta(c, row):
    f = 630
    L = []
    L.append(reveal_text(c, "S8_A", "STELIOS", MEGA, WHITE, MARGIN, 0.600, f + 4, (0, row)))
    L.append(reveal_text(c, "S8_B", "MITADIS", MEGA, WHITE, MARGIN, 0.505, f + 9, (0, row + 120)))
    L.append(rule(c, "S8_R1", MARGIN, 0.455, 0.50, f + 16, (0, row + 240)))
    L.append(reveal_text(c, "S8_C", "GRAPHIC DESIGNER", H2 * 0.72, BLUE,
                         MARGIN, 0.415, f + 20, (0, row + 320), tracking=1.4))
    L.append(reveal_text(c, "S8_D", "LET'S BUILD", H1 * 0.78, WHITE, MARGIN, 0.315, f + 28, (0, row + 440)))
    L.append(reveal_text(c, "S8_E", "YOUR BRAND", H1 * 0.78, WHITE, MARGIN, 0.240, f + 33, (0, row + 560)))
    L.append(rule(c, "S8_R2", MARGIN, 0.195, 0.62, f + 40, (0, row + 680), thick=0.006))
    return stack(c, "S8", L, (500, row))


# ----------------------------------------------------------------- wipe rig
def build_wipe(c, row):
    """One reusable hard-edge block that covers, cuts, and uncovers at each
    boundary. Vertical, alternating direction; the last one goes horizontal.

    Width/Height/Center share one rect, so every boundary writes explicit hold
    keys: the block must read as fully hidden (Height 0 or Width 0) at every
    frame outside its own 12-frame window, including while another channel is
    ramping toward the next boundary's start pose.
    """
    hk = [(0, 0.0, "STEP")]
    wk = [(0, 1.0, "STEP")]
    ck = [(0, (0.5, 0.0), "STEP")]
    for n, b in enumerate(BOUNDS):
        a, z = b - 6, b + 6
        if n == len(BOUNDS) - 1:                      # horizontal, left -> right
            hk += [(a - 2, 0.0, "STEP"), (a - 1, 1.0, "STEP"), (z, 1.0, "STEP")]
            wk += [(a - 2, 0.0, "STEP"), (a, 0.0, "quartOut"),
                   (b, 1.0, "expoIn"), (z, 0.0, "STEP")]
            ck += [(a - 2, (0.0, 0.5), "STEP"), (a, (0.0, 0.5), "quartOut"),
                   (b, (0.5, 0.5), "expoIn"), (z, (1.0, 0.5), "STEP")]
        else:                                         # vertical, alternating
            c0, c2 = ((0.0, 1.0) if n % 2 == 0 else (1.0, 0.0))
            wk += [(a, 1.0, "STEP"), (z, 1.0, "STEP")]
            hk += [(a, 0.0, "quartOut"), (b, 1.0, "expoIn"), (z, 0.0, "STEP")]
            ck += [(a, (0.5, c0), "quartOut"), (b, (0.5, 0.5), "expoIn"),
                   (z, (0.5, c2), "STEP")]
    r = c.rect("WIPE_M", 1.0, 0.0, (0.5, 0.5), (0, row))
    c.anim(r, "Height", hk)
    c.anim(r, "Width", wk)
    c.anim_xy(r, "Center", ck)
    return c.bg("WIPE", BLUE, (110, row), mask=r)


# ----------------------------------------------------------------- assembly
def build(assets):
    c = Comp()
    rows = [k * 700 for k in range(8)]
    outs = [scene_hook(c, rows[0])]
    for i in range(1, 6):
        outs.append(scene_work(c, i, rows[i], assets))
    outs.append(scene_value(c, rows[6]))
    outs.append(scene_cta(c, rows[7]))

    # gentle continuous drift per scene (long ease = never reads as linear)
    drifted = []
    for i, o in enumerate(outs):
        s, e = SCENES[i]
        d = c.xf("S%d_DRIFT" % (i + 1), o, (900, rows[i]))
        c.anim_xy(d, "Center", [(s, (0.5, 0.494), "quintOut"),
                                (e - 1, (0.5, 0.508), "quintOut")])
        drifted.append(d)

    # master chain: hard visibility cuts, hidden under the wipe
    y = 5700
    cur = c.bg("MASTER_BG", BLACK, (0, y))
    for i, d in enumerate(drifted):
        s, e = SCENES[i]
        m = c.merge("MRG_S%d" % (i + 1), cur, d, (150 + i * 110, y))
        k = []
        if s > 0:
            k.append((s - 1, 0.0, "STEP"))
        k.append((s, 1.0, "STEP"))
        if e < DUR:
            k += [(e - 1, 1.0, "STEP"), (e, 0.0, "STEP")]
        c.anim(m, "Blend", k, color=(120, 120, 120))
        cur = m

    wipe = build_wipe(c, y + 200)
    cur = c.merge("MRG_WIPE", cur, wipe, (1050, y))
    final = c.xf("FINAL_OUT", cur, (1180, y))
    return c, final


# ----------------------------------------------------------------- smoke test
def build_smoke(assets):
    """Every construct the big comp relies on, in ~12 nodes. Paste this first."""
    c = Comp()
    bg = c.bg("SMOKE_BG", BLACK, (0, 0))
    t = c.text("SMOKE_TXT", "TEST", MEGA, WHITE, (0, 120), align=H_LEFT)
    m = c.rect("SMOKE_MASK", 1.4, MEGA * 1.75, (0.5, 0.5), (0, 200))
    xf = c.xf("SMOKE_XF", t, (110, 120), mask=m)
    c.anim_xy(xf, "Center", [(0, (MARGIN, 0.40), "expoOut"), (12, (MARGIN, 0.50), "expoOut")])
    c.anim(xf, "Size", [(0, 0.85, "backOut"), (14, 1.0, "backOut")])
    m1 = c.merge("SMOKE_M1", bg, xf, (220, 0))
    r = rule(c, "SMOKE_RULE", MARGIN, 0.44, 0.40, 6, (0, 320))
    m2 = c.merge("SMOKE_M2", m1, r, (330, 0))
    ld = c.loader("WORK_01", os.path.join(assets, "WORK_01.png"), (0, 420))
    m3 = c.merge("SMOKE_M3", m2, ld, (440, 0), center=(0.5, 0.72))
    c.anim(m3, "Blend", [(0, 0.0, "STEP"), (1, 1.0, "STEP")], color=(120, 120, 120))
    return c, m3


def main():
    ap = argparse.ArgumentParser()
    here = os.path.dirname(os.path.abspath(__file__))
    ap.add_argument("--assets", default=os.path.join(here, "out", "assets"),
                    help="folder holding WORK_01..05.png, as Resolve will see it")
    ap.add_argument("--font", default="Helvetica Neue")
    ap.add_argument("--style", default="Bold")
    ap.add_argument("--out", default=os.path.join(here, "out"))
    a = ap.parse_args()

    global FONT, STYLE
    FONT, STYLE = a.font, a.style
    os.makedirs(a.out, exist_ok=True)

    c, final = build(a.assets.replace("\\", "/").rstrip("/"))
    p = os.path.join(a.out, "stelios_promo.comp")
    open(p, "w", encoding="utf-8").write(c.render(active=final))
    print("wrote %s  (%d nodes, %d frames, %s @ %dfps)"
          % (p, len(c.tools), DUR, "%dx%d" % (W, H), FPS))

    sc, sfinal = build_smoke(a.assets.replace("\\", "/").rstrip("/"))
    sp = os.path.join(a.out, "smoke_test.comp")
    open(sp, "w", encoding="utf-8").write(sc.render(active=sfinal))
    print("wrote %s  (%d nodes)" % (sp, len(sc.tools)))


FONT, STYLE = "Helvetica Neue", "Bold"
if __name__ == "__main__":
    main()
