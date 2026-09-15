#!/usr/bin/env python3
"""One inline STL block <= ~465KB: signature + curated main/master text.
GuanZhi 8x8 font, outer surface only, greedy coplanar meshing, minified ASCII
(no indentation, CELL=1 so coords stay short). Lines are dropped from the
bottom of the priority list until the whole README fits the render limit."""
import json
import math
import os

DIR = os.path.dirname(os.path.abspath(__file__))

CELL = 1.0
DEPTH = 1.0
LIMIT = 465_000          # bytes for the ```stl block (README total stays under ~500KB)
GL = json.load(open(os.path.join(DIR, 'gz8_glyphs.json')))


def cw(ch):
    return 4 if ch == ' ' else GL[ch]['cols']


def text_width(s, scale=1):
    return sum(cw(c) for c in s) * scale


def wrap(s, maxcols):
    rows, row, w = [], '', 0
    for ch in s:
        c = cw(ch)
        if w + c > maxcols and row:
            rows.append(row.rstrip())
            row, w = '', 0
        row += ch
        w += c
    if row.strip():
        rows.append(row.rstrip())
    return rows


def place(cells, row0, s, maxcols, scale=1):
    w = text_width(s, scale)
    cx = (maxcols - w) // 2
    for ch in s:
        if ch != ' ':
            g = GL[ch]
            for gy in range(8):
                for gx, v in enumerate(g['rows'][gy]):
                    if v == '1':
                        for dx in range(scale):
                            for dy in range(scale):
                                cells.add((cx + gx * scale + dx, row0 + gy * scale + dy))
        cx += cw(ch) * scale
    return 8 * scale


def runs(values):
    out = []
    for p in sorted(values):
        if out and p == out[-1][1] + 1:
            out[-1][1] = p
        else:
            out.append([p, p])
    return out


def greedy_rects(cells):
    covered = set()
    rects = []
    for (cx, cy) in sorted(cells):
        if (cx, cy) in covered:
            continue
        w = 1
        while (cx + w, cy) in cells and (cx + w, cy) not in covered:
            w += 1
        h = 1
        while all((cx + i, cy + h) in cells and (cx + i, cy + h) not in covered for i in range(w)):
            h += 1
        for i in range(w):
            for j in range(h):
                covered.add((cx + i, cy + j))
        rects.append((cx, cy, w, h))
    assert covered == cells
    return rects


def build_facets(cells, rows):
    tris = []

    def quad(a, b, c, d):
        tris.append((a, b, c))
        tris.append((a, c, d))

    for (cx, cy, w, h) in greedy_rects(cells):
        x0, x1 = cx * CELL, (cx + w) * CELL
        y0, y1 = (rows - cy - h) * CELL, (rows - cy) * CELL
        quad((x0, y0, DEPTH), (x1, y0, DEPTH), (x1, y1, DEPTH), (x0, y1, DEPTH))
        quad((x0, y0, 0.0), (x0, y1, 0.0), (x1, y1, 0.0), (x1, y0, 0.0))

    px, mx, py, my = {}, {}, {}, {}
    for (cx, cy) in cells:
        if (cx + 1, cy) not in cells: px.setdefault(cx, []).append(cy)
        if (cx - 1, cy) not in cells: mx.setdefault(cx, []).append(cy)
        if (cx, cy + 1) not in cells: my.setdefault(cy, []).append(cx)
        if (cx, cy - 1) not in cells: py.setdefault(cy, []).append(cx)

    for cx, ys in px.items():
        for a, b in runs(ys):
            x = (cx + 1) * CELL
            quad((x, (rows - 1 - b) * CELL, 0.0), (x, (rows - a) * CELL, 0.0),
                 (x, (rows - a) * CELL, DEPTH), (x, (rows - 1 - b) * CELL, DEPTH))
    for cx, ys in mx.items():
        for a, b in runs(ys):
            x = cx * CELL
            quad((x, (rows - 1 - b) * CELL, 0.0), (x, (rows - 1 - b) * CELL, DEPTH),
                 (x, (rows - a) * CELL, DEPTH), (x, (rows - a) * CELL, 0.0))
    for cy, xs in my.items():
        for a, b in runs(xs):
            y = (rows - 1 - cy) * CELL
            quad((a * CELL, y, 0.0), ((b + 1) * CELL, y, 0.0),
                 ((b + 1) * CELL, y, DEPTH), (a * CELL, y, DEPTH))
    for cy, xs in py.items():
        for a, b in runs(xs):
            y = (rows - cy) * CELL
            quad((a * CELL, y, 0.0), (a * CELL, y, DEPTH),
                 ((b + 1) * CELL, y, DEPTH), ((b + 1) * CELL, y, 0.0))
    return tris


def sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def normalize(v):
    length = math.sqrt(v[0] ** 2 + v[1] ** 2 + v[2] ** 2) or 1.0
    return (v[0] / length, v[1] / length, v[2] / length)


def fmt(v):
    return str(int(v)) if float(v).is_integer() else str(float(v))


def to_ascii(tris, name='bemly'):
    out = [f'solid {name}']
    for t in tris:
        n = normalize(cross(sub(t[1], t[0]), sub(t[2], t[0])))
        out.append(f'facet normal {fmt(n[0])} {fmt(n[1])} {fmt(n[2])}')
        out.append('outer loop')
        for v in t:
            out.append(f'vertex {fmt(v[0])} {fmt(v[1])} {fmt(v[2])}')
        out.append('endloop')
        out.append('endfacet')
    out.append(f'endsolid {name}')
    return '\n'.join(out) + '\n'


# display order == drop priority (last lines dropped first)
# kind: sig = signature text, bar = separator, label = section name, text = content line
PLAN = [
    ('sig', 'bemly'),
    ('sig', '蓝莓小果冻'),
    ('bar',),
    ('label', 'main'),
    ('text', '一名喜欢尝试各种新鲜事物却又苦于没有技术的小透明。'),
    ('text', '生命 = ∫出生→逝世 学习 dt'),
    ('text', '猫 ×? 苦力怕 → Δ好奇心 = 0'),
    ('text', '由 爱好 强驱动 的代码爱好者'),
    ('bar',),
    ('label', 'master'),
    ('text', '编辑器 / IDE · 语言 / 框架'),
]

MAXCOLS = 192


def assemble(plan):
    """Lay out plan items; returns (cells, rows, kept_items)."""
    cells = set()
    r = 0
    kept = []
    for item in plan:
        kind = item[0]
        if kind == 'bar':
            for x in range(MAXCOLS):
                cells.add((x, r))
            r += 1 + 3
            kept.append(item)
        elif kind == 'label':
            r += place(cells, r, item[1], MAXCOLS) + 2
            kept.append(item)
        elif kind in ('sig', 'text'):
            r += place(cells, r, item[1], MAXCOLS) + 2
            kept.append(item)
        elif kind == 'sig2':
            r += place(cells, r, item[1], MAXCOLS, scale=2) + 2
            kept.append(item)
    return cells, r, kept


def preview(cells, rows):
    for band in range(0, min(rows, 60)):
        print(''.join('#' if (c, band) in cells else '.' for c in range(MAXCOLS)))


if __name__ == '__main__':
    plan = PLAN
    while True:
        while plan and plan[-1][0] in ('bar', 'label') and sum(1 for k, *_ in plan if k == 'text' and True) >= 0:
            # trim trailing structure that has no text after it
            idx = plan.index(plan[-1])
            rest = plan[plan.index(plan[-1]) + 1:]
            if not any(k == 'text' for k, *_ in rest):
                plan.pop()
            else:
                break
        cells, rows, kept = assemble(plan)
        tris = build_facets(cells, rows)
        block = to_ascii(tris)
        size = len(block.encode())
        print(f'lines={sum(1 for k,*_ in kept if k=="text")} facets={len(tris)} block={size/1000:.0f}KB')
        if size <= LIMIT or sum(1 for k, *_ in kept if k == 'text') <= 1:
            break
        # drop the last droppable item (never drop signature/first bar+label)
        for i in range(len(plan) - 1, 3, -1):
            if plan[i][0] in ('text',):
                del plan[i]
                break
        else:
            break
    # trim trailing structure with no content under it
    while plan and plan[-1][0] in ('bar', 'label'):
        plan.pop()
    cells, rows, kept = assemble(plan)
    tris = build_facets(cells, rows)
    block = to_ascii(tris)
    size = len(block.encode())
    print(f'final: {rows} rows x {MAXCOLS} cols, kept {len(kept)} items, block {size/1000:.0f}KB')
    with open(os.path.join(DIR, 'final_block.txt'), 'w') as f:
        f.write(block)
    with open(os.path.join(DIR, 'final_plan.json'), 'w') as f:
        json.dump(kept, f, ensure_ascii=False, indent=1)
    print('kept lines:')
    for k, *rest in kept:
        if rest:
            print(f'  [{k}]', rest[0][:60])
    print('--- top of model ---')
    preview(cells, rows)
