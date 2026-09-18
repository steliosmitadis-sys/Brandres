#!/usr/bin/env python3
"""
templates.py -- ready-made motion-design specs.

Each function returns a plain spec dict for compbuilder.build(). Everything is
a parameter, so an agent can restyle a piece without touching node graphs.
"""
import os

SWISS = {
    "bg": "#0B0B0C", "fg": "#F2F2F4", "accent": "#124DFF", "muted": "#6B6B73",
}

DEFAULT_WORKS = [
    ("BRAND IDENTITY",   "VISUAL SYSTEM / LOGOTYPE / GUIDELINES"),
    ("EDITORIAL DESIGN", "LAYOUT SYSTEMS / TYPOGRAPHY / PRINT"),
    ("PACKAGING",        "STRUCTURE / DIELINES / SHELF PRESENCE"),
    ("DIGITAL PRODUCT",  "INTERFACE SYSTEMS / DESIGN TOKENS"),
    ("ART DIRECTION",    "CAMPAIGN / IMAGE / TONE OF VOICE"),
]

DEFAULT_VALUES = [("01", "STRATEGY FIRST"),
                  ("02", "SYSTEMS, NOT ASSETS"),
                  ("03", "BUILT TO SCALE")]


def portfolio_promo(
    name_lines=("STELIOS", "MITADIS"),
    role="GRAPHIC DESIGNER",
    cta_lines=("LET'S BUILD", "YOUR BRAND"),
    hook_lines=("BRANDS", "BUILT TO", "BE SEEN"),
    kicker="PORTFOLIO / 2026",
    subline="GRAPHIC DESIGN & ART DIRECTION",
    values_kicker="HOW I WORK",
    works=None,
    values=None,
    assets="C:/promo/assets",
    font="Helvetica Neue",
    style="Bold",
    palette=None,
    scene_frames=90,
    width=1080, height=1920, fps=30,
):
    """Vertical portfolio promo: hook, 5 work slots, value prop, end card."""
    works = list(works or DEFAULT_WORKS)[:5]
    while len(works) < 5:
        works.append(DEFAULT_WORKS[len(works)])
    values = list(values or DEFAULT_VALUES)
    pal = dict(SWISS)
    pal.update(palette or {})
    M = 0.083
    F = int(scene_frames)
    assets = str(assets).replace("\\", "/").rstrip("/")
    scenes = []

    # ---- 0-3s hook -------------------------------------------------------
    hook = [{"type": "text", "text": kicker, "size": "label", "color": "accent",
             "y": 0.845, "at": 2, "tracking": 1.35}]
    for i, line in enumerate(hook_lines[:3]):
        hook.append({"type": "text", "text": line, "size": "mega",
                     "color": "accent" if i == len(hook_lines[:3]) - 1 else "fg",
                     "y": 0.600 - i * 0.095, "at": 6 + i * 5})
    hook += [
        {"type": "rule", "y": 0.355, "width": 0.36, "at": 24},
        {"type": "text", "text": subline, "size": "body", "color": "muted",
         "y": 0.310, "at": 30, "tracking": 1.15},
    ]
    scenes.append({"start": 0, "end": F, "elements": hook})

    # ---- 3-18s the five work slots --------------------------------------
    for i in range(5):
        title, tag = works[i]
        top = i % 2 == 0
        sy = 0.435 if top else 0.125
        cap = 0.375 if top else 0.720
        scenes.append({
            "start": F * (i + 1), "end": F * (i + 2),
            "elements": [
                {"type": "image", "name": "WORK_%02d" % (i + 1),
                 "file": "%s/WORK_%02d.png" % (assets, i + 1),
                 "slot": [M, sy, 1 - 2 * M, 0.44], "at": 2,
                 "anchor": "bottom" if top else "top"},
                {"type": "text", "text": "%02d" % (i + 1), "size": 0.017 * 1.7,
                 "color": "accent", "y": cap, "at": 10, "tracking": 1.2},
                {"type": "text", "text": title, "size": "h2",
                 "y": cap - 0.050, "at": 14},
                {"type": "rule", "y": cap - 0.090, "width": 0.28, "at": 19},
                {"type": "text", "text": tag, "size": 0.024 * 0.85, "color": "muted",
                 "y": cap - 0.120, "at": 23, "tracking": 1.3},
            ],
        })

    # ---- 18-21s value proposition ---------------------------------------
    val = [{"type": "text", "text": values_kicker, "size": "label", "color": "accent",
            "y": 0.845, "at": 2, "tracking": 1.35}]
    for n, (num, txt) in enumerate(values[:3]):
        y = 0.640 - n * 0.125
        val += [
            {"type": "text", "text": num, "size": 0.017 * 1.5, "color": "accent",
             "y": y, "at": 8 + n * 7, "tracking": 1.2},
            {"type": "text", "text": txt, "size": "h2", "x": M + 0.115,
             "y": y, "at": 11 + n * 7},
        ]
    val.append({"type": "rule", "y": 0.255, "width": 0.42, "at": 36})
    scenes.append({"start": F * 6, "end": F * 7, "elements": val})

    # ---- 21-24s end card -------------------------------------------------
    cta = []
    for i, line in enumerate(name_lines[:2]):
        cta.append({"type": "text", "text": line, "size": "mega",
                    "y": 0.600 - i * 0.095, "at": 4 + i * 5})
    cta += [
        {"type": "rule", "y": 0.455, "width": 0.50, "at": 16},
        {"type": "text", "text": role, "size": 0.046 * 0.72, "color": "accent",
         "y": 0.415, "at": 20, "tracking": 1.4},
    ]
    for i, line in enumerate(cta_lines[:2]):
        cta.append({"type": "text", "text": line, "size": 0.072 * 0.78,
                    "y": 0.315 - i * 0.075, "at": 28 + i * 5})
    cta.append({"type": "rule", "y": 0.195, "width": 0.62, "at": 40, "thickness": 0.006})
    scenes.append({"start": F * 7, "end": F * 8, "elements": cta})

    return {
        "width": width, "height": height, "fps": fps, "duration": F * 8,
        "font": font, "style": style, "margin": M, "palette": pal,
        "transition": {"style": "block-wipe", "color": "accent", "frames": 12},
        "scenes": scenes,
    }


def title_card(text_lines, kicker=None, font="Helvetica Neue", style="Bold",
               palette=None, frames=90, width=1080, height=1920, fps=30):
    """A single eased title card -- the smallest useful piece."""
    pal = dict(SWISS)
    pal.update(palette or {})
    els = []
    if kicker:
        els.append({"type": "text", "text": kicker, "size": "label",
                    "color": "accent", "y": 0.78, "at": 2, "tracking": 1.35})
    for i, line in enumerate(text_lines):
        els.append({"type": "text", "text": line, "size": "mega",
                    "y": 0.56 - i * 0.095, "at": 5 + i * 5})
    els.append({"type": "rule", "y": 0.56 - len(text_lines) * 0.095, "width": 0.4,
                "at": 6 + len(text_lines) * 5})
    return {"width": width, "height": height, "fps": fps, "duration": frames,
            "font": font, "style": style, "palette": pal,
            "transition": {"style": "none"},
            "scenes": [{"start": 0, "end": frames, "elements": els}]}


TEMPLATES = {"portfolio_promo": portfolio_promo, "title_card": title_card}
