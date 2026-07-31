#!/usr/bin/env python3
"""Draw ascii.svg — a Safari-style compass logo above the word "explore".

For when there's no headshot yet to run through scripts/make_portrait.py.
One accent colour (the needle's north half), not a rainbow: the bezel draws
itself in, the needle spins and settles like it's found a direction, then the
word wipes in the same left-to-right way the rest of the page's text does.
Motion is SMIL — GitHub strips <script> from READMEs — and everything
freezes once landed: no infinite loop to be annoying on a repeat visit.

    python3 scripts/make_wordmark.py

The word is set in Fredoka (SIL OFL), subset to just e/x/p/l/o/r and inlined
as base64 — an external font URL can't work here, because the SVG is loaded
through <img> and browsers refuse subresource fetches for image documents.
Everything else (bezel, ticks, needle) is drawn with plain SVG shapes, no
font needed. Re-subset scripts/fonts/fredoka-explore.woff2 if the word ever
changes to one needing a letter this subset doesn't have.
"""
import base64
import math
import os

from fontTools.ttLib import TTFont

HERE = os.path.dirname(os.path.abspath(__file__))
FONT_FILE = os.path.join(HERE, "fonts", "fredoka-explore.woff2")
WORD = "explore"

# Same design-system tokens as scripts/generate_stats.py, so this graphic
# reads as part of one page rather than a bolted-on logo.
LIGHT = dict(ink="#424a53", dim="#8c959f", rule="#d8dee4",
             surface="#ffffff", north="#f85149")
DARK = dict(ink="#f0f6fc", dim="#8b949e", rule="#30363d",
            surface="#0d1117", north="#ff7b72")

R = 66                  # compass radius
FONT_SIZE = 50
GAP = 22                # between compass and word
PAD = 24

EASE = "0.32 0 0.67 1"


def style():
    def block(t):
        return (f".ink{{fill:{t['ink']}}}.dim{{fill:{t['dim']};"
                f"stroke:{t['dim']}}}.rule{{stroke:{t['rule']}}}"
                f".face{{fill:{t['surface']}}}.north{{fill:{t['north']}}}")
    return (f"<style>{block(LIGHT)}"
            f"@media(prefers-color-scheme:dark){{{block(DARK)}}}</style>")


def bezel(cx, cy):
    circumference = 2 * math.pi * R
    return (
        f'<circle cx="{cx}" cy="{cy}" r="{R}" class="face rule" '
        f'stroke-width="4" '
        f'stroke-dasharray="{circumference:.1f}" '
        f'stroke-dashoffset="{circumference:.1f}">'
        f'<animate attributeName="stroke-dashoffset" '
        f'from="{circumference:.1f}" to="0" begin="0s" dur="0.6s" '
        f'fill="freeze" calcMode="spline" keySplines="0.3 0 0.2 1"/>'
        f'</circle>'
        f'<circle cx="{cx}" cy="{cy}" r="{R - 11}" class="rule" '
        f'fill="none" stroke-width="1" opacity="0">'
        f'<set attributeName="opacity" to="0.7" begin="0.5s"/></circle>'
    )


def ticks(cx, cy):
    out = []
    for i in range(12):
        deg = i * 30
        major = deg % 90 == 0
        rad = math.radians(deg - 90)
        r_out = R - 4
        r_in = r_out - (11 if major else 6)
        x1, y1 = cx + r_out * math.cos(rad), cy + r_out * math.sin(rad)
        x2, y2 = cx + r_in * math.cos(rad), cy + r_in * math.sin(rad)
        out.append(
            f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
            f'class="dim" stroke-width="{2.4 if major else 1.4}" '
            f'stroke-linecap="round" opacity="0">'
            f'<set attributeName="opacity" to="1" begin="0.45s"/></line>'
        )
    return "".join(out)


def needle(cx, cy):
    """A two-tone kite that spins fast, then settles with an overshoot wobble."""
    length, half_w = R - 20, 9
    north = (f'<path d="M{cx:.1f} {cy - length:.1f}L{cx - half_w:.1f} {cy:.1f}'
              f'L{cx + half_w:.1f} {cy:.1f}Z" class="north"/>')
    south = (f'<path d="M{cx:.1f} {cy + length:.1f}L{cx - half_w:.1f} {cy:.1f}'
              f'L{cx + half_w:.1f} {cy:.1f}Z" class="dim"/>')
    pivot = f'<circle cx="{cx}" cy="{cy}" r="4" class="ink"/>'

    keytimes = "0;0.5;0.68;0.82;0.92;1"
    values = ";".join(f"{a} {cx} {cy}" for a in
                       (0, 800, 715, 760, 738, 750))
    splines = ";".join([EASE] * 5)
    spin = (f'<animateTransform attributeName="transform" type="rotate" '
            f'values="{values}" keyTimes="{keytimes}" dur="1.1s" '
            f'begin="0.4s" fill="freeze" calcMode="spline" '
            f'keySplines="{splines}"/>')
    return f'<g opacity="0"><set attributeName="opacity" to="1" begin="0.4s"/>{spin}{north}{south}{pivot}</g>'


def metrics():
    f = TTFont(FONT_FILE)
    upm = f["head"].unitsPerEm
    hmtx = f["hmtx"]
    cmap = f.getBestCmap()
    return upm, hmtx, cmap


def word_row(word, y, start_delay):
    upm, hmtx, cmap = metrics()

    def adv(ch):
        return hmtx[cmap[ord(ch)]][0] / upm * FONT_SIZE

    widths = [adv(c) for c in word]
    total_w = sum(widths)

    parts, x = [], 0.0
    row_dur = 0.5
    for i, ch in enumerate(word):
        delay = start_delay + i * (row_dur / len(word))
        w = widths[i] + 3
        safe = ch
        parts.append(
            f'<clipPath id="wc{i}"><rect x="{x - 2:.1f}" y="{y - FONT_SIZE:.1f}" '
            f'height="{FONT_SIZE * 1.3:.1f}" width="0">'
            f'<animate attributeName="width" from="0" to="{w:.1f}" '
            f'begin="{delay:.2f}s" dur="0.16s" fill="freeze"/>'
            f'</rect></clipPath>'
            f'<g clip-path="url(#wc{i})"><text x="{x:.1f}" y="{y:.1f}" '
            f'class="ink" font-family="Fredoka" font-size="{FONT_SIZE}">'
            f'{safe}</text></g>'
        )
        x += widths[i]
    return "".join(parts), total_w


def font_face():
    with open(FONT_FILE, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("ascii")
    return (f"@font-face{{font-family:Fredoka;font-style:normal;"
            f"font-weight:600;font-display:block;"
            f"src:url(data:font/woff2;base64,{b64}) format('woff2')}}")


def build_svg():
    upm, hmtx, cmap = metrics()
    word_w = sum(hmtx[cmap[ord(c)]][0] / upm * FONT_SIZE for c in WORD)

    width = int(max(2 * R, word_w) + PAD * 2)
    height = int(2 * R + GAP + FONT_SIZE + PAD * 2)
    cx, cy = width / 2, PAD + R

    text_y = PAD + 2 * R + GAP + FONT_SIZE * 0.78
    text_start_x = (width - word_w) / 2

    p = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" '
         f'height="{height}" viewBox="0 0 {width} {height}">',
         f'<style>{font_face()}</style>', style()]
    p.append(bezel(cx, cy))
    p.append(ticks(cx, cy))
    p.append(needle(cx, cy))

    word_svg, _ = word_row(WORD, text_y, start_delay=1.55)
    p.append(f'<g transform="translate({text_start_x:.1f},0)">')
    p.append(word_svg)
    p.append("</g>")

    p.append("</svg>")
    return "".join(p)


def main():
    with open("ascii.svg", "w", encoding="utf-8") as f:
        f.write(build_svg())
    print("wrote ascii.svg")


if __name__ == "__main__":
    main()
