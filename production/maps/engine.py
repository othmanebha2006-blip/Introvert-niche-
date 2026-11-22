"""Map-explainer engine: vector map renderer (skia), camera, overlay toolkit, captions.

Everything is drawn as vectors every frame at 1080x1920, so it stays sharp at any zoom.
An episode provides: script.json (+ build/timing.json from tts.py), build/geo.pkl (from geo.py),
and shots.py with CAMERA keys, STYLE keys and an overlay(T, cv, E) function.
"""
import math, os, json, pickle, random
import numpy as np
import skia
from pyproj import Transformer

W, H, FPS = 1080, 1920, 30
ASSETS = os.environ.get("MAP_ASSETS", "")


# ---------------------------------------------------------------- utils
def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x

def ease(x):                      # smooth in-out (cubic)
    x = clamp(x); return 4 * x * x * x if x < .5 else 1 - (-2 * x + 2) ** 3 / 2

def ease_out(x):
    x = clamp(x); return 1 - (1 - x) ** 3

def ease_back(x, s=1.9):          # overshoot pop
    x = clamp(x); return 1 + (s + 1) * (x - 1) ** 3 + s * (x - 1) ** 2

def lerp(a, b, t):
    return a + (b - a) * t

def win(T, t0, t1, fin=0.35, fout=0.35):
    """0..1 visibility for an element shown from t0 to t1 with eased fades."""
    if T < t0 or T > t1 + fout:
        return 0.0
    a = ease_out((T - t0) / fin) if fin > 0 else 1.0
    b = 1 - ease((T - t1) / fout) if T > t1 else 1.0
    return a * b

def hexc(h, a=1.0):
    h = h.lstrip("#"); return skia.Color4f(int(h[0:2], 16) / 255, int(h[2:4], 16) / 255, int(h[4:6], 16) / 255, a)

def mixc(c1, c2, t, a=None):
    c = skia.Color4f(lerp(c1.fR, c2.fR, t), lerp(c1.fG, c2.fG, t), lerp(c1.fB, c2.fB, t), lerp(c1.fA, c2.fA, t))
    if a is not None:
        c.fA = a
    return c

def withA(c, a):
    return skia.Color4f(c.fR, c.fG, c.fB, c.fA * a)


# ---------------------------------------------------------------- fonts
_tf = {}
def typeface(name, wght=None):
    key = (name, wght)
    if key not in _tf:
        tf = skia.Typeface.MakeFromFile(os.path.join(ASSETS, "fonts", name))
        if wght:
            V = skia.FontArguments.VariationPosition
            fa = skia.FontArguments()
            fa.setVariationDesignPosition(V(V.Coordinates([V.Coordinate(int.from_bytes(b"wght", "big"), wght)])))
            tf = tf.makeClone(fa)
        _tf[key] = tf
    return _tf[key]

def font(kind, size):
    f = {
        "serif": lambda: typeface("IMFeENrm28P.ttf"),
        "serif_i": lambda: typeface("IMFeENit28P.ttf"),
        "garamond": lambda: typeface("CormorantGaramond[wght].ttf", 600),
        "garamond_b": lambda: typeface("CormorantGaramond[wght].ttf", 700),
        "sans": lambda: typeface("Inter[opsz,wght].ttf", 600),
        "sans_b": lambda: typeface("Inter[opsz,wght].ttf", 800),
        "sans_x": lambda: typeface("Inter[opsz,wght].ttf", 900),
    }[kind]()
    ft = skia.Font(f, size)
    ft.setSubpixel(True); ft.setEdging(skia.Font.Edging.kSubpixelAntiAlias)
    return ft


# ---------------------------------------------------------------- icons
_img = {}
def icon(name):
    if name not in _img:
        base = name.replace("_3d_default", "").replace("_3d", "")
        for cand in (base, base + "_3d", base + "_3d_default"):
            p = os.path.join(ASSETS, "icons", cand + ".png")
            if os.path.exists(p):
                break
        _img[name] = skia.Image.open(p).withDefaultMipmaps()
    return _img[name]

SAMP = skia.SamplingOptions(skia.FilterMode.kLinear, skia.MipmapMode.kLinear)


def xform(path, m):
    p = skia.Path(path); p.transform(m); return p


# ---------------------------------------------------------------- geometry -> skia paths
def geom_paths(g):
    """shapely geometry -> skia.Path (world km units)."""
    p = skia.Path(); p.setFillType(skia.PathFillType.kEvenOdd)
    def ring(coords, close):
        c = list(coords)
        if len(c) < 2:
            return
        p.addPoly([skia.Point(x, y) for x, y in c], close)
    def add(gg):
        t = gg.geom_type
        if t == "Polygon":
            ring(gg.exterior.coords, True)
            for r in gg.interiors:
                ring(r.coords, True)
        elif t == "LineString" or t == "LinearRing":
            ring(gg.coords, False)
        elif hasattr(gg, "geoms"):
            for s in gg.geoms:
                add(s)
    add(g)
    return p


class Geo:
    def __init__(self, pkl):
        D = pickle.load(open(pkl, "rb"))
        pr = D["proj"]
        lat0, lon0 = pr["lat0"], pr["lon0"]
        self.P = Transformer.from_crs("EPSG:4326",
            f"+proj=lcc +lat_1={lat0-3} +lat_2={lat0+5} +lat_0={lat0} +lon_0={lon0} +units=km +ellps=WGS84", always_xy=True)
        gp = geom_paths
        self.land = gp(D["land"]); self.lakes = gp(D["lakes"])
        self.land_w = gp(D["land_wide"]); self.lakes_w = gp(D["lakes_wide"])
        self.ripples = [(d, gp(g)) for d, g in D["ripples"]]
        self.ripples_w = [(d, gp(g)) for d, g in D["ripples_wide"]]
        self.rivers = {}
        for name, rank, g in D["rivers"]:
            r = min(int(rank or 10), 12)
            self.rivers.setdefault(r, skia.Path()).addPath(gp(g))
        self.named_rivers = {}
        for name, rank, g in D["rivers"]:
            if name:
                self.named_rivers.setdefault(name, skia.Path()).addPath(gp(g))
        self.borders = skia.Path()
        for g in D["borders"]:
            self.borders.addPath(gp(g))
        self.prov = skia.Path()
        for g in D["prov_lines"]:
            self.prov.addPath(gp(g))
        self.countries = {k: gp(g) for k, g in D["countries"].items()}
        self.provinces = {k: gp(g) for k, g in D["provinces"].items()}
        self.shapes = D

    def xy(self, lon, lat):
        return self.P.transform(lon, lat)


# ---------------------------------------------------------------- camera
class Camera:
    """keys: list of (time, lon, lat, width_km). Center interpolated linearly, zoom in log space, eased."""
    def __init__(self, geo, keys):
        self.geo = geo
        self.keys = sorted(keys, key=lambda k: k[0])

    def at(self, T):
        ks = self.keys
        if T <= ks[0][0]:
            k = ks[0]; return self._xy(k)
        for a, b in zip(ks, ks[1:]):
            if a[0] <= T <= b[0]:
                u = (T - a[0]) / max(1e-6, b[0] - a[0])
                e = u if (len(a) > 4 and a[4] == "lin") else ease(u)
                ax, ay, aw = self._xy(a); bx, by, bw = self._xy(b)
                w = math.exp(lerp(math.log(aw), math.log(bw), e))
                return lerp(ax, bx, e), lerp(ay, by, e), w
        return self._xy(ks[-1])

    def _xy(self, k):
        x, y = self.geo.xy(k[1], k[2]); return x, y, k[3]

    def matrix(self, T):
        cx, cy, wkm = self.at(T)
        s = W / wkm
        m = skia.Matrix()
        m.setTranslate(W / 2, H / 2); m.preScale(s, -s); m.preTranslate(-cx, -cy)
        return m, s


# ---------------------------------------------------------------- styles
STYLES = {
    "modern": dict(sea0="#163f5f", sea1="#0d2a44", land="#6f8a55", land2="#8fa266", coast_in="#2f4527",
                   coast_out="#9fd3e6", ripple="#7fb6cf", river="#5fa0c8", border="#f1e7cf", prov="#e8ddc0",
                   lake="#1d5277", vignette=0.55, grain=0.10),
    "vintage": dict(sea0="#7d9aa0", sea1="#5e7d86", land="#dcc59c", land2="#e8d7b4", coast_in="#8a6a45",
                    coast_out="#e6dfc8", ripple="#c4d2cc", river="#6f939c", border="#7a5a3c", prov="#9b7d5c",
                    lake="#86a3a8", vignette=0.45, grain=0.16),
}

def style_mix(t):
    """t=0 modern, 1 vintage. Returns dict of Color4f + floats."""
    a, b = STYLES["modern"], STYLES["vintage"]
    out = {}
    for k in a:
        out[k] = mixc(hexc(a[k]), hexc(b[k]), t) if isinstance(a[k], str) else lerp(a[k], b[k], t)
    return out


def make_textures(seed=7):
    rng = np.random.default_rng(seed)
    def fbm(n, scales):
        acc = np.zeros((n, n))
        for sc, amp in scales:
            f = np.fft.fft2(rng.standard_normal((n, n)))
            fy = np.fft.fftfreq(n)[:, None]; fx = np.fft.fftfreq(n)[None, :]
            r = np.sqrt(fx * fx + fy * fy)
            filt = np.exp(-(r * sc) ** 2)
            v = np.real(np.fft.ifft2(f * filt)); v = (v - v.mean()) / (v.std() + 1e-9)
            acc += v * amp
        return acc
    n = 1024
    mott = fbm(n, [(40, 1.0), (12, 0.5), (4, 0.25)])
    grain = rng.standard_normal((n, n)) * 0.6 + fbm(n, [(1.5, 0.6)])
    def to_img(v, lo=-2.5, hi=2.5):
        g = np.clip((v - lo) / (hi - lo), 0, 1)
        a = np.zeros((n, n, 4), np.uint8)
        a[..., 0] = a[..., 1] = a[..., 2] = (g * 255).astype(np.uint8); a[..., 3] = 255
        return skia.Image.fromarray(a, colorType=skia.kRGBA_8888_ColorType)
    return to_img(mott), to_img(grain)


# ---------------------------------------------------------------- map renderer
class MapRenderer:
    def __init__(self, geo):
        self.g = geo
        self.mott, self.grain = make_textures()

    def draw(self, cv, m, s, vint, cx_screen_shift=(0, 0), extra=None):
        st = style_mix(vint)
        g = self.g
        # sea gradient (screen space)
        cv.drawPaint(skia.Paint(Shader=skia.GradientShader.MakeLinear(
            [skia.Point(0, 0), skia.Point(0, H)], [st["sea0"].toColor(), st["sea1"].toColor()])))
        detail = clamp((s - 0.35) / 0.35)  # 0 => continental layers, 1 => detailed
        layers = []
        if detail < 1:
            layers.append((1.0, g.land_w, g.lakes_w, g.ripples_w, 0))
        if detail > 0:
            layers.append((detail, g.land, g.lakes, g.ripples, 1))
        for alpha, land, lakes, ripples, det in layers:
            if alpha < 1:
                cv.saveLayerAlpha(None, int(alpha * 255))
            cv.save(); cv.concat(m)
            # ripples in the water (fade with on-screen spacing)
            for i, (d, rp) in enumerate(ripples):
                spacing = d * s
                fa = clamp((spacing - 5) / 18) * (1 - i / (len(ripples) + 1)) * 0.75
                if fa <= 0.01:
                    continue
                cv.drawPath(rp, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style,
                                           StrokeWidth=1.7 / s, Color4f=withA(st["ripple"], fa)))
            # coast outer glow
            cv.drawPath(land, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=7 / s,
                        Color4f=withA(st["coast_out"], 0.55), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 5 / s)))
            # land fill + world-space mottling
            cv.drawPath(land, skia.Paint(AntiAlias=True, Color4f=st["land"]))
            cv.restore()
            # textures, clipped to land
            cv.save(); cv.concat(m); cv.clipPath(land, skia.ClipOp.kIntersect, True)
            cv.resetMatrix()
            q = m.mapXY(0, 0); cx, cy = q.x(), q.y()
            tm = skia.Matrix(); tm.setTranslate(cx % 1024, cy % 1024); tm.preScale(2.8, 2.8)
            cv.drawPaint(skia.Paint(Shader=self.mott.makeShader(skia.TileMode.kRepeat, skia.TileMode.kRepeat, SAMP, tm),
                                    BlendMode=skia.BlendMode.kOverlay, Alpha=int(255 * 0.2)))
            cv.drawPaint(skia.Paint(Color4f=withA(st["land2"], 1.0), BlendMode=skia.BlendMode.kSoftLight, Alpha=90))
            # inner coast shadow
            cv.concat(m)
            cv.drawPath(land, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=10 / s,
                        Color4f=withA(st["coast_in"], 0.45), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 6 / s)))
            cv.restore()
            # lakes
            cv.save(); cv.concat(m)
            cv.drawPath(lakes, skia.Paint(AntiAlias=True, Color4f=st["lake"]))
            cv.drawPath(lakes, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=1.4 / s,
                        Color4f=withA(st["coast_in"], 0.55)))
            if det:
                for rank, path in g.rivers.items():
                    vis = clamp((s * (13 - rank) / 6 - 0.7) / 1.2)
                    if vis <= 0.02:
                        continue
                    wpx = max(0.8, 2.6 - rank * 0.17)
                    cv.drawPath(path, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=wpx / s,
                                StrokeCap=skia.Paint.kRound_Cap, StrokeJoin=skia.Paint.kRound_Join,
                                Color4f=withA(st["river"], 0.85 * vis)))
                pv = clamp((s - 0.5) / 0.6)
                if pv > 0:
                    cv.drawPath(g.prov, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=1.6 / s,
                                Color4f=withA(st["prov"], 0.55 * pv), PathEffect=skia.DashPathEffect.Make([7 / s, 5 / s], 0)))
            cv.drawPath(g.borders, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=2.4 / s,
                        Color4f=withA(st["border"], 0.75), PathEffect=skia.DashPathEffect.Make([2.5 / s, 5 / s], 0),
                        StrokeCap=skia.Paint.kRound_Cap))
            cv.restore()
            if alpha < 1:
                cv.restore()
        if extra:
            extra(cv, m, s, st)

    def finish(self, cv, vint):
        st = style_mix(vint)
        # paper grain (screen space) + vignette
        cv.drawPaint(skia.Paint(Shader=self.grain.makeShader(skia.TileMode.kRepeat, skia.TileMode.kRepeat, SAMP),
                                BlendMode=skia.BlendMode.kOverlay, Alpha=int(255 * st["grain"])))
        cv.drawPaint(skia.Paint(Shader=skia.GradientShader.MakeRadial(
            skia.Point(W / 2, H * 0.46), H * 0.72,
            [skia.Color4f(0, 0, 0, 0).toColor(), skia.Color4f(0, 0, 0, 0).toColor(), skia.Color4f(0, 0, 0, st["vignette"]).toColor()],
            [0.0, 0.55, 1.0])))


# ---------------------------------------------------------------- overlay toolkit (screen space)
class Draw:
    def __init__(self, cv, m, s, st, T):
        self.cv, self.m, self.s, self.st, self.T = cv, m, s, st, T

    def pt(self, geo, lon, lat):
        x, y = geo.xy(lon, lat); q = self.m.mapXY(x, y); return q.x(), q.y()

    def world_path(self, path):
        return xform(path, self.m)

    # -- text
    def text(self, txt, x, y, size, kind="garamond_b", color="#2b1d12", alpha=1.0, halo="#f4ead2", halo_a=0.85,
             align="center", tracking=0.0, glow=None, scale=1.0, shadow=0.0):
        if alpha <= 0.003:
            return
        cv = self.cv
        f = font(kind, size)
        widths = [f.measureText(ch) for ch in txt]
        total = sum(widths) + tracking * size * (len(txt) - 1)
        x0 = x - total / 2 if align == "center" else (x - total if align == "right" else x)
        cv.save(); cv.translate(x, y); cv.scale(scale, scale); cv.translate(-x, -y)
        def run(paint):
            xx = x0
            for ch, w in zip(txt, widths):
                cv.drawString(ch, xx, y, f, paint); xx += w + tracking * size
        if shadow:
            run(skia.Paint(AntiAlias=True, Color4f=skia.Color4f(0, 0, 0, 0.55 * alpha * shadow),
                           MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, size * 0.08)))
        if glow:
            run(skia.Paint(AntiAlias=True, Color4f=withA(hexc(glow), 0.9 * alpha),
                           MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, size * 0.16)))
        if halo:
            run(skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=size * 0.16,
                           StrokeJoin=skia.Paint.kRound_Join, Color4f=withA(hexc(halo), halo_a * alpha),
                           MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, size * 0.05)))
        run(skia.Paint(AntiAlias=True, Color4f=withA(hexc(color), alpha)))
        cv.restore()
        return total * scale

    def label(self, txt, x, y, a, size=46, dy=-34, kind="garamond_b", color="#2b1d12", halo="#f4ead2"):
        """map place label; rises in as it appears."""
        if a <= 0:
            return
        size *= 1.22
        self.text(txt, x, y + dy + (1 - a) * 14, size, kind=kind, color=color, alpha=a, halo=halo, tracking=0.02)

    # -- markers
    def dot(self, x, y, a, r=11, color="#b3261e", ring=True, pulse=None):
        if a <= 0:
            return
        cv = self.cv
        if pulse is not None:
            for k in range(2):
                ph = (pulse * 0.8 + k * 0.5) % 1.0
                cv.drawCircle(x, y, r + ph * r * 4.5, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style,
                              StrokeWidth=3, Color4f=withA(hexc(color), a * (1 - ph) * 0.8)))
        cv.drawCircle(x, y + 2, r * a + 2, skia.Paint(AntiAlias=True, Color4f=skia.Color4f(0, 0, 0, 0.35 * a),
                      MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 4)))
        if ring:
            cv.drawCircle(x, y, (r + 4) * ease_back(a), skia.Paint(AntiAlias=True, Color4f=withA(hexc("#fff8e8"), a)))
        cv.drawCircle(x, y, r * ease_back(a), skia.Paint(AntiAlias=True, Color4f=withA(hexc(color), a)))

    def glow_blob(self, x, y, r, color, a):
        if a <= 0:
            return
        c = hexc(color)
        self.cv.drawCircle(x, y, r, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial(
            skia.Point(x, y), r, [withA(c, 0.85 * a).toColor(), withA(c, 0.35 * a).toColor(), withA(c, 0).toColor()], [0, 0.4, 1])))

    def icon(self, name, x, y, size, a, pop=True, rot=0.0, bob=0.0, shadow=True, flip=False):
        if a <= 0.003:
            return
        img = icon(name)
        sc = ease_back(a) if pop else 1.0
        sz = size * max(0.0, sc)
        y = y + math.sin(self.T * 2.2 + x * 0.01) * bob
        cv = self.cv
        cv.save(); cv.translate(x, y); cv.rotate(rot)
        if flip:
            cv.scale(-1, 1)
        r = skia.Rect.MakeXYWH(-sz / 2, -sz / 2, sz, sz)
        if shadow:
            cv.drawImageRect(img, r.makeOffset(0, sz * 0.07), SAMP, skia.Paint(Alpha=int(110 * clamp(a)),
                ColorFilter=skia.ColorFilters.Blend(skia.ColorBLACK, skia.BlendMode.kSrcIn),
                MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, sz * 0.05)))
        cv.drawImageRect(img, r, SAMP, skia.Paint(Alpha=int(255 * clamp(a * 1.6))))
        cv.restore()

    # -- lines
    def arc_path(self, p0, p1, bulge=0.25):
        (x0, y0), (x1, y1) = p0, p1
        mx, my = (x0 + x1) / 2, (y0 + y1) / 2
        dx, dy = x1 - x0, y1 - y0
        cx, cy = mx - dy * bulge, my + dx * bulge
        return skia.Path().moveTo(x0, y0).quadTo(cx, cy, x1, y1)

    def stroke_progress(self, path, prog, color, width=6, a=1.0, glow=True, dash=None, head=False, phase=0.0, tail=0.0):
        """draw path from `tail` to `prog` (fractions of its length)."""
        if a <= 0 or prog <= 0:
            return None
        pm = skia.PathMeasure(path, False)
        L = pm.getLength()
        if L <= 0:
            return None
        seg = skia.Path(); pm.getSegment(L * clamp(tail), L * clamp(prog), seg, True)
        c = hexc(color) if isinstance(color, str) else color
        cv = self.cv
        if glow:
            cv.drawPath(seg, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=width * 3.2,
                        StrokeCap=skia.Paint.kRound_Cap, StrokeJoin=skia.Paint.kRound_Join,
                        Color4f=withA(c, 0.45 * a), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, width * 1.4)))
        p = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=width, StrokeCap=skia.Paint.kRound_Cap,
                       StrokeJoin=skia.Paint.kRound_Join, Color4f=withA(c, a))
        if dash:
            p.setPathEffect(skia.DashPathEffect.Make(dash, phase))
        cv.drawPath(seg, p)
        if glow:
            cv.drawPath(seg, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=max(1.5, width * 0.35),
                        StrokeCap=skia.Paint.kRound_Cap, StrokeJoin=skia.Paint.kRound_Join, Color4f=withA(hexc("#fffbe8"), 0.8 * a),
                        PathEffect=skia.DashPathEffect.Make(dash, phase) if dash else None))
        pos, tan = pm.getPosTan(L * clamp(prog))
        if head and prog > 0.02:
            ang = math.atan2(tan.y(), tan.x())
            hs = width * 3.2
            tri = skia.Path()
            tri.moveTo(pos.x() + math.cos(ang) * hs, pos.y() + math.sin(ang) * hs)
            tri.lineTo(pos.x() + math.cos(ang + 2.5) * hs, pos.y() + math.sin(ang + 2.5) * hs)
            tri.lineTo(pos.x() + math.cos(ang - 2.5) * hs, pos.y() + math.sin(ang - 2.5) * hs)
            tri.close()
            cv.drawPath(tri, skia.Paint(AntiAlias=True, Color4f=withA(c, a)))
        return pos.x(), pos.y(), math.atan2(tan.y(), tan.x())

    def pos_on(self, path, f):
        pm = skia.PathMeasure(path, False); L = pm.getLength()
        pos, tan = pm.getPosTan(L * clamp(f))
        return pos.x(), pos.y(), math.atan2(tan.y(), tan.x())

    def region(self, path_world, color, a, outline=True, glow=True, fill_a=0.38, pulse=0.0):
        if a <= 0:
            return
        cv = self.cv; c = hexc(color)
        sp = xform(path_world, self.m)
        cv.drawPath(sp, skia.Paint(AntiAlias=True, Color4f=withA(c, fill_a * a * (1 + 0.25 * pulse))))
        if glow:
            cv.drawPath(sp, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=14, Color4f=withA(c, 0.5 * a),
                        MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 9)))
        if outline:
            cv.drawPath(sp, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=3.5, Color4f=withA(c, 0.95 * a),
                        StrokeJoin=skia.Paint.kRound_Join))

    def river_glow(self, path_world, color, a, width=5, prog=1.0):
        if a <= 0:
            return
        sp = xform(path_world, self.m)
        if prog >= 1:
            c = hexc(color)
            self.cv.drawPath(sp, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=width * 3.5,
                             StrokeCap=skia.Paint.kRound_Cap, StrokeJoin=skia.Paint.kRound_Join, Color4f=withA(c, 0.5 * a),
                             MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, width * 1.6)))
            self.cv.drawPath(sp, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=width,
                             StrokeCap=skia.Paint.kRound_Cap, StrokeJoin=skia.Paint.kRound_Join, Color4f=withA(c, a)))
            self.cv.drawPath(sp, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=width * 0.35,
                             StrokeCap=skia.Paint.kRound_Cap, StrokeJoin=skia.Paint.kRound_Join, Color4f=withA(hexc("#ffffff"), 0.7 * a)))
        else:
            self.stroke_progress(sp, prog, color, width, a)

    # -- cards
    def title(self, txt, a, y=330, size=150, kind="serif", color="#fbf3df", sub=None, sub_size=54):
        """big centred date/title card with a letter-by-letter reveal and soft glow."""
        if a <= 0:
            return
        f = font(kind, size)
        n = len(txt); widths = [f.measureText(ch) for ch in txt]
        total = sum(widths) + 0.04 * size * (n - 1)
        x = W / 2 - total / 2
        cv = self.cv
        for i, (ch, w) in enumerate(zip(txt, widths)):
            la = clamp(a * (n + 3) / 3 - i * 1.0 / 3) if a < 1 else 1.0
            la = ease_out(la) * (a if a < 1 and la >= 1 else 1)
            yy = y + (1 - la) * 26
            for p in (skia.Paint(AntiAlias=True, Color4f=skia.Color4f(0, 0, 0, 0.45 * la),
                                 MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, size * 0.09)),
                      skia.Paint(AntiAlias=True, Color4f=withA(hexc("#fff1c9"), 0.55 * la),
                                 MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, size * 0.18)),
                      skia.Paint(AntiAlias=True, Color4f=withA(hexc(color), la))):
                cv.drawString(ch, x, yy, f, p)
            x += w + 0.04 * size
        if sub:
            self.text(sub, W / 2, y + sub_size * 1.5, sub_size, kind="serif_i", color=color, alpha=a, halo=None,
                      shadow=1.0)

    def card(self, x, y, w, h, a, color="#f3e6c8", radius=26):
        if a <= 0:
            return
        cv = self.cv
        r = skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x - w / 2, y - h / 2, w, h), radius, radius)
        cv.drawRRect(r.makeOffset(0, 14) if hasattr(r, "makeOffset") else r, skia.Paint(AntiAlias=True, Color4f=skia.Color4f(0, 0, 0, 0.38 * a),
                     MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 22)))
        cv.drawRRect(r, skia.Paint(AntiAlias=True, Color4f=withA(hexc(color), 0.97 * a)))
        cv.drawRRect(r, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=3,
                     Color4f=withA(hexc("#9c7a4c"), 0.8 * a)))

    def bar(self, x, y, h, a, color="#f2c14e", w=86, label=None, value=None, fade=1.0):
        """3D-ish population column rising from (x,y)."""
        if a <= 0:
            return
        cv = self.cv; c = hexc(color)
        hh = h * ease_out(a)
        grow = a; a = a * fade
        d = w * 0.38
        front = skia.Path().addRect(skia.Rect.MakeLTRB(x - w / 2, y - hh, x + w / 2, y))
        side = skia.Path(); side.moveTo(x + w / 2, y); side.lineTo(x + w / 2 + d, y - d * 0.55)
        side.lineTo(x + w / 2 + d, y - hh - d * 0.55); side.lineTo(x + w / 2, y - hh); side.close()
        top = skia.Path(); top.moveTo(x - w / 2, y - hh); top.lineTo(x + w / 2, y - hh)
        top.lineTo(x + w / 2 + d, y - hh - d * 0.55); top.lineTo(x - w / 2 + d, y - hh - d * 0.55); top.close()
        glow = skia.Paint(AntiAlias=True, Color4f=withA(c, 0.5 * a), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 26))
        cv.drawPath(front, glow)
        cv.drawPath(front, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear(
            [skia.Point(x - w / 2, 0), skia.Point(x + w / 2, 0)], [withA(c, a).toColor(), withA(mixc(c, hexc("#ffffff"), 0.25), a).toColor()])))
        cv.drawPath(side, skia.Paint(AntiAlias=True, Color4f=withA(mixc(c, hexc("#000000"), 0.32), a)))
        cv.drawPath(top, skia.Paint(AntiAlias=True, Color4f=withA(mixc(c, hexc("#ffffff"), 0.45), a)))
        if value:
            self.text(value(grow), x + d / 2, y - hh - d - 22, 64, kind="sans_x", color="#ffffff", alpha=a, halo=None, shadow=1.2)
        if label:
            self.text(label, x + d / 2, y + 62, 44, kind="sans_b", color="#ffffff", alpha=a, halo=None, shadow=1.2)


# ---------------------------------------------------------------- captions
class Captions:
    """phrase captions (2-5 words), active word highlighted; centred at y."""
    def __init__(self, timing, y=1400, size=68, maxchars=22):
        self.pages = []
        for b in timing["beats"]:
            cur = []
            for w in b["words"]:
                cur.append(w)
                txt = " ".join(x["w"] for x in cur)
                if len(txt) >= maxchars - 6 and (w["w"][-1] in ",.?!" or len(txt) >= maxchars) or w["w"][-1] in ".?!":
                    self.pages.append(cur); cur = []
            if cur:
                self.pages.append(cur)
        self.y, self.size = y, size

    def draw(self, cv, T, alpha=1.0):
        page = None
        for i, p in enumerate(self.pages):
            end = self.pages[i + 1][0]["s"] if i + 1 < len(self.pages) else p[-1]["e"] + 0.8
            end = min(end, p[-1]["e"] + 0.6)
            if p[0]["s"] - 0.05 <= T < end:
                page = p; t0 = p[0]["s"] - 0.05; break
        if not page:
            return
        f = font("sans_b", self.size)
        words = [w["w"] for w in page]
        sp = f.measureText(" ")
        widths = [f.measureText(w) for w in words]
        total = sum(widths) + sp * (len(words) - 1)
        x = W / 2 - total / 2
        intro = ease_out((T - t0) / 0.18)
        y = self.y + (1 - intro) * 10
        for w, wd, wt in zip(words, widths, page):
            active = wt["s"] - 0.03 <= T
            col = hexc("#ffffff") if active else hexc("#ffffff", 0.55)
            for p in (skia.Paint(AntiAlias=True, Color4f=skia.Color4f(0, 0, 0, 0.75 * alpha * intro),
                                 MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 7)),
                      skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=7, StrokeJoin=skia.Paint.kRound_Join,
                                 Color4f=skia.Color4f(0.05, 0.05, 0.08, 0.55 * alpha * intro)),
                      skia.Paint(AntiAlias=True, Color4f=withA(col, alpha * intro))):
                cv.drawString(w, x, y, f, p)
            x += wd + sp
