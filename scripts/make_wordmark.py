#!/usr/bin/env python3
"""Draw ascii.svg — a laptop opens, then "EXPLORE" plays on its screen.

The lid starts shut (a thin sliver flat against the base) and opens with a
scaleY-from-the-hinge move — the standard flat-SVG trick for faking a lid
tipping toward the viewer, since SVG has no real 3D transform to rotate it
on a horizontal axis. Once it's fully open, everything below plays inside
the screen, unchanged from before: a compass rose standing in for the O.

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
LETTER_GAP = 13
PAD = 30

# A single, consistent "premium" ease — decelerate quickly then settle, no
# overshoot. Every entrance in this file uses it, so the whole reveal reads
# as one motion language rather than a pile of different easings.
EASE = "0.16 1 0.3 1"

# The lid alone uses a plain ease-in-out instead: EASE is heavily front-
# loaded (76% open at just 20% of the duration), which reads as a snap
# rather than a physical hinge lifting. A hinge should move at a more even
# pace throughout.
LID_EASE = "0.45 0 0.2 1"

# Laptop timing: the lid opens first, then — once it's fully open — the
# compass sequence (rose + letters) begins. INTRO_DELAY is added to every
# begin= time in the content below so nothing plays while the screen is
# still tipping open.
LID_OPEN_BEGIN = 0.15   # a short beat with the lid shut, before it opens
LID_OPEN_DUR = 0.75
INTRO_GAP = 0.15
INTRO_DELAY = LID_OPEN_BEGIN + LID_OPEN_DUR + INTRO_GAP

# Laptop geometry. The content (508x150) is much wider and flatter than any
# real screen, so the screen's own proportions are set independently, to a
# real 16:10 laptop ratio, rather than shrink-wrapped to the content — the
# content sits centred inside it. Shrink-wrapping to the content is what
# made the whole laptop read as an odd flat letterbox.
#
# Modelled on the MacBook Air M4 (Sky Blue): a unibody slab, not a flared
# wedge, so the base is only a hair wider than the lid — and the lid itself
# is layered blue-aluminium edge -> black bezel -> screen, with a camera
# notch at the top, the way the real thing is.
SCREEN_RATIO = 16 / 10
INNER_PAD = 12    # between the content's own bounding box and the screen surface
FRAME = 9         # black bezel thickness around the screen surface
LID_EDGE = 5      # thin blue-aluminium edge around the black bezel
FLARE = 5         # how much wider the unibody base is than the lid, each side
TOP_PAD = 16
BOTTOM_PAD = 10

MB_BLUE = "#b7cede"        # chassis — MacBook Air M4 "Sky Blue"
MB_BLUE_EDGE = "#93aec8"   # chassis shading / stroke
MB_BLACK = "#1b1c1e"       # screen bezel + keyboard well
MB_KEY = "#3a3d42"         # individual keycaps
MB_TRACKPAD = "#9fb3c8"    # trackpad's barely-there outline
HINGE_GAP = 3


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
                f".dim{{fill:{t['dim']};stroke:{t['dim']}}}"
                f".rule{{stroke:{t['rule']}}}"
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


def rose(cx, cy, r, t0):
    """A compass rose split into two rigid pieces: the housing (rim, inner
    ring, tick marks) pops in once and stays fixed like a real compass's
    dial — and the blades (the 8-point star + centre pivot) spin in once on
    entrance and then freeze, like a needle that's found its heading and
    stopped. t0 shifts the whole entrance later, e.g. until after a laptop
    lid has finished opening."""
    circumference = 2 * math.pi * r
    housing = [
        f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" fill="none" '
        f'class="rule" stroke-width="2" '
        f'stroke-dasharray="{circumference:.1f}" '
        f'stroke-dashoffset="{circumference:.1f}">'
        f'<animate attributeName="stroke-dashoffset" '
        f'from="{circumference:.1f}" to="0" begin="{t0 + 0.05:.2f}s" dur="0.6s" '
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

    housing_group = _pop_in(cx, cy, t0 + 0.05, 0.6, "".join(housing))

    blade_group = (
        f'<g>'
        f'<animateTransform attributeName="transform" type="rotate" '
        f'values="-760 {cx:.1f} {cy:.1f};0 {cx:.1f} {cy:.1f}" '
        f'begin="{t0 + 0.05:.2f}s" dur="1.1s" fill="freeze" '
        f'calcMode="spline" keySplines="{EASE}"/>'
        f'{_pop_in(cx, cy, t0 + 0.05, 1.1, "".join(blades))}'
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
        f'<text x="{x:.1f}" y="{base_y:.1f}" class="word" '
        f'font-family="Fredoka" font-size="{FONT_SIZE}">{safe}</text>'
        f'</g>'
    )


def _content(t0):
    """The compass + wordmark, exactly as before, with every animation's
    begin= time shifted by t0 (so it can wait for the laptop lid)."""
    upm, hmtx, cmap = metrics()
    widths = [advance(c, upm, hmtx, cmap) for c in WORD]
    total_w = sum(widths) + LETTER_GAP * (len(WORD) - 1)

    width = int(total_w + PAD * 2)
    base_y = PAD + FONT_SIZE * 0.78
    height = int(base_y + FONT_SIZE * 0.30 + PAD)
    cap_center_y = base_y - FONT_SIZE * 0.36

    o_index = WORD.index("O")
    x = float(PAD)
    letters_svg, slot_cx, r = [], 0.0, 0.0
    non_o_i = 0
    glide_hold_end, glide_end = 1.25, 1.85
    letter_start = t0 + glide_end
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
    # This can't be a plain two-keyframe animation starting mid-timeline:
    # SMIL only applies an animation's value once it's active, so before
    # begin the attribute would sit at its base (identity) value — meaning
    # the rose would render at its TRUE position the whole time and then
    # jump to the centre offset the instant the animation started, before
    # gliding back. One animation with a flat hold segment (two identical
    # keyframes) followed by the real move avoids that jump entirely.
    rose_svg = rose(slot_cx, cap_center_y, r, t0)
    canvas_cx = width / 2
    offset_x = canvas_cx - slot_cx
    hold_frac = glide_hold_end / glide_end
    rose_svg = (
        f'<g>'
        f'<animateTransform attributeName="transform" type="translate" '
        f'values="{offset_x:.1f},0;{offset_x:.1f},0;0,0" '
        f'keyTimes="0;{hold_frac:.4f};1" begin="{t0:.2f}s" dur="{glide_end}s" '
        f'fill="freeze" calcMode="spline" keySplines="{EASE};{EASE}"/>'
        f'{rose_svg}</g>'
    )
    return rose_svg + "".join(letters_svg), width, height


def _lid_open(lid_cx, hinge_y, inner_svg):
    """scaleY-from-the-hinge: the flat-SVG trick for a lid tipping open,
    since SVG transforms can't rotate something on a horizontal 3D axis.
    Nested translate -> scale -> translate-back so the scale happens
    around the hinge point rather than the shape's own origin.

    Can't be a plain begin="0.15s" two-keyframe animation: SMIL only
    applies an animation's value once it's active, so before begin the
    lid would sit at its base (identity, i.e. fully OPEN) scale — meaning
    it would render open from the first frame and then snap shut the
    instant the animation started, before opening again. One animation
    with a flat hold segment (two identical closed keyframes) covering
    that initial beat, followed by the real open move, avoids that.
    """
    total = LID_OPEN_BEGIN + LID_OPEN_DUR
    hold_frac = LID_OPEN_BEGIN / total
    return (
        f'<g transform="translate({lid_cx:.1f},{hinge_y:.1f})">'
        f'<g>'
        f'<animateTransform attributeName="transform" type="scale" '
        f'values="1,0.035;1,0.035;1,1" keyTimes="0;{hold_frac:.4f};1" '
        f'begin="0s" dur="{total:.2f}s" fill="freeze" calcMode="spline" '
        f'keySplines="{EASE};{LID_EASE}"/>'
        f'<g transform="translate({-lid_cx:.1f},{-hinge_y:.1f})">'
        f'{inner_svg}</g></g></g>'
    )


def build_svg():
    content_svg, content_w, content_h = _content(INTRO_DELAY)

    # The screen keeps a real 16:10 ratio, sized to fit the content's width;
    # the content sits centred inside it rather than dictating its shape, so
    # there's headroom above/below it the way a wide logo would look small
    # and centred on an actual laptop's screen.
    inner_w = content_w + INNER_PAD * 2
    inner_h = max(content_h + INNER_PAD * 2, inner_w / SCREEN_RATIO)
    screen_w = inner_w + FRAME * 2
    screen_h = inner_h + FRAME * 2

    lid_w = screen_w + LID_EDGE * 2
    lid_h = screen_h + LID_EDGE * 2
    base_h = lid_w * 0.17
    width = int(lid_w + FLARE * 2)
    lid_left = FLARE
    screen_left = lid_left + LID_EDGE
    screen_top = TOP_PAD + LID_EDGE
    hinge_y = TOP_PAD + lid_h
    base_top = hinge_y + HINGE_GAP
    base_bottom = base_top + base_h
    height = int(base_bottom + BOTTOM_PAD)
    lid_cx = lid_left + lid_w / 2

    # Base: a unibody slab only a little wider than the lid (a real MacBook
    # Air's base is barely flared, unlike the old generic-laptop-icon wedge),
    # with a proper keyboard well — a grid of keys plus a wide spacebar —
    # and a big, barely-bordered trackpad, the way the Air actually looks.
    # A plain rounded rect (rather than a hand-rolled trapezoid path) gives
    # the same subtle overhang with no geometry to get wrong; the tiny bit
    # of rounding at the top corners sits under the hinge bar, unseen.
    base_w = width
    base = (
        f'<rect x="0" y="{base_top:.1f}" width="{base_w:.1f}" '
        f'height="{base_h:.1f}" rx="10" fill="{MB_BLUE}" '
        f'stroke="{MB_BLUE_EDGE}" stroke-width="1"/>'
        f'<rect x="{lid_cx - 16:.1f}" y="{hinge_y:.1f}" width="32" '
        f'height="{HINGE_GAP + 1}" rx="1.5" fill="{MB_BLUE_EDGE}"/>'
    )

    deck_pad = base_w * 0.045
    well_x, well_y = deck_pad, base_top + base_h * 0.12
    well_w, well_h = base_w - deck_pad * 2, base_h * 0.6
    base += (
        f'<rect x="{well_x:.1f}" y="{well_y:.1f}" width="{well_w:.1f}" '
        f'height="{well_h:.1f}" rx="{base_h * 0.09:.1f}" fill="{MB_BLACK}"/>'
    )

    # Key grid: three normal rows plus a bottom row with a wide spacebar.
    gap = base_h * 0.045
    rows, cols = 3, 13
    row_h = (well_h * 0.78 - gap * (rows + 1)) / rows
    row_w = well_w - gap * 2
    key_w = (row_w - gap * (cols - 1)) / cols
    for r in range(rows):
        ky = well_y + gap + r * (row_h + gap)
        for c in range(cols):
            kx = well_x + gap + c * (key_w + gap)
            base += (f'<rect x="{kx:.1f}" y="{ky:.1f}" width="{key_w:.1f}" '
                      f'height="{row_h:.1f}" rx="{row_h * 0.22:.1f}" '
                      f'fill="{MB_KEY}"/>')
    bar_y = well_y + gap + rows * (row_h + gap)
    bar_h = well_h * 0.78 - rows * (row_h + gap)
    space_w = well_w * 0.42
    for x0, w0 in ((gap, well_w * 0.16), (well_w - gap - well_w * 0.16, well_w * 0.16)):
        base += (f'<rect x="{well_x + x0:.1f}" y="{bar_y:.1f}" width="{w0:.1f}" '
                  f'height="{bar_h:.1f}" rx="{bar_h * 0.25:.1f}" fill="{MB_KEY}"/>')
    base += (f'<rect x="{well_x + well_w / 2 - space_w / 2:.1f}" y="{bar_y:.1f}" '
              f'width="{space_w:.1f}" height="{bar_h:.1f}" rx="{bar_h * 0.25:.1f}" '
              f'fill="{MB_KEY}"/>')

    pad_w, pad_h = base_h * 1.7, base_h * 0.7
    pad_x = lid_cx - pad_w / 2
    pad_y = well_y + well_h + (base_bottom - (well_y + well_h) - pad_h) / 2
    base += (
        f'<rect x="{pad_x:.1f}" y="{pad_y:.1f}" width="{pad_w:.1f}" '
        f'height="{pad_h:.1f}" rx="{pad_h * 0.22:.1f}" fill="none" '
        f'stroke="{MB_TRACKPAD}" stroke-width="1"/>'
    )

    # Lid: a thin blue-aluminium edge, then a black bezel, then the screen
    # surface, with a small camera notch dipping into the top of the screen.
    lid_edge = (
        f'<rect x="{lid_left:.1f}" y="{TOP_PAD:.1f}" width="{lid_w:.1f}" '
        f'height="{lid_h:.1f}" rx="12" fill="{MB_BLUE}" '
        f'stroke="{MB_BLUE_EDGE}" stroke-width="1"/>'
    )
    bezel = (
        f'<rect x="{screen_left:.1f}" y="{screen_top:.1f}" '
        f'width="{screen_w:.1f}" height="{screen_h:.1f}" rx="8" '
        f'fill="{MB_BLACK}"/>'
    )
    inner_x, inner_y = screen_left + FRAME, screen_top + FRAME
    surface = (
        f'<rect x="{inner_x:.1f}" y="{inner_y:.1f}" width="{inner_w:.1f}" '
        f'height="{inner_h:.1f}" rx="4" class="face"/>'
    )
    notch_w, notch_h = inner_w * 0.1, 7
    notch = (f'<rect x="{lid_cx - notch_w / 2:.1f}" y="{inner_y - 1:.1f}" '
              f'width="{notch_w:.1f}" height="{notch_h:.1f}" rx="3.5" '
              f'fill="{MB_BLACK}"/>')
    clip = (f'<clipPath id="screen"><rect x="{inner_x:.1f}" y="{inner_y:.1f}" '
            f'width="{inner_w:.1f}" height="{inner_h:.1f}" rx="4"/></clipPath>')
    content_x = inner_x + (inner_w - content_w) / 2
    content_y = inner_y + (inner_h - content_h) / 2
    screen_content = (
        f'<g clip-path="url(#screen)">'
        f'<g transform="translate({content_x:.1f},{content_y:.1f})">'
        f'{content_svg}</g></g>'
    )

    lid = _lid_open(lid_cx, hinge_y,
                     lid_edge + bezel + surface + clip + screen_content + notch)

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" '
        f'height="{height}" viewBox="0 0 {width} {height}">',
        style_defs(),
        base,
        lid,
        "</svg>",
    ]
    return "".join(parts)


def main():
    with open("ascii.svg", "w", encoding="utf-8") as f:
        f.write(build_svg())
    print("wrote ascii.svg")


if __name__ == "__main__":
    main()
