# blender -b --python bl_decimate.py -- shell.npz out.npz TARGET_TRIS [SMOOTH_ITERS]
# 体素外壳 → 拉普拉斯平滑（去阶梯、保体积）→ QEM 塌陷减面到 TARGET_TRIS → 导出三角形
import sys
import bpy
import numpy as np

a = sys.argv[sys.argv.index('--') + 1:]
src, out, target = a[0], a[1], int(a[2])
iters = int(a[3]) if len(a) > 3 else 6
d = np.load(src)
V, F = d['verts'].astype(np.float64), d['faces']

bpy.ops.wm.read_factory_settings(use_empty=True)
me = bpy.data.meshes.new('shell')
me.vertices.add(len(V))
me.vertices.foreach_set('co', V.ravel())
me.loops.add(F.size)
me.loops.foreach_set('vertex_index', F.ravel())
me.polygons.add(len(F))
me.polygons.foreach_set('loop_start', np.arange(0, F.size, 4))
me.polygons.foreach_set('loop_total', np.full(len(F), 4))
me.update()
me.validate()
ob = bpy.data.objects.new('shell', me)
bpy.context.scene.collection.objects.link(ob)
bpy.context.view_layer.objects.active = ob
ob.select_set(True)

rm = ob.modifiers.new('remesh', 'REMESH')   # OpenVDB 重建：干净的流形网格（体素外壳在边相接处是非流形，QEM 减不下去）
rm.mode = 'VOXEL'
rm.voxel_size = 1.0
sm = ob.modifiers.new('smooth', 'LAPLACIANSMOOTH')
sm.iterations = iters
sm.lambda_factor = 0.8
sm.use_volume_preserve = True
tri = ob.modifiers.new('tri', 'TRIANGULATE')
dec = ob.modifiers.new('dec', 'DECIMATE')
dec.decimate_type = 'COLLAPSE'
dg0 = bpy.context.evaluated_depsgraph_get()
dec.show_viewport = False
n0 = sum(len(p.vertices) - 2 for p in ob.evaluated_get(dg0).data.polygons)
dec.show_viewport = True
dec.ratio = min(1.0, target / n0)
dec.use_collapse_triangulate = True

dg = bpy.context.evaluated_depsgraph_get()
ev = ob.evaluated_get(dg)
m = ev.to_mesh()
m.calc_loop_triangles()
co = np.empty(len(m.vertices) * 3)
m.vertices.foreach_get('co', co)
tris = np.empty(len(m.loop_triangles) * 3, np.int64)
m.loop_triangles.foreach_get('vertices', tris)
np.savez(out, verts=co.reshape(-1, 3), tris=tris.reshape(-1, 3))
print('RESULT tris', len(m.loop_triangles), 'verts', len(m.vertices))
