#!/usr/bin/env python3
"""Draw ascii.svg — "EXPLORE" with a compass rose and a pixel-art globe
alternating in place of the O.

The rose is two rigid pieces. The housing — rim, inner ring, tick marks —
pops in once and stays fixed, like a real compass's dial. The blades — the
8-point star and its centre pivot — spin in on entrance only: several
turns, decelerating into a stop on a shared ease, then frozen there for
good — a still logo mark once it's landed, not something that keeps
turning. The whole rose plays this entrance centre-stage, then glides over
to its slot as the O; only once it's landed do the other six letters
fade/slide in, left to right, on that same ease-out.

Once everything has settled, the O keeps a second life: it crossfades
between the compass and a small pixel-art globe (an original procedural
land/ocean pattern, not traced from any reference image) that spins
continuously behind a fixed circular window, forever alternating on a
slow cycle. Everything up to that point uses fill="freeze" and plays
once; only the crossfade cycle and the globe's own spin repeat
indefinitely. Motion is SMIL because GitHub strips <script> from
READMEs.

    python3 scripts/make_wordmark.py

"EXPLORE" is set in Fredoka (SIL OFL), subset to the letters it needs and
inlined as base64 — an external font URL can't work here, since the SVG
loads through <img> and browsers refuse subresource fetches for image
documents. The rose itself is plain SVG shapes, no font involved, reading in
one neutral ink colour (the engraved-metal look of alternating solid/hollow
spikes); the letters instead get one continuous blue-to-violet gradient
swept across the whole word — a single sheen, not a flat colour, and
distinct from a per-letter rainbow, which is one hue drifting into
another rather than a row of unrelated colours.
"""
import base64
import math
import os

from fontTools.ttLib import TTFont

HERE = os.path.dirname(os.path.abspath(__file__))
FONT_FILE = os.path.join(HERE, "fonts", "fredoka-explore.woff2")
WORD = "EXPLORE"

LIGHT = dict(ink="#2d333b", dim="#8c959f", rule="#c7ced6", face="#ffffff",
             word1="#1f6feb", word2="#7c3aed")
DARK = dict(ink="#f0f6fc", dim="#8b949e", rule="#30363d", face="#0d1117",
            word1="#6fb2ff", word2="#c4a1ff")

FONT_SIZE = 84
LETTER_GAP = 13
PAD = 30

# A single, consistent "premium" ease — decelerate quickly then settle, no
# overshoot. Every entrance in this file uses it, so the whole reveal reads
# as one motion language rather than a pile of different easings.
EASE = "0.16 1 0.3 1"

# Once the compass has landed, the O alternates with the globe forever: each
# stays fully visible for CYCLE_SHOW seconds, then crossfades over
# CYCLE_FADE seconds, on repeat.
CYCLE_SHOW = 4.0
CYCLE_FADE = 0.6
CYCLE_DUR = 2 * (CYCLE_SHOW + CYCLE_FADE)


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
                f".face{{fill:{t['face']}}}"
                f".gs1{{stop-color:{t['word1']}}}.gs2{{stop-color:{t['word2']}}}")
    return (f"<style>{font_face()}{block(LIGHT)}"
            f"@media(prefers-color-scheme:dark){{{block(DARK)}}}</style>")


def word_gradient(x0, x1, y):
    """One continuous gradient swept across the whole word — a smooth
    blue-to-violet sheen rather than a flat single colour, and distinct
    from a per-letter rainbow: it's one hue drifting into another, not a
    row of unrelated colours."""
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


GLOBE_OCEAN = "#2d5f9e"
GLOBE_LAND = "#5a9450"
GLOBE_ICE = "#eceef1"
GLOBE_SPIN_DUR = 9  # seconds per full rotation, independent of the crossfade cycle


def globe(cx, cy, r):
    """A small pixel-art Earth: an original procedural land/ocean pattern
    (layered sine waves, not traced from any photo or map) clipped to a
    fixed circular window, spinning continuously behind it."""
    n = 16
    cell = (2 * r) / n
    clip_id = f"globeClip{int(cx)}{int(cy)}"
    tiles = []
    for row in range(n):
        for col in range(n):
            px = -r + (col + 0.5) * cell
            py = -r + (row + 0.5) * cell
            if math.hypot(px, py) > r - cell * 0.3:
                continue
            if abs(py) > r * 0.78:
                color = GLOBE_ICE
            else:
                val = (math.sin(col * 0.85 + row * 0.35)
                       * math.cos(row * 0.65 - col * 0.42)
                       + 0.25 * math.sin(row * 1.6) + 0.15 * math.cos(col * 1.9))
                color = GLOBE_LAND if val > 0.28 else GLOBE_OCEAN
            tiles.append(f'<rect x="{px:.1f}" y="{py:.1f}" width="{cell + 0.5:.1f}" '
                         f'height="{cell + 0.5:.1f}" fill="{color}"/>')

    # Tiles are already drawn centred on local (0,0); the outer group's
    # static translate positions that at (cx,cy), and the inner group's
    # animateTransform is the only thing controlling its own transform
    # attribute — no static base to conflict with, unlike putting a
    # static translate and an animated rotate on the very same element.
    spin = (f'<g transform="translate({cx:.1f},{cy:.1f})">'
            f'<g>'
            f'<animateTransform attributeName="transform" type="rotate" '
            f'values="0;360" begin="0s" dur="{GLOBE_SPIN_DUR}s" '
            f'repeatCount="indefinite"/>'
            f'{"".join(tiles)}</g></g>')
    return (f'<clipPath id="{clip_id}"><circle cx="{cx:.1f}" cy="{cy:.1f}" '
            f'r="{r:.1f}"/></clipPath>'
            f'<g clip-path="url(#{clip_id})">{spin}</g>')


def letter(ch, x, base_y, delay):
    safe = ch
    return (
        f'<g opacity="0">'
        f'<set attributeName="opacity" to="1" begin="{delay:.2f}s"/>'
        f'<animateTransform attributeName="transform" type="translate" '
        f'values="0,14;0,0" begin="{delay:.2f}s" dur="0.5s" fill="freeze" '
        f'calcMode="spline" keySplines="{EASE}"/>'
        f'<text x="{x:.1f}" y="{base_y:.1f}" fill="url(#wordGrad)" '
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

    # Once the compass has landed (glide_end), the O starts an indefinite
    # crossfade cycle with the globe. compass_fade's own base opacity
    # doesn't need setting explicitly — the SVG default (1) already
    # matches what's showing throughout the entrance, and matches this
    # animation's first keyframe, so there's no jump at the handoff.
    # globe_fade DOES need an explicit opacity="0" base: unlike compass,
    # the globe has no prior animation keeping it hidden before glide_end,
    # so without that static attribute it would default to visible (1)
    # and show through the compass's whole entrance — the same class of
    # pre-begin bug fixed twice already elsewhere in this file.
    t1 = CYCLE_SHOW / CYCLE_DUR
    t2 = (CYCLE_SHOW + CYCLE_FADE) / CYCLE_DUR
    t3 = (CYCLE_SHOW + CYCLE_FADE + CYCLE_SHOW) / CYCLE_DUR
    keytimes = f"0;{t1:.4f};{t2:.4f};{t3:.4f};1"
    splines = ";".join([EASE] * 4)
    compass_fade = (
        f'<animate attributeName="opacity" values="1;1;0;0;1" '
        f'keyTimes="{keytimes}" begin="{glide_end}s" dur="{CYCLE_DUR}s" '
        f'repeatCount="indefinite" calcMode="spline" keySplines="{splines}"/>'
    )
    globe_fade = (
        f'<animate attributeName="opacity" values="0;0;1;1;0" '
        f'keyTimes="{keytimes}" begin="{glide_end}s" dur="{CYCLE_DUR}s" '
        f'repeatCount="indefinite" calcMode="spline" keySplines="{splines}"/>'
    )
    rose_svg = f'<g>{compass_fade}{rose_svg}</g>'
    globe_svg = f'<g opacity="0">{globe_fade}{globe(slot_cx, cap_center_y, r)}</g>'

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" '
        f'height="{height}" viewBox="0 0 {width} {height}">',
        style_defs(),
        word_gradient(PAD, width - PAD, base_y),
        rose_svg,
        globe_svg,
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
