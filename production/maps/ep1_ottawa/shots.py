"""Episode 1: Why is Canada's capital Ottawa?  Shot list + overlays, synced to word timings."""
import math, random
import skia
from engine import (xform, W, H, clamp, ease, ease_out, ease_back, lerp, win, hexc, withA, Camera)

CITY = {
    "Ottawa": (-75.6972, 45.4215), "Toronto": (-79.3832, 43.6532), "Montreal": (-73.5674, 45.5019),
    "Kingston": (-76.4860, 44.2312), "Quebec City": (-71.2080, 46.8139), "Sackets Harbor": (-76.119, 43.946),
}
# Rideau Canal, Ottawa -> Kingston (lon, lat), following the Rideau and Cataraqui
CANAL = [(-75.697, 45.425), (-75.693, 45.37), (-75.703, 45.30), (-75.683, 45.226), (-75.74, 45.10), (-75.80, 44.99),
         (-75.836, 44.917), (-75.93, 44.90), (-76.021, 44.904), (-76.10, 44.82), (-76.19, 44.71), (-76.32, 44.65),
         (-76.27, 44.57), (-76.24, 44.55), (-76.30, 44.45), (-76.38, 44.35), (-76.44, 44.29), (-76.486, 44.231)]
# shipping route up the St. Lawrence: Lake Ontario -> Montreal
STLAW = [(-76.9, 43.95), (-76.35, 44.12), (-76.0, 44.33), (-75.68, 44.59), (-75.3, 44.84), (-74.73, 45.02),
         (-74.35, 45.17), (-73.95, 45.38), (-73.57, 45.50)]
RED, BLUE, GOLD, INK = "#c8352b", "#2f6fb5", "#f2b23a", "#2b1d12"


class Scene:
    def __init__(self, geo, timing):
        self.geo = geo
        self.B = {b["id"]: b for b in timing["beats"]}
        self.dur = timing["duration"]
        self.sfx = []
        w = self.w
        # ---- camera: (start of move, move duration, lon, lat, width km, drift factor)
        shots = [
            (0.0, 0.0, -76.9, 44.3, 860, 0.88),
            (6.7, 1.6, -76.0, 44.1, 920, 0.95),
            (w("kingston", "1841") - 0.2, 1.6, -75.4, 44.3, 640, 0.93),
            (w("montreal", "Three"), 1.4, -75.0, 44.5, 580, 0.95),
            (w("riot", "Then"), 1.3, -73.6, 45.15, 330, 0.85),
            (w("rotate", "So"), 1.5, -75.3, 44.6, 1000, 0.93),
            (w("split", "The"), 1.3, -75.6, 45.3, 1200, 0.94),
            (w("usa", "And") - 0.1, 1.5, -93.0, 38.0, 5200, 0.93),
            (w("york", "In") - 0.1, 1.6, -77.75, 43.45, 580, 0.9),
            (w("border", "Toronto"), 1.3, -76.0, 44.3, 820, 0.93),
            (w("bytown", "But"), 1.4, -75.7, 45.1, 380, 0.87),
            (w("canal", "After"), 1.3, -76.1, 44.75, 340, 0.92),
            (w("perfect", "Bytown") - 0.1, 1.3, -75.6, 45.1, 640, 0.94),
            (w("queen", "It"), 1.3, -75.7, 45.6, 480, 0.9),
            (w("critic", "Not"), 1.0, -75.75, 45.3, 560, 0.92),
            (w("today", "Today") - 0.1, 1.3, -76.4, 44.4, 880, 0.95),
        ]
        keys = []
        for i, (ts, md, lon, lat, wk, dr) in enumerate(shots):
            nxt = shots[i + 1][0] if i + 1 < len(shots) else self.dur + 0.1
            if keys:
                keys.append((ts, *self._cam_at(keys, ts)))
            keys.append((ts + md, lon, lat, wk, "lin"))
            keys.append((nxt, lon, lat, wk * dr))
            if i:
                self.sfx.append((ts, "whoosh", min(1.0, md / 1.4)))
        self.cam = Camera(geo, keys)
        self.trees = self._scatter(26, seed=3)
        self._paths = {}
        self._events()

    # ------------------------------------------------------------ helpers
    def w(self, beat, word, n=0):
        hits = [x for x in self.B[beat]["words"] if x["w"].strip(",.?!'").lower().startswith(word.lower())]
        return hits[n]["s"]

    def _cam_at(self, keys, t):
        c = Camera(self.geo, [k[:4] + (k[4:] if len(k) > 4 else ()) for k in keys])
        x, y, wk = c.at(t)
        lon, lat = self.geo.P.transform(x, y, direction="INVERSE")
        return lon, lat, wk

    def _scatter(self, n, seed):
        rng = random.Random(seed); pts = []
        while len(pts) < n:
            a = rng.uniform(0, 2 * math.pi); r = rng.uniform(22, 95)
            dx, dy = r * math.cos(a), r * math.sin(a) * 0.8
            if dy > -8 and abs(dx) < 30:   # keep the town itself clear
                continue
            pts.append((dx, dy, rng.uniform(0.75, 1.15), rng.random()))
        return pts

    def P(self, d, name):
        return d.pt(self.geo, *CITY[name])

    def lonlat_path(self, d, pts):
        p = skia.Path()
        for i, (lon, lat) in enumerate(pts):
            x, y = d.pt(self.geo, lon, lat)
            p.moveTo(x, y) if i == 0 else p.lineTo(x, y)
        return p

    def km_off(self, d, name, dx, dy):
        x, y = self.geo.xy(*CITY[name])
        q = d.m.mapXY(x + dx, y + dy); return q.x(), q.y()

    def _events(self):
        w = self.w; S = self.sfx
        for t in [w("hook", "Ottawa"), w("hook", "Toronto"), w("hook", "Montreal"), w("kingston", "capital"),
                  w("montreal", "Montreal"), w("riot", "angry"), w("rotate", "Toronto"), w("rotate", "Quebec"),
                  w("rotate", "Toronto", 1), w("rotate", "Quebec", 1), w("rotate", "boxes"), w("split", "English"),
                  w("split", "French"), w("york", "captured"), w("border", "Toronto"), w("border", "Kingston"),
                  w("border", "Montreal"), w("bytown", "Bytown"), w("perfect", "exactly"), w("queen", "Victoria"),
                  w("today", "Toronto"), w("today", "Montreal"), w("end", "Ottawa")]:
            S.append((t, "pop", 1.0))
        S += [(6.9, "rewind", 1.0), (w("riot", "burned"), "fire", 1.0), (w("york", "burned"), "fire", 0.8),
              (w("usa", "America"), "boom", 1.0), (w("queen", "picked"), "ding", 1.0), (w("canal", "Rideau"), "draw", 1.0),
              (w("kingston", "1841"), "title", 1.0), (w("riot", "1849"), "title", 1.0), (w("york", "War"), "title", 1.0),
              (w("queen", "1857"), "title", 1.0), (w("today", "Today"), "title", 1.0), (w("critic", "One"), "paper", 1.0)]

    # ------------------------------------------------------------ global looks
    def vint(self, T):
        a = ease((T - 6.95) / 1.3)
        b = ease((T - (self.w("today", "Today") - 0.4)) / 1.1)
        return clamp(a - b)

    def caption_alpha(self, T):
        c0 = self.w("critic", "a", 0) - 0.1; c1 = self.w("critic", "cockpit") + 0.6
        return 0.0 if c0 <= T <= c1 else 1.0

    # ------------------------------------------------------------ overlays (under grain/vignette)
    def overlay(self, d, T):
        w = self.w; g = self.geo
        hook_end = w("undecided", "For")

        # ===== HOOK
        if T < hook_end + 0.6:
            a_h = win(T, 0, hook_end, 0.01, 0.6)
            for name, t0 in (("Toronto", w("hook", "Toronto")), ("Montreal", w("hook", "Montreal"))):
                x, y = self.P(d, name); a = win(T, t0 - 0.1, hook_end, 0.45, 0.6)
                d.glow_blob(x, y, 150 + 18 * math.sin(T * 3), "#ffc85a", a * 0.9)
                d.dot(x, y, a, r=9, color="#ffd27a")
                d.icon("cityscape", x, y - 95, 150, a, bob=3)
                d.label(name, x + (60 if name == "Montreal" else 0), y + 78, a, size=50, kind="sans_b", color="#ffffff", halo="#0c2236")
            ox, oy = self.P(d, "Ottawa"); a = win(T, w("hook", "Ottawa") - 0.15, hook_end, 0.4, 0.6)
            t_n = w("hook", "next")
            for name, km in (("Toronto", "350 km"), ("Montreal", "165 km")):
                x, y = self.P(d, name)
                pr = ease((T - (t_n - 0.6)) / 0.9) * a_h
                if pr > 0:
                    pth = skia.Path().moveTo(ox, oy).lineTo(x, y)
                    d.stroke_progress(pth, pr, "#ffffff", 4, 0.9 * a_h, glow=False, dash=[14, 10])
                    d.text(km, (ox + x) / 2, (oy + y) / 2 - 18, 40, kind="sans_b", color="#ffffff", alpha=clamp(pr * 2 - 1) * a_h,
                           halo="#0c2236", halo_a=0.9)
            d.dot(ox, oy, a, r=12, color=RED, pulse=T)
            d.icon("red_question_mark", ox + 6, oy - 110, 130, win(T, w("hook", "Why") + 0.2, hook_end, 0.45, 0.6), bob=5)
            d.label("Ottawa", ox - 70, oy + 80, a, size=58, kind="sans_x", color="#ffffff", halo="#0c2236")

        # ===== UNDECIDED (rewind)
        t0, t1 = w("undecided", "For"), w("kingston", "1841") - 0.2
        a = win(T, t0 + 0.6, t1, 0.4, 0.4)
        if a > 0:
            x = W / 2; y = 760
            d.icon("thinking_face", x, y, 230, a, bob=8)
            for k, name in enumerate(("Toronto", "Montreal", "Kingston", "Quebec City")):
                cx, cy = self.P(d, name)
                aa = win(T, t0 + 0.9 + k * 0.2, t1, 0.3, 0.3)
                d.dot(cx, cy, aa, r=9, color=INK)
                d.label(name, cx, cy + 66, aa, size=42)

        # ===== KINGSTON 1841 / MONTREAL 1844 / RIOT 1849
        tk, tm, tr = w("kingston", "1841"), w("montreal", "Three"), w("riot", "Then")
        tr_end = w("rotate", "So")
        hop_t = w("montreal", "moved") - 0.15
        if tk - 0.3 < T < tr_end + 0.5:
            kx, ky = self.P(d, "Kingston"); mx, my = self.P(d, "Montreal")
            d.dot(kx, ky, win(T, tk + 0.3, tr_end, 0.4, 0.5), r=10, color=INK)
            d.label("Kingston", kx, ky + 70, win(T, tk + 0.3, tr_end, 0.4, 0.5), size=48)
            d.dot(mx, my, win(T, tm + 0.2, tr_end, 0.4, 0.5), r=10, color=INK)
            d.label("Montreal", mx, my + 70, win(T, tm + 0.2, tr_end, 0.4, 0.5), size=48)
            # the parliament building
            ab = win(T, w("kingston", "capital"), tr_end, 0.45, 0.5)
            hp = ease((T - hop_t) / 1.2)
            arc = d.arc_path((kx, ky - 80), (mx, my - 80), -0.28)
            if 0 < hp:
                d.stroke_progress(arc, hp, GOLD, 5, win(T, hop_t, tr - 0.2, 0.1, 0.5), dash=[16, 12], head=hp < 1)
            bx, by, _ = d.pos_on(arc, hp)
            burn = ease((T - w("riot", "burned")) / 0.8)
            d.icon("classical_building", bx, by - 6, 150, ab, bob=2)
            d.text("Capital", bx, by + 112 - 80, 34, kind="serif_i", color=INK, alpha=ab * (1 - burn), halo="#f4ead2")
            # riot: crowd, fire, smoke, embers
            ac = win(T, w("riot", "angry"), tr_end, 0.35, 0.5)
            for k, (dx, dy) in enumerate(((-120, 30), (118, 36), (-70, 92), (76, 96))):
                d.icon("busts_in_silhouette", mx + dx, my - 80 + dy, 92, win(T, w("riot", "angry") + k * 0.12, tr_end, 0.3, 0.5),
                       bob=4, flip=dx > 0)
            if burn > 0:
                af = win(T, w("riot", "burned"), tr_end, 0.3, 0.5)
                self.fire(d, T, mx, my - 95, af, scale=1.0, seed=1)

        # titles (dates)
        d.title("1841", win(T, tk, tm - 0.1, 0.8, 0.35))
        d.title("1844", win(T, tm + 0.1, tr - 0.1, 0.6, 0.35))
        d.title("1849", win(T, w("riot", "1849"), tr_end - 0.2, 0.8, 0.4), sub="April 25")

        # ===== ROTATE
        t_s, t_e = w("rotate", "So"), w("split", "The")
        if t_s - 0.2 < T < t_e + 0.5:
            names = ["Montreal", "Toronto", "Quebec City", "Toronto", "Quebec City"]
            times = [t_s, w("rotate", "Toronto") - 0.35, w("rotate", "Quebec") - 0.3, w("rotate", "Toronto", 1) - 0.35,
                     w("rotate", "Quebec", 1) - 0.3]
            base = win(T, t_s, t_e - 0.2, 0.4, 0.5)
            for name in ("Toronto", "Quebec City", "Montreal"):
                x, y = self.P(d, name)
                d.dot(x, y, base, r=10, color=INK)
                d.label(name, x, y + 70, base, size=46)
            cur = self.P(d, "Montreal"); cur = (cur[0], cur[1] - 80)
            pos = cur
            for k in range(1, len(names)):
                p0 = self.P(d, names[k - 1]); p1 = self.P(d, names[k])
                arc = d.arc_path((p0[0], p0[1] - 80), (p1[0], p1[1] - 80), 0.22 if k % 2 else -0.22)
                hp = ease((T - times[k]) / 0.75)
                if hp > 0:
                    d.stroke_progress(arc, hp, GOLD, 5, base * (0.9 if hp < 1 else 0.45), dash=[16, 12], head=hp < 1)
                    x, y, _ = d.pos_on(arc, hp); pos = (x, y)
            d.icon("classical_building", pos[0], pos[1] - 6, 140, base, pop=False, bob=2)
            tb = w("rotate", "packed")
            for k, (dx, dy) in enumerate(((-95, 70), (-30, 95), (40, 88), (100, 62))):
                d.icon("package", pos[0] + dx, pos[1] + dy, 74, win(T, tb + k * 0.12, t_e - 0.2, 0.3, 0.5), bob=3)
            d.icon("delivery_truck_3d", pos[0] - 190 + 260 * ease((T - (tb + 0.6)) / 1.6), pos[1] + 150, 120,
                   win(T, tb + 0.4, t_e - 0.2, 0.3, 0.4), pop=False, flip=True)

        # ===== SPLIT: English west, French east (also reused in PERFECT)
        t_s = w("split", "The"); t_e = w("usa", "And")
        tp = w("perfect", "between")
        for (a_e, a_f, labels) in ((win(T, w("split", "English") - 0.2, t_e - 0.2, 0.5, 0.5),
                                    win(T, w("split", "French") - 0.2, t_e - 0.2, 0.5, 0.5), True),
                                   (win(T, w("perfect", "English") - 0.2, w("queen", "It") + 0.3, 0.5, 0.6),
                                    win(T, w("perfect", "French") - 0.2, w("queen", "It") + 0.3, 0.5, 0.6), False)):
            if a_e > 0 or a_f > 0:
                d.region(g.provinces["Ontario"], RED, a_e, fill_a=0.30)
                d.region(g.provinces["Québec"], BLUE, a_f, fill_a=0.30)
                if labels:
                    x, y = d.pt(g, -79.2, 45.2)
                    d.icon("speaking_head_3d", x, y - 120, 120, a_e, bob=3)
                    d.text("ENGLISH", x, y, 66, kind="sans_x", color="#ffffff", alpha=a_e, halo=RED, halo_a=0.9, tracking=0.08)
                    x, y = d.pt(g, -71.9, 46.0)
                    d.icon("speaking_head_3d", x, y - 120, 120, a_f, bob=3, flip=True)
                    d.text("FRENCH", x, y, 66, kind="sans_x", color="#ffffff", alpha=a_f, halo=BLUE, halo_a=0.9, tracking=0.08)
        ac = win(T, w("split", "each"), t_e - 0.2, 0.35, 0.4)
        if ac > 0:
            x, y = self.P(d, "Ottawa"); y -= 40
            sway = math.sin((T - w("split", "each")) * 7) * 70 * ac
            d.icon("classical_building", x + sway, y, 150, ac, bob=0, rot=sway * 0.12)
            for sgn, col in ((-1, RED), (1, BLUE)):
                pth = skia.Path().moveTo(x + sgn * 95, y + 10).lineTo(x + sgn * 230, y + 10)
                d.stroke_progress(pth, ease((T - w("split", "each")) / 0.5), col, 9, ac, head=True)

        # ===== USA
        t_s = w("usa", "And"); t_e = w("york", "In")
        aa = win(T, w("usa", "America") - 0.25, t_e, 0.3, 0.4)
        if aa > 0:
            pulse = 0.5 + 0.5 * math.sin((T - w("usa", "America")) * 6)
            d.region(g.countries["USA"], RED, aa, fill_a=0.42, pulse=pulse)
            x, y = d.pt(g, -98.5, 39.5)
            d.text("UNITED STATES", x, y, 74, kind="sans_x", color="#ffffff", alpha=aa, halo="#5a120d", halo_a=0.8, tracking=0.12)
            x, y = d.pt(g, -100, 56)
            d.text("BRITISH NORTH AMERICA", x, y, 46, kind="sans_b", color="#ffffff", alpha=aa * 0.85, halo="#3b2a18", tracking=0.12)

        # ===== YORK 1813
        t_s = w("york", "In"); t_e = w("border", "Toronto")
        d.title("War of 1812", win(T, w("york", "War"), w("york", "troops"), 0.8, 0.4), size=120)
        if t_s - 0.2 < T < t_e + 0.4:
            tx, ty = self.P(d, "Toronto")
            ab = win(T, t_s + 0.8, t_e - 0.1, 0.4, 0.4)
            d.dot(tx, ty, ab, r=11, color=INK)
            york = win(T, w("york", "York") - 0.1, t_e - 0.1, 0.3, 0.4)
            d.label("Toronto", tx, ty + 72, ab * (1 - york), size=50)
            d.label("York", tx, ty + 72, york, size=56)
            ts = w("york", "American") - 0.2
            sh = self.P(d, "Sackets Harbor")
            d.dot(sh[0], sh[1], win(T, ts, t_e - 0.1, 0.4, 0.4), r=8, color=RED)
            d.label("U.S. Navy", sh[0], sh[1] + 64, win(T, ts, w("york", "captured"), 0.4, 0.4), size=40, kind="garamond_b")
            for k in range(3):
                path = d.arc_path((sh[0] + k * 30, sh[1] + 30 - k * 40), (tx + 70 + k * 30, ty + 40 - k * 45), 0.12)
                f = ease((T - ts - k * 0.15) / 2.2)
                a_sh = win(T, ts + k * 0.15, w("york", "burned") + 0.3, 0.3, 0.5)
                if f > 0:
                    d.stroke_progress(path, f, "#ffffff", 3, a_sh * 0.7, glow=False, dash=[6, 9])
                x, y, _ = d.pos_on(path, f)
                d.icon("sailboat", x, y - 30, 96, a_sh, pop=False, flip=True, bob=4)
            d.icon("crossed_swords", tx, ty - 110, 120, win(T, w("york", "captured"), w("york", "burned"), 0.35, 0.3), bob=3)
            if T > w("york", "burned") - 0.1:
                self.fire(d, T, tx, ty - 80, win(T, w("york", "burned"), t_e - 0.1, 0.3, 0.4), scale=0.9, seed=4)

        # ===== BORDER + ST LAWRENCE
        t_s = w("border", "Toronto"); t_e = w("bytown", "But")
        if t_s - 0.2 < T < t_e + 0.5:
            ab = win(T, w("border", "border") - 0.2, t_e - 0.1, 0.4, 0.5)
            if ab > 0:
                bp = xform(g.borders, d.m)
                d.cv.drawPath(bp, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=18,
                              Color4f=withA(hexc(RED), 0.45 * ab), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 10)))
                d.cv.drawPath(bp, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=5,
                              Color4f=withA(hexc(RED), ab), PathEffect=skia.DashPathEffect.Make([18, 10], -T * 40)))
            al = win(T, w("border", "Saint") - 0.2, t_e - 0.1, 0.4, 0.5)
            if al > 0:
                sl = self.lonlat_path(d, STLAW)
                d.stroke_progress(sl, ease((T - w("border", "Saint") + 0.2) / 1.2), "#7fd3ff", 9, al)
                x, y = d.pt(g, -74.7, 44.55)
                d.text("St. Lawrence", x + 40, y + 70, 46, kind="serif_i", color="#0e3550", alpha=al, halo="#e8f6ff", halo_a=0.9)
            for name, key in (("Toronto", "Toronto"), ("Kingston", "Kingston"), ("Montreal", "Montreal")):
                x, y = self.P(d, name); a = win(T, w("border", key) - 0.1, t_e - 0.1, 0.35, 0.5)
                d.dot(x, y, a, r=11, color=RED, pulse=T - w("border", key))
                d.label(name, x, y - 2 - 26 if name != "Kingston" else y + 74, a, size=46, dy=-40 if name != "Kingston" else -34)
            tf = w("border", "enemy") - 0.2
            sl = self.lonlat_path(d, STLAW)
            for k in range(3):
                f = ease_out((T - tf - k * 0.35) / 2.6) * 0.92
                a = win(T, tf + k * 0.35, t_e - 0.1, 0.3, 0.4)
                x, y, ang = d.pos_on(sl, f)
                d.icon("sailboat", x, y - 34, 92, a, pop=False, bob=4, flip=True)

        # ===== BYTOWN (+ PERFECT)
        t_s = w("bytown", "But"); t_e = w("queen", "It")
        ar = win(T, w("bytown", "Ottawa") - 0.2, w("canal", "After") + 0.2, 0.6, 0.6) + \
             win(T, w("perfect", "river") - 0.3, w("queen", "It") + 0.4, 0.5, 0.6)
        if ar > 0 and "Ottawa" in g.named_rivers:
            d.river_glow(g.named_rivers["Ottawa"], "#7fd3ff", clamp(ar), width=7)
            x, y = d.pt(g, -76.55, 45.62)
            d.text("Ottawa River", x, y - 30, 44, kind="serif_i", color="#0e3550", alpha=clamp(ar), halo="#e8f6ff", halo_a=0.9)
        tw_list = [(w("bytown", "small"), w("canal", "After") + 0.3), (w("perfect", "hidden") - 0.2, w("queen", "It") + 0.3),
                   (w("end", "chosen") - 0.3, self.dur + 1)]
        for (t0, t1) in tw_list:
            if t0 - 0.1 < T < t1 + 0.6:
                for k, (dx, dy, sc, ph) in enumerate(self.trees):
                    x, y = self.km_off(d, "Ottawa", dx, dy)
                    sz = 66 * sc * clamp(d.s / 2.6, 0.55, 1.1)
                    d.icon("evergreen_tree", x, y - sz * 0.4, sz, win(T, t0 + ph * 0.9, t1, 0.35, 0.5), shadow=False)
        if t_s - 0.2 < T < self.dur + 1:
            ox, oy = self.P(d, "Ottawa")
            a_by = win(T, w("bytown", "small") - 0.1, self.dur, 0.4, 0.5)
            d.icon("wood", ox + 6, oy - 92, 120, win(T, w("bytown", "lumber"), w("canal", "After") + 0.2, 0.35, 0.5), bob=3)
            ren = ease((T - w("queen", "renamed")) / 0.7)
            d.dot(ox, oy, a_by, r=12, color=RED if T > w("queen", "picked") else INK,
                  pulse=T if w("perfect", "northern") < T < w("perfect", "hidden") else None)
            if T < w("today", "Today") - 0.3:
                lab_a = a_by * win(T, w("bytown", "small"), w("today", "Today") - 0.5, 0.4, 0.4)
                d.label("Bytown", ox, oy + 76, lab_a * (1 - ren), size=54)
                d.label("Ottawa", ox, oy + 76, lab_a * ren, size=60)
                if 0 < ren < 1:
                    fw = 210 * ease(ren * 2)
                    d.cv.drawLine(ox - 105, oy + 30, ox - 105 + fw, oy + 30,
                                  skia.Paint(AntiAlias=True, StrokeWidth=5, Color4f=withA(hexc(RED), (1 - ren) * 2)))
            d.icon("bullseye", ox, oy - 100, 120, win(T, w("perfect", "exactly"), w("queen", "It"), 0.35, 0.4), bob=3)

        # ===== CANAL
        t_s = w("canal", "After"); t_e = w("queen", "It")
        if t_s - 0.2 < T < t_e + 0.6:
            cp = self.lonlat_path(d, CANAL)
            pr = ease((T - w("canal", "Rideau") + 0.2) / 2.6)
            ac = win(T, w("canal", "Rideau") - 0.2, t_e, 0.2, 0.6)
            d.stroke_progress(cp, pr, "#ffcf4a", 8, ac)
            kx, ky = self.P(d, "Kingston")
            ak = win(T, t_s + 0.2, t_e, 0.4, 0.6)
            d.dot(kx, ky, ak, r=11, color=INK)
            d.label("Kingston", kx, ky + 76, ak, size=50)
            x, y, _ = d.pos_on(cp, 0.5)
            al = win(T, w("canal", "Canal"), w("perfect", "Bytown") + 0.5, 0.4, 0.5)
            d.text("Rideau Canal", x + 150, y, 52, kind="garamond_b", color=INK, alpha=al, halo="#f8e9c4")
            d.text("202 km", x + 150, y + 52, 40, kind="sans_b", color="#7a4b12", alpha=win(T, w("canal", "two"), w("perfect", "Bytown") + 0.5, 0.4, 0.5),
                   halo="#f8e9c4")
            # danger route along the St Lawrence
            ad = win(T, w("canal", "without") - 0.3, w("perfect", "Bytown") + 0.3, 0.4, 0.5)
            if ad > 0:
                sl = self.lonlat_path(d, STLAW)
                d.stroke_progress(sl, 1.0, RED, 6, ad, glow=True, dash=[18, 12], phase=-T * 30)
                for k, f in enumerate((0.3, 0.62)):
                    x, y, _ = d.pos_on(sl, f)
                    d.icon("collision_3d", x, y, 96, win(T, w("canal", "American") - 0.2 + k * 0.2, w("perfect", "Bytown") + 0.3, 0.3, 0.5), bob=2)
            tb = w("canal", "troops") - 0.2
            f = ease((T - tb) / 2.6)
            ab = win(T, tb, w("perfect", "Bytown") + 0.2, 0.3, 0.4)
            if ab > 0:
                x, y, _ = d.pos_on(cp, f)
                d.icon("person_rowing_boat_3d_default", x, y - 30, 100, ab, pop=False, bob=3)

        # ===== QUEEN 1857
        d.title("1857", win(T, w("queen", "1857"), w("queen", "Victoria") - 0.1, 0.8, 0.3))
        aq = win(T, w("queen", "Queen") - 0.15, w("critic", "Not") - 0.1, 0.45, 0.5)
        if aq > 0:
            qx, qy = W / 2, 360
            d.glow_blob(qx, qy, 220, "#ffe7a3", aq * 0.8)
            d.icon("princess_3d_default", qx, qy, 230, aq, bob=5)
            d.text("Queen Victoria", qx, qy + 175, 60, kind="garamond_b", color=INK, alpha=aq, halo="#fbf1d8", halo_a=0.95)
            tp = w("queen", "picked")
            ox, oy = self.P(d, "Ottawa")
            pr = ease((T - tp + 0.3) / 0.6)
            if pr > 0:
                pth = d.arc_path((qx, qy + 210), (ox, oy - 150), 0.12)
                d.stroke_progress(pth, pr, GOLD, 6, aq, head=True, dash=[16, 10])
        apk = win(T, w("queen", "picked"), w("today", "Today") - 0.4, 0.45, 0.5)
        if apk > 0:
            ox, oy = self.P(d, "Ottawa")
            ring = ease_out((T - w("queen", "picked")) / 0.9)
            d.cv.drawCircle(ox, oy, 30 + ring * 190, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=6,
                            Color4f=withA(hexc(GOLD), (1 - ring) * apk)))
            d.icon("classical_building", ox, oy - 100, 150, apk, bob=2)
            d.icon("crown", ox, oy - 196, 80, win(T, w("queen", "picked") + 0.25, w("today", "Today") - 0.4, 0.4, 0.5), bob=3)

        # ===== CRITIC quote card
        tq = w("critic", "a", 0) - 0.3
        aq = win(T, tq, w("today", "Today") - 0.4, 0.5, 0.4)
        if aq > 0:
            d.cv.drawPaint(skia.Paint(Color4f=skia.Color4f(0.05, 0.04, 0.03, 0.35 * aq)))
            cx, cy = W / 2, 800
            d.card(cx, cy + (1 - ease_out(aq)) * 40, 980, 700, aq)
            lines = [("A sub-arctic lumber village", ["a", "sub-arctic", "lumber", "village"]),
                     ("converted by royal mandate", ["converted", "by", "royal", "mandate"]),
                     ("into a political cockpit.", ["into", "a", "political", "cockpit"])]
            d.text("“", cx - 400, cy - 170, 220, kind="garamond_b", color="#b08a52", alpha=aq, halo=None)
            for i, (ln, _) in enumerate(lines):
                yy = cy - 110 + i * 118 + (1 - ease_out(aq)) * 40
                tl = [w("critic", "sub"), w("critic", "converted"), w("critic", "into")][i] - 0.25
                la = clamp((T - tl) / 0.35)
                d.text(ln, cx, yy, 84, kind="garamond_b", color="#3a2614", alpha=aq * (0.22 + 0.78 * la), halo=None)
            d.text("— Goldwin Smith, historian", cx, cy + 260, 50, kind="serif_i", color="#6d4c2a", alpha=aq, halo=None)
            d.icon("unamused_face_3d", cx + 360, cy - 300, 130, win(T, w("critic", "critic"), w("today", "Today") - 0.4, 0.35, 0.4), bob=4)

        # ===== TODAY: population columns
        tt = w("today", "Today")
        d.title("Today", win(T, tt, w("end", "Which"), 0.6, 0.5), size=130)
        if T > tt - 0.2:
            for name, t0, hpx, val in (("Toronto", w("today", "Toronto"), 560, 2.8), ("Montreal", w("today", "Montreal"), 360, 1.8),
                                       ("Ottawa", w("end", "Ottawa"), 205, 1.0)):
                x, y = self.P(d, name)
                a = win(T, t0 - 0.1, self.dur, 0.9, 0.5)
                dim = 1 - 0.45 * ease((T - w("end", "hard") + 0.8) / 0.8) if name != "Ottawa" else 1.0
                col = "#f2c14e" if name != "Ottawa" else "#ff7a59"
                d.bar(x, y, hpx, a, fade=dim, color=col, w=92, label=name,
                      value=lambda f, v=val: f"{v * ease_out(f):.1f}M")

    # ------------------------------------------------------------ fire fx
    def fire(self, d, T, x, y, a, scale=1.0, seed=0):
        if a <= 0:
            return
        rng = random.Random(seed)
        d.glow_blob(x, y + 20, 230 * scale * (1 + 0.06 * math.sin(T * 13)), "#ff7a1a", a * 0.85)
        # smoke
        for k in range(7):
            ph = (T * 0.35 + k / 7 + rng.random() * 0.1) % 1.0
            sx = x + math.sin(ph * 5 + k) * 30 * scale + (k - 3) * 9
            sy = y - 60 * scale - ph * 330 * scale
            d.cv.drawCircle(sx, sy, (30 + ph * 70) * scale, skia.Paint(AntiAlias=True, Color4f=skia.Color4f(0.18, 0.16, 0.15, 0.32 * a * (1 - ph)),
                            MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 18 * scale)))
        for k, (dx, sz) in enumerate(((-38, 105), (40, 95), (0, 135))):
            fl = 1 + 0.08 * math.sin(T * 17 + k * 2)
            d.icon("fire", x + dx * scale, y - 10 * scale - (sz * scale * fl - sz * scale) / 2, sz * scale * fl, a, pop=True, shadow=False)
        # embers
        for k in range(16):
            ph = (T * 0.8 + rng.random()) % 1.0
            ex = x + (rng.random() - 0.5) * 140 * scale + math.sin(T * 3 + k) * 20
            ey = y - ph * 260 * scale
            d.cv.drawCircle(ex, ey, 3.2 * scale, skia.Paint(AntiAlias=True, Color4f=skia.Color4f(1, 0.75, 0.3, a * (1 - ph)),
                            MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 1.5)))

    # ------------------------------------------------------------ post (above grain/vignette)
    def post(self, d, T):
        # VHS rewind
        r0, r1 = 6.9, 8.5
        if r0 < T < r1:
            a = win(T, r0, r1 - 0.4, 0.15, 0.4)
            cv = d.cv
            rng = random.Random(int(T * 30))
            for k in range(9):
                y = rng.uniform(0, H); hgt = rng.uniform(2, 7)
                cv.drawRect(skia.Rect.MakeXYWH(0, y, W, hgt), skia.Paint(Color4f=skia.Color4f(1, 1, 1, 0.22 * a)))
            cv.drawPaint(skia.Paint(Color4f=skia.Color4f(0.95, 0.9, 0.8, 0.12 * a)))
            cx, cy = W / 2, 470
            for k in range(2):
                p = skia.Path(); ox = cx - 10 - k * 92 + 60
                p.moveTo(ox, cy); p.lineTo(ox + 88, cy - 58); p.lineTo(ox + 88, cy + 58); p.close()
                cv.drawPath(p, skia.Paint(AntiAlias=True, Color4f=skia.Color4f(1, 1, 1, 0.9 * a),
                            ImageFilter=skia.ImageFilters.DropShadow(0, 4, 8, 8, skia.Color4f(0, 0, 0, 0.5 * a).toColor())))
