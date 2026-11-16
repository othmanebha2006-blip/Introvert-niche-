"""Episode 2 ("I'll plan the date this time"): sets, props and every shot, rendered with Blender/Cycles.
Usage: python3 scene2.py -- <workdir> [shot ids...]   (no ids = all)
"""
import bpy, math, sys, os, random
from mathutils import Vector, Matrix

S = sys.argv[sys.argv.index('--') + 1]
ONLY = sys.argv[sys.argv.index('--') + 2:]
sys.path.insert(0, S)
import chars3d as C

TEX = os.path.join(S, 'tex'); OUT = os.path.join(S, 'renders2'); os.makedirs(OUT, exist_ok=True)
SAMP = int(os.environ.get('SAMP', '40')); PCT = int(os.environ.get('PCT', '100'))


def lin(h):
    return C.srgb_lin(h)


def reset(night=False):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    C._mats.clear()
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = SAMP; sc.cycles.use_denoising = True
    sc.cycles.max_bounces = 6
    sc.render.resolution_x = 1080; sc.render.resolution_y = 1920; sc.render.resolution_percentage = PCT
    sc.view_settings.view_transform = 'Standard'; sc.view_settings.exposure = -0.6 if not night else 0.0
    w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True
    bg = w.node_tree.nodes['Background']
    bg.inputs[0].default_value = lin('#C8D4E6') if not night else lin('#0B1230')
    bg.inputs[1].default_value = 0.25 if not night else 0.35
    return sc


def mat(name, color, rough=0.75, img=None, emit=0.0, alpha=None):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = lin(color); b.inputs['Roughness'].default_value = rough
    if img:
        t = m.node_tree.nodes.new('ShaderNodeTexImage'); t.image = bpy.data.images.load(img)
        m.node_tree.links.new(t.outputs[0], b.inputs['Base Color'])
        if emit:
            m.node_tree.links.new(t.outputs[0], b.inputs['Emission Color']); b.inputs['Emission Strength'].default_value = emit
    elif emit:
        b.inputs['Emission Color'].default_value = lin(color); b.inputs['Emission Strength'].default_value = emit
    if alpha is not None:
        b.inputs['Transmission Weight'].default_value = 1.0; b.inputs['Roughness'].default_value = 0.05
        b.inputs['Base Color'].default_value = lin(color)
    return m


def box(name, loc, size, m, bevel=0.03, segs=3, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(location=loc, rotation=rot)
    o = bpy.context.object; o.name = name; o.scale = (size[0] / 2, size[1] / 2, size[2] / 2)
    bpy.ops.object.transform_apply(scale=True)
    if bevel:
        md = o.modifiers.new('b', 'BEVEL'); md.width = bevel; md.segments = segs
    o.data.materials.append(m); bpy.ops.object.shade_smooth()
    return o


def cyl(name, loc, r, h, m, verts=48, bevel=0.01, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=h, location=loc, rotation=rot)
    o = bpy.context.object; o.name = name
    if bevel:
        md = o.modifiers.new('b', 'BEVEL'); md.width = bevel; md.segments = 3
    o.data.materials.append(m); bpy.ops.object.shade_smooth()
    return o


def plane(name, loc, size, m, rot=(math.pi / 2, 0, 0)):
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc, rotation=rot)
    o = bpy.context.object; o.name = name; o.scale = (size[0], size[1], 1); o.data.materials.append(m)
    return o


def cam(loc, target, lens=35, dof=None):
    bpy.ops.object.camera_add(location=loc); c = bpy.context.object
    c.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    c.data.lens = lens; c.data.sensor_fit = 'VERTICAL'; c.data.sensor_height = 24
    if dof:
        c.data.dof.use_dof = True; c.data.dof.focus_distance = dof[0]; c.data.dof.aperture_fstop = dof[1]
    bpy.context.scene.camera = c
    return c


def area(loc, target, energy, size, color='#FFFFFF'):
    bpy.ops.object.light_add(type='AREA', location=loc); l = bpy.context.object
    l.data.energy = energy; l.data.size = size; l.data.color = lin(color)[:3]
    l.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    return l


def point(loc, energy, color='#FFFFFF', size=0.1):
    bpy.ops.object.light_add(type='POINT', location=loc); l = bpy.context.object
    l.data.energy = energy; l.data.color = lin(color)[:3]; l.data.shadow_soft_size = size
    return l


# ================================================================== sets
SOFA_X = 0.3


def living_room_details():
    sx = SOFA_X
    # throw pillows + blanket
    for x, c, rz in ((sx - 1.05, '#E8A33D', 12), (sx + 1.05, '#F1E6D2', -14), (sx + 0.75, '#C8553D', -6)):
        box('pillow', (x, 1.6, 0.66), (0.42, 0.14, 0.38), mat('pil' + c, c, 0.95), 0.08, 4, rot=(math.radians(-12), 0, math.radians(rz)))
    box('blanket', (sx + 1.43, 1.35, 0.72), (0.27, 0.7, 0.05), mat('blank', '#7FA88B', 0.95), 0.02)
    # bookshelf on the right
    bx = sx + 2.45; wood2 = mat('shelfw', '#8E5A33', 0.6)
    box('shelf', (bx, 1.82, 1.05), (0.95, 0.35, 2.1), wood2, 0.02)
    random.seed(7)
    cols = ['#C8553D', '#3E7CB1', '#F2C14E', '#5B8E7D', '#E8E1D5', '#7C4D8B', '#2F3E46']
    for row in range(4):
        z = 0.18 + row * 0.5
        box('board', (bx, 1.66, z - 0.02), (0.88, 0.32, 0.03), wood2, 0.005)
        x = bx - 0.4
        while x < bx + 0.35:
            w = random.uniform(0.04, 0.08); h = random.uniform(0.26, 0.38)
            box('book', (x + w / 2, 1.66, z + h / 2), (w, 0.24, h), mat('bk%d%d' % (row, int(x * 100)), random.choice(cols), 0.7), 0.004)
            x += w + 0.005
    cyl('vase', (bx + 0.25, 1.66, 2.05), 0.07, 0.22, mat('vase', '#E9E2D6', 0.4))
    # wall clock + small shelf with plant on the left
    cyl('clock', (sx - 2.0, 1.97, 2.25), 0.2, 0.05, mat('clock', '#F7F3EA', 0.5), 48, 0.01, (math.pi / 2, 0, 0))
    cyl('clockrim', (sx - 2.0, 1.985, 2.25), 0.215, 0.03, mat('rim', '#2F3E46', 0.4), 48, 0.005, (math.pi / 2, 0, 0))
    box('hand1', (sx - 2.0, 1.94, 2.3), (0.02, 0.01, 0.12), mat('hnd', '#2F3E46', 0.4), 0.0)
    box('hand2', (sx - 1.95, 1.94, 2.25), (0.1, 0.01, 0.02), mat('hnd2', '#2F3E46', 0.4), 0.0)
    # coffee-table props
    cyl('mug', (SOFA_X - 0.45, -0.55, 0.48), 0.05, 0.1, mat('mug', '#E8A33D', 0.4), 32, 0.008)
    box('remote', (SOFA_X + 0.35, -0.6, 0.445), (0.18, 0.05, 0.02), mat('remote', '#222326', 0.5), 0.008, rot=(0, 0, math.radians(20)))
    box('magazine', (SOFA_X + 0.0, -0.45, 0.442), (0.32, 0.24, 0.012), mat('mag', '#3E7CB1', 0.7), 0.003, rot=(0, 0, math.radians(-12)))


def living_room():
    sc = reset()
    wall = mat('wall', '#8FB3E0', 0.9); floor = mat('floor', '#C9A27A', 0.6)
    sofa = mat('sofa', '#2F4E8C', 0.95); wood = mat('wood', '#B46528', 0.55)
    rug = mat('rug', '#EADCC8', 1.0); white = mat('white', '#F2F0EC', 0.6); leg = mat('leg', '#6B4A2E', 0.6)
    shade = mat('shade', '#FFF1D0', 0.8, emit=1.2)
    art = mat('art', '#FFFFFF', 0.55, img=os.path.join(TEX, 'painting_inner.png'))
    box('floor', (0, 0, -0.05), (16, 16, 0.1), floor, 0)
    box('wall', (0, 2.05, 4), (16, 0.1, 8.2), wall, 0)
    box('wallL', (-4.2, 0, 4), (0.1, 16, 8.2), wall, 0)
    box('skirting', (0, 1.98, 0.06), (16, 0.04, 0.12), white, 0.005)
    box('rug', (SOFA_X, 0.3, 0.01), (4.2, 2.9, 0.03), mat('rugtex', '#FFFFFF', 1.0, img=os.path.join(TEX, 'rug.png')), 0.012)
    living_room_details()
    sx = SOFA_X
    box('sofa_base', (sx, 1.45, 0.22), (2.7, 0.95, 0.30), sofa, 0.06)
    box('sofa_back', (sx, 1.82, 0.62), (2.7, 0.26, 0.9), sofa, 0.08)
    for i in range(3):
        box(f'cush{i}', (sx - 0.86 + i * 0.86, 1.38, 0.43), (0.84, 0.8, 0.14), sofa, 0.06)
        box(f'bcush{i}', (sx - 0.86 + i * 0.86, 1.66, 0.76), (0.8, 0.18, 0.5), sofa, 0.07)
    for s in (-1, 1):
        box(f'arm{s}', (sx + s * 1.43, 1.45, 0.4), (0.24, 0.95, 0.6), sofa, 0.08)
    for x in (sx - 1.4, sx + 1.4):
        for y in (1.05, 1.85):
            box('leg', (x, y, 0.035), (0.07, 0.07, 0.07), leg, 0.01)
    # wooden frame + mat + the user's painting (identical in every shot)
    fz = 2.15; aw, ah = 1.56, 1.0
    box('frame', (sx, 1.98, fz), (aw + 0.34, 0.05, ah + 0.34), wood, 0.012)
    box('mat', (sx, 1.955, fz), (aw + 0.16, 0.02, ah + 0.16), white, 0.004)
    plane('art', (sx, 1.944, fz), (aw, ah), art)
    lx = sx - 2.05
    box('table', (lx, 1.6, 0.58), (0.55, 0.55, 0.05), wood, 0.01)
    for dx in (-0.22, 0.22):
        for dy in (-0.22, 0.22):
            box('tleg', (lx + dx, 1.6 + dy, 0.28), (0.04, 0.04, 0.56), wood, 0.005)
    cyl('lampbase', (lx, 1.6, 0.66), 0.1, 0.1, wood); cyl('lampstem', (lx, 1.6, 0.85), 0.025, 0.35, wood, 16)
    bpy.ops.mesh.primitive_cone_add(vertices=48, radius1=0.24, radius2=0.16, depth=0.3, location=(lx, 1.6, 1.15))
    o = bpy.context.object; o.data.materials.append(shade); bpy.ops.object.shade_smooth()
    point((lx, 1.6, 1.12), 140, '#FFB866', 0.15)
    dx_ = -3.3
    box('doorframe', (dx_, 1.98, 1.05), (1.05, 0.06, 2.15), white, 0.01)
    box('door', (dx_, 1.95, 1.02), (0.9, 0.05, 2.0), mat('door', '#F7F5F0', 0.5), 0.01)
    cyl('knob', (dx_ + 0.33, 1.9, 1.0), 0.035, 0.06, mat('knob', '#C9A64B', 0.3), 24, 0.005, (math.pi / 2, 0, 0))
    px = sx + 2.1
    cyl('pot', (px, 1.6, 0.22), 0.2, 0.44, mat('pot', '#E9E2D6', 0.6))
    for i, (ox, oy, h) in enumerate([(0, 0, 0.9), (0.1, 0.05, 0.75), (-0.1, -0.03, 0.8)]):
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=0.22, location=(px + ox, 1.6 + oy, 0.44 + h * 0.6))
        bpy.context.object.data.materials.append(mat(f'leaf{i}', '#4E8F5A', 0.8))
    # coffee table (foreground)
    ctw = mat('ctwood', '#C27A3E', 0.5); cy = -0.55
    box('ct_top', (sx, cy, 0.40), (1.9, 0.8, 0.07), ctw, 0.02)
    for ddx in (-0.85, 0.85):
        for ddy in (-0.32, 0.32):
            box('ct_leg', (sx + ddx, cy + ddy, 0.18), (0.08, 0.08, 0.36), ctw, 0.01)
    area((1.5, -3.2, 3.2), (0.3, 1.2, 0.8), 230, 4.0, '#FFF4E6')
    area((-3.5, -1.2, 2.5), (0, 1.2, 1), 90, 3.0, '#FFD9A8')
    area((2.8, 0.5, 2.6), (0.3, 1.5, 1.0), 40, 2.0, '#C9DBFF')
    return sc


def car_interior(night_outside='city'):
    sc = reset(night=True)
    sc.view_settings.exposure = 0.2
    seat = mat('seat', '#3D4049', 0.9); trim = mat('trim', '#2A2C33', 0.8); dash = mat('dash', '#24262C', 0.7)
    glass = mat('glass', '#9FB4D0', alpha=True)
    box('floor', (0, 0.2, 0.05), (1.6, 2.6, 0.1), trim, 0.02)
    for x in (-0.36, 0.36):
        box('seat', (x, 0.15, 0.36), (0.55, 0.55, 0.16), seat, 0.07)
        bk = box('back', (x, 0.45, 0.78), (0.55, 0.16, 0.8), seat, 0.08, rot=(math.radians(-10), 0, 0))
        box('headrest', (x, 0.52, 1.32), (0.3, 0.12, 0.2), seat, 0.05)
    box('console', (0, 0.0, 0.42), (0.2, 0.7, 0.2), trim, 0.04)
    box('rearbench', (0, 1.3, 0.55), (1.5, 0.5, 0.25), seat, 0.07)
    box('rearback', (0, 1.55, 0.95), (1.5, 0.18, 0.75), seat, 0.08)
    box('roof', (0, 0.4, 1.62), (1.7, 2.8, 0.06), trim, 0.03)
    for s in (-1, 1):
        box('door', (s * 0.85, 0.3, 0.55), (0.06, 2.0, 0.6), trim, 0.02)
        box('pillar', (s * 0.82, 1.65, 1.2), (0.08, 0.1, 0.8), trim, 0.02)
        plane('sidewin', (s * 0.86, 0.3, 1.18), (2.0, 0.62), glass, rot=(math.pi / 2, 0, math.pi / 2))
    plane('rearwin', (0, 1.72, 1.22), (1.4, 0.55), glass)
    # dashboard + steering wheel (driver = +X = image right)
    box('dash', (0, -0.95, 0.85), (1.7, 0.45, 0.32), dash, 0.08)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.19, minor_radius=0.025, location=(0.36, -0.58, 0.98), rotation=(math.radians(62), 0, 0))
    bpy.context.object.data.materials.append(mat('wheel', '#1A1B1F', 0.5))
    cyl('column', (0.36, -0.72, 0.9), 0.03, 0.3, trim, 16, 0.0, (math.radians(62), 0, 0))
    # outside: night city lights behind
    world_out = mat('outdark', '#0E1530', 0.9)
    plane('backdrop', (0, 9, 2), (30, 10), world_out)
    random.seed(4)
    for i in range(60):
        x = random.uniform(-8, 8); z = random.uniform(0.6, 4.5)
        col = random.choice(['#FFD27A', '#FFE9B5', '#9BC6FF', '#FF9E6E'])
        plane('lightdot', (x, 8.9, z), (random.uniform(0.08, 0.3), random.uniform(0.08, 0.25)), mat(f'ld{i}', col, emit=3.0))
    # lighting: dashboard glow + streetlight from the side + soft fill
    area((0, -1.4, 1.2), (0, 0.3, 1.1), 55, 1.2, '#BFD3FF')
    area((-2.5, 0.2, 2.2), (0, 0.3, 1.0), 120, 1.0, '#FFB46B')
    area((1.6, -1.2, 1.8), (0, 0.4, 1.0), 25, 1.5, '#9FB8FF')
    return sc


def store_front():
    sc = reset(night=True); sc.view_settings.exposure = 0.1
    box('street', (0, -2, -0.05), (20, 12, 0.1), mat('asphalt', '#2B2D33', 0.9), 0)
    box('sidewalk', (0, 0.6, 0.06), (20, 3.0, 0.12), mat('walk', '#8C8A86', 0.9), 0.01)
    fac = mat('facade', '#B9A48C', 0.9)
    # facade pieces around the window opening (x -1.5..1.9, z 0.4..2.3)
    box('facL', (-3.0, 2.3, 2.2), (3.0, 0.3, 4.4), fac, 0.0)
    box('facR', (3.2, 2.3, 2.2), (2.6, 0.3, 4.4), fac, 0.0)
    box('facT', (0.2, 2.3, 3.35), (3.4, 0.3, 2.1), fac, 0.0)
    box('facB', (0.2, 2.3, 0.2), (3.4, 0.3, 0.4), fac, 0.0)
    box('shopfloor', (0.2, 3.2, 0.39), (3.4, 2.0, 0.02), mat('shopfl', '#B89B7A', 0.8), 0.0)
    # window with warm interior + mattress
    wf = mat('wframe', '#2E2F35', 0.6)
    box('wfT', (0.2, 2.13, 2.27), (3.45, 0.1, 0.08), wf, 0.01); box('wfB', (0.2, 2.13, 0.43), (3.45, 0.1, 0.08), wf, 0.01)
    box('wfL', (-1.5, 2.13, 1.35), (0.08, 0.1, 1.9), wf, 0.01); box('wfR', (1.9, 2.13, 1.35), (0.08, 0.1, 1.9), wf, 0.01)
    box('wfM', (0.2, 2.13, 1.35), (0.05, 0.08, 1.9), wf, 0.01)
    plane('interior', (0.2, 4.1, 1.6), (3.6, 2.6), mat('intwall', '#E9D9B8', 0.9, emit=0.5))
    box('mattress', (0.3, 2.9, 0.62), (1.9, 1.1, 0.3), mat('matt', '#F3F1EE', 0.85), 0.08, 4, rot=(0, math.radians(0), 0))
    box('mattband', (0.3, 2.9, 0.62), (1.92, 1.12, 0.06), mat('mband', '#7CA6D8', 0.8), 0.02)
    box('door', (-2.3, 2.12, 1.1), (1.0, 0.06, 2.2), mat('sdoor', '#3B3D44', 0.6), 0.01)
    plane('closed', (-2.3, 2.08, 1.45), (0.5, 0.25), mat('closed', '#FFFFFF', 0.6, img=os.path.join(TEX, 'sign_closed.png'), emit=0.6))
    box('signbox', (0.2, 2.1, 3.0), (4.2, 0.12, 0.8), mat('signb', '#1E2856', 0.6), 0.02)
    plane('sign', (0.2, 2.03, 3.0), (4.0, 0.72), mat('sign', '#FFFFFF', 0.5, img=os.path.join(TEX, 'sign_mattress.png'), emit=2.2))
    point((0.2, 3.2, 2.0), 160, '#FFD9A0', 0.5)
    # streetlight
    cyl('pole', (3.6, 0.2, 2.2), 0.05, 4.4, mat('pole', '#3A3C42', 0.5), 16)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.18, location=(3.3, 0.2, 4.35)); bpy.context.object.data.materials.append(mat('bulb', '#FFE3B0', emit=8))
    point((3.3, 0.0, 4.2), 900, '#FFC98A', 0.4)
    area((0, -5, 3), (0, 1, 1.2), 120, 6, '#8FA8FF')
    return sc


def stars(n=220, seed=2):
    random.seed(seed)
    for i in range(n):
        a = random.uniform(-1.2, 1.2); e = random.uniform(0.15, 1.2); d = 40
        loc = (d * math.sin(a) * math.cos(e), d * math.cos(a) * math.cos(e) + 5, d * math.sin(e))
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=random.uniform(0.05, 0.13), location=loc)
        bpy.context.object.data.materials.append(STAR)


STAR = None


def gas_station(with_car=False):
    global STAR
    sc = reset(night=True); sc.view_settings.exposure = -0.55
    STAR = mat('star', '#FFFFFF', emit=12)
    box('ground', (0, 2, -0.05), (40, 40, 0.1), mat('asphalt', '#33353B', 0.9), 0)
    box('island', (0, 2.0, 0.08), (4.2, 0.9, 0.16), mat('curb', '#B8B5AE', 0.8), 0.02)
    canopy_under = mat('canopyU', '#FFF6E8', 0.5, emit=0.3)
    box('canopy', (0, 2.0, 4.2), (9, 5, 0.5), mat('canopy', '#EDEDED', 0.6), 0.03)
    plane('canopy_lights', (0, 2.0, 3.94), (8.6, 4.6), canopy_under, rot=(0, 0, 0))
    box('canopy_band', (0, -0.52, 4.2), (9.02, 0.04, 0.5), mat('band', '#D42A22', 0.5), 0.0)
    for x in (-3.8, 3.8):
        box('pillar', (x, 2.0, 2.0), (0.3, 0.3, 4.0), mat('pil', '#DADAD6', 0.6), 0.02)
    pump = mat('pump', '#D42A22', 0.5); pumpw = mat('pumpw', '#F2F2F2', 0.5)
    for x in (-1.2, 1.2):
        box('pump', (x, 2.0, 0.95), (0.6, 0.4, 1.6), pumpw, 0.04)
        box('pumptop', (x, 2.0, 1.6), (0.62, 0.42, 0.3), pump, 0.04)
        plane('screen', (x, 1.79, 1.15), (0.28, 0.2), mat('pscr', '#66D18A', emit=1.5))
    # convenience store behind
    box('shop', (0, 9, 1.6), (10, 3, 3.2), mat('shop', '#D9D2C4', 0.9), 0.02)
    plane('shopwin', (0, 7.48, 1.3), (6, 1.4), mat('shopwin', '#FFE9B0', emit=2.0))
    plane('gassign', (0, -0.55, 4.2), (2.6, 0.46), mat('gassign', '#FFFFFF', 0.5, img=os.path.join(TEX, 'sign_gas.png'), emit=1.5))
    area((0, 2.0, 3.9), (0, 2.0, 0), 380, 6.0, '#F4F7FF')
    area((0, -6, 3), (0, 2, 1), 80, 6, '#7C93E0')
    stars()
    return sc


def truck(loc, rot_z=0):
    bodym = mat('truck', '#6E8B5C', 0.6); win = mat('twin', '#1B2333', 0.2); tire = mat('tire', '#1A1A1C', 0.9)
    objs = []
    objs.append(box('cab', (0, 0.0, 1.15), (1.9, 1.5, 1.0), bodym, 0.12))
    objs.append(box('hood', (0, -1.2, 0.95), (1.9, 1.0, 0.6), bodym, 0.1))
    objs.append(box('bed', (0, 1.6, 0.85), (1.9, 1.8, 0.55), bodym, 0.06))
    objs.append(box('lower', (0, 0.2, 0.55), (1.95, 4.2, 0.4), bodym, 0.08))
    objs.append(box('wind', (0, -0.76, 1.32), (1.7, 0.04, 0.55), win, 0.02))
    for s in (-1, 1):
        objs.append(box('sidew', (s * 0.96, 0.0, 1.35), (0.04, 1.2, 0.5), win, 0.02))
        for y in (-1.15, 1.5):
            objs.append(cyl('tire', (s * 0.92, y, 0.38), 0.38, 0.3, tire, 32, 0.04, (0, math.pi / 2, 0)))
    root = bpy.data.objects.new('truck', None); bpy.context.collection.objects.link(root)
    for o in objs:
        o.parent = root
    root.location = loc; root.rotation_euler = (0, 0, rot_z)
    return root


# ================================================================== props
def attach(obj_list, hand_mat, offset=(0, 0, 0), rot=(0, 0, 0)):
    M_ = hand_mat @ Matrix.Translation(offset) @ Matrix.Rotation(rot[0], 4, 'X') @ Matrix.Rotation(rot[1], 4, 'Y') @ Matrix.Rotation(rot[2], 4, 'Z')
    root = bpy.data.objects.new('prop', None); bpy.context.collection.objects.link(root)
    for o in obj_list:
        o.parent = root
    root.matrix_world = M_
    return root


def phone(screen='phone_search.png', facing_out=True):
    body = box('phone', (0, 0, 0), (0.085, 0.012, 0.17), mat('phb', '#1E1E24', 0.3), 0.008)
    scr = plane('phscr', (0, -0.0065 if facing_out else 0.0065, 0), (0.077, 0.158), mat('phs', '#FFFFFF', 0.3, img=os.path.join(TEX, screen), emit=0.55),
                rot=(math.pi / 2, 0, 0 if facing_out else math.pi))
    return [body, scr]


def sandwich():
    crust = mat('crust', '#D9A55E', 0.8); bread = mat('bread', '#F3E3C2', 0.9)
    objs = []
    def tri(name, z, h, m, s=1.0):
        bpy.ops.mesh.primitive_cylinder_add(vertices=3, radius=0.075 * s, depth=h, location=(0, 0, z))
        o = bpy.context.object; o.name = name
        md = o.modifiers.new('b', 'BEVEL'); md.width = 0.012; md.segments = 3
        o.data.materials.append(m); bpy.ops.object.shade_smooth(); return o
    objs.append(tri('b1', 0.0, 0.022, bread)); objs.append(tri('lettuce', 0.016, 0.01, mat('let', '#6DBB4A', 0.7), 1.08))
    objs.append(tri('tom', 0.026, 0.01, mat('tom', '#D9443A', 0.6), 1.02)); objs.append(tri('cheese', 0.035, 0.008, mat('che', '#F2C14E', 0.6), 1.05))
    objs.append(tri('b2', 0.05, 0.022, bread))
    return objs


def dress(color, name):
    m = mat(name, color, 0.85); hang = mat('hanger', '#C68A4B', 0.5)
    objs = []
    bpy.ops.mesh.primitive_cone_add(vertices=48, radius1=0.30, radius2=0.12, depth=0.55, location=(0, 0, -0.62))
    o = bpy.context.object; o.data.materials.append(m); bpy.ops.object.shade_smooth(); objs.append(o)
    objs.append(box('bodice', (0, 0, -0.24), (0.26, 0.12, 0.3), m, 0.05))
    for s in (-1, 1):
        objs.append(box('sleeve', (s * 0.15, 0, -0.14), (0.1, 0.11, 0.12), m, 0.04))
    bpy.ops.mesh.primitive_torus_add(major_radius=0.17, minor_radius=0.012, location=(0, 0, -0.08), rotation=(math.pi / 2, 0, 0))
    t = bpy.context.object; t.scale = (1, 0.35, 1); t.data.materials.append(hang); objs.append(t)
    objs.append(cyl('hook', (0, 0, 0.0), 0.01, 0.12, hang, 12, 0.0))
    return objs


def sweat(head_center, r):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.022, location=Vector(head_center) + Vector((-r * 0.75, -r * 0.45, r * 0.55)))
    o = bpy.context.object; o.scale = (1, 1, 1.5); o.data.materials.append(mat('sweat', '#8EC9FF', 0.1)); bpy.ops.object.shade_smooth()
    return o


# ================================================================== poses (arm directions: (yaw,pitch) upper, (yaw,pitch) forearm)
def A(r=None, l=None, **kw):
    d = {}
    if r: d['armR'] = r
    if l: d['armL'] = l
    d.update(kw); return d


HANG_R, HANG_L = ((-90, -76), (-90, -82)), ((90, -76), (90, -82))
CROSS = dict(armR=((14, -38), (62, 6)), armL=((-14, -38), (-62, -2)))
PALM_UP_R = ((-35, -62), (-18, -6))
HAND_UP_R = ((-60, -10), (-15, 75))
CHEST_R = ((-15, -68), (80, 28))
PHONE = dict(armR=((12, -62), (8, 40)), armL=((-12, -62), (-8, 40)))
DRIVE = dict(armR=((-8, -50), (-4, -8)), armL=((8, -50), (4, -8)))
POINT_R = ((-40, 5), (-35, 10))
OPEN_ARMS = dict(armR=((-70, -35), (-55, -10)), armL=((70, -35), (55, -10)))
OFFER_R = ((-12, -45), (-5, -4))
EAT_R = ((12, -70), (22, 76))
STARS_R = ((-35, 55), (-25, 72))
SHRUG = dict(armR=((-40, -66), (-55, -8)), armL=((40, -66), (55, -8)), handR=90, handL=-90)
SCRATCH_R = ((-55, 35), (45, 55))
SALUTE_R = ((-28, -18), (70, 62))
DRESS = dict(armR=((-48, -40), (-30, 6)), armL=((48, -40), (30, 6)))

# ---------------------------------------------------------------- face presets
F_ANGRY = dict(brow=16, mouth='flat')
F_DEAD = dict(brow=8, mouth='flat', eyes='half')
F_SKEPT = dict(brow_R=16, brow_L=-6, brow_lift_L=4, mouth='flat')
F_TOUCHED = dict(brow=-14, brow_lift=2, mouth='smile')
F_WORRY = dict(brow=-14, brow_lift=2, mouth='wavy')
F_HAPPY = dict(eyes='happy', brows=False, mouth='smile')
F_BIGHAPPY = dict(eyes='happy', brows=False, mouth='bigsmile')
F_PROUD = dict(eyes='happy', brow=-4, brow_lift=3, mouth='smile')
F_SMUG = dict(eyes='half', brow=4, mouth='smirk')
F_CURIOUS = dict(brow_R=-8, brow_L=-8, brow_lift=3, mouth='smile')
F_SURPRISE = dict(arched=True, mouth='o')
F_FOCUS = dict(brow=22, eyes='half', mouth='flat')
F_NEUTRAL = dict(brow=4, mouth='flat')
F_SQUINT = dict(brow=18, eyes='half', mouth='smirk')

GFZ = 0.0


# ================================================================== shots
def lr_couch(bf_pose, bf_face, gf_pose=None, gf_face=None, gf_sit=True, gf_loc=None, bf_head=(0, 0), gf_head=(0, 0), extra=None):
    living_room()
    bfr = C.build_character('bf', pose=dict(bf_pose, legs='sit', head=bf_head), face=bf_face, loc=(SOFA_X - 0.45, 1.42, -0.32))
    gfr = None
    if gf_pose is not None:
        if gf_sit:
            gfr = C.build_character('gf', pose=dict(gf_pose, legs='sit', head=gf_head), face=gf_face, loc=(SOFA_X + 0.5, 1.42, -0.30))
        else:
            gfr = C.build_character('gf', pose=dict(gf_pose, head=gf_head), face=gf_face, loc=gf_loc or (SOFA_X + 0.9, 0.35, 0))
    return bfr, gfr


def S_wide_couch_talk():
    b, g = lr_couch(A(r=PALM_UP_R, l=HANG_L, handR=90), F_HAPPY, A(r=HANG_R, l=HANG_L), F_SURPRISE, bf_head=(25, 0), gf_head=(-25, 0))
    cam((SOFA_X, -3.3, 1.45), (SOFA_X, 1.3, 0.8), 24)


def cu(target, dist=1.15, height=0.0, lens=55, side=0.0):
    t = Vector(target); loc = t + Vector((side, -dist, height))
    cam(loc, t + Vector((0, 0, -0.12)), lens, dof=(dist, 2.2))


BF_SIT_HEAD = (SOFA_X - 0.45, 1.42, -0.32 + 1.515)
GF_SIT_HEAD = (SOFA_X + 0.5, 1.42, -0.30 + 1.385)


def S_gf_cu_couch(face, pose=None, head=(-15, 0)):
    def f():
        lr_couch(A(r=HANG_R, l=HANG_L), F_NEUTRAL, pose or A(r=HANG_R, l=HANG_L), face, gf_head=head)
        cu(GF_SIT_HEAD, side=-0.1)
    return f


def S_bf_cu_couch(pose, face, head=(12, 0), extra=None):
    def f():
        b, g = lr_couch(pose, face, A(r=HANG_R, l=HANG_L), F_NEUTRAL, bf_head=head)
        if extra:
            extra(b)
        cu(BF_SIT_HEAD, side=0.12)
    return f


def S_dresses():
    living_room()
    g = C.build_character('gf', pose=dict(DRESS), face=dict(brow=12, brow_lift_L=3, mouth='frown'), loc=(SOFA_X, 0.55, 0))
    attach(dress('#1E1E22', 'blackdress'), g['hands']['R'], (0, 0, 0.02), (0, 0, 0))
    attach(dress('#C8202A', 'reddress'), g['hands']['L'], (0, 0, 0.02), (0, 0, 0))
    for p in bpy.data.objects:
        if p.name.startswith('prop'):
            mw = p.matrix_world.copy(); p.matrix_world = Matrix.Translation(mw.translation)  # hang straight down
    cam((SOFA_X, -2.6, 1.25), (SOFA_X, 0.8, 0.95), 30, dof=(3.1, 4.0))


def S_waiting(gf_face=F_ANGRY):
    def f():
        living_room()
        C.build_character('bf', pose=dict(A(r=HANG_R, l=HANG_L), legs='sit', lean=0), face=dict(eyes='half', brow=0, mouth='smile'),
                          loc=(SOFA_X - 0.45, 1.42, -0.32))
        C.build_character('gf', pose=dict(CROSS, head=(-30, 0)), face=gf_face, loc=(SOFA_X + 1.15, 0.25, 0), rot_z=math.radians(-20))
        cam((SOFA_X + 0.2, -3.4, 1.5), (SOFA_X + 0.2, 1.0, 0.85), 24)
    return f


def S_gf_cu_stand(face, pose=None, head=(-25, 0)):
    def f():
        living_room()
        C.build_character('bf', pose=dict(A(r=HANG_R, l=HANG_L), legs='sit'), face=F_NEUTRAL, loc=(SOFA_X - 0.45, 1.42, -0.32))
        C.build_character('gf', pose=dict(pose or CROSS, head=head), face=face, loc=(SOFA_X + 1.15, 0.25, 0), rot_z=math.radians(-20))
        cu((SOFA_X + 1.15, 0.25, 1.385), dist=1.2, side=-0.25)
    return f


def S_phone_cu():
    b, g = lr_couch(PHONE, F_FOCUS, A(r=HANG_R, l=HANG_L), F_NEUTRAL)
    hm = b['hands']['R']; hl = b['hands']['L']
    mid = (hm.translation + hl.translation) / 2
    attach(phone(facing_out=False), Matrix.Translation(mid + Vector((0, -0.02, 0.06))), rot=(math.radians(-15), 0, 0))
    cu(BF_SIT_HEAD, dist=1.2, height=-0.05, side=0.1)


def S_phone_screen():
    b, g = lr_couch(PHONE, F_FOCUS, A(r=HANG_R, l=HANG_L), F_NEUTRAL)
    hm = b['hands']['R']; hl = b['hands']['L']
    mid = (hm.translation + hl.translation) / 2
    p = attach(phone(facing_out=True), Matrix.Translation(mid + Vector((0, -0.02, 0.06))), rot=(math.radians(-15), 0, 0))
    t = mid + Vector((0, 0, 0.12))
    cam(t + Vector((0.04, -0.62, 0.02)), t + Vector((0, 0, 0.05)), 40, dof=(0.6, 2.8))


def S_defuse():
    b, g = lr_couch(PHONE, dict(brow=24, eyes='open', mouth='wavy'), A(r=HANG_R, l=HANG_L), F_NEUTRAL)
    hm = b['hands']['R']; hl = b['hands']['L']; mid = (hm.translation + hl.translation) / 2
    attach(phone(facing_out=False), Matrix.Translation(mid + Vector((0, -0.02, 0.06))), rot=(math.radians(-15), 0, 0))
    sweat(BF_SIT_HEAD, 0.185)
    cu(BF_SIT_HEAD, dist=0.95, height=0.02, side=0.08, lens=55)


# ---------------- car
CAR_BF = (0.36, 0.18, -0.38)     # driver (image right)
CAR_GF = (-0.36, 0.18, -0.34)


def in_car(bf_pose, bf_face, gf_pose, gf_face, bf_head=(0, 0), gf_head=(0, 0)):
    car_interior()
    b = C.build_character('bf', pose=dict(bf_pose, legs='drive', head=bf_head), face=bf_face, loc=CAR_BF)
    g = C.build_character('gf', pose=dict(gf_pose, legs='sit', head=gf_head), face=gf_face, loc=CAR_GF)
    return b, g


def S_car_wide(bf_pose, bf_face, gf_pose, gf_face, bf_head=(0, 0), gf_head=(0, 0), extra=None):
    def f():
        b, g = in_car(bf_pose, bf_face, gf_pose, gf_face, bf_head, gf_head)
        if extra:
            extra(b, g)
        cam((0, -1.25, 1.12), (0, 0.4, 1.0), 20)
    return f


def S_car_cu(who, bf_pose, bf_face, gf_pose, gf_face, bf_head=(0, 0), gf_head=(0, 0), extra=None):
    def f():
        b, g = in_car(bf_pose, bf_face, gf_pose, gf_face, bf_head, gf_head)
        if extra:
            extra(b, g)
        if who == 'bf':
            h = Vector(CAR_BF) + Vector((0, 0, 1.515))
            cam(h + Vector((-0.18, -0.95, 0.0)), h + Vector((0, 0, -0.14)), 45, dof=(0.97, 2.4))
        else:
            h = Vector(CAR_GF) + Vector((0, 0, 1.385))
            cam(h + Vector((0.18, -0.92, 0.0)), h + Vector((0, 0, -0.14)), 45, dof=(0.94, 2.4))
    return f


def eat_extra(b, g):
    attach(sandwich(), g['hands']['R'], (0, -0.03, 0.0), (math.radians(90), 0, 0))


def S_truck_view():
    gas_station()
    car_interior_parts_in_gas()


def car_interior_parts_in_gas():
    pass


# ---------------- store
def store(bf_pose, bf_face, gf_pose, gf_face, bf_head=(0, 0), gf_head=(0, 0)):
    store_front()
    b = C.build_character('bf', pose=dict(bf_pose, head=bf_head), face=bf_face, loc=(-0.55, 0.3, 0.12), rot_z=math.radians(15))
    g = C.build_character('gf', pose=dict(gf_pose, head=gf_head), face=gf_face, loc=(0.55, 0.25, 0.12), rot_z=math.radians(-15))
    return b, g


def S_store_wide(bf_pose, bf_face, gf_pose, gf_face, bf_head=(0, 0), gf_head=(0, 0)):
    def f():
        store(bf_pose, bf_face, gf_pose, gf_face, bf_head, gf_head)
        cam((0.1, -4.0, 1.35), (0.1, 1.5, 1.45), 24)
    return f


def S_store_cu(who, bf_pose, bf_face, gf_pose, gf_face, bf_head=(0, 0), gf_head=(0, 0)):
    def f():
        store(bf_pose, bf_face, gf_pose, gf_face, bf_head, gf_head)
        if who == 'bf':
            cu((-0.55, 0.3, 0.12 + 1.515), dist=1.25, side=0.15)
        else:
            cu((0.55, 0.25, 0.12 + 1.385), dist=1.2, side=-0.15)
    return f


# ---------------- gas station
def gas(bf_pose, bf_face, gf_pose, gf_face, bf_head=(0, 0), gf_head=(0, 0), extra=None):
    gas_station()
    b = C.build_character('bf', pose=dict(bf_pose, head=bf_head), face=bf_face, loc=(-0.6, 0.4, 0), rot_z=math.radians(12))
    g = C.build_character('gf', pose=dict(gf_pose, head=gf_head), face=gf_face, loc=(0.6, 0.35, 0), rot_z=math.radians(-12))
    if extra:
        extra(b, g)
    return b, g


def S_gas_wide():
    gas(OPEN_ARMS, F_BIGHAPPY, CROSS, F_DEAD)
    cam((0, -4.6, 1.5), (0, 1.5, 1.6), 24)


def S_gas_sandwich():
    gas(A(r=OFFER_R, l=HANG_L), F_HAPPY, A(r=HANG_R, l=HANG_L), F_DEAD, bf_head=(18, 0), gf_head=(-15, 0),
        extra=lambda b, g: attach(sandwich(), b['hands']['R'], (0, -0.02, 0.0), (math.radians(90), 0, 0)))
    cam((0, -2.6, 1.3), (0, 0.6, 1.2), 32, dof=(3.0, 4.0))


def S_gas_stars():
    gas(A(r=STARS_R, l=HANG_L), F_BIGHAPPY, CROSS, F_DEAD, bf_head=(0, 0))
    cam((0.3, -3.2, 0.55), (0, 1.0, 2.4), 22)


def S_truck():
    # inside the car at the gas station, looking forward past them at the truck
    gas_station()
    seat = mat('seat', '#3D4049', 0.9); trim = mat('trim', '#2A2C33', 0.8)
    base = Vector((0, -5.5, 0))
    for x in (-0.36, 0.36):
        box('seat', base + Vector((x, 0.15, 0.36)), (0.55, 0.55, 0.16), seat, 0.07)
        box('back', base + Vector((x, 0.45, 0.78)), (0.55, 0.16, 0.8), seat, 0.08)
        box('headrest', base + Vector((x, 0.52, 1.32)), (0.3, 0.12, 0.2), seat, 0.05)
    box('roof', base + Vector((0, 0.0, 1.62)), (1.7, 2.6, 0.06), trim, 0.03)
    box('dash', base + Vector((0, -0.95, 0.85)), (1.7, 0.45, 0.32), mat('dash', '#24262C', 0.7), 0.08)
    for s in (-1, 1):
        box('pillarA', base + Vector((s * 0.8, -1.0, 1.25)), (0.08, 0.1, 0.8), trim, 0.02)
        box('door', base + Vector((s * 0.85, 0.0, 0.55)), (0.06, 2.0, 0.6), trim, 0.02)
    # characters facing forward (+Y towards the truck): rot_z = pi
    b = C.build_character('bf', pose=dict(A(r=HANG_R, l=HANG_L), legs='sit'), face=F_HAPPY, loc=base + Vector((0.36, 0.18, -0.38)), rot_z=math.pi)
    g = C.build_character('gf', pose=dict(A(r=EAT_R, l=HANG_L), legs='sit'), face=F_DEAD, loc=base + Vector((-0.36, 0.18, -0.34)), rot_z=math.pi)
    truck((1.6, 3.6, 0), rot_z=math.radians(90))
    guy = C.build_character('bf', pose=A(r=((-10, -40), (-5, -10)), l=HANG_L), face=F_NEUTRAL, loc=(0.4, 2.6, 0), rot_z=math.radians(-70),
                            override=dict(tee='#E39A2B', pants='#3B3B3B', skin='#C98A5E'))
    cam(base + Vector((0, 1.6, 1.45)), base + Vector((0, -2.0, 1.0)) + Vector((0, 8, 0)) * 0, 30)
    c = bpy.context.scene.camera
    c.rotation_euler = (Vector((0.6, 3.0, 0.9)) - c.location).to_track_quat('-Z', 'Y').to_euler()


SHOTS = [
    # (start, id, builder)
    (0.00, 's01', S_wide_couch_talk),
    (3.10, 's02', S_gf_cu_couch(F_TOUCHED, head=(-18, 0))),
    (5.60, 's03', S_bf_cu_couch(A(r=CHEST_R, l=HANG_L), F_PROUD)),
    (9.15, 's04', S_gf_cu_couch(F_CURIOUS, head=(-18, 0))),
    (10.80, 's05', S_bf_cu_couch(CROSS, F_SMUG, head=(8, 0))),
    (12.25, 's06', S_dresses),
    (18.35, 's07', S_waiting(F_NEUTRAL)),
    (22.25, 's08', S_gf_cu_stand(F_SKEPT)),
    (24.25, 's09', S_bf_cu_couch(A(r=HAND_UP_R, l=HANG_L, handR=0), dict(eyes='half', brow=0, mouth='smile'), head=(10, 0))),
    (26.80, 's10', S_waiting(F_ANGRY)),
    (28.10, 's11', S_phone_cu),
    (31.50, 's12', S_phone_screen),
    (33.90, 's13', S_defuse),
    (38.85, 's14', S_gf_cu_stand(F_SKEPT, head=(-30, 0))),
    (41.15, 's15', S_bf_cu_couch(A(r=HANG_R, l=HANG_L), dict(F_WORRY, look=6), head=(20, 0))),
    (42.95, 's16', S_gf_cu_stand(F_DEAD)),
    (46.90, 's17', S_car_wide(DRIVE, F_HAPPY, CROSS, F_NEUTRAL)),
    (48.20, 's18', S_car_cu('bf', DRIVE, F_HAPPY, CROSS, F_NEUTRAL, bf_head=(-15, 0))),
    (50.40, 's19', S_car_cu('gf', DRIVE, F_HAPPY, CROSS, F_SKEPT, gf_head=(15, 0))),
    (52.40, 's20', S_car_cu('bf', DRIVE, F_WORRY, CROSS, F_NEUTRAL, bf_head=(-10, 0))),
    (56.70, 's21', S_car_cu('gf', DRIVE, F_HAPPY, CROSS, F_DEAD, gf_head=(10, 0))),
    (57.90, 's22', S_car_wide(A(r=SALUTE_R, l=DRIVE['armL']), F_SQUINT, A(r=HANG_R, l=HANG_L), F_DEAD)),
    (63.30, 's23', S_car_cu('bf', A(r=POINT_R, l=DRIVE['armL']), F_SURPRISE, CROSS, F_NEUTRAL, bf_head=(-25, 0))),
    (65.80, 's24', S_store_wide(A(r=POINT_R, l=HANG_L), F_SURPRISE, CROSS, F_DEAD, bf_head=(0, 0))),
    (68.55, 's25', S_store_cu('gf', A(r=HANG_R, l=HANG_L), F_SURPRISE, CROSS, F_ANGRY, gf_head=(-10, 0))),
    (72.80, 's26', S_store_cu('bf', A(r=SCRATCH_R, l=HANG_L), F_WORRY, CROSS, F_DEAD)),
    (75.40, 's27', S_store_cu('gf', A(r=HANG_R, l=HANG_L), F_NEUTRAL, CROSS, F_SKEPT, gf_head=(-20, 0))),
    (77.95, 's28', S_store_cu('bf', SHRUG, F_NEUTRAL, CROSS, F_DEAD, bf_head=(15, 0))),
    (80.35, 's29', S_store_wide(A(r=HAND_UP_R, l=HANG_L), F_SMUG, A(r=HANG_R, l=PALM_UP_R and ((35, -62), (18, -6)), handL=-90), F_CURIOUS, bf_head=(15, 0), gf_head=(-15, 0))),
    (84.90, 's30', S_gas_wide),
    (87.10, 's31', S_gas_sandwich),
    (89.90, 's32', S_gas_stars),
    (92.80, 's33', S_car_wide(A(r=HANG_R, l=HANG_L), F_HAPPY, A(r=EAT_R, l=HANG_L), F_DEAD, extra=eat_extra)),
    (95.30, 's34', S_truck),
    (97.70, 's35', S_car_cu('bf', A(r=HANG_R, l=HANG_L), F_BIGHAPPY, A(r=EAT_R, l=HANG_L), F_DEAD, bf_head=(-25, 0), extra=eat_extra)),
    (101.70, 's36', S_car_cu('gf', A(r=HANG_R, l=HANG_L), F_BIGHAPPY, A(r=EAT_R, l=HANG_L), F_DEAD, gf_head=(22, 0), extra=eat_extra)),
    (103.20, 's37', S_car_cu('bf', A(r=CHEST_R, l=HANG_L), F_PROUD, A(r=EAT_R, l=HANG_L), F_DEAD, bf_head=(-20, 0), extra=eat_extra)),
]

if __name__ == '__main__':
    for st, sid, fn in SHOTS:
        if ONLY and sid not in ONLY:
            continue
        fn()
        sc = bpy.context.scene
        sc.render.filepath = os.path.join(OUT, sid + '.png')
        bpy.ops.render.render(write_still=True)
        print('RENDERED', sid, flush=True)
