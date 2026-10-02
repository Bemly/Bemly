"""摆好姿势的网格 → 高分辨率实心体素 → 外壳四边形网格（顶点共享，给 Blender 平滑 + 减面）。
python3 shell.py pos.f32 idx.u32 H out.npz
"""
import sys
import numpy as np
from scipy import ndimage
import dschan_voxelize as VX

P = np.fromfile(sys.argv[1], np.float32).reshape(-1, 3).astype(np.float64)
I = np.fromfile(sys.argv[2], np.uint32)
H = int(sys.argv[3])
occ, s = VX.voxelize(P, I, H)
occ = ndimage.binary_closing(np.pad(occ, 2), np.ones((3, 3, 3)))[2:-2, 2:-2, 2:-2] | occ
lab, n = ndimage.label(occ)
sizes = ndimage.sum(occ, lab, range(1, n + 1))
occ = np.isin(lab, 1 + np.argmax(sizes))  # 只留最大的连通体（碎发丝去掉）
pad = np.pad(occ, 1)
quads = []
# 每个外露面一个四边形（外法线逆时针），角点是整数格点
C = {
    (0, 1): [(1, 0, 0), (1, 1, 0), (1, 1, 1), (1, 0, 1)],
    (0, -1): [(0, 0, 0), (0, 0, 1), (0, 1, 1), (0, 1, 0)],
    (1, 1): [(0, 1, 0), (0, 1, 1), (1, 1, 1), (1, 1, 0)],
    (1, -1): [(0, 0, 0), (1, 0, 0), (1, 0, 1), (0, 0, 1)],
    (2, 1): [(0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)],
    (2, -1): [(0, 0, 0), (0, 1, 0), (1, 1, 0), (1, 0, 0)],
}
for (axis, d), corners in C.items():
    sh = [0, 0, 0]
    sh[axis] = d
    nb = np.roll(pad, -d, axis=axis)
    xs, ys, zs = np.nonzero(pad & ~nb)
    base = np.stack([xs, ys, zs], 1) - 1
    quads.append(base[:, None, :] + np.array(corners)[None])
Q = np.concatenate(quads)                      # (F, 4, 3)
verts, inv = np.unique(Q.reshape(-1, 3), axis=0, return_inverse=True)
faces = inv.reshape(-1, 4)
np.savez(sys.argv[4], verts=verts.astype(np.float32), faces=faces.astype(np.int32), scale=s)
print('grid', occ.shape, 'voxels', occ.sum(), 'verts', len(verts), 'quads', len(faces), 'voxel size', s)
