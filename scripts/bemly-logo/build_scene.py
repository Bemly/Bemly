"""Blender side of the BEMLY logo animation.

    blender -b -P build_scene.py -- --render OUT_DIR [--frames A B] [--save scene.blend]
    blender -b -P build_scene.py -- --poses sheet.png      # all 24 orientations of every gizmo
    blender -b -P build_scene.py -- --idpass OUT_DIR       # un-antialiased id/depth pass for make_svg.py

Each gizmo is the intersection of two extruded glyphs, so it reads as a
katakana from the front and as a Latin letter from a second side.  Two PNG
passes are rendered per frame (beauty + glow mask); post.py adds the bloom,
the dust and the encode.
"""
import bpy, bmesh, sys, os, json
import numpy as np
from math import radians, pi, sin
from itertools import product
from mathutils import Matrix, Quaternion, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from glyphs import GLYPHS, PAIRS

FPS, FRAMES = 30, 229
PX_PER_U = 10.3            # the original's letters are ~165 px tall = 16 u
CAM_Z = 100.0
GAP = 2.3                  # between letters, in u

# --- timing, measured off the reference clip (frames @30fps) ---------------
T_ON = 30                              # hard cut from black
WAVES = [38.5, 54.0, 72.0, 95.5]       # start of each left-to-right wave
STAGGER, SPIN = 2.1, 7.0               # per-gizmo delay / spin duration
GLOW_IN, GLOW_OUT = 4.0, 5.0

# --- orientations each gizmo passes through (indices into ROTS) ------------
# first is always the katakana, last always the letter; see --poses sheet
POSES = {
    'BE': None, 'MU': None, 'RI': None, 'CHOON': None, 'SMALL_I': None,
}


def all_rotations():
    seen, out = set(), []
    for a, b, c in product(range(4), repeat=3):
        m = (Matrix.Rotation(a * pi / 2, 3, 'X') @ Matrix.Rotation(b * pi / 2, 3, 'Y')
             @ Matrix.Rotation(c * pi / 2, 3, 'Z'))
        key = tuple(round(v) for row in m for v in row)
        if key not in seen:
            seen.add(key)
            out.append(Matrix([[round(v) for v in row] for row in m]))
    return out


ROTS = all_rotations()


# ------------------------------------------------------------- geometry ----
def prism(poly, depth):
    pts = []
    for p in poly:
        if not pts or (Vector(p) - Vector(pts[-1])).length > 1e-5:
            pts.append(p)
    if (Vector(pts[0]) - Vector(pts[-1])).length < 1e-5:
        pts.pop()
    bm = bmesh.new()
    lo = [bm.verts.new((x, y, -depth / 2)) for x, y in pts]
    hi = [bm.verts.new((x, y, depth / 2)) for x, y in pts]
    bm.faces.new(lo)
    bm.faces.new(hi)
    n = len(pts)
    for i in range(n):
        bm.faces.new((lo[i], lo[(i + 1) % n], hi[(i + 1) % n], hi[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bmesh.ops.triangulate(bm, faces=bm.faces)
    me = bpy.data.meshes.new('prism')
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new('prism', me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def bake_modifier(ob, mod):
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
    ob.modifiers.remove(mod)
    old, ob.data = ob.data, me
    bpy.data.meshes.remove(old)


def boolean(a, b, op):
    m = a.modifiers.new('bool', 'BOOLEAN')
    m.operation, m.object, m.solver = op, b, 'EXACT'
    bake_modifier(a, m)
    bpy.data.objects.remove(b)
    return a


def glyph_solid(name, depth=40):
    w, h, ops = GLYPHS[name] if isinstance(name, str) else name
    solid = None
    for op, poly in ops:
        p = prism([(x - w / 2, y - h / 2) for x, y in poly], depth if op == 'add' else depth + 20)
        if solid is None:
            solid = p
        else:
            boolean(solid, p, {'add': 'UNION', 'sub': 'DIFFERENCE', 'clip': 'INTERSECT'}[op])
    return solid


def gizmo(kana, latin, axis, third):
    """-> (object, rotation matrix that turns the letter towards the camera)."""
    a, b = glyph_solid(kana), glyph_solid(latin)
    r_l = Matrix.Rotation(pi / 2, 3, 'Y' if axis == 'y' else 'X')
    b.matrix_world = r_l.to_4x4()
    boolean(a, b, 'INTERSECT')
    if third:
        # 'y': carving is drawn in (x, z) and cut along y; 'x': in (-z, y), cut along x
        size = (GLYPHS[kana][0], GLYPHS[latin][0]) if axis == 'y' else (GLYPHS[latin][1], GLYPHS[kana][1])
        c = glyph_solid((size[0], size[1], third))
        c.matrix_world = Matrix.Rotation(pi / 2, 4, 'X' if axis == 'y' else 'Y')
        boolean(a, c, 'INTERSECT')
    me = a.data
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)
    bmesh.ops.dissolve_limit(bm, angle_limit=radians(0.5), verts=bm.verts, edges=bm.edges)
    bm.to_mesh(me)
    bm.free()
    bev = a.modifiers.new('bevel', 'BEVEL')
    bev.width, bev.segments, bev.limit_method, bev.angle_limit = 0.16, 3, 'ANGLE', radians(40)
    bake_modifier(a, bev)
    me = a.data
    me.polygons.foreach_set('use_smooth', [True] * len(me.polygons))
    me.set_sharp_from_angle(angle=radians(40))
    a.name = kana + '_' + latin
    a.rotation_mode = 'QUATERNION'
    a['glow'], a['flat'], a['front'] = 0.0, 0.0, 8.0
    return a, Matrix([[round(v) for v in row] for row in r_l.inverted()])


# ------------------------------------------------------------ materials ----
def srgb(r, g, b):
    f = lambda c: (c / 255 / 12.92) if c / 255 <= 0.04045 else ((c / 255 + 0.055) / 1.055) ** 2.4
    return (f(r), f(g), f(b), 1.0)


def obj_attr(nt, name):
    n = nt.nodes.new('ShaderNodeAttribute')
    n.attribute_type, n.attribute_name = 'OBJECT', name
    return n.outputs['Fac']


def math(nt, op, a, b=None, clamp=False):
    n = nt.nodes.new('ShaderNodeMath')
    n.operation, n.use_clamp = op, clamp
    for sock, v in zip(n.inputs, (a, b)):
        if v is None:
            continue
        if isinstance(v, (int, float)):
            sock.default_value = v
        else:
            nt.links.new(v, sock)
    return n.outputs[0]


def mix(nt, fac, a, b):
    n = nt.nodes.new('ShaderNodeMix')
    n.data_type = 'RGBA'
    for idx, v in ((0, fac), (6, a), (7, b)):
        if isinstance(v, tuple):
            n.inputs[idx].default_value = v
        elif isinstance(v, (int, float)):
            n.inputs[idx].default_value = v
        else:
            nt.links.new(v, n.inputs[idx])
    return n.outputs[2]


def ramp(nt, fac, stops):
    n = nt.nodes.new('ShaderNodeValToRGB')
    el = n.color_ramp.elements
    while len(el) < len(stops):
        el.new(0.5)
    for e, (pos, col) in zip(el, stops):
        e.position, e.color = pos, col
    nt.links.new(fac, n.inputs[0])
    return n.outputs[0]


def emission_material(name, build):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    em = nt.nodes.new('ShaderNodeEmission')
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    nt.links.new(em.outputs[0], out.inputs[0])
    col = build(nt)
    nt.links.new(col, em.inputs['Color'])
    return mat


def beauty_color(nt):
    # how far behind the gizmo's front-most point a pixel is (0..1 over 16 u)
    cam = nt.nodes.new('ShaderNodeCameraData')
    z_world = math(nt, 'SUBTRACT', CAM_Z, cam.outputs['View Z Depth'])
    behind = math(nt, 'DIVIDE', math(nt, 'SUBTRACT', obj_attr(nt, 'front'), z_world), 16.0, clamp=True)
    geo = nt.nodes.new('ShaderNodeNewGeometry')
    dot = nt.nodes.new('ShaderNodeVectorMath')
    dot.operation = 'DOT_PRODUCT'
    nt.links.new(geo.outputs['Normal'], dot.inputs[0])
    nt.links.new(geo.outputs['Incoming'], dot.inputs[1])
    side = math(nt, 'SUBTRACT', 1.0, dot.outputs['Value'], clamp=True)
    t = math(nt, 'ADD', behind, math(nt, 'MULTIPLY', side, 0.22), clamp=True)
    white = ramp(nt, t, [(0.0, srgb(255, 255, 255)), (0.2, srgb(244, 245, 248)), (1.0, srgb(224, 227, 234))])
    glow = ramp(nt, t, [(0.0, srgb(228, 243, 255)), (0.3, srgb(214, 235, 255)), (0.55, srgb(150, 205, 255)),
                        (0.8, srgb(40, 140, 252)), (1.0, srgb(10, 90, 230))])
    lit = mix(nt, obj_attr(nt, 'glow'), white, glow)
    return mix(nt, obj_attr(nt, 'flat'), lit, (1.0, 1.0, 1.0, 1.0))


def mask_color(nt):
    n = nt.nodes.new('ShaderNodeCombineColor')
    g = obj_attr(nt, 'glow')
    for s in n.inputs:
        nt.links.new(g, s)
    return n.outputs[0]


def id_color(nt):
    """R = which gizmo, G = how far behind its front (same measure the beauty ramps use)."""
    cam = nt.nodes.new('ShaderNodeCameraData')
    z_world = math(nt, 'SUBTRACT', CAM_Z, cam.outputs['View Z Depth'])
    behind = math(nt, 'DIVIDE', math(nt, 'SUBTRACT', obj_attr(nt, 'front'), z_world), 16.0, clamp=True)
    n = nt.nodes.new('ShaderNodeCombineColor')
    nt.links.new(obj_attr(nt, 'gid'), n.inputs[0])
    nt.links.new(behind, n.inputs[1])
    return n.outputs[0]


# ---------------------------------------------------------------- scene ----
def setup_scene(res_x=1920, res_y=1080):
    sc = bpy.context.scene
    try:
        sc.render.engine = 'BLENDER_EEVEE'
    except TypeError:
        sc.render.engine = 'BLENDER_EEVEE_NEXT'
    sc.eevee.taa_render_samples = 24
    sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = res_x, res_y, 100
    sc.render.fps = FPS
    sc.render.film_transparent = True
    sc.render.image_settings.file_format = 'PNG'
    sc.render.image_settings.color_mode = 'RGBA'
    sc.render.image_settings.color_depth = '8'
    sc.view_settings.view_transform = 'Standard'
    sc.view_settings.look = 'None'
    sc.frame_start, sc.frame_end = 0, FRAMES - 1
    cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam'))
    cam.data.type, cam.data.ortho_scale = 'ORTHO', res_x / PX_PER_U
    cam.data.clip_start, cam.data.clip_end = 1, 300
    cam.location = (0, 0, CAM_Z)
    sc.collection.objects.link(cam)
    sc.camera = cam
    return sc


_coords = {}


def front_of(ob, rot):
    """World z of the point nearest the camera for a given orientation."""
    if ob.data.name not in _coords:
        co = np.empty(len(ob.data.vertices) * 3)
        ob.data.vertices.foreach_get('co', co)
        _coords[ob.data.name] = co.reshape(-1, 3)
    return float((_coords[ob.data.name] @ np.array(rot)[2]).max())


def ease(t):
    """Slow start, fast middle, small overshoot and settle (like the original)."""
    if t <= 0:
        return 0.0
    if t >= 1:
        return 1.0
    u = t * t * (3 - 2 * t)
    u = u ** 1.15
    c1 = 1.25
    return 1 + (c1 + 1) * (u - 1) ** 3 + c1 * (u - 1) ** 2


def turn(q0, q1, e):
    """slerp that tolerates e > 1 (the overshoot)."""
    d = q0.inverted() @ q1
    if d.w < 0:
        d.negate()
    axis, angle = d.to_axis_angle()
    return q0 @ Quaternion(axis, angle * e)


def smooth(t):
    t = min(1.0, max(0.0, t))
    return t * t * (3 - 2 * t)


def layout(gizmos):
    """x centre of every slot; the lockup is centred on the frame."""
    widths = [GLYPHS[p[1]][0] for p in PAIRS]
    total = sum(widths) + GAP * (len(widths) - 1)
    x, xs = -total / 2, []
    for w in widths:
        xs.append(x + w / 2)
        x += w + GAP
    return xs


def animate(gizmos, finals):
    xs = layout(gizmos)
    meta = {'fps': FPS, 'frames': FRAMES, 'px_per_u': PX_PER_U, 'waves': WAVES, 't_on': T_ON,
            'stagger': STAGGER, 'spin': SPIN, 'slots': xs}
    meta['states'] = []
    for i, (ob, (kana, latin, *_)) in enumerate(zip(gizmos, PAIRS)):
        states = []
        meta['states'].append(states)
        quats = [ROTS[k].to_quaternion() for k in POSES[kana]]
        assert POSES[kana][0] == 0 and ROTS[POSES[kana][-1]] == finals[i], 'path must run kana -> letter'
        for a, b in zip(quats, quats[1:]):
            if a.dot(b) < 0:
                b.negate()
        kh, lh = GLYPHS[kana][1], GLYPHS[latin][1]
        y0, y1 = (kh - 16) / 2, 0.0          # small kana sits on the baseline
        starts = [w + i * STAGGER for w in WAVES]
        for f in range(FRAMES):
            seg, t = 0, 0.0
            for k, s in enumerate(starts):
                if f >= s:
                    seg, t = k, min(1.0, (f - s) / SPIN)
            q = turn(quats[seg], quats[seg + 1], ease(t))
            ob.rotation_quaternion = q
            y = y0 if seg < 3 else y0 + (y1 - y0) * smooth(t)
            ob.location = (xs[i], y, 0)
            glow = smooth((f - (starts[0] - 1.5)) / GLOW_IN) * (1 - smooth((f - (starts[3] + SPIN - 3.5)) / GLOW_OUT))
            flat = smooth((f - (starts[3] + SPIN - 1.0)) / 4.0)
            ob['glow'], ob['flat'] = glow, flat
            states.append([round(glow, 4), round(flat, 4), [round(v, 5) for v in q] + [round(y, 4)]])
            ob['front'] = front_of(ob, q.to_matrix())
            visible = f >= T_ON
            ob.hide_render = not visible
            ob.keyframe_insert('rotation_quaternion', frame=f)
            ob.keyframe_insert('location', frame=f)
            ob.keyframe_insert('hide_render', frame=f)
            for prop in ('glow', 'flat', 'front'):
                ob.keyframe_insert('["%s"]' % prop, frame=f)
    return meta


def build():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    gizmos, finals = [], []
    for kana, latin, axis, third in PAIRS:
        ob, fin = gizmo(kana, latin, axis, third)
        gizmos.append(ob)
        finals.append(fin)
        print('gizmo', ob.name, len(ob.data.vertices), 'verts')
    beauty = emission_material('beauty', beauty_color)
    mask = emission_material('mask', mask_color)
    for ob in gizmos:
        ob.data.materials.clear()      # baking modifiers leaves an empty slot behind
        ob.data.materials.append(beauty)
    return gizmos, finals, beauty, mask


def poses_sheet(path):
    gizmos, finals, beauty, mask = build()
    cell = 26
    sc = setup_scene(12 * 150, 10 * 150)
    sc.camera.data.ortho_scale = 12 * cell
    sc.render.film_transparent = False
    world = bpy.data.worlds.new('w')
    world.use_nodes = True
    world.node_tree.nodes['Background'].inputs[0].default_value = (0.02, 0.02, 0.03, 1)
    sc.world = world
    for gi, ob in enumerate(gizmos):
        fin = [k for k, r in enumerate(ROTS) if r == finals[gi]]
        print(ob.name, 'final pose index', fin, 'identity index',
              [k for k, r in enumerate(ROTS) if r == Matrix.Identity(3)])
        for k, r in enumerate(ROTS):
            c = ob.copy()
            sc.collection.objects.link(c)
            c.rotation_quaternion = r.to_quaternion()
            c.location = ((k % 12 - 5.5) * cell, (4.5 - (gi * 2 + k // 12)) * cell, 0)
            c['glow'], c['flat'], c['front'] = 0.85, 0.0, front_of(ob, r)
        ob.hide_render = True
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)


def render(out_dir, f0, f1, save=None):
    gizmos, finals, beauty, mask = build()
    sc = setup_scene()
    meta = animate(gizmos, finals)
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, 'meta.json'), 'w') as fh:
        json.dump(meta, fh)
    if save:
        bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(save))
    sc.frame_start, sc.frame_end = f0, f1
    for name, mat in (('beauty', beauty), ('mask', mask)):
        for ob in gizmos:
            ob.data.materials[0] = mat
        sc.render.filepath = os.path.join(out_dir, name + '_')
        bpy.ops.render.render(animation=True)


def id_pass(out_dir, width=1200, height=340, ss=3):
    """Cropped, supersampled, un-antialiased pass that make_svg.py traces into paths."""
    gizmos, finals, beauty, mask = build()
    sc = setup_scene(width * ss, height * ss)
    sc.camera.data.ortho_scale = width / PX_PER_U
    sc.eevee.taa_render_samples = 1
    sc.render.filter_size = 0.01
    sc.render.dither_intensity = 0
    meta = animate(gizmos, finals)
    meta.update(width=width, height=height, ss=ss)
    mat = emission_material('id', id_color)
    for k, ob in enumerate(gizmos):
        ob['gid'] = (k + 1) / 6
        ob.data.materials[0] = mat
    # only frames where something changes
    moving = [f for f in range(T_ON, FRAMES) if f == T_ON or any(s[f] != s[f - 1] for s in meta['states'])]
    meta['first'], meta['last'] = moving[0], moving[-1]
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, 'meta.json'), 'w') as fh:
        json.dump(meta, fh)
    sc.frame_start, sc.frame_end = moving[0], moving[-1]
    sc.render.filepath = os.path.join(out_dir, 'id_')
    bpy.ops.render.render(animation=True)


if __name__ == '__main__':
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    # filled in after looking at the --poses sheet
    POSES.update(json.load(open(os.path.join(HERE, 'poses.json'))) if os.path.exists(os.path.join(HERE, 'poses.json')) else {})
    if '--idpass' in argv:
        id_pass(os.path.abspath(argv[argv.index('--idpass') + 1]))
    elif '--poses' in argv:
        poses_sheet(os.path.abspath(argv[argv.index('--poses') + 1]))
    elif '--render' in argv:
        f0, f1 = 0, FRAMES - 1
        if '--frames' in argv:
            i = argv.index('--frames')
            f0, f1 = int(argv[i + 1]), int(argv[i + 2])
        save = argv[argv.index('--save') + 1] if '--save' in argv else None
        render(os.path.abspath(argv[argv.index('--render') + 1]), f0, f1, save)
