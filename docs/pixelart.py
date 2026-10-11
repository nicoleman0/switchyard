#!/usr/bin/env python3
"""Draw the Switchyard banner and social preview as pixel art.
Usage: python3 docs/pixelart.py docs
Writes switchyard.svg and social-preview.png into the folder.
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


class Canvas:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.px = [[GRASS] * w for _ in range(h)]

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

    def svg(self, scale, title):
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
                    runs.add((c, x0, x - x0))
            for key in list(open_runs):
                if key not in runs:
                    c, x0, w = key
                    y0 = open_runs.pop(key)
                    rects.setdefault(c, []).append(f"M{x0} {y0}h{w}v{y - y0}h-{w}z")
            # Sorted, so the same drawing always writes the same file.
            for key in sorted(runs):
                open_runs.setdefault(key, y)
        out = [
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}" '
            f'width="{self.w * scale}" height="{self.h * scale}" shape-rendering="crispEdges" '
            f'role="img" aria-labelledby="title">',
            f'  <title id="title">{title}</title>',
        ]
        for c in sorted(rects):
            out.append(f'  <path fill="{c}" d="{"".join(rects[c])}"/>')
        out.append("</svg>")
        return "\n".join(out) + "\n"

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


def pine(cv, x, base, tall=False):
    """A small tree whose trunk stands on row `base`."""
    top = base - (6 if tall else 4)
    cv.dot(x, top, TREE)
    cv.rect(x - 1, top + 1, 3, 1, TREE)
    cv.rect(x - 2, top + 2, 5, 1, TREE)
    if tall:
        cv.rect(x - 1, top + 3, 3, 1, TREE)
        cv.rect(x - 3, top + 4, 7, 1, TREE)
        cv.dot(x + 2, top + 4, TREE_DK)
    cv.dot(x + 1, top + 2, TREE_DK)
    cv.dot(x, base - 1 if not tall else base - 1, BRN_DK)
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


def smoke(cv, x, y):
    for dx, dy, w in [(0, 0, 2), (-3, -3, 3), (-4, -4, 3), (-8, -6, 4), (-9, -7, 3), (-14, -9, 5), (-13, -10, 3)]:
        cv.rect(x + dx, y + dy, w, 1, WHITE)
    cv.rect(x - 7, y - 5, 3, 1, CLOUD_SH)
    cv.rect(x - 13, y - 8, 4, 1, CLOUD_SH)


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


def banner():
    cv = Canvas(200, 65)
    backdrop(cv, 14, 7, [(8, 2, 16), (52, 5, 11), (96, 1, 20), (141, 4, 13), (176, 2, 15)])
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

    pine(cv, 6, 30, True); pine(cv, 14, 26); pine(cv, 22, 34, True); pine(cv, 33, 24); pine(cv, 41, 38)
    pond(cv, 10, 42)
    water_tower(cv, 52, 31)
    pine(cv, 150, 22); pine(cv, 158, 27, True); pine(cv, 192, 24, True); pine(cv, 185, 20)
    signal_box(cv, 166, 49)
    crates(cv, 152, 47)

    signal(cv, 121, sidings[2], False)
    signal(cv, 131, sidings[1], False)
    signal(cv, 141, sidings[0], True)

    wagon(cv, 96, sidings[2], RED, RED_DK, "#E8695C")
    wagon(cv, 82, sidings[1], TEAL, TEAL_DK, "#57AAA5")
    wagon(cv, 108, sidings[0], YEL, YEL_DK, "#F7D07F")

    wagon(cv, 1, main, NAVY_LT, NAVY, "#5C80B0")
    wagon(cv, 14, main, BRN, BRN_DK, "#D8AA78")
    engine(cv, 27, main)
    smoke(cv, 40, 47)
    wagon(cv, 184, main, GRN, GRN_DK, "#7BD9AA")
    return cv


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


if __name__ == "__main__":
    out = Path(sys.argv[1])
    b, s = banner(), social()
    (out / "switchyard.svg").write_text(b.svg(4, "Pixel art of a rail yard. A steam engine brings wagons in on the main line. Switches sort one wagon onto each of three sidings, each siding ends at a signal, and a signal box watches a wagon leave."))
    (out / "social-preview.png").write_bytes(s.png(8))
