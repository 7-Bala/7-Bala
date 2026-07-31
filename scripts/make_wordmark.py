#!/usr/bin/env python3
"""Draw ascii.svg — an animated compass badge, the whole profile page.

A stamp-style emblem: the badge stamps itself into place with an elastic
overshoot and a fading impact ring, the rim ticks pop in, "EXPLORE" bounces
in one letter at a time along the top arc, and the needle spins fast before
settling — like it just found a direction. After that a small idle loop
(a slow needle sway, two twinkling stars) keeps it alive without looping the
whole entrance: everything else uses fill="freeze" and plays once, since
GitHub strips <script> from READMEs and SMIL is the only motion available.

    python3 scripts/make_wordmark.py

"EXPLORE" is set in Fredoka (SIL OFL), subset to the upper- and lowercase
letters it needs and inlined as base64 — an external font URL can't work
here, since the SVG loads through <img> and browsers refuse subresource
fetches for image documents. Everything else (bezel, ticks, needle, stars) is
plain SVG shapes, no font involved.
"""
import base64
import math
import os

from fontTools.ttLib import TTFont

HERE = os.path.dirname(os.path.abspath(__file__))
FONT_FILE = os.path.join(HERE, "fonts", "fredoka-explore.woff2")
WORD = "EXPLORE"

LIGHT = dict(ink="#2d333b", dim="#8c959f", rule="#c7ced6", face="#ffffff",
             north="#f24b42", star="#ffcc4d",
             g1="#c7d0da", g2="#eef2f6", g3="#9aa7b3")
DARK = dict(ink="#f0f6fc", dim="#8b949e", rule="#30363d", face="#0d1117",
            north="#ff6b62", star="#ffd76a",
            g1="#30363d", g2="#4b535c", g3="#21262c")

R_OUTER, R_BEZEL, R_FACE, R_TEXT = 100, 92, 82, 63
FONT_SIZE = 24
NEEDLE_LEN, NEEDLE_HALF_W = 44, 9
PAD = 24
EASE = "0.32 0 0.67 1"
BOUNCE_TIMES = "0;0.5;0.68;0.82;0.92;1"


def metrics():
    f = TTFont(FONT_FILE)
    upm = f["head"].unitsPerEm
    return upm, f["hmtx"], f.getBestCmap()


def advance(ch, size, upm, hmtx, cmap):
    return hmtx[cmap[ord(ch)]][0] / upm * size


def font_face():
    with open(FONT_FILE, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("ascii")
    return (f"@font-face{{font-family:Fredoka;font-style:normal;"
            f"font-weight:600;font-display:block;"
            f"src:url(data:font/woff2;base64,{b64}) format('woff2')}}")


def style_defs():
    def block(t):
        return (f".ink{{fill:{t['ink']}}}.dim{{fill:{t['dim']};"
                f"stroke:{t['dim']}}}.rule{{stroke:{t['rule']}}}"
                f".face{{fill:{t['face']}}}.north{{fill:{t['north']}}}"
                f".star{{fill:{t['star']}}}"
                f".s1{{stop-color:{t['g1']}}}.s2{{stop-color:{t['g2']}}}"
                f".s3{{stop-color:{t['g3']}}}")
    return (f"<style>{font_face()}{block(LIGHT)}"
            f"@media(prefers-color-scheme:dark){{{block(DARK)}}}</style>")


def gradient(cx, cy):
    return (f'<radialGradient id="bezelGrad" cx="{cx}" cy="{cy}" r="{R_BEZEL}" '
            f'gradientUnits="userSpaceOnUse">'
            f'<stop offset="0%" class="s2"/>'
            f'<stop offset="55%" class="s1"/>'
            f'<stop offset="100%" class="s3"/>'
            f'</radialGradient>')


def shadow(cx, cy):
    return (f'<ellipse cx="{cx}" cy="{cy + R_OUTER + 6}" rx="{R_OUTER * 0.7:.0f}" '
            f'ry="10" fill="#000" opacity="0">'
            f'<animate attributeName="opacity" from="0" to="0.16" '
            f'begin="0.05s" dur="0.5s" fill="freeze"/></ellipse>')


def badge_stamp(cx, cy, inner_svg):
    """Wrap the badge body in one elastic stamp-in: scale + slight rotate."""
    scale_vals = "0.15;1.14;0.93;1.04;0.98;1"
    rot_vals = "-24;6;-3;1.5;-0.5;0"
    splines = ";".join([EASE] * 5)
    return (
        f'<g transform="translate({cx},{cy})">'
        f'<g>'
        f'<animateTransform attributeName="transform" type="rotate" '
        f'values="{rot_vals}" keyTimes="{BOUNCE_TIMES}" dur="0.7s" '
        f'begin="0s" fill="freeze" calcMode="spline" keySplines="{splines}"/>'
        f'<g>'
        f'<animateTransform attributeName="transform" type="scale" '
        f'values="{scale_vals}" keyTimes="{BOUNCE_TIMES}" dur="0.7s" '
        f'begin="0s" fill="freeze" calcMode="spline" keySplines="{splines}"/>'
        f'<g transform="translate({-cx},{-cy})">{inner_svg}</g>'
        f'</g></g></g>'
    )


def impact_ring(cx, cy):
    return (
        f'<circle cx="{cx}" cy="{cy}" r="{R_FACE * 0.4:.0f}" fill="none" '
        f'class="rule" stroke-width="2.5" opacity="0">'
        f'<set attributeName="opacity" to="0.5" begin="0.55s"/>'
        f'<animate attributeName="r" from="{R_FACE * 0.4:.0f}" '
        f'to="{R_OUTER * 1.55:.0f}" begin="0.55s" dur="0.55s" fill="freeze" '
        f'calcMode="spline" keySplines="0.2 0 0.4 1"/>'
        f'<animate attributeName="opacity" from="0.5" to="0" begin="0.55s" '
        f'dur="0.55s" fill="freeze"/>'
        f'</circle>'
    )


def stamp_ring(cx, cy):
    return (f'<circle cx="{cx}" cy="{cy}" r="{R_OUTER}" fill="none" '
            f'class="rule" stroke-width="2.5" stroke-dasharray="1.5 6.5" '
            f'stroke-linecap="round"/>')


def ticks(cx, cy):
    out = []
    for i in range(12):
        deg = i * 30
        major = deg % 90 == 0
        rad = math.radians(deg - 90)
        r_out = R_FACE - 4
        r_in = r_out - (13 if major else 7)
        x1, y1 = cx + r_out * math.cos(rad), cy + r_out * math.sin(rad)
        x2, y2 = cx + r_in * math.cos(rad), cy + r_in * math.sin(rad)
        delay = 0.32 + i * 0.025
        out.append(
            f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
            f'class="dim" stroke-width="{2.6 if major else 1.5}" '
            f'stroke-linecap="round" opacity="0">'
            f'<set attributeName="opacity" to="1" begin="{delay:.2f}s"/>'
            f'</line>'
        )
    return "".join(out)


def arced_word(cx, cy):
    """EXPLORE, one letter per group, following the top of the rim."""
    upm, hmtx, cmap = metrics()
    widths = [advance(c, FONT_SIZE, upm, hmtx, cmap) for c in WORD]
    gap = 3.2
    total = sum(widths) + gap * (len(WORD) - 1)
    span = total / R_TEXT                      # radians
    start = -math.pi / 2 - span / 2
    out, run = [], 0.0
    for i, ch in enumerate(WORD):
        theta = start + (run + widths[i] / 2) / R_TEXT
        run += widths[i] + gap
        x = cx + R_TEXT * math.cos(theta)
        y = cy + R_TEXT * math.sin(theta)
        rot = math.degrees(theta) + 90
        delay = 0.78 + i * 0.055
        scale_vals = "0.1;1.3;0.85;1.08;0.96;1"
        splines = ";".join([EASE] * 5)
        out.append(
            f'<g transform="translate({x:.1f},{y:.1f}) rotate({rot:.1f})">'
            f'<g opacity="0">'
            f'<set attributeName="opacity" to="1" begin="{delay:.2f}s"/>'
            f'<animateTransform attributeName="transform" type="scale" '
            f'values="{scale_vals}" keyTimes="{BOUNCE_TIMES}" dur="0.42s" '
            f'begin="{delay:.2f}s" fill="freeze" calcMode="spline" '
            f'keySplines="{splines}"/>'
            f'<text x="0" y="0" text-anchor="middle" class="ink" '
            f'font-family="Fredoka" font-size="{FONT_SIZE}">{ch}</text>'
            f'</g></g>'
        )
    return "".join(out)


def needle(cx, cy):
    north = (f'<path d="M{cx:.1f} {cy - NEEDLE_LEN:.1f}'
             f'L{cx - NEEDLE_HALF_W:.1f} {cy:.1f}'
             f'L{cx + NEEDLE_HALF_W:.1f} {cy:.1f}Z" class="north"/>')
    south = (f'<path d="M{cx:.1f} {cy + NEEDLE_LEN:.1f}'
             f'L{cx - NEEDLE_HALF_W:.1f} {cy:.1f}'
             f'L{cx + NEEDLE_HALF_W:.1f} {cy:.1f}Z" class="dim"/>')
    sheen = (f'<path d="M{cx - 2:.1f} {cy - NEEDLE_LEN + 6:.1f}'
             f'L{cx:.1f} {cy - 4:.1f}" stroke="#fff" stroke-opacity="0.45" '
             f'stroke-width="1.6" stroke-linecap="round"/>')
    pivot = f'<circle cx="{cx}" cy="{cy}" r="4.2" class="ink"/>'

    spin_values = ";".join(f"{a} {cx} {cy}" for a in
                            (0, 800, 715, 760, 738, 750))
    splines = ";".join([EASE] * 5)
    settle_deg = 750 % 360
    sway_values = (f"{settle_deg} {cx} {cy};{settle_deg - 4} {cx} {cy};"
                   f"{settle_deg + 4} {cx} {cy};{settle_deg} {cx} {cy}")

    spin = (f'<animateTransform attributeName="transform" type="rotate" '
            f'values="{spin_values}" keyTimes="{BOUNCE_TIMES}" dur="1.1s" '
            f'begin="1.05s" fill="freeze" calcMode="spline" '
            f'keySplines="{splines}"/>')
    sway = (f'<animateTransform attributeName="transform" type="rotate" '
            f'values="{sway_values}" dur="4.5s" begin="2.15s" '
            f'repeatCount="indefinite" calcMode="spline" '
            f'keySplines="0.45 0 0.55 1;0.45 0 0.55 1;0.45 0 0.55 1"/>')
    return (f'<g opacity="0"><set attributeName="opacity" to="1" '
            f'begin="1.05s"/>{spin}{sway}{north}{south}{sheen}{pivot}</g>')


def star(cx, cy, size, delay, period):
    d = (f'M{cx:.1f} {cy - size:.1f}L{cx + size * 0.28:.1f} {cy - size * 0.28:.1f}'
         f'L{cx + size:.1f} {cy:.1f}L{cx + size * 0.28:.1f} {cy + size * 0.28:.1f}'
         f'L{cx:.1f} {cy + size:.1f}L{cx - size * 0.28:.1f} {cy + size * 0.28:.1f}'
         f'L{cx - size:.1f} {cy:.1f}L{cx - size * 0.28:.1f} {cy - size * 0.28:.1f}Z')
    return (f'<path d="{d}" class="star" opacity="0">'
            f'<set attributeName="opacity" to="0.9" begin="{delay:.2f}s"/>'
            f'<animate attributeName="opacity" values="0.9;0.35;0.9" '
            f'dur="{period}s" begin="{delay + 0.3:.2f}s" '
            f'repeatCount="indefinite" calcMode="spline" '
            f'keySplines="0.45 0 0.55 1;0.45 0 0.55 1"/></path>')


def build_svg():
    width = height = R_OUTER * 2 + PAD * 2
    cx = cy = width / 2

    body = [
        f'<defs>{gradient(cx, cy)}</defs>',
        stamp_ring(cx, cy),
        f'<circle cx="{cx}" cy="{cy}" r="{R_BEZEL}" fill="url(#bezelGrad)" '
        f'class="rule" stroke-width="2"/>',
        f'<circle cx="{cx}" cy="{cy}" r="{R_FACE}" class="face rule" '
        f'stroke-width="1.5"/>',
        ticks(cx, cy),
        arced_word(cx, cy),
        star(cx - 46, cy + 40, 5, 1.5, 2.6),
        star(cx + 50, cy + 34, 4, 1.9, 3.1),
    ]

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" '
        f'height="{height}" viewBox="0 0 {width} {height}">',
        style_defs(),
        shadow(cx, cy),
        impact_ring(cx, cy),
        badge_stamp(cx, cy, "".join(body)),
        needle(cx, cy),
        "</svg>",
    ]
    return "".join(parts)


def main():
    with open("ascii.svg", "w", encoding="utf-8") as f:
        f.write(build_svg())
    print("wrote ascii.svg")


if __name__ == "__main__":
    main()
