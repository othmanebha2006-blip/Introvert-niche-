"""Loads Natural Earth GeoJSON, clips, projects to a Lambert conformal conic in km, simplifies,
and precomputes coastal ripple lines. Writes a pickle the renderer loads.

usage: python3 geo.py <natural_earth_geojson_dir> <out.pkl> <lon0> <lat0>
"""
import json, sys, pickle, os
import numpy as np
from pyproj import Transformer
from shapely.geometry import shape, box, mapping
from shapely.ops import transform, unary_union
from shapely import make_valid

src, out = sys.argv[1], sys.argv[2]
lon0, lat0 = float(sys.argv[3]), float(sys.argv[4])
P = Transformer.from_crs("EPSG:4326",
    f"+proj=lcc +lat_1={lat0-3} +lat_2={lat0+5} +lat_0={lat0} +lon_0={lon0} +units=km +ellps=WGS84", always_xy=True)
proj = lambda g: transform(lambda x, y, z=None: P.transform(x, y), g)

def load(name, bbox, tol, filt=None):
    d = json.load(open(os.path.join(src, name + ".geojson")))
    B = box(*bbox); res = []
    for f in d["features"]:
        if not f.get("geometry") or (filt and not filt(f["properties"])):
            continue
        g = make_valid(shape(f["geometry"]))
        if not g.intersects(B):
            continue
        g = proj(g.intersection(B))
        if tol:
            g = g.simplify(tol, preserve_topology=True)
        g = make_valid(g)
        if not g.is_empty:
            res.append((f["properties"], g))
    return res

REG = (-100, 30, -48, 62)       # detailed region (10m)
WIDE = (-135, 14, -45, 72)       # continent (50m)
D = {}
D["land_wide"] = unary_union([g for _, g in load("ne_50m_land", WIDE, 2.0)])
D["land"] = unary_union([g for _, g in load("ne_10m_land", REG, 0.15)])
lakes = load("ne_10m_lakes", REG, 0.15) + load("ne_10m_lakes_north_america", REG, 0.12)
D["lakes"] = unary_union([g for _, g in lakes])
D["lakes_wide"] = unary_union([g for p, g in load("ne_50m_lakes", WIDE, 2.0)])
rivers = load("ne_10m_rivers_lake_centerlines", REG, 0.1) + load("ne_10m_rivers_north_america", REG, 0.1)
D["rivers"] = [(p.get("name") or "", p.get("scalerank", 10), g) for p, g in rivers]
D["borders"] = [g for _, g in load("ne_10m_admin_0_boundary_lines_land", WIDE, 0.2)]
D["prov_lines"] = [g for _, g in load("ne_10m_admin_1_states_provinces_lines", REG, 0.2)]
countries = load("ne_50m_admin_0_countries_lakes", WIDE, 1.0, lambda p: p.get("ADM0_A3") in ("USA", "CAN", "MEX"))
D["countries"] = {p["ADM0_A3"]: g for p, g in countries}
D["countries"]["USA"] = D["countries"]["USA"].intersection(proj(box(-127, 22, -64, 50)))  # contiguous US only
provs = load("ne_10m_admin_1_states_provinces_lakes", REG, 0.3, lambda p: p.get("adm0_a3") in ("CAN", "USA"))
D["provinces"] = {p["name"]: g for p, g in provs}

# coastal ripples: inward offsets of the water (sea + big lakes)
water = box(*proj(box(*REG)).bounds).difference(D["land"]).union(
    unary_union([g for g in getattr(D["lakes"], "geoms", [D["lakes"]]) if g.area > 400]))
water = water.simplify(0.8)
D["ripples"] = []
for dist in (2.5, 6, 10.5, 16, 23, 32):
    r = water.buffer(-dist, resolution=4).simplify(0.6).boundary
    D["ripples"].append((dist, r))
wwide = box(*proj(box(*WIDE)).bounds).difference(D["land_wide"]).simplify(6)
D["ripples_wide"] = [(d, wwide.buffer(-d, resolution=3).simplify(4).boundary) for d in (25, 60, 110)]

def P1(lon, lat):
    return P.transform(lon, lat)
D["proj"] = dict(lon0=lon0, lat0=lat0)
pickle.dump(D, open(out, "wb"))
print("ok", {k: (len(v) if isinstance(v, (list, dict)) else v.geom_type) for k, v in D.items() if k != "proj"})
