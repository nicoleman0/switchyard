#!/usr/bin/env python3
"""Draw the Switchyard banner and social preview as pixel art.
Usage: python3 docs/pixelart.py docs
Writes switchyard.svg, workflow.svg, and social-preview.png into the folder.
The banner is animated with CSS, in whole-pixel steps.
"""
import random
import struct
import sys
import zlib
from pathlib import Path

SKY1, SKY2, SKY3 = "#C9E4F2", "#D9EDF6", "#E8F4F9"
CLOUD, CLOUD_SH = "#FFFFFF", "#BDD9E8"
HILL, TREE, TREE_DK = "#BFE0CC", "#86BFA0", "#5E9F80"
GRASS, TUFT, TUFT_DK = "#D7E9C8", "#C2DDB0", "#A9CC98"
RAIL, TIE, DARK = "#3B4756", "#B9966B", "#2B3440"
NAVY, NAVY_LT = "#1F3A5F", "#3B5F8F"
RED, RED_DK = "#D9483B", "#A8352B"
TEAL, TEAL_DK = "#3A8F8A", "#2B6E6A"
YEL, YEL_DK = "#F2B84B", "#C98F2B"
GRN, GRN_DK = "#4CC38A", "#2F9C68"
BRN, BRN_DK = "#C4905A", "#A9743F"
GREY, GLASS, WHITE = "#5B6470", "#CFE8F3", "#FFFFFF"
STONE, STONE_DK = "#C9CFC4", "#A8B0A4"
SKIN = "#F2C9A0"


class Canvas:
    def __init__(self, w, h, fill=GRASS):
        self.w, self.h = w, h
        self.px = [[fill] * w for _ in range(h)]

    def dot(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.px[y][x] = c

    def rect(self, x, y, w, h, c):
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                self.dot(xx, yy, c)

    def sprite(self, x, y, rows, colors):
        for dy, row in enumerate(rows):
            for dx, ch in enumerate(row):
                if ch != ".":
                    self.dot(x + dx, y + dy, colors[ch])

    def paths(self):
        """One path per colour. Unset pixels are skipped, so layers can stack."""
        rects = {}
        open_runs = {}
        for y in range(self.h + 1):
            runs = set()
            if y < self.h:
                x = 0
                while x < self.w:
                    c = self.px[y][x]
                    x0 = x
                    while x < self.w and self.px[y][x] == c:
                        x += 1
                    if c:
                        runs.add((c, x0, x - x0))
            for key in list(open_runs):
                if key not in runs:
                    c, x0, w = key
                    y0 = open_runs.pop(key)
                    rects.setdefault(c, []).append(f"M{x0} {y0}h{w}v{y - y0}h-{w}z")
            # Sorted, so the same drawing always writes the same file.
            for key in sorted(runs):
                open_runs.setdefault(key, y)
        return [f'<path fill="{c}" d="{"".join(rects[c])}"/>' for c in sorted(rects)]

    def png(self, scale):
        raw = bytearray()
        for row in self.px:
            line = bytearray()
            for c in row:
                line += bytes.fromhex(c[1:]) * scale
            for _ in range(scale):
                raw += b"\x00" + line
        def chunk(kind, data):
            body = kind + data
            return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body))
        head = struct.pack(">IIBBBBB", self.w * scale, self.h * scale, 8, 2, 0, 0, 0)
        return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", head) + chunk(b"IDAT", zlib.compress(bytes(raw), 9)) + chunk(b"IEND", b"")


def cloud(cv, x, y, w):
    cv.rect(x + 2, y, w - 5, 1, CLOUD)
    cv.rect(x + 1, y + 1, w - 2, 1, CLOUD)
    cv.rect(x, y + 2, w, 1, CLOUD)
    cv.rect(x + 1, y + 3, w - 2, 1, CLOUD_SH)


def pine(cv, x, base, tall=False, lean=0):
    """A small tree whose trunk stands on row `base`. `lean` shifts its top sideways."""
    top = base - (6 if tall else 4)
    tip = x + lean
    # A tall tree bends its whole upper tier, a short one only its tip.
    mid = tip if tall else x
    cv.dot(tip, top, TREE)
    cv.rect(tip - 1, top + 1, 3, 1, TREE)
    cv.rect(mid - 2, top + 2, 5, 1, TREE)
    if tall:
        cv.rect(x - 1, top + 3, 3, 1, TREE)
        cv.rect(x - 3, top + 4, 7, 1, TREE)
        cv.dot(x + 2, top + 4, TREE_DK)
    cv.dot(mid + 1, top + 2, TREE_DK)
    cv.dot(x, base - 1, BRN_DK)
    cv.dot(x, base, BRN_DK)


def backdrop(cv, horizon, seed, clouds):
    third = horizon // 3
    cv.rect(0, 0, cv.w, third, SKY1)
    cv.rect(0, third, cv.w, third, SKY2)
    cv.rect(0, 2 * third, cv.w, horizon - 2 * third, SKY3)
    for x, y, w in clouds:
        cloud(cv, x, y, w)
    rng = random.Random(seed)
    # Far hills, then a ragged tree line on the horizon.
    height = 2
    for x in range(cv.w):
        if x % 5 == 0:
            height = max(1, min(4, height + rng.choice([-1, 0, 0, 1])))
        cv.rect(x, horizon - height, 1, height, HILL)
    x = rng.randint(0, 4)
    while x < cv.w:
        tall = rng.random() < 0.4
        top = horizon - (4 if tall else 3)
        cv.dot(x, top, TREE)
        cv.rect(x - 1, top + 1, 3, horizon - top - 1, TREE)
        if tall:
            cv.rect(x - 2, horizon - 1, 5, 1, TREE)
        cv.dot(x + 1, horizon - 1, TREE_DK)
        x += rng.choice([3, 4, 4, 6, 9])
    cv.rect(0, horizon, cv.w, cv.h - horizon, GRASS)
    for _ in range(cv.w * (cv.h - horizon) // 26):
        tx, ty = rng.randrange(cv.w - 1), rng.randrange(horizon + 1, cv.h)
        cv.rect(tx, ty, 2, 1, TUFT)
        if rng.random() < 0.35:
            cv.dot(tx + 1, ty - 1, TUFT_DK)


def track_h(cv, x0, x1, y):
    for x in range(x0, x1 + 1):
        if x % 3 == 0:
            cv.dot(x, y - 1, TIE)
            cv.dot(x, y + 1, TIE)
    cv.rect(x0, y, x1 - x0 + 1, 1, RAIL)


def track_d(cv, x0, y0, steps, dx):
    """A 45 degree track from (x0, y0) going up, to the right when dx is 1."""
    for i in range(steps + 1):
        x, y = x0 + dx * i, y0 - i
        if i % 3 == 1:
            cv.dot(x - 1, y, TIE)
            cv.dot(x + 2, y, TIE)
        cv.rect(x, y, 2, 1, RAIL)


def switch(cv, x, y):
    cv.rect(x - 1, y - 1, 3, 3, DARK)
    cv.dot(x, y, YEL)


WAGON = [
    "SSSSSSSSSSSS",
    "BBBBBSSBBBBB",
    "BLBBBSSBBBBB",
    "BLBBBSSBBBBB",
    "BBBBBSSBBBBB",
    "KKKKKKKKKKKK",
    ".KK......KK.",
    ".KK......KK.",
]


def wagon(cv, x, rail, body, shade, light=None):
    cv.sprite(x, rail - 8, WAGON, {"B": body, "S": shade, "L": light or body, "K": DARK})
    cv.dot(x - 1, rail - 3, DARK)
    cv.dot(x + 12, rail - 3, DARK)


ENGINE = [
    ".............KK....",
    "..NNNNNN.....KK....",
    "..RRRRRR..YY.KK....",
    "..RGGGGR.RRRRRRRR..",
    "..RGGGGRRRRRRRRRRR.",
    "..RRRRRRRRRRRRRRRRY",
    "..rrrrrrrrrrrrrrrr.",
    ".KKKKKKKKKKKKKKKKKK",
    "..KKK..KKK..KKK..K.",
    "..KYK..KYK..KYK.K..",
    "..KKK..KKK..KKK....",
]


def engine(cv, x, rail):
    cv.sprite(x, rail - 11, ENGINE, {"K": DARK, "N": NAVY, "R": RED, "r": RED_DK, "G": GLASS, "Y": YEL})
    cv.dot(x, rail - 4, DARK)


# Two frames of the same plume, as (puffs, shade).
SMOKE = [
    ([(0, 0, 2), (-3, -3, 3), (-4, -4, 3), (-8, -6, 4), (-9, -7, 3), (-14, -9, 5), (-13, -10, 3)],
     [(-7, -5, 3), (-13, -8, 4)]),
    ([(-1, -1, 2), (-2, -2, 3), (-6, -4, 3), (-6, -5, 4), (-11, -7, 3), (-12, -8, 5), (-15, -10, 3)],
     [(-5, -3, 3), (-11, -6, 4)]),
]


def smoke(cv, x, y, frame=0):
    puffs, shade = SMOKE[frame]
    for dx, dy, w in puffs:
        cv.rect(x + dx, y + dy, w, 1, WHITE)
    for dx, dy, w in shade:
        cv.rect(x + dx, y + dy, w, 1, CLOUD_SH)


def signal(cv, x, rail, go):
    cv.rect(x, rail - 7, 1, 7, DARK)
    cv.rect(x - 1, rail - 13, 3, 7, NAVY)
    cv.rect(x - 2, rail - 14, 5, 1, DARK)
    cv.dot(x, rail - 12, GREY if go else RED)
    cv.dot(x, rail - 11, GREY if go else RED)
    cv.dot(x, rail - 9, GRN if go else GREY)
    cv.dot(x, rail - 8, GRN if go else GREY)
    cv.rect(x - 1, rail, 3, 1, DARK)


def signal_box(cv, x, base):
    """A two-storey signal box whose footing is on row `base`."""
    cv.rect(x - 1, base - 20, 17, 1, DARK)
    cv.rect(x, base - 19, 15, 2, NAVY)
    cv.rect(x + 1, base - 22, 13, 2, NAVY)
    cv.rect(x + 3, base - 23, 9, 1, NAVY_LT)
    cv.rect(x + 11, base - 26, 2, 4, RED_DK)
    cv.rect(x + 1, base - 17, 13, 7, WHITE)
    for wx in (2, 6, 10):
        cv.rect(x + wx, base - 16, 3, 4, YEL)
        cv.rect(x + wx, base - 14, 3, 1, YEL_DK)
    cv.rect(x, base - 10, 15, 1, DARK)
    cv.rect(x + 1, base - 9, 13, 9, RED)
    for by in range(base - 8, base, 2):
        for bx in range(x + 1 + (by % 4), x + 14, 4):
            cv.dot(bx, by, RED_DK)
    cv.rect(x + 9, base - 6, 3, 6, NAVY)
    cv.dot(x + 11, base - 3, YEL)
    cv.rect(x + 2, base - 7, 4, 3, GLASS)
    cv.rect(x + 2, base - 6, 4, 1, NAVY)
    cv.rect(x, base, 15, 1, STONE_DK)
    # Outside stair to the lever floor.
    for i in range(5):
        cv.rect(x + 15 + i, base - 9 + 2 * i, 2, 1, BRN_DK)
        cv.dot(x + 16 + i, base - 8 + 2 * i, BRN_DK)


def crates(cv, x, base):
    cv.rect(x, base - 3, 4, 4, BRN)
    cv.rect(x, base - 3, 4, 1, BRN_DK)
    cv.rect(x + 5, base - 2, 3, 3, BRN)
    cv.rect(x + 5, base - 2, 3, 1, BRN_DK)
    cv.rect(x + 2, base - 6, 3, 3, BRN)
    cv.rect(x + 2, base - 6, 3, 1, BRN_DK)


def pond(cv, x, y):
    cv.rect(x + 2, y, 8, 1, CLOUD_SH)
    cv.rect(x, y + 1, 12, 2, CLOUD_SH)
    cv.rect(x + 1, y + 3, 9, 1, CLOUD_SH)
    cv.rect(x + 3, y + 1, 4, 1, SKY3)
    cv.dot(x + 11, y, TREE)
    cv.dot(x + 11, y - 1, TREE)
    cv.dot(x - 1, y + 2, TREE)


def water_tower(cv, x, base):
    cv.rect(x + 1, base - 13, 7, 1, NAVY)
    cv.rect(x, base - 12, 9, 1, DARK)
    cv.rect(x, base - 11, 9, 5, BRN)
    for bx in (x + 2, x + 5):
        cv.rect(bx, base - 11, 1, 5, BRN_DK)
    cv.rect(x, base - 9, 9, 1, DARK)
    cv.rect(x, base - 6, 9, 1, DARK)
    for lx in (x + 1, x + 7):
        cv.rect(lx, base - 5, 1, 6, DARK)
    cv.rect(x + 2, base - 3, 5, 1, GREY)
    cv.rect(x + 9, base - 8, 3, 1, GREY)
    cv.dot(x + 11, base - 7, GREY)


BANNER_W, BANNER_H = 200, 65
# Longer than the banner, so the train is off screen before its copy comes in.
TRAIN_LOOP = 260


def banner():
    """The banner as layers: the still yard, then each thing that moves over it."""
    cv = Canvas(BANNER_W, BANNER_H)
    backdrop(cv, 14, 7, [])
    main, sidings = 60, [50, 40, 30]
    track_h(cv, 0, 199, main)
    track_d(cv, 48, main, 30, 1)
    track_d(cv, 163, main, 30, -1)
    for i, y in enumerate(sidings):
        track_h(cv, 60 + 10 * i, 152 - 10 * i, y)
        switch(cv, 59 + 10 * i, y)
        switch(cv, 153 - 10 * i, y)
    switch(cv, 48, main)
    switch(cv, 164, main)

    pond(cv, 10, 42)
    water_tower(cv, 52, 31)
    signal_box(cv, 166, 49)
    crates(cv, 152, 47)

    signal(cv, 121, sidings[2], False)
    signal(cv, 131, sidings[1], False)
    signal(cv, 141, sidings[0], True)

    wagon(cv, 96, sidings[2], RED, RED_DK, "#E8695C")
    wagon(cv, 82, sidings[1], TEAL, TEAL_DK, "#57AAA5")
    wagon(cv, 108, sidings[0], YEL, YEL_DK, "#F7D07F")

    names = ["sky", "cars", "puff1", "puff2", "lamp", "calm0", "calm1", "lean0", "lean1"]
    b = {name: Canvas(BANNER_W, BANNER_H, None) for name in names}
    sky, cars, puff1, puff2, lamp = (b[name] for name in names[:5])
    pines = [(6, 30, True), (14, 26, False), (22, 34, True), (33, 24, False), (41, 38, False),
             (150, 22, False), (158, 27, True), (192, 24, True), (185, 20, False)]
    # Two groups, so neighbours sway out of step. No pine touches anything else in the yard.
    for i, (x, base, tall) in enumerate(pines):
        pine(b[f"calm{i % 2}"], x, base, tall)
        pine(b[f"lean{i % 2}"], x, base, tall, 1)
    for x, y, w in [(8, 2, 16), (52, 5, 11), (96, 1, 20), (141, 4, 13), (176, 2, 15)]:
        cloud(sky, x, y, w)
    wagon(cars, 1, main, GRN, GRN_DK, "#7BD9AA")
    wagon(cars, 14, main, NAVY_LT, NAVY, "#5C80B0")
    wagon(cars, 27, main, BRN, BRN_DK, "#D8AA78")
    engine(cars, 40, main)
    smoke(puff1, 53, 47, 0)
    smoke(puff2, 53, 47, 1)
    # Covers the green lamp of the go signal, to blink it.
    lamp.rect(141, sidings[0] - 9, 1, 2, GREY)
    return {"yard": cv, **b}


def loop(name, cv, period):
    """A layer and a copy one period behind it, so sliding by a period repeats."""
    return [f'<g class="{name}">', f'<g id="{name}">', *cv.paths(), "</g>",
            f'<use href="#{name}" x="-{period}"/>', "</g>"]


def group(name, b):
    return [f'<g class="{name}">', *b[name.split()[0]].paths(), "</g>"]


def banner_svg(scale, title):
    b = banner()
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {BANNER_W} {BANNER_H}" '
        f'width="{BANNER_W * scale}" height="{BANNER_H * scale}" shape-rendering="crispEdges" '
        f'role="img" aria-labelledby="title">',
        f'<title id="title">{title}</title>',
        "<style>",
        # One step per pixel keeps the art on its grid.
        f".sky{{animation:drift 120s steps({BANNER_W}) infinite}}",
        f".train{{animation:roll 20s steps({TRAIN_LOOP}) infinite}}",
        ".puff1{animation:hide 1s step-end infinite}",
        ".puff2{opacity:0;animation:show 1s step-end infinite}",
        ".lamp{opacity:0;animation:show 2s step-end infinite}",
        ".calm0,.calm1{animation:hide 3s step-end infinite}",
        ".lean0,.lean1{opacity:0;animation:show 3s step-end infinite}",
        ".late{animation-delay:-1.2s}",
        f"@keyframes drift{{to{{transform:translate({BANNER_W}px)}}}}",
        f"@keyframes roll{{to{{transform:translate({TRAIN_LOOP}px)}}}}",
        "@keyframes hide{50%{opacity:0}}",
        "@keyframes show{50%{opacity:1}}",
        "@media (prefers-reduced-motion:reduce){*{animation:none!important}}",
        "</style>",
        *b["yard"].paths(),
        *group("calm0", b), *group("lean0", b),
        *group("calm1 late", b), *group("lean1 late", b),
        *loop("sky", b["sky"], BANNER_W),
        *group("lamp", b),
        '<g class="train">',
        *loop("cars", b["cars"], TRAIN_LOOP),
        *loop("puff1", b["puff1"], TRAIN_LOOP),
        *loop("puff2", b["puff2"], TRAIN_LOOP),
        "</g>",
        "</svg>",
    ]
    return "\n".join(out) + "\n"


FONT5 = {
    "S": [".###.", "#...#", "#....", ".###.", "....#", "#...#", ".###."],
    "W": ["#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"],
    "I": ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "#####"],
    "T": ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."],
    "C": [".###.", "#...#", "#....", "#....", "#....", "#...#", ".###."],
    "H": ["#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    "Y": ["#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."],
    "A": [".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    "R": ["####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"],
    "D": ["####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."],
}
FONT3 = {
    "A": [".#.", "#.#", "###", "#.#", "#.#"], "D": ["##.", "#.#", "#.#", "#.#", "##."],
    "E": ["###", "#..", "##.", "#..", "###"], "I": ["###", ".#.", ".#.", ".#.", "###"],
    "L": ["#..", "#..", "#..", "#..", "###"], "N": ["#..#", "##.#", "#.##", "#..#", "#..#"],
    "O": ["###", "#.#", "#.#", "#.#", "###"], "P": ["###", "#.#", "###", "#..", "#.."],
    "Q": ["###", "#.#", "#.#", "###", "..#"], "R": ["##.", "#.#", "##.", "#.#", "#.#"],
    "S": [".##", "#..", ".#.", "..#", "##."], "T": ["###", ".#.", ".#.", ".#.", ".#."],
    "U": ["#.#", "#.#", "#.#", "#.#", "###"], "V": ["#.#", "#.#", "#.#", "#.#", ".#."],
    "W": ["#...#", "#...#", "#.#.#", "##.##", "#...#"], ".": ["...", "...", "...", "...", ".#."],
    "B": ["##.", "#.#", "##.", "#.#", "##."], "C": [".##", "#..", "#..", "#..", ".##"],
    "F": ["###", "#..", "##.", "#..", "#.."], "G": [".##", "#..", "#.#", "#.#", ".##"],
    "M": ["#...#", "##.##", "#.#.#", "#...#", "#...#"], "X": ["#.#", "#.#", ".#.", "#.#", "#.#"],
    "Y": ["#.#", "#.#", ".#.", ".#.", ".#."],
    " ": ["...", "...", "...", "...", "..."],
}


def text(cv, x, y, s, font, size, color, shadow=None):
    for ch in s:
        width = len(font[ch][0])
        for dy, row in enumerate(font[ch]):
            for dx, bit in enumerate(row):
                if bit == "#":
                    if shadow:
                        cv.rect(x + dx * size + 1, y + dy * size + 1, size, size, shadow)
        for dy, row in enumerate(font[ch]):
            for dx, bit in enumerate(row):
                if bit == "#":
                    cv.rect(x + dx * size, y + dy * size, size, size, color)
        x += (width + 1) * size


def lamp_stand(cv, x, rail):
    """A switch stand with a lit lamp, standing beside the points."""
    cv.rect(x - 2, rail - 1, 5, 1, DARK)
    cv.rect(x, rail - 9, 1, 8, DARK)
    cv.rect(x - 1, rail - 6, 3, 1, RED)
    cv.rect(x - 2, rail - 14, 5, 5, DARK)
    cv.rect(x - 1, rail - 13, 3, 3, YEL)
    cv.dot(x, rail - 12, WHITE)
    cv.rect(x - 1, rail - 15, 3, 1, DARK)
    for dx, dy in [(-4, -12), (4, -12), (0, -17), (-3, -15), (3, -15)]:
        cv.dot(x + dx, rail + dy, YEL)


def social():
    cv = Canvas(160, 80)
    backdrop(cv, 39, 11, [(6, 3, 18), (128, 2, 22)])
    text(cv, 21, 9, "SWITCHYARD", FONT5, 2, NAVY, CLOUD_SH)
    text(cv, 23, 28, "ISSUES IN. REVIEWED PRS OUT.", FONT3, 1, NAVY)
    main, branch = 70, 52
    track_h(cv, 0, 159, main)
    track_d(cv, 62, main, 18, 1)
    track_h(cv, 81, 159, branch)
    switch(cv, 62, main)
    lamp_stand(cv, 57, main + 6)

    pine(cv, 8, 50, True); pine(cv, 17, 46); pine(cv, 30, 52, True); pine(cv, 44, 47); pine(cv, 152, 46)
    pond(cv, 96, 61)
    crates(cv, 124, 64)
    pine(cv, 140, 66, True)

    signal(cv, 88, branch, True)
    wagon(cv, 98, branch, RED, RED_DK, "#E8695C")
    wagon(cv, 111, branch, TEAL, TEAL_DK, "#57AAA5")
    wagon(cv, 9, main, YEL, YEL_DK, "#F7D07F")
    wagon(cv, 22, main, NAVY_LT, NAVY, "#5C80B0")
    engine(cv, 35, main)
    smoke(cv, 48, 57)
    return cv


def text_width(s, font):
    return sum(len(font[ch][0]) + 1 for ch in s) - 1


PERSON = [".HH.", ".HH.", "SSSS", "SSSS", ".SS.", ".KK.", "K..K"]


def person(cv, x, y):
    cv.sprite(x, y, PERSON, {"H": SKIN, "S": YEL, "K": DARK})


PAPER = "#F7F9F3"


def track_v(cv, x, y0, y1):
    """A quiet vertical track: one role's line through the whole run."""
    for y in range(y0, y1 + 1):
        if y % 3 == 0:
            cv.dot(x - 1, y, STONE)
            cv.dot(x + 1, y, STONE)
    cv.rect(x, y0, 1, y1 - y0 + 1, STONE_DK)


def handoff(cv, x0, x1, y, label):
    """Work moving from one role's track to another's: a switch where it leaves, an arrow where it lands."""
    step = 1 if x1 > x0 else -1
    end = x1 - 3 * step
    track_h(cv, min(x0, end), max(x0, end), y)
    for i, half in enumerate([2, 1, 0]):
        cv.rect(end + step * i, y - half, 1, 2 * half + 1, DARK)
    switch(cv, x0, y)
    w = text_width(label, FONT3)
    text(cv, (x0 + x1) // 2 - w // 2, y - 8, label, FONT3, 1, NAVY)


def dotted_frame(cv, x0, y0, x1, y1):
    for x in range(x0, x1 + 1, 2):
        cv.dot(x, y0, GREY)
        cv.dot(x, y1, GREY)
    for y in range(y0, y1 + 1, 2):
        cv.dot(x0, y, GREY)
        cv.dot(x1, y, GREY)


def workflow():
    """One issue as a sequence diagram: a track per role, a handoff per message."""
    roles = [("YOU", YEL), ("COORDINATOR", NAVY_LT), ("PLANNER", TEAL), ("IMPLEMENTER", RED), ("REVIEWER", GRN)]
    gap, box = 56, 52
    xs = [30 + gap * i for i in range(len(roles))]
    you, coord, plan, build, check = xs
    steps = [
        (you, coord, "ISSUE"), (coord, you, "QUESTIONS"), (coord, plan, "BRIEF"), (plan, coord, "PLAN"),
        (coord, you, "DECISIONS"), None, (coord, build, "ANSWERS"), (build, coord, "COMMIT"),
        (coord, check, "REVIEW"), (check, coord, "VERDICT"), None, (coord, you, "PULL REQUEST"),
        (you, coord, "APPROVE"),
    ]
    rows, y = [], 30
    for i, s in enumerate(steps):
        if s is None:
            # Room above the loop frame for its tab, and below it for the next label.
            y += 12 if i == 5 else 6
            rows.append(None)
            continue
        rows.append(y)
        y += 13
    merge_y = y + 2
    cv = Canvas(xs[-1] + 30, merge_y + 14, PAPER)
    for x in xs:
        track_v(cv, x, 15, cv.h - 3)

    # The fix round: after a failing verdict, build and review run again.
    loop = [r for r in rows[6:10]]
    fx0, fy0, fx1, fy1 = coord - 6, loop[0] - 18, check + 6, loop[-1] + 4
    dotted_frame(cv, fx0, fy0, fx1, fy1)
    tab = "UNTIL PASS"
    tw = text_width(tab, FONT3) + 4
    cv.rect(fx0, fy0, tw, 8, STONE)
    text(cv, fx0 + 2, fy0 + 2, tab, FONT3, 1, NAVY)

    for s, ry in zip(steps, rows):
        if s:
            handoff(cv, s[0], s[1], ry, s[2])

    for (name, stripe), x in zip(roles, xs):
        bx = x - box // 2
        cv.rect(bx - 1, 2, box + 2, 13, DARK)
        cv.rect(bx, 3, box, 11, WHITE)
        cv.rect(bx, 3, box, 1, stripe)
        w = text_width(name, FONT3)
        if name == "YOU":
            person(cv, x - (w + 6) // 2, 6)
            text(cv, x - (w + 6) // 2 + 6, 7, name, FONT3, 1, NAVY)
        else:
            text(cv, x - w // 2, 7, name, FONT3, 1, NAVY)

    # The coordinator merges, then the line ends at a clear signal.
    label = "MERGE"
    w = text_width(label, FONT3) + 4
    cv.rect(coord - w // 2 - 1, merge_y - 1, w + 2, 9, DARK)
    cv.rect(coord - w // 2, merge_y, w, 7, WHITE)
    cv.rect(coord - w // 2, merge_y, w, 1, GRN)
    text(cv, coord - w // 2 + 2, merge_y + 2, label, FONT3, 1, NAVY)
    return cv


def static_svg(cv, scale, title):
    return "\n".join([
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {cv.w} {cv.h}" '
        f'width="{cv.w * scale}" height="{cv.h * scale}" shape-rendering="crispEdges" '
        f'role="img" aria-labelledby="title">',
        f'<title id="title">{title}</title>',
        *cv.paths(),
        "</svg>",
    ]) + "\n"


if __name__ == "__main__":
    out = Path(sys.argv[1])
    s = social()
    (out / "switchyard.svg").write_text(banner_svg(4, "Pixel art of a rail yard. A steam engine brings wagons in on the main line. Switches sort one wagon onto each of three sidings, each siding ends at a signal, and a signal box watches over the yard."))
    (out / "workflow.svg").write_text(static_svg(workflow(), 3, "A sequence diagram drawn as rail tracks, one vertical track per role: you, coordinator, planner, implementer, and reviewer. You hand the coordinator an issue and answer its questions. The coordinator briefs the planner, gets the plan back, and brings you the decisions. It passes the answers to the implementer, gets a commit, sends it to the reviewer, and gets a verdict, repeating build and review until the verdict is pass. The coordinator opens a pull request, you approve it, and the coordinator merges."))
    (out / "social-preview.png").write_bytes(s.png(8))
