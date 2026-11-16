import bpy, math, sys, os
from mathutils import Vector

S = sys.argv[sys.argv.index('--') + 1]
which = sys.argv[sys.argv.index('--') + 2:]  # list of shots to render
TEX = os.path.join(S, 'tex'); OUT = os.path.join(S, 'renders')


def hexc(h, a=1.0):
    h = h.lstrip('#'); c = [int(h[i:i+2], 16) / 255 for i in (0, 2, 4)]
    c = [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
    return (*c, a)


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    sc.cycles.device = 'CPU'
    sc.cycles.samples = int(os.environ.get('SAMP','96'))
    sc.cycles.use_denoising = True
    sc.render.resolution_x = 1080; sc.render.resolution_y = 1920
    sc.render.resolution_percentage = int(os.environ.get('PCT','100'))
    sc.view_settings.exposure = float(os.environ.get('EXP','-0.6'))
    sc.view_settings.view_transform = 'Standard'
    sc.view_settings.look = 'None'
    w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True
    w.node_tree.nodes['Background'].inputs[0].default_value = hexc('#C8D4E6')
    w.node_tree.nodes['Background'].inputs[1].default_value = 0.25
    return sc


def mat(name, color, rough=0.75, img=None, emit=0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = hexc(color)
    b.inputs['Roughness'].default_value = rough
    if img:
        t = m.node_tree.nodes.new('ShaderNodeTexImage'); t.image = bpy.data.images.load(img)
        m.node_tree.links.new(t.outputs[0], b.inputs['Base Color'])
        if emit:
            m.node_tree.links.new(t.outputs[0], b.inputs['Emission Color'])
            b.inputs['Emission Strength'].default_value = emit
    elif emit:
        b.inputs['Emission Color'].default_value = hexc(color); b.inputs['Emission Strength'].default_value = emit
    return m


def box(name, loc, size, m, bevel=0.03, segs=3):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    o = bpy.context.object; o.name = name; o.scale = (size[0] / 2, size[1] / 2, size[2] / 2)
    bpy.ops.object.transform_apply(scale=True)
    if bevel:
        md = o.modifiers.new('b', 'BEVEL'); md.width = bevel; md.segments = segs
    o.data.materials.append(m)
    bpy.ops.object.shade_smooth()
    return o


def cyl(name, loc, r, h, m, verts=48, bevel=0.01, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=h, location=loc, rotation=rot)
    o = bpy.context.object; o.name = name
    if bevel:
        md = o.modifiers.new('b', 'BEVEL'); md.width = bevel; md.segments = 3
    o.data.materials.append(m); bpy.ops.object.shade_smooth()
    return o


def cam(loc, target, lens=35, dof=None):
    bpy.ops.object.camera_add(location=loc)
    c = bpy.context.object
    d = Vector(target) - Vector(loc)
    c.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    c.data.lens = lens; c.data.sensor_fit = 'VERTICAL'; c.data.sensor_height = 24
    if dof:
        c.data.dof.use_dof = True; c.data.dof.focus_distance = dof[0]; c.data.dof.aperture_fstop = dof[1]
    bpy.context.scene.camera = c
    return c


def light_area(loc, target, energy, size, color='#FFFFFF'):
    bpy.ops.object.light_add(type='AREA', location=loc)
    l = bpy.context.object; l.data.energy = energy; l.data.size = size; l.data.color = hexc(color)[:3]
    l.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    return l


def coffee_table(y=-0.75):
    wood = mat('ctwood', '#C27A3E', 0.5)
    box('ct_top', (0.15, y, 0.43), (2.0, 0.85, 0.08), wood, 0.02)
    box('ct_apron', (0.15, y, 0.36), (1.85, 0.72, 0.07), wood, 0.01)
    for dx in (-0.85, 1.15):
        for dy in (-0.32, 0.32):
            box('ct_leg', (dx, y + dy, 0.17), (0.09, 0.09, 0.34), wood, 0.01)


# ---------------------------------------------------------------- living room
def living_room():
    sc = reset()
    wall = mat('wall', '#8FB3E0', 0.9); floor = mat('floor', '#C9A27A', 0.6)
    sofa = mat('sofa', '#2F4E8C', 0.95); wood = mat('wood', '#B46528', 0.55)
    rug = mat('rug', '#EADCC8', 1.0); white = mat('white', '#F2F0EC', 0.6)
    shade = mat('shade', '#FFF1D0', 0.8, emit=1.2); art = mat('art', '#FFFFFF', 0.8, img=os.path.join(TEX, 'art.png'))
    leg = mat('leg', '#6B4A2E', 0.6)
    box('floor', (0, 0, -0.05), (14, 14, 0.1), floor, 0)
    box('wall', (0, 2.05, 4), (14, 0.1, 8.2), wall, 0)
    box('wallL', (-4.0, 0, 4), (0.1, 14, 8.2), wall, 0)
    box('skirting', (0, 1.98, 0.06), (14, 0.04, 0.12), white, 0.005)
    # rug
    box('rug', (0.2, 0.2, 0.01), (4.2, 2.8, 0.03), rug, 0.012)
    # sofa (3 seat) centred x=0.5
    sx = 0.5
    box('sofa_base', (sx, 1.45, 0.3), (2.6, 0.95, 0.38), sofa, 0.06)
    box('sofa_back', (sx, 1.82, 0.72), (2.6, 0.26, 0.9), sofa, 0.08)
    for i in range(3):
        box(f'cush{i}', (sx - 0.83 + i * 0.83, 1.38, 0.56), (0.8, 0.8, 0.16), sofa, 0.06)
        box(f'bcush{i}', (sx - 0.83 + i * 0.83, 1.66, 0.88), (0.78, 0.18, 0.5), sofa, 0.07)
    for s in (-1, 1):
        box(f'arm{s}', (sx + s * 1.38, 1.45, 0.48), (0.24, 0.95, 0.66), sofa, 0.08)
    for x in (sx - 1.35, sx + 1.35):
        for y in (1.05, 1.85):
            box('leg', (x, y, 0.05), (0.07, 0.07, 0.1), leg, 0.01)
    # framed art
    box('frame', (sx, 1.98, 2.3), (1.8, 0.05, 1.25), wood, 0.012)
    box('mat', (sx, 1.955, 2.3), (1.64, 0.02, 1.09), white, 0.004)
    bpy.ops.mesh.primitive_plane_add(size=1, location=(sx, 1.94, 2.3), rotation=(math.pi / 2, 0, 0))
    p = bpy.context.object; p.scale = (1.41, 0.94, 1); p.data.materials.append(art)
    # side table + lamp (left of sofa)
    lx = sx - 2.0
    box('table', (lx, 1.6, 0.58), (0.55, 0.55, 0.05), wood, 0.01)
    for dx in (-0.22, 0.22):
        for dy in (-0.22, 0.22):
            box('tleg', (lx + dx, 1.6 + dy, 0.28), (0.04, 0.04, 0.56), wood, 0.005)
    cyl('lampbase', (lx, 1.6, 0.66), 0.1, 0.1, wood)
    cyl('lampstem', (lx, 1.6, 0.85), 0.025, 0.35, wood, 16)
    bpy.ops.mesh.primitive_cone_add(vertices=48, radius1=0.24, radius2=0.16, depth=0.3, location=(lx, 1.6, 1.15))
    o = bpy.context.object; o.data.materials.append(shade); bpy.ops.object.shade_smooth()
    bpy.ops.object.light_add(type='POINT', location=(lx, 1.6, 1.12)); l = bpy.context.object
    l.data.energy = 140; l.data.color = hexc('#FFB866')[:3]; l.data.shadow_soft_size = 0.15
    # door on the left wall area (back wall, far left)
    dx_ = -3.0
    box('doorframe', (dx_, 1.98, 1.05), (1.05, 0.06, 2.15), white, 0.01)
    box('door', (dx_, 1.95, 1.02), (0.9, 0.05, 2.0), mat('door', '#F7F5F0', 0.5), 0.01)
    cyl('knob', (dx_ + 0.33, 1.9, 1.0), 0.035, 0.06, mat('knob', '#C9A64B', 0.3), 24, 0.005, (math.pi / 2, 0, 0))
    # plant on right
    px = sx + 2.05
    cyl('pot', (px, 1.6, 0.22), 0.2, 0.44, mat('pot', '#E9E2D6', 0.6))
    for i, (ox, oy, h) in enumerate([(0, 0, 0.9), (0.1, 0.05, 0.75), (-0.1, -0.03, 0.8)]):
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=0.22, location=(px + ox, 1.6 + oy, 0.44 + h * 0.6))
        o = bpy.context.object; o.data.materials.append(mat(f'leaf{i}', '#4E8F5A', 0.8))
    # lights
    light_area((1.5, -3.0, 3.2), (0.3, 1.5, 0.8), 260, 4.0)
    light_area((-3.5, -1.0, 2.5), (0, 1.5, 1), 70, 3.0, '#FFE2BC')
    return sc


def table_layer():
    sc = living_room()
    for o in list(bpy.data.objects):
        if o.type == 'MESH':
            o.visible_camera = False
    coffee_table()
    sc.render.film_transparent = True
    return sc


def void():
    sc = reset()
    sc.render.film_transparent = True
    sc.render.resolution_x = 1080; sc.render.resolution_y = 1080
    bpy.ops.mesh.primitive_plane_add(size=20, location=(0, 0, 0))
    g = bpy.context.object; g.is_shadow_catcher = True
    light_area((1.5, -2.5, 3.5), (0, 0, 0.2), 500, 3.0)
    light_area((-2.5, -1.0, 2.0), (0, 0, 0.3), 150, 2.0, '#FFE8CC')
    return sc


def prop(kind):
    if kind == 'basket':
        wick = mat('wick', '#D8B98A', 0.9)
        b = box('basket', (0, 0, 0.22), (0.9, 0.6, 0.44), wick, 0.05)
        md = b.modifiers.new('s', 'SOLIDIFY')
        # clothes pile
        cols = ['#F2F2F2', '#E07A5F', '#3D5A80', '#F2CC8F', '#81B29A', '#9C89B8']
        import random; random.seed(3)
        for i in range(9):
            box(f'cl{i}', (random.uniform(-0.28, 0.28), random.uniform(-0.15, 0.15), 0.42 + i * 0.035),
                (random.uniform(0.3, 0.45), random.uniform(0.25, 0.35), 0.08), mat(f'c{i}', cols[i % 6], 0.95), 0.03)
        return cam((0, -3.0, 1.75), (0, 0, 0.36), 50)
    if kind == 'pills':
        cyl('bottle', (0, 0, 0.18), 0.1, 0.36, mat('pb', '#F4F1EA', 0.35), 64, 0.02)
        cyl('label', (0, 0, 0.17), 0.103, 0.18, mat('lab', '#1474EE', 0.6), 64, 0.0)
        cyl('cap', (0, 0, 0.39), 0.105, 0.08, mat('cap', '#D52C24', 0.5), 64, 0.015)
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.035, location=(0.22, -0.05, 0.03)); o = bpy.context.object
        o.scale = (1, 0.7, 0.45); o.data.materials.append(mat('pill', '#E9874C', 0.4)); bpy.ops.object.shade_smooth()
        return cam((0, -1.25, 0.55), (0.04, 0, 0.2), 50)
    if kind == 'shampoo':
        b = box('sh', (0, 0, 0.3), (0.26, 0.13, 0.6), mat('shb', '#F3A6B9', 0.35), 0.06)
        box('shl', (0, -0.066, 0.28), (0.2, 0.01, 0.26), mat('shl', '#FFFFFF', 0.6), 0.01)
        cyl('pump', (0, 0, 0.66), 0.035, 0.12, mat('pump', '#FFFFFF', 0.4))
        box('noz', (0.05, 0, 0.72), (0.12, 0.04, 0.03), mat('pump2', '#FFFFFF', 0.4), 0.01)
        bpy.ops.mesh.primitive_torus_add(major_radius=0.33, minor_radius=0.03, location=(0.42, 0.1, 0.03))
        o = bpy.context.object; o.scale = (1, 1, 0.3); o.data.materials.append(mat('tw', '#7AC4D6', 0.95))
        box('towel', (-0.4, 0.05, 0.08), (0.42, 0.32, 0.16), mat('tw2', '#FFFFFF', 0.95), 0.05)
        return cam((0, -2.7, 1.2), (0, 0, 0.3), 45)
    if kind == 'book':
        box('cover', (0, 0, 0.05), (0.6, 0.42, 0.1), mat('cv', '#2E7D5B', 0.6), 0.015)
        box('pages', (0.012, 0, 0.05), (0.57, 0.39, 0.085), mat('pg', '#F7F1E1', 0.9), 0.004)
        box('cover2', (0.0, 0, 0.085), (0.6, 0.42, 0.012), mat('cv2', '#2E7D5B', 0.6), 0.004)
        box('cover3', (0.0, 0, 0.012), (0.6, 0.42, 0.012), mat('cv3', '#2E7D5B', 0.6), 0.004)
        box('band', (0.0, 0, 0.093), (0.6, 0.06, 0.003), mat('bd', '#E3B23C', 0.4), 0.001)
        o = bpy.data.objects
        for n in ('cover', 'pages', 'cover2', 'cover3', 'band'):
            o[n].rotation_euler = (0, 0, 0.35)
        return cam((0, -1.9, 1.3), (0, 0, 0.05), 50)
    if kind == 'cake':
        ic = mat('icing', '#FBF7F2', 0.5)
        for i, (r, h) in enumerate([(0.36, 0.26), (0.26, 0.22), (0.17, 0.2)]):
            z = [0.13, 0.37, 0.58][i]
            cyl(f't{i}', (0, 0, z), r, h, ic, 64, 0.03)
            bpy.ops.mesh.primitive_torus_add(major_radius=r, minor_radius=0.02, location=(0, 0, z - h / 2 + 0.02))
            bpy.context.object.data.materials.append(mat(f'rib{i}', '#F2B8C6', 0.5))
        for a in range(6):
            bpy.ops.mesh.primitive_uv_sphere_add(radius=0.04, location=(0.17 * math.cos(a), 0.17 * math.sin(a), 0.7))
            bpy.context.object.data.materials.append(mat(f'fl{a}', '#E8708A', 0.6)); bpy.ops.object.shade_smooth()
        cyl('plate', (0, 0, 0.01), 0.48, 0.02, mat('plate', '#D9D9D9', 0.3))
        return cam((0, -2.0, 0.9), (0, 0, 0.35), 45)
    if kind == 'phone':
        box('phone', (0, 0, 0.02), (0.38, 0.76, 0.04), mat('ph', '#1E1E24', 0.3), 0.03)
        bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 0.0405)); p = bpy.context.object
        p.scale = (0.33, 0.69, 1); p.data.materials.append(mat('scr', '#FFFFFF', 0.2, img=os.path.join(TEX, 'phone.png'), emit=1.0))
        return cam((0, -0.9, 1.35), (0, 0.02, 0.0), 50)


SHOTS = {
    'room_wide': (living_room, lambda: cam((0.15, -3.9, 1.75), (0.15, 1.6, 1.15), 21)),
    'room_table': (lambda: table_layer(), lambda: cam((0.15, -3.9, 1.75), (0.15, 1.6, 1.15), 21)),
    'room_cu_a': (living_room, lambda: cam((0.9, -1.0, 1.15), (0.9, 1.9, 1.3), 40, dof=(2.0, 2.8))),
    'room_cu_b': (living_room, lambda: cam((-0.6, -1.0, 1.15), (-0.6, 1.9, 1.3), 40, dof=(2.0, 2.8))),
    'room_med': (living_room, lambda: cam((0.3, -2.6, 1.05), (0.3, 1.8, 1.0), 35, dof=(3.6, 4.0))),
}
for k in ('basket', 'pills', 'shampoo', 'book', 'cake', 'phone'):
    SHOTS['prop_' + k] = (void, (lambda k: (lambda: prop(k)))(k))

for name in which:
    build, camf = SHOTS[name]
    sc = build(); camf()
    sc.render.filepath = os.path.join(OUT, name + '.png')
    bpy.ops.render.render(write_still=True)
    print('RENDERED', name)
