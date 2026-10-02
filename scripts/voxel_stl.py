"""体素外表面 → 最少三角形 → 紧凑 ASCII STL（README 里 ```stl 围栏用）。

几何：cols = {(x, y): (z0, z1)} 柱子（实心区间 [z0, z1)），x/y/z 都是整数格。
每个轴向平面求"必须覆盖"的单位方格 R 和"允许覆盖"的方格 A = R ∪ 被实体包在里面的方格
（浮雕里矮一层的顶面可以伸进更高的柱子里、侧墙可以往下伸进实体，反正看不见），
用矩形覆盖 R（矩形只落在 A 里，矩形之间允许重叠），每个平面试几种贪心取矩形最少的；1 矩形 = 2 三角形。

输出格式按 GitHub 查看器的解析器（three.js STLLoader.parseASCII，纯正则）来省字节，见 AGENTS.md。
"""
from collections import defaultdict


# ---------------- 2D 矩形覆盖 ----------------
def cover_partition(R, order='xy'):
    """互不重叠的贪心划分（只用 R），order 决定先横向还是先纵向延伸。"""
    cells = R
    covered = set()
    rects = []
    key = (lambda p: (p[1], p[0])) if order == 'xy' else (lambda p: (p[0], p[1]))
    for (x, y) in sorted(cells, key=key):
        if (x, y) in covered:
            continue
        if order == 'xy':
            w = 1
            while (x + w, y) in cells and (x + w, y) not in covered:
                w += 1
            h = 1
            while all((x + i, y + h) in cells and (x + i, y + h) not in covered for i in range(w)):
                h += 1
        else:
            h = 1
            while (x, y + h) in cells and (x, y + h) not in covered:
                h += 1
            w = 1
            while all((x + w, y + j) in cells and (x + w, y + j) not in covered for j in range(h)):
                w += 1
        for i in range(w):
            for j in range(h):
                covered.add((x + i, y + j))
        rects.append((x, y, w, h))
    return rects


def cover_overlap(R, A):
    """可重叠的贪心覆盖：矩形落在 A 里，每次取"新覆盖 R 最多"的候选。"""
    unc = set(R)
    rects = []
    for (x, y) in sorted(R, key=lambda p: (p[1], p[0])):
        if (x, y) not in unc:
            continue
        # 本行在 A 里的最大连续段 [l, r]
        l = x
        while (l - 1, y) in A:
            l -= 1
        r = x
        while (r + 1, y) in A:
            r += 1
        best = None
        for a in sorted({l, x}):
            for b in range(x, r + 1):
                # 纵向扩展：上下都在 A 里
                y0 = y
                while all((i, y0 - 1) in A for i in range(a, b + 1)):
                    y0 -= 1
                y1 = y
                while all((i, y1 + 1) in A for i in range(a, b + 1)):
                    y1 += 1
                gain = sum(1 for i in range(a, b + 1) for j in range(y0, y1 + 1) if (i, j) in unc)
                area = (b - a + 1) * (y1 - y0 + 1)
                if best is None or (gain, -area) > (best[0], -best[1]):
                    best = (gain, area, a, y0, b - a + 1, y1 - y0 + 1)
        _, _, a, y0, w, h = best
        for i in range(a, a + w):
            for j in range(y0, y0 + h):
                unc.discard((i, j))
        rects.append((a, y0, w, h))
    return rects


def shrink(rects, R):
    """去掉多余矩形：如果某个矩形覆盖的 R 全部被其它矩形覆盖了，删掉它。"""
    cnt = defaultdict(int)
    for (x, y, w, h) in rects:
        for i in range(x, x + w):
            for j in range(y, y + h):
                if (i, j) in R:
                    cnt[(i, j)] += 1
    out = []
    for rc in sorted(rects, key=lambda r: r[2] * r[3]):
        x, y, w, h = rc
        mine = [(i, j) for i in range(x, x + w) for j in range(y, y + h) if (i, j) in R]
        if all(cnt[c] > 1 for c in mine):
            for c in mine:
                cnt[c] -= 1
        else:
            out.append(rc)
    return out


def best_cover(R, A):
    if not R:
        return []
    cands = [cover_partition(R, 'xy'), cover_partition(R, 'yx')]
    if A is not R and len(A) > len(R):
        cands.append(shrink(cover_overlap(R, A), R))
    cands.append(shrink(cover_overlap(R, R), R))
    best = min(cands, key=len)
    # 校验：恰好覆盖 R，且不越出 A
    got = set()
    for (x, y, w, h) in best:
        for i in range(x, x + w):
            for j in range(y, y + h):
                assert (i, j) in A, 'rect outside allowed'
                got.add((i, j))
    assert R <= got
    return best


# ---------------- 体素 → 各平面 ----------------
def solid_at(cols, x, y, z):
    c = cols.get((x, y))
    return c is not None and c[0] <= z < c[1]


def surfaces(cols):
    """返回 {(轴, 方向, 平面坐标): (R, A)}。轴 0=x 1=y 2=z；方向 +1/-1 = 法线朝向。
    平面内二维坐标：z 面 (x, y)，x 面 (y, z)，y 面 (x, z)。"""
    planes = defaultdict(lambda: (set(), set()))
    xs = [x for x, _ in cols]
    ys = [y for _, y in cols]
    zmax = max(c[1] for c in cols.values())
    # z 方向：每根柱子的顶/底
    tops = defaultdict(set)
    bots = defaultdict(set)
    for (x, y), (z0, z1) in cols.items():
        tops[z1].add((x, y))
        bots[z0].add((x, y))
    for z, cs in tops.items():
        # 允许：该高度平面处于实体内部的方格（上下都是实心）
        A = set(cs) | {(x, y) for (x, y), (a, b) in cols.items() if a < z < b}
        planes[(2, 1, z)] = (cs, A)
    for z, cs in bots.items():
        A = set(cs) | {(x, y) for (x, y), (a, b) in cols.items() if a < z < b}
        planes[(2, -1, z)] = (cs, A)
    # x / y 方向侧墙：相邻柱子间
    for axis in (0, 1):
        for (x, y), (z0, z1) in cols.items():
            for d in (1, -1):
                nx, ny = (x + d, y) if axis == 0 else (x, y + d)
                pc = (x + (d > 0)) if axis == 0 else (y + (d > 0))
                key = (axis, d, pc)
                if key not in planes:
                    planes[key] = (set(), set())
                R, A = planes[key]
                n = cols.get((nx, ny))
                for z in range(z0, z1):
                    u = y if axis == 0 else x
                    if n is None or not (n[0] <= z < n[1]):
                        R.add((u, z))
                    A.add((u, z))  # 本格实心：如果邻格也实心就是内部面（不可见，允许覆盖）；否则是 R
                # 内部：本格和邻格都实心的方格才算 A，单边实心的已经在 R 里
    # 修正侧墙 A：只保留 R ∪ (两边都实心)
    for (axis, d, pc), (R, A) in list(planes.items()):
        if axis == 2:
            continue
        keep = set(R)
        for (u, z) in A:
            if (u, z) in R:
                continue
            if axis == 0:
                a, b = (pc - 1, u), (pc, u)
            else:
                a, b = (u, pc - 1), (u, pc)
            if solid_at(cols, *a, z) and solid_at(cols, *b, z):
                keep.add((u, z))
        planes[(axis, d, pc)] = (R, keep)
    return {k: v for k, v in planes.items() if v[0]}


def emit(groups, axis, d, pc, rects, scale=1, off=(0, 0, 0)):
    """平面里的矩形 → 世界坐标四边形（外法线逆时针），按法线分组。
    平面内二维坐标：z 面 (x, y)，x 面 (y, z)，y 面 (x, z)。"""
    for (u, v, w, h) in rects:
        u0, u1, v0, v1 = u, u + w, v, v + h
        if axis == 2:
            p = [(u0, v0, pc), (u1, v0, pc), (u1, v1, pc), (u0, v1, pc)]
        elif axis == 0:
            p = [(pc, u0, v0), (pc, u1, v0), (pc, u1, v1), (pc, u0, v1)]
        else:
            p = [(u0, pc, v0), (u1, pc, v0), (u1, pc, v1), (u0, pc, v1)]
        # p 的顺序对 axis=2 是绕 +z 逆时针；对 x 平面 (y,z) 是绕 +x 逆时针；对 y 平面 (x,z) 是绕 -y 逆时针
        ccw_dir = {2: 1, 0: 1, 1: -1}[axis]
        if d != ccw_dir:
            p = p[::-1]
        p = [tuple(c * scale + o for c, o in zip(q, off)) for q in p]
        n = [0, 0, 0]
        n[axis] = d
        groups[tuple(n)].append(p)


def quads(cols, scale=1, off=(0, 0, 0), groups=None):
    """柱子表示（cols）→ 四边形。scale/off：格子坐标 × scale + off（文字在字体像素格里合并，再放大）。"""
    groups = defaultdict(list) if groups is None else groups
    for (axis, d, pc), (R, A) in surfaces(cols).items():
        emit(groups, axis, d, pc, best_cover(R, A), scale, off)
    return groups


def quads_occ(occ, scale=1, off=(0, 0, 0), groups=None):
    """任意 3D 体素（numpy bool 数组 occ[x, y, z]）→ 四边形。
    每个轴向切片：R = 实心且该方向邻格为空的面，A = R ∪ 两侧都实心的内部面（看不见，矩形可以伸进去）。"""
    import numpy as np
    groups = defaultdict(list) if groups is None else groups
    pad = np.pad(occ, 1)
    for axis in range(3):
        o = np.moveaxis(pad, axis, 0)          # o[i, u, v]，(u, v) 是另外两个轴按原顺序
        for d in (1, -1):
            for i in range(1, o.shape[0] - 1):
                cur, nb = o[i], o[i + d]
                R = cur & ~nb
                if not R.any():
                    continue
                A = R | (cur & nb)
                Rs = {(u - 1, v - 1) for u, v in zip(*np.nonzero(R))}
                As = {(u - 1, v - 1) for u, v in zip(*np.nonzero(A))}
                pc = (i - 1) + (1 if d > 0 else 0)
                emit(groups, axis, d, pc, best_cover(Rs, As), scale, off)
    return groups


def to_stl(groups, name='bemly'):
    """紧凑格式：每个法线一个 facet 块，块里连续放三角形顶点（three.js STLLoader 正则解析，
    不读 outer loop/endloop，块内法线对所有顶点生效）。"""
    out = [f'solid {name}']
    for n, qs in sorted(groups.items()):
        out.append('facet normal %d %d %d' % n)
        for p in qs:
            for t in ((p[0], p[1], p[2]), (p[0], p[2], p[3])):
                for v in t:
                    out.append('vertex %d %d %d' % v)
        out.append('endfacet')
    out.append(f'endsolid {name}')
    return '\n'.join(out) + '\n'


def tri_count(groups):
    return sum(len(q) for q in groups.values()) * 2
