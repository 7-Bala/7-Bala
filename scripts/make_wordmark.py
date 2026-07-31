#!/usr/bin/env python3
"""Draw ascii.svg — "EXPLORE" with a compass rose standing in for the O.

The rose is two rigid pieces. The housing — rim, inner ring, tick marks —
pops in once and stays fixed, like a real compass's dial. The blades — the
8-point star and its centre pivot — spin in on entrance only: several
turns, decelerating into a stop on a shared ease, then frozen there for
good — a still logo mark once it's landed, not something that keeps
turning. The whole rose plays this entrance centre-stage, then glides over
to its slot as the O; only once it's landed do the other six letters
fade/slide in, left to right, on that same ease-out. Everything uses
fill="freeze" and plays once — nothing loops. Motion is SMIL because
GitHub strips <script> from READMEs.

    python3 scripts/make_wordmark.py

"EXPLORE" is set in Urban Jungle (KC Fonts) — a distressed, urban/graffiti
display face with a city-skyline silhouette cut into the letterforms —
subset to the six letters it needs and inlined as base64. An external font
URL can't work here, since the SVG loads through <img> and browsers refuse
subresource fetches for image documents.

Urban Jungle's stock licence is personal-use only and explicitly excludes
public media (scripts/fonts/UrbanJungle-LICENSE.txt); it's used here only
because the repo owner obtained separate permission from KC Fonts for this
public README. Re-check that permission before reusing this font subset
anywhere else.

The rose itself is plain SVG shapes, no font involved, reading in one
neutral ink colour (the engraved-metal look of alternating solid/hollow
spikes); the letters instead get one continuous amber-to-rust gradient
swept across the whole word — an old-map/brass-compass feel, deliberately
not the blue-to-violet gradient that's become an "AI product" cliché, and
distinct from a per-letter rainbow: one hue drifting into another, not a
row of unrelated colours.
"""
import base64
import math
import os

from fontTools.ttLib import TTFont

HERE = os.path.dirname(os.path.abspath(__file__))
FONT_FILE = os.path.join(HERE, "fonts", "urbanjungle-explore.woff2")
WORD = "EXPLORE"

LIGHT = dict(ink="#2d333b", dim="#8c959f", rule="#c7ced6", face="#ffffff",
             word1="#b45309", word2="#9a3412")
DARK = dict(ink="#f0f6fc", dim="#8b949e", rule="#30363d", face="#0d1117",
            word1="#fbbf24", word2="#f97316")

FONT_SIZE = 84
LETTER_GAP = 13
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
    return (f"@font-face{{font-family:UrbanJungle;font-style:normal;"
            f"font-weight:400;font-display:block;"
            f"src:url(data:font/woff2;base64,{b64}) format('woff2')}}")


def style_defs():
    def block(t):
        return (f".ink{{fill:{t['ink']};stroke:{t['ink']}}}"
                f".dim{{stroke:{t['dim']}}}.rule{{stroke:{t['rule']}}}"
                f".face{{fill:{t['face']}}}"
                f".gs1{{stop-color:{t['word1']}}}.gs2{{stop-color:{t['word2']}}}")
    return (f"<style>{font_face()}{block(LIGHT)}"
            f"@media(prefers-color-scheme:dark){{{block(DARK)}}}</style>")


def word_gradient(x0, x1, y):
    """One continuous gradient swept across the whole word — amber into
    rust, like an old map or a brass compass case, rather than the
    blue-to-violet "AI product" gradient cliché, and distinct from a
    per-letter rainbow: it's one hue drifting into another, not a row of
    unrelated colours."""
    return (f'<linearGradient id="wordGrad" gradientUnits="userSpaceOnUse" '
            f'x1="{x0:.1f}" y1="{y:.1f}" x2="{x1:.1f}" y2="{y:.1f}">'
            f'<stop offset="0%" class="gs1"/><stop offset="100%" class="gs2"/>'
            f'</linearGradient>')


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


def _pop_in(cx, cy, delay, dur, inner_svg):
    """Fade + scale-around-(cx,cy) pop-in, frozen at scale 1. Reused by both
    the fixed housing and the spinning blades below."""
    return (
        f'<g transform="translate({cx:.1f},{cy:.1f})">'
        f'<g opacity="0">'
        f'<set attributeName="opacity" to="1" begin="{delay:.2f}s"/>'
        f'<animateTransform attributeName="transform" type="scale" '
        f'values="0.35;1" begin="{delay:.2f}s" dur="{dur:.2f}s" fill="freeze" '
        f'calcMode="spline" keySplines="{EASE}"/>'
        f'<g transform="translate({-cx:.1f},{-cy:.1f})">{inner_svg}</g>'
        f'</g></g>'
    )


def rose(cx, cy, r):
    """A compass rose split into two rigid pieces: the housing (rim, inner
    ring, tick marks) pops in once and then stays fixed like a real
    compass's dial — and the blades (the 8-point star + centre pivot)
    spin in on entrance and then keep spinning slowly forever, like a
    needle that never quite stops searching."""
    circumference = 2 * math.pi * r
    housing = [
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
    for deg in range(0, 360, 22):
        if deg % 45 == 0:
            continue
        rad = math.radians(deg - 90)
        r1, r2 = r * 0.86, r * 0.97
        x1, y1 = cx + r1 * math.cos(rad), cy + r1 * math.sin(rad)
        x2, y2 = cx + r2 * math.cos(rad), cy + r2 * math.sin(rad)
        housing.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" '
                        f'y2="{y2:.1f}" class="dim" stroke-width="1"/>')

    blades = []
    for deg in (0, 90, 180, 270):
        blades.append(spike(cx, cy, deg, r * 0.92, r * 0.11))
    for deg in (45, 135, 225, 315):
        blades.append(spike(cx, cy, deg, r * 0.56, r * 0.075))
    blades.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r * 0.06:.1f}" '
                  f'class="ink"/>')

    housing_group = _pop_in(cx, cy, 0.05, 0.6, "".join(housing))

    # Blades: one entrance spin only — several turns, decelerating into a
    # stop on the shared ease — then frozen there for good. No idle loop:
    # it spins once, the way it did the first time the page opened, and
    # then it's a still logo mark, not something that keeps turning.
    blade_group = (
        f'<g>'
        f'<animateTransform attributeName="transform" type="rotate" '
        f'values="-760 {cx:.1f} {cy:.1f};0 {cx:.1f} {cy:.1f}" begin="0.05s" '
        f'dur="1.1s" fill="freeze" calcMode="spline" keySplines="{EASE}"/>'
        f'{_pop_in(cx, cy, 0.05, 1.1, "".join(blades))}'
        f'</g>'
    )
    return housing_group + blade_group


def letter(ch, x, base_y, delay):
    safe = ch
    return (
        f'<g opacity="0">'
        f'<set attributeName="opacity" to="1" begin="{delay:.2f}s"/>'
        f'<animateTransform attributeName="transform" type="translate" '
        f'values="0,14;0,0" begin="{delay:.2f}s" dur="0.5s" fill="freeze" '
        f'calcMode="spline" keySplines="{EASE}"/>'
        f'<text x="{x:.1f}" y="{base_y:.1f}" fill="url(#wordGrad)" '
        f'font-family="UrbanJungle" font-size="{FONT_SIZE}">{safe}</text>'
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
    letters_svg, rose_svg, slot_cx, r = [], "", 0.0, 0.0
    non_o_i = 0
    # Letters wait until the compass has both landed centre-stage and
    # glided over to its slot — matches glide_end below.
    glide_hold_end, glide_end = 1.25, 1.85
    letter_start = glide_end
    for i, ch in enumerate(WORD):
        if i == o_index:
            r = widths[i] / 2 * 1.08
            slot_cx = x + widths[i] / 2
        else:
            delay = letter_start + non_o_i * 0.10
            letters_svg.append(letter(ch, x, base_y, delay))
            non_o_i += 1
        x += widths[i] + LETTER_GAP

    # The rose is built at its true final position (slot_cx) so all of its
    # own internal pivot math is correct, then wrapped in a group that
    # holds it shifted to dead centre while it plays its own entrance, and
    # only then glides over to its (0,0) offset — i.e. true position.
    #
    # This can't be a plain begin="1.25s" two-keyframe animation: SMIL only
    # applies an animation's value once it's active, so before begin the
    # attribute would sit at its base (identity) value — meaning the rose
    # would render at its TRUE position the whole time and then jump to
    # the centre offset the instant the animation started, before gliding
    # back. Using one animation with a flat hold segment (two identical
    # keyframes) followed by the real move avoids that jump entirely.
    rose_svg = rose(slot_cx, cap_center_y, r)
    canvas_cx = width / 2
    offset_x = canvas_cx - slot_cx
    hold_frac = glide_hold_end / glide_end
    rose_svg = (
        f'<g>'
        f'<animateTransform attributeName="transform" type="translate" '
        f'values="{offset_x:.1f},0;{offset_x:.1f},0;0,0" '
        f'keyTimes="0;{hold_frac:.4f};1" begin="0s" dur="{glide_end}s" '
        f'fill="freeze" calcMode="spline" keySplines="{EASE};{EASE}"/>'
        f'{rose_svg}</g>'
    )

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" '
        f'height="{height}" viewBox="0 0 {width} {height}">',
        style_defs(),
        word_gradient(PAD, width - PAD, base_y),
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
