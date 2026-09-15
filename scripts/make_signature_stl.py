#!/usr/bin/env python3
"""Regenerate the signature-only README: bemly + 蓝莓小果冻 in GuanZhi 8x8.

SCALE = cubes per font pixel; GAP = design-px inserted between characters
and between the two lines. Writes README.md (a single ```stl block) to the
repo root. Facet count is independent of SCALE thanks to greedy meshing.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_readme_stl as M

SCALE = 10
GAP = 2
MAXCOLS = 500


def cw(ch):
    return 4 if ch == ' ' else M.GL[ch]['cols']


def place(cells, row0, s, maxcols):
    total_w = sum(cw(c) for c in s) * SCALE + (len(s) - 1) * GAP * SCALE
    cx = (maxcols - total_w) // 2
    for ch in s:
        if ch != ' ':
            g = M.GL[ch]
            for gy in range(8):
                for gx, v in enumerate(g['rows'][gy]):
                    if v == '1':
                        for dx in range(SCALE):
                            for dy in range(SCALE):
                                cells.add((cx + gx * SCALE + dx, row0 + gy * SCALE + dy))
        cx += (cw(ch) + GAP) * SCALE
    return 8 * SCALE


def main():
    cells = set()
    r = 0
    r += place(cells, r, 'bemly', MAXCOLS)
    r += GAP * SCALE
    r += place(cells, r, '蓝莓小果冻', MAXCOLS)
    tris = M.build_facets(cells, r)
    block = M.to_ascii(tris, name='bemly')
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'README.md')
    with open(out, 'w') as f:
        f.write('```stl\n' + block + '```\n')
    print(f'facets={len(tris)} block={len(block.encode()) / 1000:.0f}KB rows={r}')


if __name__ == '__main__':
    main()
