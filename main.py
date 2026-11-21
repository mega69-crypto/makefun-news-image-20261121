#!/usr/bin/env python3
"""Sum up 21 November 2026 world news in one image.

Draws a 1024x1024 newspaper front page with the six most consequential
stories of Saturday 21 November 2026, plus a ticker of three more.
Everything is drawn with Pillow from the story data below; no network,
no randomness, no clock, so two runs write identical bytes.

Stories verified from reporting on 21 Nov 2026 (ICJ, Reuters, AP,
Al Jazeera, The Daily Short):
  1. ICJ finds Myanmar committed genocide against the Rohingya.
  2. Russian missiles cross into Poland; NATO allies respond.
  3. Trump, Xi and Putin hold a first three-way summit in Shenzhen.
  4. Magnitude 6.8 earthquake strikes central Peru.
  5. Tech sell-off drags markets down as Anthropic shares slide.
  6. Gen Z protests sweep 25 European countries.
Ticker: Houthi missile hits a Riyadh tower; Mamdani sets 2032 to close
Rikers Island; COP31 climate deal stalls.
"""

import os

from PIL import Image, ImageDraw, ImageFont

W, H = 1024, 1024
OUT_DIR = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
OUT_PATH = os.path.join(OUT_DIR, "entry.png")

# --- palette ---------------------------------------------------------------
BG = (13, 27, 42)        # deep navy
PANEL = (22, 39, 61)      # panel navy
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


# --- fonts -----------------------------------------------------------------
def load_font(bold, size):
    names = ("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf",)
    bases = (
        "/usr/share/fonts/truetype/dejavu/",
        "/usr/share/fonts/TTF/",
        "/usr/share/fonts/",
    )
    for base in bases:
        for name in names:
            path = os.path.join(base, name)
            if os.path.exists(path):
                return ImageFont.truetype(path, size)
    return ImageFont.load_default()


# --- helpers ---------------------------------------------------------------
def wrap(draw, text, font, max_width):
    """Greedy word wrap returning a list of lines that fit max_width."""
    words = text.split()
    lines, cur = [], ""
    for word in words:
        trial = word if not cur else cur + " " + word
        if draw.textlength(trial, font=font) <= max_width:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def draw_icon(draw, kind, box, color):
    """Draw a simple geometric icon inside box (x, y, w, h)."""
    x, y, w, h = box
    cx, cy = x + w // 2, y + h // 2
    if kind == "scales":
        draw.line([(cx, y + 6), (cx, y + h - 8)], fill=color, width=4)
        draw.line([(x + 8, y + 12), (x + w - 8, y + 12)], fill=color, width=4)
        draw.line([(x + 8, y + 12), (x + 4, y + h - 14)], fill=color, width=3)
        draw.line([(x + w - 8, y + 12), (x + w - 4, y + h - 14)],
                  fill=color, width=3)
        draw.polygon([(x + 4, y + h - 14), (x + 16, y + h - 14),
                      (cx - 6, y + h - 2)], fill=color)
        draw.polygon([(x + w - 16, y + h - 14), (x + w - 4, y + h - 14),
                      (cx + 6, y + h - 2)], fill=color)
        draw.line([(x + 10, y + h - 2), (x + w - 10, y + h - 2)],
                  fill=color, width=4)
    elif kind == "missile":
        draw.polygon([(cx + 14, y + 4), (cx + 22, y + 18), (cx + 2, y + 30),
                      (cx - 6, y + 20)], fill=color)
        draw.polygon([(cx + 2, y + 30), (cx - 10, y + 34), (cx - 4, y + 22)],
                     fill=color)
        draw.polygon([(cx + 2, y + 30), (cx + 12, y + 40), (cx + 2, y + 42)],
                     fill=color)
        draw.ellipse([cx - 14, y + h - 16, cx - 2, y + h - 4], fill=color)
        draw.ellipse([cx - 22, y + h - 12, cx - 12, y + h - 2], fill=color)
    elif kind == "people":
        for dx, r in ((-18, 11), (0, 13), (18, 11)):
            draw.ellipse([cx + dx - r, y + 6, cx + dx + r, y + 6 + 2 * r],
                         fill=color)
            draw.pieslice([cx + dx - 15, y + 26, cx + dx + 15, y + 58],
                          start=180, end=360, fill=color)
    elif kind == "seismic":
        pts = [(x + 2, cy), (x + 14, cy), (x + 20, cy - 16),
               (x + 28, cy + 16), (x + 36, cy - 22), (x + 44, cy + 10),
               (x + 52, cy), (x + w - 2, cy)]
        draw.line(pts, fill=color, width=4, joint="curve")
    elif kind == "chart":
        draw.line([(x + 6, y + 6), (x + 6, y + h - 8)], fill=color, width=3)
        draw.line([(x + 6, y + h - 8), (x + w - 4, y + h - 8)],
                  fill=color, width=3)
        pts = [(x + 10, y + 12), (x + 22, y + 20), (x + 32, y + 16),
               (x + 44, y + 30), (x + w - 8, y + h - 16)]
        draw.line(pts, fill=color, width=4, joint="curve")
        draw.polygon([(x + w - 8, y + h - 16), (x + w - 18, y + h - 18),
                      (x + w - 12, y + h - 6)], fill=color)
    elif kind == "megaphone":
        draw.polygon([(x + 8, cy - 6), (x + w - 14, y + 6),
                      (x + w - 14, y + h - 10), (x + 8, cy + 8)],
                     fill=color)
        draw.rectangle([x + 2, cy - 6, x + 10, cy + 8], fill=color)
        draw.line([(x + w - 6, y + 14), (x + w - 2, y + 14),
                   (x + w - 2, y + h - 16), (x + w - 6, y + h - 16)],
                  fill=color, width=3)


# --- page ------------------------------------------------------------------
def build():
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)

    f_date = load_font(True, 46)
    f_sub = load_font(True, 24)
    f_kick = load_font(True, 20)
    f_head = load_font(True, 30)
    f_sum = load_font(False, 21)
    f_tick = load_font(False, 17)
    f_foot = load_font(False, 15)

    mx = 28  # margin

    # Header
    draw.text((mx, 26), "SATURDAY, 21 NOVEMBER 2026", font=f_date, fill=WHITE)
    draw.text((mx, 84), "THE WORLD IN ONE IMAGE", font=f_sub, fill=GOLD)
    draw.rectangle([mx, 128, W - mx, 132], fill=GOLD)

    # Story grid: 2 columns x 3 rows
    gx, gy = mx, 150
    gw, gh = W - 2 * mx, 770
    col_w = (gw - 16) // 2
    row_h = (gh - 2 * 14) // 3
    for i, story in enumerate(STORIES):
        col, row = i % 2, i // 2
        px = gx + col * (col_w + 16)
        py = gy + row * (row_h + 14)
        draw.rounded_rectangle([px, py, px + col_w, py + row_h],
                               radius=10, fill=PANEL,
                               outline=PANEL_LINE, width=2)
        # icon + kicker
        draw_icon(draw, story["icon"], (px + 16, py + 16, 56, 56),
                  story["color"])
        draw.text((px + 86, py + 30), story["kicker"], font=f_kick,
                  fill=story["color"])
        # headline
        inner = col_w - 32
        head_lines = wrap(draw, story["headline"], f_head, inner)
        hy = py + 88
        for line in head_lines[:2]:
            draw.text((px + 16, hy), line, font=f_head, fill=WHITE)
            hy += 36
        # summary
        sy = hy + 6
        sum_lines = wrap(draw, story["summary"], f_sum, inner)
        for line in sum_lines[:3]:
            draw.text((px + 16, sy), line, font=f_sum, fill=MUTED)
            sy += 26

    # Ticker
    ty = gy + gh + 16
    draw.rectangle([mx, ty, W - mx, ty + 2], fill=PANEL_LINE)
    tick_lines = wrap(draw, TICKER, f_tick, W - 2 * mx)
    tyy = ty + 10
    for line in tick_lines[:2]:
        draw.text((mx, tyy), line, font=f_tick, fill=WHITE)
        tyy += 22
    draw.text((mx, H - 26), FOOTER, font=f_foot, fill=FAINT)

    return img


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    img = build()
    img.save(OUT_PATH, format="PNG", optimize=True)


if __name__ == "__main__":
    main()
