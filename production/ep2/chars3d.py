"""Posable 3D replicas of the series' two characters (built to match characters/*_reference.png).

build_character(kind, pose={}, face={}, loc=(0,0,0), rot_z=0) -> dict with root + hand matrices.
kind: 'bf' (bald, blue tee) or 'gf' (black bob, red tee). Characters face -Y at rot_z=0.
"""
import bpy, bmesh, math
from mathutils import Vector, Matrix, Euler


def srgb_lin(h):
    h = h.lstrip('#'); c = [int(h[i:i+2], 16) / 255 for i in (0, 2, 4)]
    return tuple([x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c] + [1.0])


_mats = {}


def M(name, hexcol, rough=0.6, sss=0.0):
    key = (name, hexcol)
    if key in _mats:
        return _mats[key]
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = srgb_lin(hexcol)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Specular IOR Level'].default_value = 0.25
    _mats[key] = m
    return m


SPEC = {
    'bf': dict(H=1.70, skin='#F9B98C', tee='#1474EE', pants='#22335C', shoes='#4A4B4A', hair=None,
               head_r=0.185, head_z=1.515, neck_r=0.062, torso_w=0.45, torso_d=0.25, torso_z=(0.78, 1.31),
               sh_x=0.205, sh_z=1.235, upper=0.26, fore=0.24, arm_r=0.06, hand=(0.105, 0.055, 0.13),
               hip_x=0.105, hip_z=0.84, thigh=0.38, shin=0.36, leg_r=0.108, shoe=(0.19, 0.30, 0.10),
               eye=(0.031, 0.033), eye_yaw=22, eye_pitch=-4, brow=(0.068, 0.017), brow_pitch=7, brow_yaw=22,
               mouth_w=0.075, mouth_pitch=-33, stroke=0.012),
    'gf': dict(H=1.60, skin='#F7A469', tee='#D42A22', pants='#46424A', shoes='#514A4A', hair='#3A3433',
               head_r=0.158, head_z=1.385, neck_r=0.052, torso_w=0.37, torso_d=0.21, torso_z=(0.75, 1.20),
               sh_x=0.17, sh_z=1.125, upper=0.24, fore=0.22, arm_r=0.052, hand=(0.088, 0.046, 0.11),
               hip_x=0.095, hip_z=0.80, thigh=0.36, shin=0.35, leg_r=0.098, shoe=(0.17, 0.27, 0.09),
               eye=(0.035, 0.05), eye_yaw=24, eye_pitch=-6, brow=(0.066, 0.017), brow_pitch=10, brow_yaw=23,
               mouth_w=0.06, mouth_pitch=-33, stroke=0.011),
}


# ------------------------------------------------------------------ helpers
def _link(o, parent):
    o.parent = parent
    return o


def rbox(name, size, mat, bevel=0.03, segs=4):
    bpy.ops.mesh.primitive_cube_add()
    o = bpy.context.object; o.name = name
    o.scale = (size[0] / 2, size[1] / 2, size[2] / 2); bpy.ops.object.transform_apply(scale=True)
    md = o.modifiers.new('b', 'BEVEL'); md.width = bevel; md.segments = segs; md.limit_method = 'NONE'
    o.data.materials.append(mat); bpy.ops.object.shade_smooth()
    return o


def capsule(name, p0, p1, r0, r1, mat, cap=True):
    """Tapered tube from p0 to p1 with rounded ends."""
    p0, p1 = Vector(p0), Vector(p1); d = p1 - p0; L = d.length
    bpy.ops.mesh.primitive_cone_add(vertices=32, radius1=r0, radius2=r1, depth=L)
    o = bpy.context.object; o.name = name
    o.data.materials.append(mat); bpy.ops.object.shade_smooth()
    o.location = (p0 + p1) / 2
    o.rotation_euler = d.to_track_quat('Z', 'Y').to_euler()
    objs = [o]
    if cap:
        for p, r in ((p0, r0), (p1, r1)):
            bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=r * 0.995, location=p)
            s = bpy.context.object; s.data.materials.append(mat); bpy.ops.object.shade_smooth(); objs.append(s)
    return objs


def dirv(yaw, pitch):
    """Direction in body space from yaw (deg, + = toward character's left/+X) and pitch (deg, + = up), forward = -Y."""
    y, p = math.radians(yaw), math.radians(pitch)
    return Vector((math.sin(y) * math.cos(p), -math.cos(y) * math.cos(p), math.sin(p)))


# ------------------------------------------------------------------ face decals projected onto the head sphere
def face_shape(name, poly, centre_dir, r, centre, mat, roll=0.0, offset=0.0016):
    """poly: list of (u,v) in metres on the tangent plane (u = right on screen, v = up)."""
    n = centre_dir.normalized()
    up = Vector((0, 0, 1))
    t1 = up.cross(n).normalized()
    t2 = n.cross(t1).normalized()
    c, s = math.cos(roll), math.sin(roll)
    bm = bmesh.new()
    vs = [bm.verts.new((u * c - v * s, u * s + v * c, 0)) for u, v in poly]
    bm.faces.new(vs)
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    for _ in range(3):
        bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=1, use_grid_fill=True)
    p0 = Vector(centre) + n * r
    for v in bm.verts:
        u, w = v.co.x, v.co.y
        q = p0 + t1 * u + t2 * w
        q = Vector(centre) + (q - Vector(centre)).normalized() * (r + offset)
        v.co = q
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(o)
    o.data.materials.append(mat)
    md = o.modifiers.new('s', 'SOLIDIFY'); md.thickness = 0.003; md.offset = 1
    return o


def ellipse(w, h, n=40):
    return [(w / 2 * math.cos(2 * math.pi * i / n), h / 2 * math.sin(2 * math.pi * i / n)) for i in range(n)]


def rrect(w, h, n=10):
    r = h / 2; pts = []
    for cx, a0 in ((w / 2 - r, -90), (-(w / 2 - r), 90)):
        for i in range(n + 1):
            a = math.radians(a0 + 180 * i / n); pts.append((cx + r * math.cos(a), r * math.sin(a)))
    return pts


def arc_stroke(w, h, t, up=True, n=24, a0=200, a1=340):
    """Thick arc, like ^ (up=True: hump at top) or a smile (up=False)."""
    pts_o, pts_i = [], []
    for i in range(n + 1):
        a = math.radians(a0 + (a1 - a0) * i / n)
        ox, oy = (w / 2) * math.cos(a), (h / 2) * math.sin(a)
        ix, iy = (w / 2 - t) * math.cos(a), (h / 2 - t) * math.sin(a)
        if up:
            oy, iy = -oy, -iy
        pts_o.append((ox, oy)); pts_i.append((ix, iy))
    # round caps approximated by the polygon closure
    return pts_o + pts_i[::-1]


def build_face(sp, centre, head_yaw_pitch, face, parent, black):
    r = sp['head_r']; hy, hp = head_yaw_pitch
    objs = []
    def at(yaw, pitch):
        return dirv(yaw + hy, pitch + hp)
    eyes = face.get('eyes', 'open')
    ew, eh = sp['eye']
    for side in (-1, 1):
        d = at(side * sp['eye_yaw'], sp['eye_pitch'])
        look = face.get('look', 0.0)   # shift pupils sideways
        if eyes == 'open':
            objs.append(face_shape('eye', ellipse(ew, eh), at(side * sp['eye_yaw'] + look, sp['eye_pitch']), r, centre, black))
        elif eyes == 'half':
            pts = [p for p in ellipse(ew, eh) if p[1] <= eh * 0.08]
            objs.append(face_shape('eye', pts, d, r, centre, black))
            objs.append(face_shape('lid', rrect(ew * 1.25, sp['stroke']), at(side * sp['eye_yaw'], sp['eye_pitch'] + 1.5), r, centre, black))
        elif eyes == 'happy':
            objs.append(face_shape('eye', arc_stroke(ew * 1.5, eh * 1.0, sp['stroke']), at(side * sp['eye_yaw'], sp['eye_pitch'] - 1), r, centre, black))
        elif eyes == 'closed':
            objs.append(face_shape('eye', arc_stroke(ew * 1.5, eh * 0.7, sp['stroke'], up=False), at(side * sp['eye_yaw'], sp['eye_pitch'] + 2), r, centre, black))
        # brows: angle >0 = inner end down (angry); <0 = inner end up (worried)
        if face.get('brows', True):
            ang = face.get('brow_' + ('R' if side < 0 else 'L'), face.get('brow', 12))
            lift = face.get('brow_lift', 0) + (face.get('brow_lift_' + ('R' if side < 0 else 'L'), 0))
            bw, bh = sp['brow']
            if face.get('arched'):
                objs.append(face_shape('brow', arc_stroke(bw * 1.1, bw * 0.55, bh * 0.85), at(side * sp['brow_yaw'], sp['brow_pitch'] + 2 + lift), r, centre, black))
            else:
                roll = math.radians(ang) * (-1 if side < 0 else 1)
                objs.append(face_shape('brow', rrect(bw, bh), at(side * sp['brow_yaw'], sp['brow_pitch'] + lift), r, centre, black, roll=roll))
    mouth = face.get('mouth', 'flat'); mw = sp['mouth_w']; st = sp['stroke']
    md = at(face.get('mouth_yaw', 0), sp['mouth_pitch'])
    if mouth == 'flat':
        objs.append(face_shape('mouth', rrect(mw, st * 0.95), md, r, centre, black, roll=math.radians(face.get('mouth_tilt', 0))))
    elif mouth == 'frown':
        objs.append(face_shape('mouth', arc_stroke(mw * 1.05, mw * 0.32, st * 0.95), md, r, centre, black))
    elif mouth == 'smile':
        objs.append(face_shape('mouth', arc_stroke(mw * 1.05, mw * 0.6, st, up=False), at(0, sp['mouth_pitch'] + 3), r, centre, black))
    elif mouth == 'bigsmile':
        pts = [p for p in ellipse(mw * 1.1, mw * 0.8) if p[1] <= 0.0005]
        objs.append(face_shape('mouth', pts, at(0, sp['mouth_pitch'] + 4), r, centre, black))
    elif mouth == 'o':
        objs.append(face_shape('mouth', ellipse(mw * 0.32, mw * 0.42), at(0, sp['mouth_pitch'] - 1), r, centre, black))
    elif mouth == 'smirk':
        objs.append(face_shape('mouth', arc_stroke(mw * 0.9, mw * 0.3, st, up=False, a0=200, a1=300), md, r, centre, black))
    elif mouth == 'wavy':
        pts_o = []; pts_i = []
        for i in range(25):
            u = -mw / 2 + mw * i / 24; v = 0.006 * math.sin(i / 24 * 2 * math.pi * 1.5)
            pts_o.append((u, v + st / 2)); pts_i.append((u, v - st / 2))
        objs.append(face_shape('mouth', pts_o + pts_i[::-1], md, r, centre, black))
    for o in objs:
        o.parent = parent
    return objs


# ------------------------------------------------------------------ hair (gf)
def build_hair(sp, centre, mat):
    c = Vector(centre); r = sp['head_r']
    pieces = []
    def ico(rad, loc, scale):
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=rad, location=loc)
        o = bpy.context.object; o.scale = scale; bpy.ops.object.transform_apply(scale=True)
        o.data.materials.append(mat); bpy.ops.object.shade_flat(); return o
    top = ico(r * 1.2, c + Vector((0.0, 0.03, 0.03)), (1.36, 1.06, 1.0))
    bpy.ops.mesh.primitive_cube_add(location=c + Vector((0.0, 0.045, -0.10)))
    curtain = bpy.context.object; curtain.scale = (r * 1.6, r * 0.95, r * 1.2)
    bpy.ops.object.transform_apply(scale=True)
    bv = curtain.modifiers.new('bv', 'BEVEL'); bv.width = r * 0.45; bv.segments = 2
    bpy.context.view_layer.objects.active = curtain; bpy.ops.object.modifier_apply(modifier='bv')
    curtain.data.materials.append(mat)
    def apply_bool(target, cutter, op):
        md = target.modifiers.new('bo', 'BOOLEAN'); md.operation = op; md.object = cutter; md.solver = 'EXACT'
        bpy.context.view_layer.objects.active = target; bpy.ops.object.modifier_apply(modifier='bo')
        bpy.data.objects.remove(cutter, do_unlink=True)
    apply_bool(top, curtain, 'UNION'); hair = top
    # face window: everything in front of the face, under a diagonal fringe line (fringe on her right = screen-left)
    bpy.ops.mesh.primitive_cube_add(location=c + Vector((0.012, -0.28, -0.13)))
    win = bpy.context.object; win.scale = (0.128, 0.3, 0.19); win.rotation_euler = (0, math.radians(-13), 0)
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    bv = win.modifiers.new('bv', 'BEVEL'); bv.width = 0.05; bv.segments = 3
    bpy.context.view_layer.objects.active = win; bpy.ops.object.modifier_apply(modifier='bv')
    apply_bool(hair, win, 'DIFFERENCE')
    bpy.context.view_layer.objects.active = hair
    bpy.ops.object.shade_flat()
    return hair


# ------------------------------------------------------------------ main builder
DEFAULT_POSE = dict(
    armR=((-90, -76), (-90, -82)), armL=((90, -76), (90, -82)),   # (upper yaw,pitch), (fore yaw,pitch) — hanging
    handR=0, handL=0,             # hand roll degrees
    legs='stand', head=(0, 0), lean=0, hand_shape=('fist', 'fist'),
)


def build_character(kind, pose=None, face=None, loc=(0, 0, 0), rot_z=0.0, name=None, override=None):
    sp = dict(SPEC[kind], **(override or {})); pose = dict(DEFAULT_POSE, **(pose or {})); face = face or {}
    root = bpy.data.objects.new(name or kind, None); bpy.context.collection.objects.link(root)
    skin = M(kind + 'skin', sp['skin'], 0.55); tee = M(kind + 'tee', sp['tee'], 0.8)
    pants = M(kind + 'pants', sp['pants'], 0.85); shoes = M(kind + 'shoes', sp['shoes'], 0.6)
    black = M('ink', '#141416', 0.35)
    parts = []
    sitting = pose['legs'] in ('sit', 'drive')
    hip_z = sp['hip_z']
    # ---------------- legs
    for side in (-1, 1):
        hx = side * sp['hip_x']
        hip = Vector((hx, 0, hip_z))
        if pose['legs'] == 'stand':
            knee = hip + Vector((0, 0, -sp['thigh'])); ankle = knee + Vector((0, 0, -sp['shin']))
        elif pose['legs'] == 'walk':
            a = math.radians(22 * side)
            knee = hip + Vector((0, -math.sin(a) * sp['thigh'], -math.cos(a) * sp['thigh']))
            b = math.radians(22 * side - (12 if side > 0 else -4))
            ankle = knee + Vector((0, -math.sin(b) * sp['shin'], -math.cos(b) * sp['shin']))
        else:  # sit: thighs forward, shins down
            knee = hip + Vector((side * 0.02, -sp['thigh'], 0.0)); ankle = knee + Vector((0, 0.03, -sp['shin']))
        lr = sp['leg_r']
        if pose['legs'] == 'stand':
            parts += capsule('leg', hip, ankle + Vector((0, 0, 0.03)), lr * 1.03, lr * 0.98, pants)
        else:
            parts += capsule('thigh', hip, knee, lr * 1.04, lr, pants)
            parts += capsule('shin', knee, ankle + Vector((0, 0, 0.03)), lr, lr * 0.97, pants)
        sh = rbox('shoe', sp['shoe'], shoes, 0.045)
        sh.location = ankle + Vector((0, -sp['shoe'][1] * 0.22, -sp['shoe'][2] * 0.35)); parts.append(sh)
    # pelvis
    pel = rbox('pelvis', (2 * (sp['hip_x'] + sp['leg_r']) * 0.98, sp['torso_d'] * 0.92, 0.24), pants, 0.08)
    pel.location = (0, 0, hip_z + 0.0); parts.append(pel)
    # ---------------- torso (tee), slightly tapered box
    tz0, tz1 = sp['torso_z']
    tor = rbox('torso', (sp['torso_w'], sp['torso_d'], tz1 - tz0), tee, 0.09, 6)
    tor.location = (0, 0, (tz0 + tz1) / 2); parts.append(tor)
    if kind == 'gf':  # scoop neckline: skin patch at the top front
        bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=0.045, location=(0, -sp['torso_d'] / 2 + 0.01, tz1 - 0.02))
        nk = bpy.context.object; nk.scale = (1.7, 0.3, 0.55); nk.data.materials.append(skin); bpy.ops.object.shade_smooth(); parts.append(nk)
    # neck + head
    parts += capsule('neck', (0, 0.0, tz1 - 0.04), (0, 0.0, sp['head_z'] - sp['head_r'] * 0.6), sp['neck_r'], sp['neck_r'], skin, cap=False)
    hc = Vector((0, 0, sp['head_z']))
    bpy.ops.mesh.primitive_uv_sphere_add(segments=64, ring_count=32, radius=sp['head_r'], location=hc)
    head = bpy.context.object; head.name = 'head'; head.data.materials.append(skin); bpy.ops.object.shade_smooth()
    if kind == 'gf':
        head.scale = (0.98, 0.98, 1.04)
    parts.append(head)
    hy, hp = pose['head']
    face_objs = build_face(sp, hc, (hy, hp), face, None, black)
    hair = build_hair(sp, hc, M('hair', sp['hair'], 0.7)) if sp['hair'] else None
    head_group = [head] + face_objs + ([hair] if hair else [])
    # head yaw/pitch: rotate the head group about the neck point
    if hy or hp:
        pivot = Vector((0, 0, sp['head_z'] - sp['head_r'] * 0.7))
        R = (Matrix.Rotation(math.radians(hy), 4, 'Z') @ Matrix.Rotation(math.radians(-hp) * 0.0, 4, 'X'))
        for o in [head] + ([hair] if hair else []):
            o.matrix_world = Matrix.Translation(pivot) @ R @ Matrix.Translation(-pivot) @ o.matrix_world
        # face decals were already placed with the yaw/pitch baked in; rotate only the hair/head for yaw
        for o in face_objs:
            pass
    parts += head_group
    # ---------------- arms
    hands = {}
    for side, key in ((-1, 'R'), (1, 'L')):
        (uy, up_), (fy, fp) = pose['arm' + key]
        # pose yaw is given for the character's right arm mirrored automatically for left when using same numbers
        sh_pt = Vector((side * (sp['torso_w'] / 2 - sp['arm_r'] * 0.6), 0.0, sp['torso_z'][1] - sp['arm_r'] * 1.6))
        d1 = dirv(uy, up_); d2 = dirv(fy, fp)
        el = sh_pt + d1 * sp['upper']; wr = el + d2 * sp['fore']
        ar = sp['arm_r']
        parts += capsule('upper', sh_pt, el, ar * 1.05, ar, skin)
        parts += capsule('fore', el, wr, ar, ar * 0.92, skin)
        # sleeve: short tube over the top of the upper arm
        sl_end = sh_pt + d1 * (sp['upper'] * 0.48)
        parts += capsule('sleeve', sh_pt + d1 * (-0.035), sl_end, ar * 1.38, ar * 1.42, tee, cap=False)
        bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=ar * 1.36, location=sh_pt + d1 * (-0.035))
        s = bpy.context.object; s.scale = (1, 1, 0.8); s.data.materials.append(tee); bpy.ops.object.shade_smooth(); parts.append(s)
        # hand: rounded box aligned with forearm, plus a thumb
        hw, hd, hh = sp['hand']
        hd_obj = rbox('hand', (hw, hd, hh), skin, 0.02)
        roll = math.radians(pose['hand' + key])
        z = (-d2).normalized()
        ref = Vector((1, 0, 0)) if abs(z.x) < 0.9 else Vector((0, 0, 1))
        x = z.cross(ref).normalized(); y = z.cross(x).normalized()
        rot = Matrix((x, y, z)).transposed().to_4x4() @ Matrix.Rotation(roll, 4, 'Z')
        center = wr + d2 * (hh * 0.45)
        hd_obj.matrix_world = Matrix.Translation(center) @ rot; parts.append(hd_obj)
        th = capsule('thumb', (0, 0, 0), (0, 0, -hh * 0.3), hd * 0.4, hd * 0.36, skin)
        for o in th:
            o.matrix_world = Matrix.Translation(center) @ rot @ Matrix.Translation((-side * hw * 0.42, -hd * 0.15, hh * 0.18)) @ Matrix.Rotation(math.radians(side * 12), 4, 'Y') @ o.matrix_world
        parts += th
        hands[key] = Matrix.Translation(wr + d2 * (hh * 0.55)) @ rot
    for o in parts:
        if o.parent is None:
            o.parent = root
    root.location = loc; root.rotation_euler = (0, 0, rot_z)
    if sitting:
        pass
    bpy.context.view_layer.update()
    return dict(root=root, hands={k: root.matrix_world @ v for k, v in hands.items()}, spec=sp)
