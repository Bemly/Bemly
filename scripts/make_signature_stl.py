#!/usr/bin/env python3
"""Regenerate the README model:

    Bemly
    蓝莓小果冻
    ────────────
    猫害死好奇心。
         [大肥鱼娘低多边形 3D 模型，站在格言前面]

Font: fusion-pixel-font 12px proportional, rasterized to scripts/fusion12_glyphs.json
(scripts/rasterize_pixel.swift). GAP = design-px between characters and between lines;
the rule is RULE design-px thick and spans the full model width. Text = cubes, meshed on the
font-pixel grid with rectangle covers (voxel_stl) and scaled by K.

Figure: scripts/dschan/dschan_lowpoly.txt — posed v2c model from the deepseek player →
solid voxels (dschan_voxelize.py) → outer shell (dschan_shell.py) → OpenVDB remesh + smooth +
QEM decimation in Blender (dschan_decimate_blender.py) → integer vertices. Facing -y (toward
GitHub's default camera), z up. Triangles are grouped by quantized normal (trimesh_stl).
"""
import json
import os
import sys

import numpy as np

DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, DIR)
import trimesh_stl as TS
import voxel_stl as V

GL = json.load(open(os.path.join(DIR, 'fusion12_glyphs.json')))

GAP = 2
RULE = 1   # divider thickness in design-px
LINE_NAME = 'Bemly'
LINE_SUB = '蓝莓小果冻'
LINE_MOTTO = '猫害死好奇心。'

FIGURE = os.path.join(DIR, 'dschan', 'dschan_lowpoly.txt')
FIG_PX = 30         # figure height in font pixels
FIG_GAP = 20        # font px between the motto and the back of the figure (keeps the figure below the
                    # text in GitHub's default view instead of covering it)
NORMAL_DIRS = 256   # normal clusters: mean lighting error ~4.7°, ~35 bytes per facet block
LIMIT = 500_000     # README.md bytes (GitHub stops rendering around 500KB)


def cw(ch):
    return 6 if ch == ' ' else GL[ch]['cols']


def width(s):
    return sum(cw(c) for c in s) + (len(s) - 1) * GAP


def place(cells, row0, s, maxcols):
    """Place one text line centered in maxcols design-px; returns its height in design-px."""
    cx = (maxcols - width(s)) // 2
    n_rows = 0
    for ch in s:
        if ch != ' ':
            g = GL[ch]
            n_rows = max(n_rows, len(g['rows']))
            for gy in range(len(g['rows'])):
                for gx, v in enumerate(g['rows'][gy]):
                    if v == '1':
                        cells.add((cx + gx, row0 + gy))
        cx += cw(ch) + GAP
    return n_rows


def text_cells():
    maxcols = max(width(LINE_NAME), width(LINE_SUB), width(LINE_MOTTO))
    cells = set()
    r = place(cells, 0, LINE_NAME, maxcols) + GAP
    r += place(cells, r, LINE_SUB, maxcols) + GAP
    for x in range(maxcols):
        for dy in range(RULE):
            cells.add((x, r + dy))
    r += RULE + GAP
    r += place(cells, r, LINE_MOTTO, maxcols)
    return cells, r, maxcols


def load_figure(path):
    lines = open(path).read().split('\n')
    nv, nt = map(int, lines[0].split())
    V_ = np.array([list(map(int, l.split())) for l in lines[1:1 + nv]])
    T_ = np.array([list(map(int, l.split())) for l in lines[1 + nv:1 + nv + nt]])
    return V_, T_


def main():
    FV, FT = load_figure(FIGURE)
    FV = FV - FV.min(0)
    K = max(1, round(FV[:, 2].max() / FIG_PX))   # model units per font pixel
    cells, rows, maxcols = text_cells()
    FV[:, 0] += (maxcols * K - FV[:, 0].max()) // 2
    text_y = FV[:, 1].max() + FIG_GAP * K            # text block starts behind the figure
    text = V.quads({(x, rows - 1 - y): (0, 1) for (x, y) in cells}, scale=K, off=(0, text_y, 0))
    blocks = {}
    for n, qs in text.items():
        tris = blocks.setdefault('%d %d %d' % n, [])
        for p in qs:
            tris += [(p[0], p[1], p[2]), (p[0], p[2], p[3])]
    t_tris = sum(len(t) for t in blocks.values())
    fig, err, err_max, f_tris = TS.blocks(FV, FT, NORMAL_DIRS)
    for k, tris in fig.items():
        blocks.setdefault(k, []).extend(tris)
    md = '```stl\n' + TS.to_stl(blocks) + '```\n'
    size = len(md.encode())
    print(f'text {t_tris} tris | figure {f_tris} tris, {len(fig)} normal blocks, '
          f'normal error mean {err:.1f}° max {err_max:.1f}° | README {size} B')
    assert size <= LIMIT, 'README over the GitHub render limit'
    with open(os.path.join(DIR, '..', 'README.md'), 'w') as f:
        f.write(md)


if __name__ == '__main__':
    main()
