"""任意三角网格 → 分组格式 ASCII STL 的块。
三角形按法线方向聚类（球面上 n 个均匀方向，取最近的），每类一个 facet 块，块法线 = 组内平均法线。
返回 {法线(写出的字符串): [三角形顶点列表]}，和 voxel_stl 的块合在一起输出。"""
import numpy as np


def fib_dirs(n):
    i = np.arange(n) + 0.5
    phi = np.arccos(1 - 2 * i / n)
    th = np.pi * (1 + 5 ** 0.5) * i
    return np.stack([np.cos(th) * np.sin(phi), np.sin(th) * np.sin(phi), np.cos(phi)], 1)


def blocks(V, T, n_dirs=512, digits=2):
    """V: 整数顶点 (N,3)；T: 三角形索引 (M,3)。返回 (blocks, 平均法线误差°, 最大误差°)。"""
    a, b, c = V[T[:, 0]], V[T[:, 1]], V[T[:, 2]]
    nrm = np.cross(b - a, c - a).astype(np.float64)
    ln = np.linalg.norm(nrm, axis=1)
    keep = ln > 0                                   # 量化后退化的三角形丢掉
    a, b, c, nrm = a[keep], b[keep], c[keep], nrm[keep] / ln[keep, None]
    D = fib_dirs(n_dirs)
    lab = np.argmax(nrm @ D.T, axis=1)
    out = {}
    errs = []
    for k in np.unique(lab):
        m = lab == k
        mean = nrm[m].sum(0)
        mean /= np.linalg.norm(mean)
        q = np.round(mean, digits)
        qn = q / np.linalg.norm(q)
        errs.append(np.degrees(np.arccos(np.clip(nrm[m] @ qn, -1, 1))))
        key = ' '.join(fmt(x) for x in q)
        tris = np.stack([a[m], b[m], c[m]], 1)
        out.setdefault(key, []).extend(tris.tolist())
    e = np.concatenate(errs)
    return out, float(e.mean()), float(e.max()), int(keep.sum())


def fmt(x):
    s = ('%.2f' % x).rstrip('0').rstrip('.')
    s = s.replace('0.', '.', 1) if s.startswith('0.') else s.replace('-0.', '-.', 1)
    return '0' if s in ('', '-0', '-') else s


def to_stl(blocks, name='bemly'):
    """分组格式：每个法线一个 facet 块，块里连续放三角形顶点（GitHub/three.js STLLoader 正则解析，
    不读 outer loop/endloop，块内法线对所有顶点生效）。"""
    out = [f'solid {name}']
    for n, tris in blocks.items():
        out.append('facet normal ' + n)
        for t in tris:
            for v in t:
                out.append('vertex %d %d %d' % tuple(v))
        out.append('endfacet')
    out.append(f'endsolid {name}')
    return '\n'.join(out) + '\n'
