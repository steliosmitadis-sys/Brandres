#!/usr/bin/env python3
"""
make_placeholders.py — generate the five WORK_0N placeholder stills.

Pure stdlib (zlib + struct): no Pillow, no install step. Each placeholder is a
dark card with an electric-blue hairline frame, a large index numeral and a
tick-row, sized to exactly fill the comp's image slot so the promo renders
correctly the moment you paste it -- before you have swapped in real work.

To swap in your own screenshot later: either overwrite assets/WORK_01.png, or
point the WORK_01 Loader node at any file you like.
"""
import argparse, os, struct, zlib

# slot is 0.834 x 0.44 of a 1080x1920 frame
SLOT_W, SLOT_H = 900, 844

BG     = (0x14, 0x14, 0x16)
FRAME  = (0x12, 0x4D, 0xFF)
DIGIT  = (0xF2, 0xF2, 0xF4)
MUTED  = (0x3A, 0x3A, 0x40)

# 5x7 bitmap digits
FONT = {
    "0": ["01110", "10001", "10011", "10101", "11001", "10001", "01110"],
    "1": ["00100", "01100", "00100", "00100", "00100", "00100", "01110"],
    "2": ["01110", "10001", "00001", "00010", "00100", "01000", "11111"],
    "3": ["11111", "00010", "00100", "00010", "00001", "10001", "01110"],
    "4": ["00010", "00110", "01010", "10010", "11111", "00010", "00010"],
    "5": ["11111", "10000", "11110", "00001", "00001", "10001", "01110"],
    "6": ["00110", "01000", "10000", "11110", "10001", "10001", "01110"],
    "7": ["11111", "00001", "00010", "00100", "01000", "01000", "01000"],
    "8": ["01110", "10001", "10001", "01110", "10001", "10001", "01110"],
    "9": ["01110", "10001", "10001", "01111", "00001", "00010", "01100"],
}


class Canvas:
    def __init__(self, w, h, fill):
        self.w, self.h = w, h
        self.px = bytearray(bytes(fill) * (w * h))

    def rect(self, x, y, w, h, color):
        c = bytes(color)
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(self.w, x + w), min(self.h, y + h)
        for yy in range(y0, y1):
            base = (yy * self.w + x0) * 3
            self.px[base:base + (x1 - x0) * 3] = c * (x1 - x0)

    def frame(self, x, y, w, h, t, color):
        self.rect(x, y, w, t, color)
        self.rect(x, y + h - t, w, t, color)
        self.rect(x, y, t, h, color)
        self.rect(x + w - t, y, t, h, color)

    def glyph(self, ch, x, y, scale, color):
        rows = FONT.get(ch)
        if not rows:
            return 0
        for ry, row in enumerate(rows):
            for rx, bit in enumerate(row):
                if bit == "1":
                    self.rect(x + rx * scale, y + ry * scale, scale, scale, color)
        return 5 * scale

    def text(self, s, x, y, scale, color, gap=2):
        cx = x
        for ch in s:
            cx += self.glyph(ch, cx, y, scale, color) + gap * scale
        return cx

    def png(self, path):
        raw = b"".join(
            b"\x00" + bytes(self.px[y * self.w * 3:(y + 1) * self.w * 3])
            for y in range(self.h)
        )
        def chunk(tag, data):
            return (struct.pack(">I", len(data)) + tag + data
                    + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))
        with open(path, "wb") as f:
            f.write(b"\x89PNG\r\n\x1a\n")
            f.write(chunk(b"IHDR", struct.pack(">IIBBBBB", self.w, self.h, 8, 2, 0, 0, 0)))
            f.write(chunk(b"IDAT", zlib.compress(raw, 9)))
            f.write(chunk(b"IEND", b""))


def build(index, w, h):
    c = Canvas(w, h, BG)
    m = 28
    c.frame(m, m, w - 2 * m, h - 2 * m, 2, FRAME)

    # large index numeral, optically centred
    label = "%02d" % index
    scale = 18
    tw = len(label) * 5 * scale + (len(label) - 1) * 2 * scale
    c.text(label, (w - tw) // 2, (h - 7 * scale) // 2 - 30, scale, DIGIT)

    # tick row: filled up to `index`, muted after
    tick_w, tick_gap, n = 54, 14, 5
    total = n * tick_w + (n - 1) * tick_gap
    tx, ty = (w - total) // 2, (h // 2) + 96
    for i in range(n):
        c.rect(tx + i * (tick_w + tick_gap), ty, tick_w, 6,
               FRAME if i < index else MUTED)

    # corner registration marks
    for (cx, cy) in ((m + 18, m + 18), (w - m - 18 - 34, m + 18),
                     (m + 18, h - m - 18 - 34), (w - m - 18 - 34, h - m - 18 - 34)):
        c.rect(cx, cy + 16, 34, 2, MUTED)
        c.rect(cx + 16, cy, 2, 34, MUTED)
    return c


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(os.path.dirname(__file__), "out", "assets"))
    ap.add_argument("--width", type=int, default=SLOT_W)
    ap.add_argument("--height", type=int, default=SLOT_H)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    for i in range(1, 6):
        p = os.path.join(a.out, "WORK_%02d.png" % i)
        build(i, a.width, a.height).png(p)
        print("wrote", p)


if __name__ == "__main__":
    main()
