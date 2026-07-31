#!/usr/bin/env python3
"""Draw ascii.svg — "EXPLORE" with a compass rose standing in for the O.

The rose resolves first: rim, star and ticks all spin together as one rigid
body — several full turns, decelerating into the stop on a single smooth
ease, no bounce — then freeze completely static, like a logo mark. Only
once it's still do the other six letters fade/slide in, left to right, each
on that same ease-out. Nothing loops: everything uses fill="freeze" and
plays once. Motion is SMIL because GitHub strips <script> from READMEs.

    python3 scripts/make_wordmark.py

"EXPLORE" is set in Fredoka (SIL OFL), subset to the letters it needs and
inlined as base64 — an external font URL can't work here, since the SVG
loads through <img> and browsers refuse subresource fetches for image
documents. The rose itself is plain SVG shapes, no font involved, reading in
one neutral ink colour (the engraved-metal look of alternating solid/hollow
spikes); the letters get their own single accent colour instead of that
neutral ink, so the wordmark doesn't read as flat grey text.
"""
import base64
import math
import os

from fontTools.ttLib import TTFont

HERE = os.path.dirname(os.path.abspath(__file__))
FONT_FILE = os.path.join(HERE, "fonts", "fredoka-explore.woff2")
WORD = "EXPLORE"

LIGHT = dict(ink="#2d333b", dim="#8c959f", rule="#c7ced6", face="#ffffff",
             word="#1f6feb")
DARK = dict(ink="#f0f6fc", dim="#8b949e", rule="#30363d", face="#0d1117",
            word="#58a6ff")

FONT_SIZE = 84
LETTER_GAP = 3
PAD = 30

# A single, consistent "premium" ease — decelerate quickly then settle, no
# overshoot. Every entrance in this file uses it, so the whole reveal reads
# as one motion language rather than a pile of different easings.
EASE = "0.16 1 0.3 1"


def metrics():
    f = TTFont(FONT_FILE)
    upm = f["head"].unitsPerEm
    return upm, f["hmtx"], f.getBestCmap()


def advance(ch, upm, hmtx, cmap):
    return hmtx[cmap[ord(ch)]][0] / upm * FONT_SIZE


def font_face():
    with open(FONT_FILE, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("ascii")
    return (f"@font-face{{font-family:Fredoka;font-style:normal;"
            f"font-weight:600;font-display:block;"
            f"src:url(data:font/woff2;base64,{b64}) format('woff2')}}")


def style_defs():
    def block(t):
        return (f".ink{{fill:{t['ink']};stroke:{t['ink']}}}"
                f".dim{{stroke:{t['dim']}}}.rule{{stroke:{t['rule']}}}"
                f".face{{fill:{t['face']}}}.word{{fill:{t['word']}}}")
    return (f"<style>{font_face()}{block(LIGHT)}"
            f"@media(prefers-color-scheme:dark){{{block(DARK)}}}</style>")


def spike(cx, cy, deg, length, half_w):
    """One point of the rose: two triangles sharing a base, alternating
    solid ink / hollow face so opposite halves read as engraved metal."""
    rad = math.radians(deg - 90)
    perp = math.radians(deg)
    tip = (cx + length * math.cos(rad), cy + length * math.sin(rad))
    a = (cx + half_w * math.cos(perp), cy + half_w * math.sin(perp))
    b = (cx - half_w * math.cos(perp), cy - half_w * math.sin(perp))
    tri1 = f'M{cx:.1f} {cy:.1f}L{tip[0]:.1f} {tip[1]:.1f}L{a[0]:.1f} {a[1]:.1f}Z'
    tri2 = f'M{cx:.1f} {cy:.1f}L{tip[0]:.1f} {tip[1]:.1f}L{b[0]:.1f} {b[1]:.1f}Z'
    return (f'<path d="{tri1}" class="ink"/>'
            f'<path d="{tri2}" class="face rule" stroke-width="1"/>')


def rose(cx, cy, r):
    """A layered compass rose: rim, star, ticks, centre point — one rigid
    body that spins several turns and settles, rather than a fixed rim with
    an independently-spinning star inside it."""
    circumference = 2 * math.pi * r
    parts = [
        f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" fill="none" '
        f'class="rule" stroke-width="2" '
        f'stroke-dasharray="{circumference:.1f}" '
        f'stroke-dashoffset="{circumference:.1f}">'
        f'<animate attributeName="stroke-dashoffset" '
        f'from="{circumference:.1f}" to="0" begin="0.05s" dur="0.6s" '
        f'fill="freeze" calcMode="spline" keySplines="{EASE}"/></circle>',
        '<circle cx="{:.1f}" cy="{:.1f}" r="{:.1f}" fill="none" '
        'class="rule" stroke-width="1"/>'.format(cx, cy, r * 0.74),
    ]
    for deg in (0, 90, 180, 270):
        parts.append(spike(cx, cy, deg, r * 0.92, r * 0.11))
    for deg in (45, 135, 225, 315):
        parts.append(spike(cx, cy, deg, r * 0.56, r * 0.075))
    for deg in range(0, 360, 22):
        if deg % 45 == 0:
            continue
        rad = math.radians(deg - 90)
        r1, r2 = r * 0.86, r * 0.97
        x1, y1 = cx + r1 * math.cos(rad), cy + r1 * math.sin(rad)
        x2, y2 = cx + r2 * math.cos(rad), cy + r2 * math.sin(rad)
        parts.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" '
                      f'y2="{y2:.1f}" class="dim" stroke-width="1"/>')
    parts.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r * 0.06:.1f}" '
                 f'class="ink"/>')

    # Outer group spins the WHOLE rose — rim included — around (cx, cy)
    # using rotate's own pivot form (no static base transform to fight
    # with): several full turns, decelerating into the stop on the same
    # ease used everywhere else, so it reads as one piece finding its
    # direction rather than a rim sitting still while the star spins
    # inside it. Middle/inner nest a translate -> scale -> translate-back
    # so the pop-in scale happens around that same point.
    group = (
        f'<g>'
        f'<animateTransform attributeName="transform" type="rotate" '
        f'values="-760 {cx:.1f} {cy:.1f};0 {cx:.1f} {cy:.1f}" begin="0.05s" '
        f'dur="1.1s" fill="freeze" calcMode="spline" keySplines="{EASE}"/>'
        f'<g transform="translate({cx:.1f},{cy:.1f})">'
        f'<g opacity="0">'
        f'<set attributeName="opacity" to="1" begin="0.05s"/>'
        f'<animateTransform attributeName="transform" type="scale" '
        f'values="0.35;1" begin="0.05s" dur="1.1s" fill="freeze" '
        f'calcMode="spline" keySplines="{EASE}"/>'
        f'<g transform="translate({-cx:.1f},{-cy:.1f})">{"".join(parts)}</g>'
        f'</g></g></g>'
    )
    return group


def letter(ch, x, base_y, delay):
    safe = ch
    return (
        f'<g opacity="0">'
        f'<set attributeName="opacity" to="1" begin="{delay:.2f}s"/>'
        f'<animateTransform attributeName="transform" type="translate" '
        f'values="0,14;0,0" begin="{delay:.2f}s" dur="0.5s" fill="freeze" '
        f'calcMode="spline" keySplines="{EASE}"/>'
        f'<text x="{x:.1f}" y="{base_y:.1f}" class="word" '
        f'font-family="Fredoka" font-size="{FONT_SIZE}">{safe}</text>'
        f'</g>'
    )


def build_svg():
    upm, hmtx, cmap = metrics()
    widths = [advance(c, upm, hmtx, cmap) for c in WORD]
    total_w = sum(widths) + LETTER_GAP * (len(WORD) - 1)

    width = int(total_w + PAD * 2)
    base_y = PAD + FONT_SIZE * 0.78
    height = int(base_y + FONT_SIZE * 0.30 + PAD)
    cap_center_y = base_y - FONT_SIZE * 0.36

    o_index = WORD.index("O")
    x = float(PAD)
    letters_svg, rose_svg = [], ""
    non_o_i = 0
    for i, ch in enumerate(WORD):
        if i == o_index:
            r = widths[i] / 2 * 1.16
            rose_svg = rose(x + widths[i] / 2, cap_center_y, r)
        else:
            delay = 1.30 + non_o_i * 0.10
            letters_svg.append(letter(ch, x, base_y, delay))
            non_o_i += 1
        x += widths[i] + LETTER_GAP

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" '
        f'height="{height}" viewBox="0 0 {width} {height}">',
        style_defs(),
        rose_svg,
        "".join(letters_svg),
        "</svg>",
    ]
    return "".join(parts)


def main():
    with open("ascii.svg", "w", encoding="utf-8") as f:
        f.write(build_svg())
    print("wrote ascii.svg")


if __name__ == "__main__":
    main()
