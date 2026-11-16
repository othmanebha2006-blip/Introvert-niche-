"""Episode 2 backgrounds (no characters) + foreground occluder layers + props.
The user's own character cutouts are composited between bg and fg in compose3.py.
Usage: python3 scene3.py -- <workdir> [ids...]
"""
import bpy, math, sys, os
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scene2 as T   # set builders (scene2 only renders when run as __main__)

S = T.S; OUT = os.path.join(S, 'bg2'); os.makedirs(OUT, exist_ok=True)
ONLY = T.ONLY


def rack():
    m = T.mat('rackm', '#C9CCD2', 0.3)
    x0, y0 = T.SOFA_X + 1.0, 0.9
    T.cyl('rbar', (x0, y0, 1.62), 0.018, 1.3, m, 16, 0.0, (0, math.pi / 2, 0))
    for dx in (-0.62, 0.62):
        T.cyl('rpole', (x0 + dx, y0, 0.82), 0.018, 1.6, m, 16, 0.0)
        T.box('rfoot', (x0 + dx, y0, 0.02), (0.06, 0.5, 0.03), m, 0.01)
    for dx, col, nm in ((-0.3, '#1E1E22', 'blackdress'), (0.3, '#C8202A', 'reddress')):
        objs = T.dress(col, nm)
        root = bpy.data.objects.new('dressroot', None); bpy.context.collection.objects.link(root)
        for o in objs:
            o.parent = root
        root.location = (x0 + dx, y0, 1.6)


def gas_truck_view():
    T.gas_station()
    seat = T.mat('seat', '#3D4049', 0.9); trim = T.mat('trim', '#2A2C33', 0.8)
    base = Vector((0, -4.6, 0))          # car faces +Y (towards the truck)
    for x in (-0.36, 0.36):
        T.box('seat', base + Vector((x, -0.15, 0.36)), (0.55, 0.55, 0.16), seat, 0.07)
    T.box('roof', base + Vector((0, 0.0, 1.62)), (1.7, 2.6, 0.06), trim, 0.03)
    T.box('dash', base + Vector((0, 0.95, 0.85)), (1.7, 0.45, 0.32), T.mat('dash', '#24262C', 0.7), 0.08)
    for s_ in (-1, 1):
        T.box('pillarA', base + Vector((s_ * 0.8, 1.0, 1.25)), (0.08, 0.1, 0.8), trim, 0.02)
        T.box('door', base + Vector((s_ * 0.85, 0.0, 0.55)), (0.06, 2.0, 0.6), trim, 0.02)
    T.truck((1.0, 1.0, 0), rot_z=math.radians(90))
    T.area(base + Vector((0, 0.5, 1.4)), base + Vector((0, -0.5, 1.0)), 30, 1.0, '#9FB8FF')
    T.cam(base + Vector((0, -1.25, 1.32)), (0.4, 1.2, 0.95), 26)


def void_prop(kind):
    T.reset(); sc = bpy.context.scene; sc.render.film_transparent = True
    sc.render.resolution_x = 1080; sc.render.resolution_y = 1080
    T.area((1.5, -2.5, 2.5), (0, 0, 0), 120, 2.0); T.area((-2.0, -1.0, 1.5), (0, 0, 0), 50, 2.0, '#FFE8CC')
    if kind == 'phone':
        objs = T.phone(facing_out=True)
        T.cam((0, -0.55, 0.0), (0, 0, 0), 50)
    else:
        objs = T.sandwich()
        root = bpy.data.objects.new('sw', None); bpy.context.collection.objects.link(root)
        for o in objs:
            o.parent = root
        root.rotation_euler = (math.radians(-28), 0, math.radians(20))
        T.cam((0, -0.42, 0.18), (0, 0, 0.02), 50)


GF_CU = (T.SOFA_X + 0.5, 1.42, 1.08)
BF_CU = (T.SOFA_X - 0.45, 1.42, 1.19)
BG = {
    # name: (builder, camera fn, foreground object-name prefixes)
    'lr_wide': (T.living_room, lambda: T.cam((T.SOFA_X, -3.3, 1.45), (T.SOFA_X, 1.3, 0.8), 24), ('ct_',)),
    'lr_cu_gf': (T.living_room, lambda: T.cam((GF_CU[0] - 0.1, GF_CU[1] - 1.25, GF_CU[2] + 0.1), (GF_CU[0], GF_CU[1] + 0.5, GF_CU[2] + 0.35), 40, dof=(1.3, 2.2)), ()),
    'lr_cu_bf': (T.living_room, lambda: T.cam((BF_CU[0] + 0.1, BF_CU[1] - 1.25, BF_CU[2] + 0.1), (BF_CU[0], BF_CU[1] + 0.5, BF_CU[2] + 0.35), 40, dof=(1.3, 2.2)), ()),
    'lr_rack': (lambda: (T.living_room(), rack()), lambda: T.cam((T.SOFA_X + 0.5, -2.4, 1.3), (T.SOFA_X + 0.5, 1.2, 1.15), 30), ()),
    'car_wide': (T.car_interior, lambda: T.cam((0, -1.25, 1.12), (0, 0.4, 1.0), 20), ('dash', 'Torus', 'column')),
    'car_cu_bf': (T.car_interior, lambda: T.cam((0.30, -0.42, 1.2), (0.36, 0.18, 1.05), 40, dof=(0.62, 2.4)), ()),
    'car_cu_gf': (T.car_interior, lambda: T.cam((-0.30, -0.42, 1.12), (-0.36, 0.18, 0.97), 40, dof=(0.62, 2.4)), ()),
    'store_wide': (T.store_front, lambda: T.cam((0.1, -4.0, 1.35), (0.1, 1.5, 1.45), 24), ()),
    'store_cu': (T.store_front, lambda: T.cam((0.0, -1.0, 1.55), (0.0, 1.5, 1.75), 40, dof=(1.3, 2.0)), ()),
    'gas_wide': (T.gas_station, lambda: T.cam((0, -4.6, 1.5), (0, 1.5, 1.6), 24), ()),
    'gas_med': (T.gas_station, lambda: T.cam((0, -2.6, 1.3), (0, 0.6, 1.2), 32, dof=(3.0, 4.0)), ()),
    'gas_low': (T.gas_station, lambda: T.cam((0.3, -3.2, 0.55), (0, 1.0, 2.4), 22), ()),
    'gas_truck': (gas_truck_view, lambda: None, ()),
    'prop_phone': (lambda: void_prop('phone'), lambda: None, ()),
    'prop_sandwich': (lambda: void_prop('sandwich'), lambda: None, ()),
}

if __name__ == '__main__':
    for name, (build, camf, fg) in BG.items():
        if ONLY and name not in ONLY:
            continue
        build(); camf()
        sc = bpy.context.scene
        sc.render.filepath = os.path.join(OUT, name + '.png'); bpy.ops.render.render(write_still=True)
        print('RENDERED', name, flush=True)
        if fg:
            for o in bpy.data.objects:
                if o.type in ('MESH', 'CURVE'):
                    o.visible_camera = any(o.name.startswith(p) for p in fg)
            sc.render.film_transparent = True
            sc.render.filepath = os.path.join(OUT, name + '_fg.png'); bpy.ops.render.render(write_still=True)
            print('RENDERED', name + '_fg', flush=True)
