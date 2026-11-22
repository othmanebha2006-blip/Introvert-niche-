"""@Mecmation built from the user's own image (cars/character_mecmation/mecmation_reference.png), never redrawn.

Everything is matched to the user's animation (cars/character_mecmation/animation_reference.mov, analysed frame by frame):
  - legs + shoes: the original pixels, never move
  - shirt: original pixels, leans (shear about the hem) up to ~3 degrees toward the gesture, like the reference
  - head + beanie: original pixels, rotate with the lean around the neck
  - arms: at rest the original arm pixels; when gesturing, a smooth curved line of the same width/colour as the
          original arm, ending in the ORIGINAL hand pixels (rotated), poses measured from the reference
  - mouth: original smile when silent, otherwise the reference's own mouth drawings (sprites/mouth_*.png)
  - blink: the reference's blink drawing (sprites/eyes_blink.png), 4 frames, about every 3.6 s
"""
import math, os
import numpy as np, cairo
from PIL import Image
from scipy import ndimage as nd

HERE = os.path.dirname(__file__)
CHAR = os.path.join(HERE, "..", "character_mecmation")
REF = os.path.join(CHAR, "mecmation_reference.png")
SKIN = (254 / 255, 209 / 255, 164 / 255)
EYES = [(452, 482, 369, 411), (558, 588, 369, 410)]
MOUTH = (449, 592, 475, 507)
NECK = (518, 592)
HEM = 1000.0
ARM_W = 20.0
MOUTH_XY = (416.9, 447.0)
EYES_XY = (438.4, 343.0)


def _surf(rgba):
    a = rgba[..., 3:4].astype(np.float32) / 255
    pre = (rgba[..., :3].astype(np.float32) * a).astype(np.uint8)
    bgra = np.dstack([pre[..., 2], pre[..., 1], pre[..., 0], rgba[..., 3]]).copy()
    h, w = bgra.shape[:2]
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
    buf = np.ndarray((h, s.get_stride() // 4, 4), np.uint8, s.get_data())
    buf[:, :w] = bgra
    s.mark_dirty()
    return s


def _catmull(pts, n=10):
    pts = [pts[0]] + list(pts) + [pts[-1]]
    out = []
    for i in range(1, len(pts) - 2):
        p0, p1, p2, p3 = pts[i - 1], pts[i], pts[i + 1], pts[i + 2]
        for k in range(n):
            t = k / n; t2 = t * t; t3 = t2 * t
            out.append(tuple(0.5 * ((2 * p1[j]) + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t2
                                    + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t3) for j in (0, 1)))
    out.append(pts[-2])
    return out


class Mecmation:
    def __init__(self, path_png=REF):
        im = np.asarray(Image.open(path_png).convert("RGB")).astype(np.int16)
        H, W, _ = im.shape
        white = im.min(2) > 200
        lab, _ = nd.label(white)
        border = np.unique(np.r_[lab[0], lab[-1], lab[:, 0], lab[:, -1]]); border = border[border > 0]
        bg = np.isin(lab, border)
        fg = ~bg
        lum = im.mean(2)
        alpha = np.where(fg, 255, 0).astype(np.float32)
        edge = nd.binary_dilation(bg, iterations=2) & fg
        alpha[edge] = np.clip((215 - lum[edge]) / (215 - 70) * 255, 0, 255)
        rgb = im.copy(); rgb[edge] = np.minimum(rgb[edge], 40)
        rgba = np.dstack([rgb, alpha]).astype(np.uint8)
        dark = im.max(2) < 90
        self.ink = tuple((im[dark].mean(0) / 255).tolist()) if dark.any() else (0.05, 0.05, 0.05)

        red = (im[..., 0] > 170) & (im[..., 1] < 110) & (im[..., 2] < 110)
        shirt = nd.binary_fill_holes(nd.binary_closing(red, iterations=3))
        lab2, n2 = nd.label(shirt); sizes = nd.sum(shirt, lab2, range(1, n2 + 1))
        shirt = nd.binary_fill_holes(lab2 == (np.argmax(sizes) + 1))
        shirt_d = nd.binary_dilation(shirt, iterations=18)
        yy, xx = np.mgrid[0:H, 0:W]
        head = fg & ((yy < 335) | (((xx - 518) / 232.0) ** 2 + ((yy - 415) / 186.0) ** 2 <= 1)) & (yy < 600)
        arms = fg & ~shirt_d & ~head & (yy > 560) & (yy < 1040) & ((xx < 420) | (xx > 615))
        lab3, n3 = nd.label(arms); sz = nd.sum(arms, lab3, range(1, n3 + 1))
        arms = np.isin(lab3, [i + 1 for i in np.argsort(sz)[::-1][:2]])
        arms = nd.binary_dilation(arms, iterations=3) & fg & ~shirt_d & ~head

        def lay(mask):
            r = rgba.copy(); r[..., 3] = np.where(mask, r[..., 3], 0); return _surf(r)

        self.side = {}
        for sd, sel in (("L", xx < W / 2), ("R", xx >= W / 2)):
            m = arms & sel
            ys, xs = np.where(m)
            top = ys < ys.min() + 30
            sh = np.array([xs[top].mean(), ys[top].mean()])
            st_ = ys < ys.min() + 200
            d = np.array([xs[st_].mean(), ys[st_].mean()]) - sh; d /= np.linalg.norm(d)
            t = (xs - sh[0]) * d[0] + (ys - sh[1]) * d[1]
            perp = (xs - sh[0]) * -d[1] + (ys - sh[1]) * d[0]
            # wrist = first t where the mask gets much wider than the arm line (fingers start)
            tw = None
            for tt in np.arange(60, t.max(), 4):
                sl = np.abs(t - tt) < 3
                if sl.any() and perp[sl].max() - perp[sl].min() > ARM_W * 1.9:
                    tw = tt - 14; break
            tw = tw or t.max() * 0.8
            hand = np.zeros_like(m); hand[ys[t >= tw], xs[t >= tw]] = True
            W0 = tuple(sh + d * tw)
            self.side[sd] = dict(arm=lay(m), hand=lay(hand), sh=tuple(sh), w0=W0, ang=math.degrees(math.atan2(d[1], d[0])))

        body = fg & ~arms & ~head
        b = rgba.copy(); b[..., 3] = np.where(body, b[..., 3], 0)
        under = head & (yy > 560) & red
        b[..., 3] = np.where(under, 255, b[..., 3])
        legs = body & (yy > HEM) & ~shirt_d
        top = b.copy(); top[..., 3] = np.where(legs, 0, top[..., 3])
        bot = b.copy(); bot[..., 3] = np.where(legs, bot[..., 3], 0)
        self.shirt = _surf(top); self.legs = _surf(bot)
        h = rgba.copy(); h[..., 3] = np.where(head, h[..., 3], 0)
        self.head = _surf(h)
        sp = os.path.join(CHAR, "sprites")
        self.sprites = {n[:-4]: cairo.ImageSurface.create_from_png(os.path.join(sp, n)) for n in os.listdir(sp) if n.endswith(".png")}

    # ------------------------------------------------------------------
    def rest_points(self, sd):
        g = self.side[sd]
        (x0, y0), (x1, y1) = g["sh"], g["w0"]
        dx, dy = x1 - x0, y1 - y0
        # start a little inside the shirt so the line is hidden at the shoulder
        return [(x0 - dx * 0.06 + dx * 1.06 * k / 4, y0 - dy * 0.06 + dy * 1.06 * k / 4) for k in range(5)], g["ang"], False

    def draw(self, ctx, st):
        s = st.get("s", 0.6)
        lean = math.radians(st.get("lean", 0.0))
        k = math.tan(lean)
        ctx.save()
        ctx.save(); ctx.translate(st["x"], st["ground"] - 6); ctx.scale(1, 0.12)
        ctx.arc(0, 0, 210 * s, 0, 2 * math.pi); ctx.set_source_rgba(0, 0, 0, 0.14); ctx.fill(); ctx.restore()
        ctx.translate(st["x"] - 518 * s, st["ground"] - 1455 * s)
        ctx.scale(s, s)
        self._paint(ctx, self.legs)
        arms = st["arms"]   # side -> (points, hand_angle_deg, front) or None for the original rest arm
        shear = cairo.Matrix(1, 0, -k, 1, k * HEM, 0)       # x' = x + k*(HEM - y)
        for sd in ("L", "R"):
            if arms[sd] is None:
                ctx.save(); ctx.transform(shear); self._paint(ctx, self.side[sd]["arm"]); ctx.restore()
            elif not arms[sd][2]:
                self._arm(ctx, sd, arms[sd], k)
        ctx.save(); ctx.transform(shear); self._paint(ctx, self.shirt); ctx.restore()
        for sd in ("L", "R"):
            if arms[sd] is not None and arms[sd][2]:
                self._arm(ctx, sd, arms[sd], k)
        ctx.save()
        ctx.translate(k * (HEM - NECK[1]), 0)
        ctx.translate(*NECK); ctx.rotate(lean); ctx.translate(-NECK[0], -NECK[1])
        self._paint(ctx, self.head)
        self._face(ctx, st)
        ctx.restore()
        ctx.restore()

    def _paint(self, ctx, surf, x=0, y=0):
        ctx.set_source_surface(surf, x, y)
        ctx.get_source().set_filter(cairo.FILTER_GOOD)
        ctx.paint()

    def _arm(self, ctx, sd, spec, k):
        pts, ang, front = spec
        pts = [(x + k * (HEM - y), y) for x, y in pts]
        curve = _catmull(pts, 10)
        ctx.move_to(*curve[0])
        for p in curve[1:]:
            ctx.line_to(*p)
        ctx.set_source_rgb(*self.ink[:3]); ctx.set_line_width(ARM_W)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.set_line_join(cairo.LINE_JOIN_ROUND); ctx.stroke()
        g = self.side[sd]
        W = pts[-1]
        ctx.save()
        ctx.translate(*W); ctx.rotate(math.radians(ang - g["ang"])); ctx.translate(-g["w0"][0], -g["w0"][1])
        self._paint(ctx, g["hand"])
        ctx.restore()

    def _skin(self, ctx, cx, cy, rx, ry):
        ctx.save(); ctx.translate(cx, cy); ctx.scale(rx, ry); ctx.arc(0, 0, 1, 0, 2 * math.pi); ctx.restore()
        ctx.set_source_rgb(*SKIN); ctx.fill()

    def _face(self, ctx, st):
        if st.get("blink", 0) > 0.5:
            for x0, x1, y0, y1 in EYES:
                self._skin(ctx, (x0 + x1) / 2, (y0 + y1) / 2, (x1 - x0) / 2 + 7, (y1 - y0) / 2 + 7)
            self._paint(ctx, self.sprites["eyes_blink"], *EYES_XY)
        v = st.get("viseme", "rest")
        if v != "rest":
            x0, x1, y0, y1 = MOUTH
            self._skin(ctx, (x0 + x1) / 2, (y0 + y1) / 2, (x1 - x0) / 2 + 14, (y1 - y0) / 2 + 12)
            name = {"grin": "mouth_grin", "open": "mouth_open", "teeth": "mouth_teeth",
                    "o": "mouth_o" if st.get("open", 0) > 0.45 else "mouth_o_small"}[v]
            self._paint(ctx, self.sprites[name], *MOUTH_XY)


# ---------------------------------------------------------------- poses measured from the reference clip
# per arm: 5 points from the hidden shoulder to the wrist (image px), hand angle (deg, direction of the fingers),
# front (True: drawn over the shirt). The right arm is the mirror of the left one.
def _mir(spec):
    pts, ang, front = spec
    return [(1036 - x, y) for x, y in pts], 180 - ang, front


ARMS = {
    "out":   ([(405, 640), (355, 690), (290, 690), (215, 722), (150, 772)], 125, False),
    "up":    ([(405, 650), (345, 705), (262, 735), (222, 690), (209, 625)], 225, False),
    "side":  ([(404, 640), (351, 684), (256, 672), (186, 668), (129, 672)], 160, False),
    "chest": ([(352, 688), (328, 745), (338, 812), (410, 812), (472, 790)], -35, True),
    "raise": ([(404, 650), (342, 711), (269, 747), (234, 700), (228, 627)], 227, False),
}
GESTURES = {   # gesture -> (screen-left arm, screen-right arm); None = original rest arm
    "rest":            (None, None),
    "arms_out":        ("out", "out"),
    "hands_up":        ("up", "up"),
    "present_R":       ("chest", "side"),
    "present_L":       ("side", None),
    "present_L_chest": ("side", "chest"),
    "chest":           ("chest", None),
    "wave_R":          (None, "raise"),
    "wave":            (None, "raise"),
}
LEAN = {"rest": 0.0, "arms_out": 0.0, "hands_up": -2.0, "present_R": 2.5, "present_L": -2.5, "present_L_chest": -2.5,
        "chest": 1.0, "wave_R": -1.5, "wave": -1.5}


def _spec(sd, name):
    if name is None:
        return None
    s = ARMS[name]
    return s if sd == "L" else _mir(s)


def gesture_arms(mec, g_prev, g_cur, t, wave=0.0):
    out = {}
    for i, sd in enumerate(("L", "R")):
        a = _spec(sd, GESTURES[g_prev][i]); b = _spec(sd, GESTURES[g_cur][i])
        if b is None and (a is None or t >= 1):
            out[sd] = None; continue
        ra = mec.rest_points(sd)
        a = a or ra; b = b or ra
        pts = [(p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t) for p, q in zip(a[0], b[0])]
        d = (b[1] - a[1] + 180) % 360 - 180
        ang = a[1] + d * t
        if GESTURES[g_cur][i] == "raise":
            ang += wave
        out[sd] = (pts, ang, b[2] if t > 0.5 else a[2])
    return out


def gesture_lean(g_prev, g_cur, t):
    return LEAN[g_prev] + (LEAN[g_cur] - LEAN[g_prev]) * t
