"""摆好姿势的大肥鱼娘网格（three.js 世界坐标：y 朝上、脸朝 +z）→ 实心体素。
用法：python3 voxelize.py pos.f32 idx.u32 H out.txt
输出 out.txt：第一行 'nx ny nz'，之后每行 'x y z0 z1 z0 z1 ...'（STL 坐标：z 朝上、脸朝 -y，按柱子存实心区间）。
"""
import sys
import numpy as np
from scipy import ndimage


def voxelize(P, I, H, shift=(0, 0, 0)):
    # three (x, y↑, z→脸) → STL (x, -z, y)：脸朝 -y，z 朝上
    P = np.stack([P[:, 0], -P[:, 2], P[:, 1]], axis=1)
    lo, hi = P.min(0), P.max(0)
    s = (hi[2] - lo[2]) / H                 # 体素边长：人物高 H 格
    lo = lo - np.array(shift) * s          # 网格起点偏移（0–1 格），换对齐方式能少掉不少零碎面
    dims = np.ceil((hi - lo) / s).astype(int) + 1
    occ = np.zeros(dims, bool)
    tri = P[I.reshape(-1, 3)]               # (T, 3, 3)
    # 三角形表面采样：按最长边细分，保证采样点间距 < 半格
    e = np.max(np.linalg.norm(tri - np.roll(tri, 1, axis=1), axis=2), axis=1)
    k = np.maximum(1, np.ceil(e / (s * 0.5)).astype(int))
    for kk in np.unique(k):
        sel = tri[k == kk]
        a, b = np.meshgrid(np.arange(kk + 1), np.arange(kk + 1))
        m = (a + b) <= kk
        u = (a[m] / kk)[None, :, None]
        v = (b[m] / kk)[None, :, None]
        pts = sel[:, 0:1] + u * (sel[:, 1:2] - sel[:, 0:1]) + v * (sel[:, 2:3] - sel[:, 0:1])
        g = np.floor((pts.reshape(-1, 3) - lo) / s).astype(int)
        occ[g[:, 0], g[:, 1], g[:, 2]] = True
    occ = ndimage.binary_fill_holes(occ)    # 封闭的身体内部填实；薄片（裙摆、头发片）保持一格厚
    return occ, s


def save(occ, path):
    nx, ny, nz = occ.shape
    lines = [f'{nx} {ny} {nz}']
    for x in range(nx):
        for y in range(ny):
            col = occ[x, y]
            if not col.any():
                continue
            d = np.diff(np.concatenate([[0], col.astype(int), [0]]))
            st, en = np.nonzero(d == 1)[0], np.nonzero(d == -1)[0]
            lines.append(f'{x} {y} ' + ' '.join(f'{a} {b}' for a, b in zip(st, en)))
    open(path, 'w').write('\n'.join(lines) + '\n')


if __name__ == '__main__':
    P = np.fromfile(sys.argv[1], np.float32).reshape(-1, 3).astype(np.float64)
    I = np.fromfile(sys.argv[2], np.uint32)
    H = int(sys.argv[3])
    shift = tuple(map(float, sys.argv[5].split(','))) if len(sys.argv) > 5 else (0, 0, 0)
    occ, s = voxelize(P, I, H, shift)
    save(occ, sys.argv[4])
    print('grid', occ.shape, 'voxels', int(occ.sum()))
