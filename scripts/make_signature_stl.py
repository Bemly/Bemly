#!/usr/bin/env python3
"""Regenerate the signature-only README:

    Bemly
    蓝莓小果冻
    ────────────
    猫害死好奇心。

Font: fusion-pixel-font 12px proportional, rasterized to scripts/fusion12_glyphs.json
(scripts/rasterize_pixel.swift). Each font pixel becomes a SCALE x SCALE x SCALE cube
(SCALE=10 -> 10x10x10). GAP = design-px inserted between characters and between lines;
the rule is RULE design-px thick and spans the full model width. Facet count is
independent of SCALE.
"""
import json
import os
import sys

DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, DIR)
import make_readme_stl as M

M.GL = json.load(open(os.path.join(DIR, 'fusion12_glyphs.json')))
M.DEPTH = 10.0  # extrusion depth in cubes -> font pixels become SCALE^3 cubes

SCALE = 10
GAP = 2
RULE = 1   # divider thickness in design-px
LINE_NAME = 'Bemly'
LINE_SUB = '蓝莓小果冻'
LINE_MOTTO = '猫害死好奇心。'


def cw(ch):
    return 6 if ch == ' ' else M.GL[ch]['cols']


def place(cells, row0, s, maxcols):
    """Place one text line centered in maxcols design-px; returns its height in cubes."""
    total_w = sum(cw(c) for c in s) + (len(s) - 1) * GAP
    cx = (maxcols - total_w) // 2
    n_rows = 0
    for ch in s:
        if ch != ' ':
            g = M.GL[ch]
            n_rows = max(n_rows, len(g['rows']))
            for gy in range(len(g['rows'])):
                for gx, v in enumerate(g['rows'][gy]):
                    if v == '1':
                        for dx in range(SCALE):
                            for dy in range(SCALE):
                                cells.add(((cx + gx) * SCALE + dx, row0 + gy * SCALE + dy))
        cx += cw(ch) + GAP
    return n_rows * SCALE


def main():
    def width(s):
        return sum(cw(c) for c in s) + (len(s) - 1) * GAP

    maxcols = max(width(LINE_NAME), width(LINE_SUB), width(LINE_MOTTO))

    cells = set()
    r = place(cells, 0, LINE_NAME, maxcols)
    r += GAP * SCALE
    r += place(cells, r, LINE_SUB, maxcols)
    r += GAP * SCALE
    for dy in range(RULE * SCALE):
        for x in range(maxcols * SCALE):
            cells.add((x, r + dy))     # rule: RULE design-px thick, full width
    r += RULE * SCALE
    r += GAP * SCALE
    r += place(cells, r, LINE_MOTTO, maxcols)

    tris = M.build_facets(cells, r)
    block = M.to_ascii(tris, name='bemly')
    out = os.path.join(DIR, '..', 'README.md')
    with open(out, 'w') as f:
        f.write('```stl\n' + block + '```\n')
    print(f'facets={len(tris)} block={len(block.encode()) / 1000:.0f}KB '
          f'grid={maxcols * SCALE}x{r}x{int(M.DEPTH)}cubes')


if __name__ == '__main__':
    main()
