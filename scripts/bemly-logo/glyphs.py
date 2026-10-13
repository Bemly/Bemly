"""2D glyph outlines for the BEMLY gizmos.

Every glyph is a list of (op, polygon) applied in order, in "units" (a full
cell is 16 x 16 u, strokes are 4 u, slits 2 u).  op is 'add', 'sub' or 'clip'
(intersect).  Pure Python so both the PIL preview and Blender can import it.
"""
from math import atan2, cos, sin, tan, pi, hypot, acos, radians


def rect(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def round_poly(pts, radii, step=radians(7)):
    """Fillet each vertex of a polygon with the matching radius (0 = sharp)."""
    out = []
    n = len(pts)
    for i, (v, r) in enumerate(zip(pts, radii)):
        if r <= 0:
            out.append(v)
            continue
        p, q = pts[i - 1], pts[(i + 1) % n]
        ax, ay = p[0] - v[0], p[1] - v[1]
        bx, by = q[0] - v[0], q[1] - v[1]
        la, lb = hypot(ax, ay), hypot(bx, by)
        ax, ay, bx, by = ax / la, ay / la, bx / lb, by / lb
        th = acos(max(-1, min(1, ax * bx + ay * by)))
        t = r / tan(th / 2)
        mx, my = ax + bx, ay + by
        lm = hypot(mx, my)
        cx, cy = v[0] + mx / lm * r / sin(th / 2), v[1] + my / lm * r / sin(th / 2)
        a0 = atan2(v[1] + ay * t - cy, v[0] + ax * t - cx)
        a1 = atan2(v[1] + by * t - cy, v[0] + bx * t - cx)
        d = (a1 - a0 + pi) % (2 * pi) - pi
        k = max(2, int(abs(d) / step) + 1)
        out += [(cx + r * cos(a0 + d * j / k), cy + r * sin(a0 + d * j / k)) for j in range(k + 1)]
    return out


def rrect(x0, y0, x1, y1, bl=0, br=0, tr=0, tl=0):
    return round_poly(rect(x0, y0, x1, y1), [bl, br, tr, tl])


def ring_sector(cx, cy, r0, r1, a0, a1, step=7):
    k = max(2, int(abs(a1 - a0) / step) + 1)
    angs = [radians(a0 + (a1 - a0) * j / k) for j in range(k + 1)]
    return ([(cx + r1 * cos(a), cy + r1 * sin(a)) for a in angs] +
            [(cx + r0 * cos(a), cy + r0 * sin(a)) for a in reversed(angs)])


def stroke(pts, w):
    """Polyline -> polygon, butt caps, miter joins."""
    h = w / 2
    left, right = [], []
    n = len(pts)
    for i, (x, y) in enumerate(pts):
        if i == 0:
            dx, dy = pts[1][0] - x, pts[1][1] - y
        elif i == n - 1:
            dx, dy = x - pts[i - 1][0], y - pts[i - 1][1]
        else:
            d0 = (x - pts[i - 1][0], y - pts[i - 1][1])
            d1 = (pts[i + 1][0] - x, pts[i + 1][1] - y)
            l0, l1 = hypot(*d0), hypot(*d1)
            dx, dy = d0[0] / l0 + d1[0] / l1, d0[1] / l0 + d1[1] / l1
        l = hypot(dx, dy)
        nx, ny = -dy / l, dx / l
        s = h
        if 0 < i < n - 1:  # miter length
            d0 = (x - pts[i - 1][0], y - pts[i - 1][1])
            l0 = hypot(*d0)
            s = h / abs(nx * (-d0[1] / l0) + ny * (d0[0] / l0))
        left.append((x + nx * s, y + ny * s))
        right.append((x - nx * s, y - ny * s))
    return left + right[::-1]


# ---------------------------------------------------------------- Latin ----
B = [
    ('add', rrect(0, 0, 16, 16, br=5, tr=5)),
    ('sub', rrect(4, 10, 11.5, 12, br=1, tr=1)),
    ('sub', rrect(4, 4, 11.5, 6, br=1, tr=1)),
    ('sub', rrect(13.2, 7.2, 17, 8.8, bl=0.8, tl=0.8)),
]
E = [
    ('add', rect(0, 0, 16, 16)),
    ('sub', rect(4, 10, 17, 12)),
    ('sub', rect(4, 4, 17, 6)),
    ('sub', rect(13, 5, 17, 11)),
]
M = [
    ('add', rrect(0, 0, 16, 16, tr=4.5)),
    ('sub', rect(4, -1, 6, 12)),
    ('sub', rect(10, -1, 12, 12)),
]
L = [
    ('add', round_poly([(0, 0), (16, 0), (16, 4.5), (4.5, 4.5), (4.5, 16), (0, 16)],
                       [4.5, 0, 0, 0, 0, 0])),
]
Y = [  # 12 wide: shares its width with the small kana
    ('add', rrect(0, 5.5, 12, 16, bl=5.5, br=5.5)),
    ('sub', rrect(4.25, 9.5, 7.75, 17, bl=1.75, br=1.75)),
    ('add', rect(3.9, 0, 8.1, 7)),
]

# ------------------------------------------------------------- Katakana ----
BE = [  # ベ
    ('add', stroke([(-3.2, 0.1), (5.4, 11.7), (17.5, -1.0)], 4.0)),
    ('add', [(9.9, 16), (12.0, 16), (13.5, 12.3), (11.4, 12.3)]),
    ('add', [(13.1, 16), (15.2, 16), (16.7, 12.3), (14.6, 12.3)]),
    ('clip', rect(0, 0, 16, 16)),
]
MU = [  # ム
    ('add', [(5.8, 16), (10.2, 16), (4.4, 1), (0, 1)]),
    ('add', rect(0.4, 1, 13, 5)),
    ('add', [(8.6, 10.2), (12.8, 10.2), (16, 0), (11.8, 0)]),
]
RI = [  # リ
    ('add', rect(1, 7, 5, 16)),
    ('add', rect(11, 7.9, 15, 16)),
    ('add', ring_sector(7, 8, 4, 8, -90, 0)),
    ('add', [(4.6, 0), (7.1, 0), (7.1, 4), (5.6, 4)]),
]
CHOON = [  # ー
    ('add', rect(0, 6, 16, 10)),
]
SMALL_I = [  # ィ in a 12 x 12 box
    ('add', stroke([(14.5, 13.3), (-2.5, 3.4)], 3.5)),
    ('add', rect(5.3, 0, 8.8, 8.6)),
    ('clip', rect(0, 0, 12, 12)),
]

# name, size and outline of every glyph
GLYPHS = {
    'B': (16, 16, B), 'E': (16, 16, E), 'M': (16, 16, M), 'L': (16, 16, L), 'Y': (12, 16, Y),
    'BE': (16, 16, BE), 'MU': (16, 16, MU), 'RI': (16, 16, RI), 'CHOON': (16, 16, CHOON),
    'SMALL_I': (12, 12, SMALL_I),
}

# ----------------------------------------------- third-axis carvings ----
# Cut through each gizmo along its remaining axis so the in-between poses
# read as glyphs too.  Each one was checked on a voxel grid (with a
# 0.75 u safety margin) to leave both real silhouettes untouched.
SLIT2 = [('add', rect(0, 0, 16, 16)), ('sub', rect(4, -1, 6, 11)), ('sub', rect(10, 5, 12, 17))]
DOT2 = [('add', rect(0, 0, 16, 16)), ('sub', rrect(3.5, 3.5, 7, 7, .6, .6, .6, .6)),
        ('sub', rrect(9, 9, 12.5, 12.5, .6, .6, .6, .6))]
HCUT = [('add', rect(0, 0, 16, 16)), ('sub', rect(6, -1, 10, 5.5)), ('sub', rect(6, 10.5, 10, 17))]
SLOT = [('add', rect(0, 0, 16, 12)), ('sub', rrect(3, 4.9, 13, 7.1, .6, .6, .6, .6))]

# (katakana, latin, shared axis, third-axis carving).  'y': the two glyphs
# share their vertical axis (latin is read from the side), 'x': they share
# the horizontal axis (latin is read from above).  The shared axis must have
# ink in the same slices of both glyphs, otherwise one silhouette would eat
# the other.
PAIRS = [('BE', 'B', 'y', SLIT2), ('MU', 'E', 'y', DOT2), ('RI', 'M', 'y', HCUT),
         ('CHOON', 'L', 'x', None), ('SMALL_I', 'Y', 'x', SLOT)]
