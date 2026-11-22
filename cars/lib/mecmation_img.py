"""@Mecmation built from the user's own image, pixel for pixel (cars/character_mecmation/mecmation_reference.png).

Nothing is redrawn. The image is cut into layers and only these move, as in the user's reference animation
(cars/character_mecmation/animation_reference.mov):
  - arms: each arm is cut at the elbow into two original pieces (upper arm, forearm+hand) that rotate like a cut-out puppet
  - head: the original head + beanie layer tilts very slightly around the neck
  - mouth: original smile when silent; while talking it is covered with skin and a mouth shape is drawn (lip sync)
  - eyes: blink / happy closed eyes;  brows: the original brow pixels are lifted
Legs, shoes, shirt, emblem, beanie and text never change.
"""
import math, os
import numpy as np, cairo
from PIL import Image
from scipy import ndimage as nd
from ink import qbez, ellipse, path, hexc, INK

REF = os.path.join(os.path.dirname(__file__), "..", "character_mecmation", "mecmation_reference.png")
SKIN = (254 / 255, 208 / 255, 164 / 255)
BROWS = [(437, 485, 314, 340), (552, 601, 314, 340)]     # x0,x1,y0,y1 in image px
EYES = [(452, 482, 369, 411), (558, 588, 369, 410)]
MOUTH = (449, 592, 475, 507)
NECK = (518, 592)
ARM_W = 20


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


class Mecmation:
    def __init__(self, path_png=REF):
        im = np.asarray(Image.open(path_png).convert("RGB")).astype(np.int16)
        H, W, _ = im.shape
        self.W, self.H = W, H
        # background = white connected to the border; soft alpha on the anti-aliased edge
        white = im.min(2) > 200
        lab, _ = nd.label(white)
        border = np.unique(np.r_[lab[0], lab[-1], lab[:, 0], lab[:, -1]]); border = border[border > 0]
        bg = np.isin(lab, border)
        fg = ~bg
        lum = im.mean(2)
        alpha = np.where(fg, 255, 0).astype(np.float32)
        edge = nd.binary_dilation(bg, iterations=2) & fg
        alpha[edge] = np.clip((215 - lum[edge]) / (215 - 70) * 255, 0, 255)
        # anti-aliased edge pixels become ink coloured, so no white halo
        rgb = im.copy()
        rgb[edge] = np.minimum(rgb[edge], 40)
        rgba = np.dstack([rgb, alpha]).astype(np.uint8)

        red = (im[..., 0] > 170) & (im[..., 1] < 110) & (im[..., 2] < 110)
        shirt = nd.binary_fill_holes(nd.binary_closing(red, iterations=3))
        lab2, n2 = nd.label(shirt); sizes = nd.sum(shirt, lab2, range(1, n2 + 1))
        shirt = lab2 == (np.argmax(sizes) + 1)
        shirt = nd.binary_fill_holes(shirt)
        shirt_d = nd.binary_dilation(shirt, iterations=18)
        yy, xx = np.mgrid[0:H, 0:W]
        head = fg & ((yy < 335) | (((xx - 518) / 232.0) ** 2 + ((yy - 415) / 186.0) ** 2 <= 1)) & (yy < 600)
        arms = fg & ~shirt_d & ~head & (yy > 560) & (yy < 1040) & ((xx < 420) | (xx > 615))
        # keep only the two big arm components, then take their anti-aliased fringe too
        lab3, n3 = nd.label(arms)
        sz = nd.sum(arms, lab3, range(1, n3 + 1))
        keep = [i + 1 for i in np.argsort(sz)[::-1][:2]]
        arms = np.isin(lab3, keep)
        arms = nd.binary_dilation(arms, iterations=3) & fg & ~shirt_d & ~head
        self.side = {}
        for side, sel in (("L", xx < W / 2), ("R", xx >= W / 2)):
            m = arms & sel
            ys, xs = np.where(m)
            top = ys < ys.min() + 30
            sh = np.array([xs[top].mean(), ys[top].mean()])
            # straight part of the arm -> axis
            st_ = ys < ys.min() + 230
            d = np.array([xs[st_].mean(), ys[st_].mean()]) - sh
            d /= np.linalg.norm(d)
            t = (xs - sh[0]) * d[0] + (ys - sh[1]) * d[1]
            perp = np.abs((xs - sh[0]) * -d[1] + (ys - sh[1]) * d[0])
            core = perp < ARM_W * 1.2
            wrist_t = t[core].max() if core.any() else t.max()
            # the wrist is where the straight line ends and fingers start
            hand_start = np.percentile(t, 70)
            L_arm = hand_start
            el_t = L_arm * 0.5
            up = np.zeros_like(m); fo = np.zeros_like(m)
            up[ys[t < el_t], xs[t < el_t]] = True
            fo[ys[t >= el_t], xs[t >= el_t]] = True
            shp = tuple(sh - d * 6)                     # pivot slightly inside the shirt
            elb = tuple(sh + d * el_t)
            ang = math.atan2(d[1], d[0])
            def lay(mask):
                r = rgba.copy(); r[..., 3] = np.where(mask, r[..., 3], 0); return _surf(r)
            self.side[side] = dict(up=lay(up), fo=lay(fo), sh=shp, el=elb, ang=ang, lu=math.dist(shp, elb))
        body = fg & ~arms & ~head
        b = rgba.copy(); b[..., 3] = np.where(body, b[..., 3], 0)
        # the head covers the top of the shirt; keep shirt pixels under the head so a tilt never shows a hole
        under = head & (yy > 560) & red
        b[..., 3] = np.where(under, 255, b[..., 3])
        self.body = _surf(b)
        h = rgba.copy(); h[..., 3] = np.where(head, h[..., 3], 0)
        self.head = _surf(h)
        self.brows = []
        for x0, x1, y0, y1 in BROWS:
            c = rgba[y0 - 3:y1 + 3, x0 - 3:x1 + 3].copy()
            dark = c[..., :3].max(2) < 120
            c[..., 3] = np.where(dark, 255, 0)
            self.brows.append((_surf(c), x0 - 3, y0 - 3))

    # ------------------------------------------------------------------
    def arm_angles_rest(self, side):
        return self.side[side]["ang"]

    def draw(self, ctx, st):
        s = st.get("s", 0.6)
        ctx.save()
        k = 1.0
        ctx.save(); ctx.translate(st["x"], st["ground"] - 6); ctx.scale(1, 0.12)
        ctx.arc(0, 0, 210 * s, 0, 2 * math.pi); ctx.set_source_rgba(0, 0, 0, 0.14); ctx.fill(); ctx.restore()
        ctx.translate(st["x"] - 518 * s, st["ground"] - 1455 * s)
        ctx.scale(s, s)
        arms = st["arms"]                     # {"L": (upper_angle, fore_angle), "R": ...} absolute radians
        front = st.get("front", set())
        for sd in ("L", "R"):
            self._upper(ctx, sd, arms[sd][0])
        for sd in ("L", "R"):
            if sd not in front:
                self._fore(ctx, sd, *arms[sd])
        self._paint(ctx, self.body)
        for sd in ("L", "R"):
            if sd in front:
                self._fore(ctx, sd, *arms[sd])
        # head
        ctx.save()
        ctx.translate(*NECK); ctx.rotate(st.get("tilt", 0)); ctx.translate(-NECK[0], -NECK[1])
        self._paint(ctx, self.head)
        self._face(ctx, st)
        ctx.restore()
        ctx.restore()

    def _paint(self, ctx, surf):
        ctx.set_source_surface(surf, 0, 0)
        ctx.get_source().set_filter(cairo.FILTER_GOOD)
        ctx.paint()

    def _upper(self, ctx, sd, a):
        g = self.side[sd]
        ctx.save()
        ctx.translate(*g["sh"]); ctx.rotate(a - g["ang"]); ctx.translate(-g["sh"][0], -g["sh"][1])
        self._paint(ctx, g["up"])
        ctx.restore()

    def _fore(self, ctx, sd, au, af):
        g = self.side[sd]
        ex = g["sh"][0] + math.cos(au) * g["lu"]; ey = g["sh"][1] + math.sin(au) * g["lu"]
        ctx.save()
        ctx.translate(ex, ey); ctx.rotate(af - g["ang"]); ctx.translate(-g["el"][0], -g["el"][1])
        self._paint(ctx, g["fo"])
        ctx.restore()
        # round elbow joint hides the cut
        ctx.arc(ex, ey, ARM_W / 2 + 0.5, 0, 2 * math.pi); ctx.set_source_rgba(*INK); ctx.fill()

    # ------------------------------------------------------------------ face
    def _skin(self, ctx, cx, cy, rx, ry):
        ctx.save(); ctx.translate(cx, cy); ctx.scale(rx, ry); ctx.arc(0, 0, 1, 0, 2 * math.pi); ctx.restore()
        ctx.set_source_rgb(*SKIN); ctx.fill()

    def _face(self, ctx, st):
        lift = st.get("brow_lift", 0.0)
        if lift > 0.5:
            for (surf, x0, y0), (bx0, bx1, by0, by1) in zip(self.brows, BROWS):
                self._skin(ctx, (bx0 + bx1) / 2, (by0 + by1) / 2, (bx1 - bx0) / 2 + 8, (by1 - by0) / 2 + 7)
                ctx.set_source_surface(surf, x0, y0 - lift); ctx.paint()
        if st.get("happy", 0) > 0.5 or st.get("blink", 0) > 0.5:
            for x0, x1, y0, y1 in EYES:
                cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
                self._skin(ctx, cx, cy, (x1 - x0) / 2 + 6, (y1 - y0) / 2 + 6)
                if st.get("happy", 0) > 0.5:
                    pts = qbez((cx - 19, cy + 8), (cx, cy - 18), (cx + 19, cy + 8), 12)
                else:
                    pts = qbez((cx - 17, cy + 2), (cx, cy + 9), (cx + 17, cy + 2), 12)
                self._stroke(ctx, pts, 9)
        v = st.get("viseme", "rest")
        if v != "rest":
            x0, x1, y0, y1 = MOUTH
            self._skin(ctx, (x0 + x1) / 2, (y0 + y1) / 2, (x1 - x0) / 2 + 18, (y1 - y0) / 2 + 13)
            self._mouth(ctx, v, st.get("open", 0.5))

    def _stroke(self, ctx, pts, w):
        path(ctx, pts, False)
        ctx.set_source_rgba(*INK); ctx.set_line_width(w)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.set_line_join(cairo.LINE_JOIN_ROUND); ctx.stroke()

    def _mouth(self, ctx, v, o):
        x, y = 520, 486
        if v == "o":
            m = ellipse(x, y + 6, 13 + 7 * o, 15 + 13 * o, 30)
            path(ctx, m); ctx.set_source_rgba(*hexc("#B71C1C")); ctx.fill_preserve()
            ctx.set_source_rgba(*INK); ctx.set_line_width(8); ctx.stroke()
            return
        if v == "teeth":          # clenched teeth (s, t, z sounds)
            w, h = 48, 20
            r = [(x - w, y - 4), (x + w, y - 4), (x + w, y + h - 4), (x - w, y + h - 4)]
            path(ctx, r); ctx.set_source_rgb(1, 1, 1); ctx.fill_preserve()
            ctx.set_source_rgba(*INK); ctx.set_line_width(5); ctx.stroke()
            for i in range(1, 6):
                xx = x - w + i * 2 * w / 6
                ctx.move_to(xx, y - 4); ctx.line_to(xx, y + h - 4)
            ctx.move_to(x - w, y + h / 2 - 4); ctx.line_to(x + w, y + h / 2 - 4)
            ctx.set_line_width(3); ctx.stroke()
            return
        # grin (teeth) or open (tongue): D shape like the reference
        w = 66 if v == "grin" else 58
        h = (16 + 18 * o) if v == "grin" else (22 + 30 * o)
        top = qbez((x - w, y - 8), (x, y + 2), (x + w, y - 8), 12)
        bot = [(x + w, y - 8)] + [(x + w * math.cos(t), y - 8 + h * math.sin(t)) for t in np.linspace(0, math.pi, 20)]
        m = top + bot[1:]
        path(ctx, m); ctx.set_source_rgba(*hexc("#4A0E12")); ctx.fill()
        ctx.save(); path(ctx, m); ctx.clip()
        if v == "open":
            ctx.save(); ctx.translate(x, y + h * 0.95); ctx.scale(34, 16 + 6 * o); ctx.arc(0, 0, 1, 0, 2 * math.pi); ctx.restore()
            ctx.set_source_rgba(*hexc("#E35D6A")); ctx.fill()
        ctx.rectangle(x - w - 5, y - 30, 2 * w + 10, 30 + min(14, h * 0.45)); ctx.set_source_rgb(1, 1, 1); ctx.fill()
        ctx.restore()
        path(ctx, m); ctx.set_source_rgba(*INK); ctx.set_line_width(8); ctx.set_line_join(cairo.LINE_JOIN_ROUND); ctx.stroke()


# ---------------------------------------------------------------- poses: absolute arm angles (degrees)
# screen-left arm angles; the right arm mirrors (180 - a). 90 = straight down, 180 = out to the side, 270 = up.
POSES_DEG = {
    "rest":     {"L": None, "R": None},
    "arms_out": {"L": (150, 158), "R": (150, 158)},
    "hands_up": {"L": (128, 238), "R": (128, 238)},
    "side":     {"L": (183, 182)},
    "chest":    {"L": (108, -12)},
    "raise":    {"L": (122, 258)},
}
GESTURES = {   # gesture -> per arm pose name
    "rest":            ("rest", "rest"),
    "arms_out":        ("arms_out", "arms_out"),
    "hands_up":        ("hands_up", "hands_up"),
    "present_R":       ("chest", "side"),
    "present_L":       ("side", "rest"),
    "present_L_chest": ("side", "chest"),
    "chest":           ("chest", "rest"),
    "wave_R":          ("rest", "raise"),
    "wave":            ("rest", "raise"),
}


def arm_target(mec, side, pose):
    rest = mec.side[side]["ang"]
    spec = POSES_DEG[pose].get("L") if pose in POSES_DEG else None
    if spec is None:
        return (rest, rest)
    u, f = [math.radians(a) for a in spec]
    if side == "R":
        u, f = math.pi - u, math.pi - f
    return (u, f)


def gesture_arms(mec, g_prev, g_cur, t, wave=0.0):
    out = {}
    for i, sd in enumerate(("L", "R")):
        a0 = arm_target(mec, sd, GESTURES[g_prev][i])
        a1 = arm_target(mec, sd, GESTURES[g_cur][i])
        def lerp_ang(p, q):
            d = (q - p + math.pi) % (2 * math.pi) - math.pi
            return p + d * t
        u, f = lerp_ang(a0[0], a1[0]), lerp_ang(a0[1], a1[1])
        if sd == "R" and GESTURES[g_cur][i] == "raise":
            f += wave
        out[sd] = (u, f)
    front = {sd for i, sd in enumerate(("L", "R")) if "chest" in (GESTURES[g_cur][i], GESTURES[g_prev][i] if t < 0.5 else "")}
    return out, front
