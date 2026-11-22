#!/usr/bin/env python3
"""Sum up 21 November 2026 world news in one image.

A 1024x1024 newspaper front page: the six most consequential stories
of Saturday 21 November 2026 in a 2x3 grid, plus a ticker of three more
and a sources footer. Dark navy design, big date header.

Written with the Python standard library ONLY (no Pillow, no other
third-party code): text is set from a bitmap font atlas (atlas.png,
baked at build time from DejaVu) that is decoded here with zlib,
shapes are drawn with small raster helpers written below, and the
final PNG is encoded by hand. No network, no clock, no randomness:
every run writes identical bytes.

Run:  python3 main.py                       (writes ./entry.png if /output is absent)
      MAKEFUN_OUTPUT_DIR=out python3 main.py
"""

import binascii
import math
import os
import struct
import zlib

W = 1024
H = 1024

# --- palette ---------------------------------------------------------------
BG = (13, 27, 42)        # deep navy page
PANEL = (22, 39, 61)      # story panel
PANEL_LINE = (47, 79, 112)
GOLD = (232, 184, 75)
WHITE = (255, 255, 255)
MUTED = (185, 199, 214)
FAINT = (133, 150, 168)

STORIES = [
    {
        "kicker": "JUSTICE",
        "color": (232, 184, 75),
        "headline": "MYANMAR GUILTY OF GENOCIDE",
        "summary": "World court finds Myanmar committed genocide against the Rohingya, a first in its history.",
        "icon": "scales",
    },
    {
        "kicker": "WAR",
        "color": (228, 87, 46),
        "headline": "RUSSIAN MISSILES HIT POLAND",
        "summary": "Moscow's missiles cross into Poland as NATO allies respond.",
        "icon": "missile",
    },
    {
        "kicker": "SUMMIT",
        "color": (46, 196, 182),
        "headline": "TRUMP, XI & PUTIN MEET",
        "summary": "Three leaders hold a first three-way summit in Shenzhen.",
        "icon": "people",
    },
    {
        "kicker": "QUAKE",
        "color": (244, 162, 89),
        "headline": "6.8 QUAKE SHAKES PERU",
        "summary": "Strong earthquake strikes central Peru; tremors felt in Lima.",
        "icon": "seismic",
    },
    {
        "kicker": "MARKETS",
        "color": (127, 179, 213),
        "headline": "TECH STOCKS TUMBLE",
        "summary": "Sell-off drags markets down as Anthropic shares slide.",
        "icon": "chart",
    },
    {
        "kicker": "PROTEST",
        "color": (199, 125, 255),
        "headline": "GEN Z TAKES TO THE STREETS",
        "summary": "Thousands rally across 25 European countries over costs, war and climate.",
        "icon": "megaphone",
    },
]

TICKER = ("ALSO: Houthi missile hits Riyadh tower, no injuries  |  "
          "Mamdani sets 2032 to close Rikers Island  |  "
          "COP31 climate deal stalls")
FOOTER = "SOURCES: ICJ  |  REUTERS  |  AP  |  AL JAZEERA  -  21 NOV 2026"


# --- font atlas ------------------------------------------------------------
# atlas.png: RGBA, white glyphs on transparent ground, baked from DejaVu
# at size 80. 16 cells per row, cell 96x112, baseline 84 px down from the
# cell top. Regular glyphs live in rows 0-5, bold in rows 6-11.
# Per glyph: (advance, left, top, right, bottom) in atlas px; left/right
# are measured from the cell's left edge, top/bottom from the baseline
# (negative above it). Advance is the pen move for the glyph.
ATLAS_FILE = "atlas.png"
ATLAS_SIZE = 80
ATLAS_CELL_W = 96
ATLAS_CELL_H = 112
ATLAS_COLS = 16
ATLAS_BASELINE = 84
ATLAS_ASCENT = 75
ATLAS_PAD = 8
ATLAS_BOLD_ROW = 6

GLYPH_REG = {
    32: (25, 8, 0, 33, 0), 33: (32, 8, -58, 40, 0), 34: (37, 8, -58, 45, 0), 35: (67, 8, -57, 75, 0),
    36: (51, 8, -61, 59, 12), 37: (76, 8, -59, 84, 1), 38: (62, 8, -59, 70, 1), 39: (22, 8, -58, 30, 0),
    40: (31, 8, -61, 39, 10), 41: (31, 8, -61, 39, 10), 42: (40, 8, -59, 48, 0), 43: (67, 8, -50, 75, 0),
    44: (25, 8, -10, 33, 9), 45: (29, 8, -25, 37, 0), 46: (25, 8, -10, 33, 0), 47: (27, 8, -58, 35, 8),
    48: (51, 8, -59, 59, 1), 49: (51, 8, -58, 59, 0), 50: (51, 8, -59, 59, 0), 51: (51, 8, -59, 59, 1),
    52: (51, 8, -58, 59, 0), 53: (51, 8, -58, 59, 1), 54: (51, 8, -59, 59, 1), 55: (51, 8, -58, 59, 0),
    56: (51, 8, -59, 59, 1), 57: (51, 8, -59, 59, 1), 58: (27, 8, -41, 35, 0), 59: (27, 8, -41, 35, 9),
    60: (67, 8, -47, 75, 0), 61: (67, 8, -35, 75, 0), 62: (67, 8, -47, 75, 0), 63: (42, 8, -59, 50, 0),
    64: (80, 8, -56, 88, 14), 65: (55, 8, -58, 63, 0), 66: (55, 8, -58, 63, 0), 67: (56, 8, -59, 64, 1),
    68: (62, 8, -58, 70, 0), 69: (51, 8, -58, 59, 0), 70: (46, 8, -58, 54, 0), 71: (62, 8, -59, 70, 1),
    72: (60, 8, -58, 68, 0), 73: (24, 8, -58, 32, 0), 74: (24, 3, -58, 32, 16), 75: (52, 8, -58, 63, 0),
    76: (45, 8, -58, 53, 0), 77: (69, 8, -58, 77, 0), 78: (60, 8, -58, 68, 0), 79: (63, 8, -59, 71, 1),
    80: (48, 8, -58, 56, 0), 81: (63, 8, -59, 71, 10), 82: (56, 8, -58, 64, 0), 83: (51, 8, -59, 59, 1),
    84: (49, 7, -58, 58, 0), 85: (59, 8, -58, 67, 1), 86: (55, 8, -58, 63, 0), 87: (79, 8, -58, 87, 0),
    88: (55, 8, -58, 63, 0), 89: (49, 7, -58, 58, 0), 90: (55, 8, -58, 63, 0), 91: (31, 8, -61, 39, 10),
    92: (27, 8, -58, 35, 8), 93: (31, 8, -61, 39, 10), 94: (67, 8, -58, 75, 0), 95: (40, 7, 0, 49, 19),
    96: (40, 8, -64, 48, 0), 97: (49, 8, -45, 57, 1), 98: (51, 8, -61, 59, 1), 99: (44, 8, -45, 52, 1),
    100: (51, 8, -61, 59, 1), 101: (49, 8, -45, 57, 1), 102: (28, 8, -61, 38, 0), 103: (51, 8, -45, 59, 17),
    104: (51, 8, -61, 59, 0), 105: (22, 8, -61, 30, 0), 106: (22, 6, -61, 30, 17), 107: (46, 8, -61, 55, 0),
    108: (22, 8, -61, 30, 0), 109: (78, 8, -45, 86, 0), 110: (51, 8, -45, 59, 0), 111: (49, 8, -45, 57, 1),
    112: (51, 8, -45, 59, 17), 113: (51, 8, -45, 59, 17), 114: (33, 8, -45, 41, 0), 115: (42, 8, -45, 50, 1),
    116: (31, 8, -56, 39, 0), 117: (51, 8, -45, 59, 1), 118: (47, 8, -44, 55, 0), 119: (65, 8, -44, 73, 0),
    120: (47, 8, -44, 55, 0), 121: (47, 8, -44, 55, 17), 122: (42, 8, -44, 50, 0), 123: (51, 8, -61, 59, 13),
    124: (27, 8, -61, 35, 19), 125: (51, 8, -61, 59, 13), 126: (67, 8, -32, 75, 0),
}
GLYPH_BOLD = {
    32: (28, 8, 0, 36, 0), 33: (36, 8, -58, 44, 0), 34: (42, 8, -58, 50, 0), 35: (67, 8, -57, 75, 0),
    36: (56, 8, -61, 64, 12), 37: (80, 8, -59, 88, 1), 38: (70, 8, -59, 78, 1), 39: (24, 8, -58, 33, 0),
    40: (37, 8, -61, 45, 10), 41: (37, 8, -61, 45, 10), 42: (42, 8, -59, 50, 0), 43: (67, 8, -51, 75, 0),
    44: (30, 8, -15, 38, 11), 45: (33, 8, -29, 41, 0), 46: (30, 8, -15, 38, 0), 47: (29, 8, -58, 38, 8),
    48: (56, 8, -59, 64, 1), 49: (56, 8, -58, 64, 0), 50: (56, 8, -59, 64, 0), 51: (56, 8, -59, 64, 1),
    52: (56, 8, -58, 64, 0), 53: (56, 8, -58, 64, 1), 54: (56, 8, -59, 64, 1), 55: (56, 8, -58, 64, 0),
    56: (56, 8, -59, 64, 1), 57: (56, 8, -59, 64, 1), 58: (32, 8, -44, 40, 0), 59: (32, 8, -44, 40, 11),
    60: (67, 8, -48, 75, 0), 61: (67, 8, -39, 75, 0), 62: (67, 8, -48, 75, 0), 63: (46, 8, -58, 54, 0),
    64: (80, 8, -56, 88, 14), 65: (62, 8, -58, 70, 0), 66: (61, 8, -58, 69, 0), 67: (59, 8, -59, 67, 1),
    68: (66, 8, -58, 74, 0), 69: (55, 8, -58, 63, 0), 70: (55, 8, -58, 63, 0), 71: (66, 8, -59, 74, 1),
    72: (67, 8, -58, 75, 0), 73: (30, 8, -58, 38, 0), 74: (30, 3, -58, 38, 16), 75: (62, 8, -58, 73, 0),
    76: (51, 8, -58, 59, 0), 77: (80, 8, -58, 88, 0), 78: (67, 8, -58, 75, 0), 79: (68, 8, -59, 76, 1),
    80: (59, 8, -58, 67, 0), 81: (68, 8, -59, 76, 12), 82: (62, 8, -58, 70, 0), 83: (58, 8, -59, 66, 1),
    84: (55, 8, -58, 63, 0), 85: (65, 8, -58, 73, 1), 86: (62, 8, -58, 70, 0), 87: (88, 8, -58, 96, 0),
    88: (62, 8, -58, 70, 0), 89: (58, 7, -58, 67, 0), 90: (58, 8, -58, 66, 0), 91: (37, 8, -61, 45, 10),
    92: (29, 8, -58, 38, 8), 93: (37, 8, -61, 45, 10), 94: (67, 8, -58, 75, 0), 95: (40, 8, 0, 48, 19),
    96: (40, 8, -64, 48, 0), 97: (54, 8, -45, 62, 1), 98: (57, 8, -61, 65, 1), 99: (47, 8, -45, 55, 1),
    100: (57, 8, -61, 65, 1), 101: (54, 8, -45, 62, 1), 102: (35, 8, -61, 44, 0), 103: (57, 8, -45, 65, 17),
    104: (57, 8, -61, 65, 0), 105: (27, 8, -61, 35, 0), 106: (27, 5, -61, 35, 17), 107: (53, 8, -61, 63, 0),
    108: (27, 8, -61, 35, 0), 109: (83, 8, -45, 91, 0), 110: (57, 8, -45, 65, 0), 111: (55, 8, -45, 63, 1),
    112: (57, 8, -45, 65, 17), 113: (57, 8, -45, 65, 17), 114: (39, 8, -45, 48, 0), 115: (48, 8, -45, 56, 1),
    116: (38, 8, -56, 46, 0), 117: (57, 8, -44, 65, 1), 118: (52, 8, -44, 60, 0), 119: (74, 8, -44, 82, 0),
    120: (52, 8, -44, 60, 0), 121: (52, 8, -44, 60, 17), 122: (47, 8, -44, 55, 0), 123: (57, 8, -61, 65, 13),
    124: (29, 8, -61, 37, 19), 125: (57, 8, -61, 65, 13), 126: (67, 8, -33, 75, 0),
}


# --- PNG codec -------------------------------------------------------------
# Minimal reader (8-bit, non-interlaced, colour types 0/2/3/4/6) and writer
# for the atlas and the finished page. Written from the PNG spec, no libs.

def _png_chunk(typ, payload):
    return (struct.pack(">I", len(payload)) + typ + payload +
            struct.pack(">I", binascii.crc32(typ + payload) & 0xFFFFFFFF))


def encode_png(rgb, w, h):
    """Encode raw RGB bytes as a PNG (filter 0 on every row)."""
    raw = bytearray()
    stride = w * 3
    for y in range(h):
        raw.append(0)
        raw += rgb[y * stride:(y + 1) * stride]
    comp = zlib.compress(bytes(raw), 9)
    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + _png_chunk(b"IHDR", ihdr) +
            _png_chunk(b"IDAT", comp) + _png_chunk(b"IEND", b""))


def read_png_rgba(path):
    """Read a PNG file and return (width, height, RGBA bytes)."""
    with open(path, "rb") as f:
        data = f.read()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("not a PNG file: %s" % path)
    pos = 8
    width = height = None
    depth = ctype = interlace = None
    palette = None
    trns = None
    idat = bytearray()
    while pos < len(data):
        ln = struct.unpack(">I", data[pos:pos + 4])[0]
        typ = data[pos + 4:pos + 8]
        chunk = data[pos + 8:pos + 8 + ln]
        if typ == b"IHDR":
            width, height, depth, ctype, _, _, interlace = struct.unpack(
                ">IIBBBBB", chunk)
        elif typ == b"PLTE":
            palette = chunk
        elif typ == b"tRNS":
            trns = chunk
        elif typ == b"IDAT":
            idat += chunk
        elif typ == b"IEND":
            break
        pos += 12 + ln
    if depth != 8 or interlace != 0:
        raise ValueError("unsupported PNG depth/interlace")
    nch = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}.get(ctype)
    if nch is None:
        raise ValueError("unsupported PNG colour type %r" % ctype)
    stride = width * nch
    raw = zlib.decompress(bytes(idat))
    out = bytearray(width * height * 4)
    prev = bytearray(stride)
    p = 0
    for y in range(height):
        ft = raw[p]
        p += 1
        row = bytearray(raw[p:p + stride])
        p += stride
        if ft == 1:
            for i in range(nch, stride):
                row[i] = (row[i] + row[i - nch]) & 255
        elif ft == 2:
            for i in range(stride):
                row[i] = (row[i] + prev[i]) & 255
        elif ft == 3:
            for i in range(stride):
                a = row[i - nch] if i >= nch else 0
                row[i] = (row[i] + ((a + prev[i]) >> 1)) & 255
        elif ft == 4:
            for i in range(stride):
                a = row[i - nch] if i >= nch else 0
                b = prev[i]
                cc = prev[i - nch] if i >= nch else 0
                pp = a + b - cc
                pa, pb, pc = abs(pp - a), abs(pp - b), abs(pp - cc)
                pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else cc)
                row[i] = (row[i] + pr) & 255
        elif ft != 0:
            raise ValueError("bad PNG filter %d" % ft)
        if ctype == 6:
            out[y * width * 4:(y + 1) * width * 4] = row
        elif ctype == 2:
            for x in range(width):
                o = (y * width + x) * 4
                s = x * 3
                out[o] = row[s]
                out[o + 1] = row[s + 1]
                out[o + 2] = row[s + 2]
                out[o + 3] = 255
        elif ctype == 0:
            for x in range(width):
                o = (y * width + x) * 4
                v = row[x]
                out[o] = v
                out[o + 1] = v
                out[o + 2] = v
                out[o + 3] = 255
        elif ctype == 3:
            for x in range(width):
                k = row[x]
                o = (y * width + x) * 4
                out[o] = palette[k * 3]
                out[o + 1] = palette[k * 3 + 1]
                out[o + 2] = palette[k * 3 + 2]
                out[o + 3] = trns[k] if trns and k < len(trns) else 255
        elif ctype == 4:
            for x in range(width):
                o = (y * width + x) * 4
                v = row[x * 2]
                out[o] = v
                out[o + 1] = v
                out[o + 2] = v
                out[o + 3] = row[x * 2 + 1]
        prev = row
    return width, height, bytes(out)


# --- canvas ----------------------------------------------------------------
canvas = bytearray(W * H * 3)


def _set(x, y, c):
    if 0 <= x < W and 0 <= y < H:
        i = (y * W + x) * 3
        canvas[i] = c[0]
        canvas[i + 1] = c[1]
        canvas[i + 2] = c[2]


def _blend(x, y, c, a):
    if a <= 0:
        return
    if 0 <= x < W and 0 <= y < H:
        i = (y * W + x) * 3
        if a >= 255:
            canvas[i] = c[0]
            canvas[i + 1] = c[1]
            canvas[i + 2] = c[2]
        else:
            canvas[i] = (canvas[i] * (255 - a) + c[0] * a) // 255
            canvas[i + 1] = (canvas[i + 1] * (255 - a) + c[1] * a) // 255
            canvas[i + 2] = (canvas[i + 2] * (255 - a) + c[2] * a) // 255


def hline(x0, x1, y, c):
    if y < 0 or y >= H:
        return
    if x0 > x1:
        x0, x1 = x1, x0
    x0 = max(0, x0)
    x1 = min(W - 1, x1)
    for x in range(x0, x1 + 1):
        i = (y * W + x) * 3
        canvas[i] = c[0]
        canvas[i + 1] = c[1]
        canvas[i + 2] = c[2]


def fill_rect(x, y, w, h, c):
    x0 = max(0, x)
    y0 = max(0, y)
    x1 = min(W, x + w)
    y1 = min(H, y + h)
    for yy in range(y0, y1):
        base = yy * W * 3 + x0 * 3
        for xx in range(x0, x1):
            i = base + (xx - x0) * 3
            canvas[i] = c[0]
            canvas[i + 1] = c[1]
            canvas[i + 2] = c[2]


def line(x0, y0, x1, y1, c):
    """Bresenham line, 1 px wide."""
    dx = abs(x1 - x0)
    dy = -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    while True:
        _set(x0, y0, c)
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy


def fill_poly(points, c):
    """Scanline fill of a simple polygon (even-odd rule)."""
    if len(points) < 3:
        return
    ys = [p[1] for p in points]
    y0, y1 = min(ys), max(ys)
    n = len(points)
    for y in range(y0, y1 + 1):
        xs = []
        for i in range(n):
            xa, ya = points[i]
            xb, yb = points[(i + 1) % n]
            if ya == yb:
                continue
            if (ya <= y < yb) or (yb <= y < ya):
                xs.append(xa + (y - ya) * (xb - xa) / (yb - ya))
        xs.sort()
        for k in range(0, len(xs) - 1, 2):
            hline(int(xs[k]), int(xs[k + 1]), y, c)


def thick_seg(x0, y0, x1, y1, t, c):
    """A line segment drawn t px thick (filled quad, or a disc for a dot)."""
    dx, dy = x1 - x0, y1 - y0
    d = math.hypot(dx, dy)
    if d == 0:
        disc(x0, y0, max(1, t // 2), c)
        return
    px = -dy / d * t / 2.0
    py = dx / d * t / 2.0
    fill_poly([(int(x0 + px), int(y0 + py)), (int(x1 + px), int(y1 + py)),
               (int(x1 - px), int(y1 - py)), (int(x0 - px), int(y0 - py))], c)


def disc(cx, cy, r, c):
    for dy in range(-r, r + 1):
        dx = int(math.sqrt(r * r - dy * dy))
        hline(cx - dx, cx + dx, cy + dy, c)


def dome(cx, cy, rx, ry, c):
    """Upper half of a filled ellipse (shoulders under a head)."""
    for dy in range(-ry, 1):
        f = 1.0 - (dy * dy) / float(ry * ry)
        dx = int(rx * math.sqrt(f)) if f > 0 else 0
        hline(cx - dx, cx + dx, cy + dy, c)


def fill_round(x, y, w, h, r, c):
    """Filled rectangle with rounded corners of radius r."""
    for yy in range(y, y + h):
        if yy - y < r:
            d = (y + r) - yy
            dx = int(math.sqrt(r * r - d * d))
            x0 = x + r - dx
            x1 = x + w - r + dx - 1
        elif (y + h - 1) - yy < r:
            d = yy - (y + h - 1 - r)
            dx = int(math.sqrt(r * r - d * d))
            x0 = x + r - dx
            x1 = x + w - r + dx - 1
        else:
            x0 = x
            x1 = x + w - 1
        hline(x0, x1, yy, c)


# --- text from the atlas ---------------------------------------------------
ATLAS_W = 0
ATLAS_H = 0
ATLAS = b""
_GLYPH_CACHE = {}


def _load_atlas():
    global ATLAS_W, ATLAS_H, ATLAS
    here = os.path.dirname(os.path.abspath(__file__))
    ATLAS_W, ATLAS_H, ATLAS = read_png_rgba(os.path.join(here, ATLAS_FILE))


def _resample(src, sw, sh, tw, th):
    """Area-average a grayscale bitmap from sw x sh down to tw x th."""
    out = bytearray(tw * th)
    xs = sw / tw
    ys = sh / th
    for ty in range(th):
        sy0 = ty * ys
        sy1 = sy0 + ys
        j0 = int(sy0)
        j1 = int(sy1)
        if j1 >= sh:
            j1 = sh - 1
        for tx in range(tw):
            sx0 = tx * xs
            sx1 = sx0 + xs
            i0 = int(sx0)
            i1 = int(sx1)
            if i1 >= sw:
                i1 = sw - 1
            total = 0.0
            wsum = 0.0
            for j in range(j0, j1 + 1):
                wy = min(sy1, j + 1) - max(sy0, j)
                if wy <= 0:
                    continue
                base = j * sw
                for i in range(i0, i1 + 1):
                    wx = min(sx1, i + 1) - max(sx0, i)
                    if wx <= 0:
                        continue
                    total += src[base + i] * wx * wy
                    wsum += wx * wy
            out[ty * tw + tx] = int(total / wsum + 0.5) if wsum else 0
    return bytes(out)


def _glyph(ch, bold, size):
    """Scaled bitmap for one character: (w, h, alpha bytes, xoff, yoff).

    xoff/yoff place the bitmap relative to the pen position and the
    baseline: xoff is the ink's left edge, yoff its top edge.
    """
    key = (ch, bold, size)
    g = _GLYPH_CACHE.get(key)
    if g is not None:
        return g
    table = GLYPH_BOLD if bold else GLYPH_REG
    code = ord(ch)
    m = table.get(code)
    if m is None:
        m = table[63]
        code = 63
    adv, left, top, right, bottom = m
    scale = size / ATLAS_SIZE
    tw = int(round((right - left) * scale))
    th = int(round((bottom - top) * scale))
    if tw <= 0 or th <= 0:
        g = (0, 0, b"", 0, 0, adv, scale)
        _GLYPH_CACHE[key] = g
        return g
    idx = code - 32
    col = idx % ATLAS_COLS
    row = idx // ATLAS_COLS + (ATLAS_BOLD_ROW if bold else 0)
    sx = col * ATLAS_CELL_W + left
    sy = row * ATLAS_CELL_H + ATLAS_BASELINE + top
    sw = right - left
    sh = bottom - top
    src = bytearray(sw * sh)
    for j in range(sh):
        base = ((sy + j) * ATLAS_W + sx) * 4 + 3
        for i in range(sw):
            src[j * sw + i] = ATLAS[base + i * 4]
    bmp = _resample(bytes(src), sw, sh, tw, th)
    g = (tw, th, bmp, int(round((left - ATLAS_PAD) * scale)),
         int(round(top * scale)), adv, scale)
    _GLYPH_CACHE[key] = g
    return g


def text_width(s, size, bold):
    table = GLYPH_BOLD if bold else GLYPH_REG
    total = 0.0
    for ch in s:
        m = table.get(ord(ch), table[63])
        total += m[0] * size / ATLAS_SIZE
    return total


def draw_text(s, x, y, size, bold, color):
    """Draw text with (x, y) at the ascender top, like Pillow's default."""
    scale = size / ATLAS_SIZE
    baseline = y + int(round(ATLAS_ASCENT * scale))
    cx = float(x)
    for ch in s:
        tw, th, bmp, ox, oy, adv, _ = _glyph(ch, bold, size)
        if tw > 0 and th > 0:
            gx = int(round(cx)) + ox
            gy = baseline + oy
            for dy in range(th):
                yy = gy + dy
                if yy < 0 or yy >= H:
                    continue
                base = dy * tw
                for dx in range(tw):
                    a = bmp[base + dx]
                    if a:
                        _blend(gx + dx, yy, color, a)
        cx += adv * scale
    return cx


def wrap(text, size, bold, max_width):
    """Greedy word wrap returning lines that fit max_width."""
    words = text.split(" ")
    lines = []
    cur = ""
    for word in words:
        trial = word if not cur else cur + " " + word
        if text_width(trial, size, bold) <= max_width:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


# --- icons -----------------------------------------------------------------
def draw_icon(kind, box, color):
    """Geometric icon inside box (x, y, w, h), same shapes as round 1."""
    x, y, w, h = box
    cx, cy = x + w // 2, y + h // 2
    if kind == "scales":
        thick_seg(cx, y + 6, cx, y + h - 8, 4, color)
        thick_seg(x + 8, y + 12, x + w - 8, y + 12, 4, color)
        thick_seg(x + 8, y + 12, x + 4, y + h - 14, 3, color)
        thick_seg(x + w - 8, y + 12, x + w - 4, y + h - 14, 3, color)
        fill_poly([(x + 4, y + h - 14), (x + 16, y + h - 14),
                   (cx - 6, y + h - 2)], color)
        fill_poly([(x + w - 16, y + h - 14), (x + w - 4, y + h - 14),
                   (cx + 6, y + h - 2)], color)
        thick_seg(x + 10, y + h - 2, x + w - 10, y + h - 2, 4, color)
    elif kind == "missile":
        fill_poly([(cx + 14, y + 4), (cx + 22, y + 18), (cx + 2, y + 30),
                   (cx - 6, y + 20)], color)
        fill_poly([(cx + 2, y + 30), (cx - 10, y + 34), (cx - 4, y + 22)],
                  color)
        fill_poly([(cx + 2, y + 30), (cx + 12, y + 40), (cx + 2, y + 42)],
                  color)
        disc(cx - 8, y + h - 8, 6, color)
        disc(cx - 17, y + h - 6, 5, color)
    elif kind == "people":
        for dx, r in ((-18, 11), (0, 13), (18, 11)):
            disc(cx + dx, y + 6 + r, r, color)
            dome(cx + dx, y + 42, 15, 16, color)
    elif kind == "seismic":
        pts = [(x + 2, cy), (x + 14, cy), (x + 20, cy - 16),
               (x + 28, cy + 16), (x + 36, cy - 22), (x + 44, cy + 10),
               (x + 52, cy), (x + w - 2, cy)]
        for a, b in zip(pts, pts[1:]):
            thick_seg(a[0], a[1], b[0], b[1], 4, color)
    elif kind == "chart":
        thick_seg(x + 6, y + 6, x + 6, y + h - 8, 3, color)
        thick_seg(x + 6, y + h - 8, x + w - 4, y + h - 8, 3, color)
        pts = [(x + 10, y + 12), (x + 22, y + 20), (x + 32, y + 16),
               (x + 44, y + 30), (x + w - 8, y + h - 16)]
        for a, b in zip(pts, pts[1:]):
            thick_seg(a[0], a[1], b[0], b[1], 4, color)
        fill_poly([(x + w - 8, y + h - 16), (x + w - 22, y + h - 22),
                   (x + w - 14, y + h - 4)], color)
    elif kind == "megaphone":
        fill_poly([(x + 8, cy - 6), (x + w - 14, y + 6),
                   (x + w - 14, y + h - 10), (x + 8, cy + 8)], color)
        fill_rect(x + 2, cy - 6, 8, 14, color)
        thick_seg(x + w - 6, y + 14, x + w - 2, y + 14, 3, color)
        thick_seg(x + w - 2, y + 14, x + w - 2, y + h - 16, 3, color)
        thick_seg(x + w - 2, y + h - 16, x + w - 6, y + h - 16, 3, color)


# --- page ------------------------------------------------------------------
def build():
    _load_atlas()
    fill_rect(0, 0, W, H, BG)
    mx = 28

    # header
    draw_text("SATURDAY, 21 NOVEMBER 2026", mx, 26, 46, True, WHITE)
    draw_text("THE WORLD IN ONE IMAGE", mx, 84, 24, True, GOLD)
    fill_rect(mx, 128, W - 2 * mx + 1, 5, GOLD)

    # story grid: 2 columns x 3 rows
    gx, gy = mx, 150
    gw, gh = W - 2 * mx, 770
    col_w = (gw - 16) // 2
    row_h = (gh - 2 * 14) // 3
    for i, story in enumerate(STORIES):
        col, row = i % 2, i // 2
        px = gx + col * (col_w + 16)
        py = gy + row * (row_h + 14)
        fill_round(px, py, col_w + 1, row_h + 1, 10, PANEL_LINE)
        fill_round(px + 2, py + 2, col_w - 3, row_h - 3, 8, PANEL)
        draw_icon(story["icon"], (px + 16, py + 16, 56, 56),
                  story["color"])
        draw_text(story["kicker"], px + 86, py + 30, 20, True,
                  story["color"])
        inner = col_w - 32
        head_lines = wrap(story["headline"], 30, True, inner)
        hy = py + 88
        for ln in head_lines[:2]:
            draw_text(ln, px + 16, hy, 30, True, WHITE)
            hy += 36
        sy = hy + 6
        for ln in wrap(story["summary"], 21, False, inner)[:3]:
            draw_text(ln, px + 16, sy, 21, False, MUTED)
            sy += 24

    # ticker
    ty = gy + gh + 16
    fill_rect(mx, ty, W - 2 * mx + 1, 3, PANEL_LINE)
    tyy = ty + 10
    for ln in wrap(TICKER, 17, False, W - 2 * mx)[:2]:
        draw_text(ln, mx, tyy, 17, False, WHITE)
        tyy += 22
    draw_text(FOOTER, mx, H - 26, 15, False, FAINT)

    return bytes(canvas)


def main():
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR")
    if not outdir:
        outdir = "/output" if os.path.isdir("/output") else os.getcwd()
    os.makedirs(outdir, exist_ok=True)
    data = encode_png(build(), W, H)
    path = os.path.join(outdir, "entry.png")
    with open(path, "wb") as f:
        f.write(data)
    print("wrote", path, len(data), "bytes")


if __name__ == "__main__":
    main()
