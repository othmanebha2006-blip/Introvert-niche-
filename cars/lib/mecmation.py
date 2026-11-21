"""@Mecmation: the channel's presenter, redrawn as vectors from `cars/character_mecmation/mecmation_reference.png`
so every part can move (arms, hands, legs, eyes, brows, mouth, beanie).

All shapes use the reference image's coordinates (1043 x 1508 px). draw_mecmation() places it on screen.

state keys: x (screen centre), ground (screen y under the shoes), s (scale), mouth 0..1, shape ah/ee/oh, blink 0..1,
brows, look (dx,dy), pose (dict from lerp_pose), lean (rad), tilt (rad), bob (ref px, up), squash (1=none), hop (screen px),
smile (0..1), wave (phase, for the 'wave' pose).
"""
import math, cairo
from ink import *

GREY = hexc("#727373"); GREY_D = hexc("#5E5F5F")
SKIN = hexc("#FED0A4")
RED = hexc("#EE2220"); RED_D = hexc("#C9161A")
WHITE = hexc("#FFFFFF")
LW = 12.5                      # outline width in reference px

HIP = (518, 1000)              # upper body pivots here
NECK = (518, 585)
SH = {"L": (398, 622), "R": (640, 618)}           # where the arms leave the shirt
ANKLE = {"L": (436, 1368), "R": (590, 1368)}
HIPJ = {"L": (430, 1000), "R": (603, 1004)}

# arm poses: (elbow offset, hand offset) from the shoulder, hand kind
POSES = {
    "rest":    {"L": ((-68, 140), (-138, 282), "relax"), "R": ((68, 140), (136, 282), "relax")},
    "hips":    {"L": ((-150, 150), (-35, 300), "fist"), "R": ((150, 150), (35, 300), "fist")},
    "explain": {"L": ((-120, 170), (40, 120), "open"), "R": ((68, 140), (136, 282), "relax")},
    "point":   {"L": ((-120, -60), (-150, -290), "point"), "R": ((150, 150), (35, 300), "fist")},
    "shrug":   {"L": ((-150, 110), (-260, -10), "open"), "R": ((150, 110), (260, -10), "open")},
    "count":   {"L": ((-120, 170), (30, 100), "open"), "R": ((120, 170), (-30, 70), "point")},
    "thumb":   {"L": ((-150, 150), (-35, 300), "fist"), "R": ((150, 140), (80, 10), "thumb")},
    "wave":    {"L": ((-68, 140), (-138, 282), "relax"), "R": ((160, -40), (190, -260), "open")},
}


def lerp_pose(a, b, t):
    out = {}
    for side in ("L", "R"):
        (e1, h1, k1), (e2, h2, k2) = POSES[a][side], POSES[b][side]
        out[side] = ((e1[0] + (e2[0] - e1[0]) * t, e1[1] + (e2[1] - e1[1]) * t),
                     (h1[0] + (h2[0] - h1[0]) * t, h1[1] + (h2[1] - h1[1]) * t), k2 if t > 0.5 else k1)
    return out


def _rot(p, c, a):
    s, co = math.sin(a), math.cos(a)
    x, y = p[0] - c[0], p[1] - c[1]
    return (c[0] + x * co - y * s, c[1] + x * s + y * co)


def _upper_tf(p, st):
    """reference-space transform of the upper body (bob, squash, lean), for joining the legs."""
    x, y = p
    y = HIP[1] + (y - HIP[1]) * st.get("squash", 1.0) - st.get("bob", 0)
    return _rot((x, y), HIP, st.get("lean", 0))


def _upper_ctx(ctx, st):
    ctx.translate(*HIP); ctx.rotate(st.get("lean", 0)); ctx.translate(-HIP[0], -HIP[1])
    ctx.translate(0, -st.get("bob", 0))
    ctx.translate(0, HIP[1]); ctx.scale(1, st.get("squash", 1.0)); ctx.translate(0, -HIP[1])


# ------------------------------------------------------------------ parts
def _legs(ctx, st, salt):
    for side in ("L", "R"):
        h = _upper_tf(HIPJ[side], st)
        a = ANKLE[side]
        k = (h[0] + a[0]) / 2 + (-10 if side == "L" else 10), (h[1] + a[1]) / 2
        pts = qbez(h, k, a, 14)
        line(ctx, pts, 27, INK, salt=salt)


def _shoes(ctx, salt):
    for side, sx in (("L", 1), ("R", -1)):
        cx = 388 if side == "L" else 645
        # toe points outwards
        pts = [(cx + sx * 82, 1372), (cx + sx * 84, 1432), (cx - sx * 50, 1452), (cx - sx * 82, 1428), (cx - sx * 60, 1388),
               (cx + sx * 10, 1366)]
        if side == "R":
            pts = pts[::-1]
        ink(ctx, rpoly(pts, 34), GREY, LW, salt=salt)
        for i in range(3):
            lx = cx + sx * (18 - i * 22)
            line(ctx, [(lx - 6, 1394), (lx + 6, 1378)], 7, WHITE, sketch=False)
        line(ctx, [(cx - 70, 1438), (cx + 70, 1440)], 4, GREY_D, sketch=False)


def _shirt(ctx, salt):
    left = bez((408, 578), (362, 690), (338, 840), (345, 965), 16)
    bottom = qbez((345, 965), (518, 1062), (692, 965), 14)
    right = bez((692, 965), (697, 840), (676, 690), (628, 578), 16)
    pts = left + bottom[1:] + right[1:]
    g = lin_grad(340, 0, 700, 0, [(0, RED_D), (0.22, RED), (0.85, RED), (1, RED_D)])
    ink(ctx, pts, None, LW, grad=g, salt=salt)
    # emblem: steering wheel
    cx, cy = 570, 688
    ink(ctx, ellipse(cx, cy, 64, 64), WHITE, 9, salt=salt)
    line(ctx, ellipse(cx, cy, 42, 42, 40), 10, salt=salt)
    line(ctx, [(cx - 42, cy - 2), (cx - 12, cy - 6)], 10, salt=salt)
    line(ctx, [(cx + 12, cy - 6), (cx + 42, cy - 2)], 10, salt=salt)
    line(ctx, [(cx, cy + 8), (cx, cy + 42)], 10, salt=salt)
    ink(ctx, ellipse(cx, cy - 4, 12, 12, 16), WHITE, 8, salt=salt)


def _hand(ctx, w, d, kind, side, salt, wave=0.0):
    ang = math.atan2(d[1], d[0])
    ctx.save(); ctx.translate(*w); ctx.rotate(ang)
    m = 1 if side == "L" else -1     # mirror so the thumb is on the right side
    def f(a, L, curl=0.25, wdt=12):
        p0 = (0, 0)
        p1 = (math.cos(a) * L * 0.55, math.sin(a) * L * 0.55)
        p2 = (math.cos(a + curl) * L, math.sin(a + curl) * L)
        line(ctx, qbez(p0, p1, p2, 8), wdt, salt=salt)
    if kind == "relax":
        for a, L, c in ((-0.42 * m, 76, -0.3 * m), (-0.14 * m, 90, 0.05 * m), (0.14 * m, 90, 0.1 * m), (0.4 * m, 72, 0.32 * m)):
            f(a, L, c)
    elif kind == "open":
        ctx.rotate(wave)
        for a in (-0.9, -0.35, 0.1, 0.55):
            f(a * m, 80, 0.05 * m)
        f(1.35 * m, 58, 0.2 * m)
    elif kind == "point":
        f(0, 100, 0)
        for a in (0.55, 0.95, 1.3):
            f(a * m, 40, 1.2 * m)
        f(-0.8 * m, 46, 0.3 * m)
    elif kind == "thumb":
        for a in (0.4, 0.75, 1.1, 1.45):
            f(a * m, 42, 1.4 * m)
        ctx.rotate(-ang)
        line(ctx, qbez((0, 0), (4, -40), (2, -80), 8), 13, salt=salt)
    else:  # fist
        for a in (-0.5, -0.15, 0.2, 0.55):
            f(a, 40, 1.6 * m)
    ctx.restore()


def _arm(ctx, side, sh, e, h, kind, salt, wave):
    el = (sh[0] + e[0], sh[1] + e[1]); ha = (sh[0] + h[0], sh[1] + h[1])
    pts = qbez(sh, el, ha, 16)
    line(ctx, pts, LW + 1, salt=salt)
    d = (pts[-1][0] - pts[-3][0], pts[-1][1] - pts[-3][1]); n = math.hypot(*d) or 1
    _hand(ctx, ha, (d[0] / n, d[1] / n), kind, side, salt, wave)


def _head(ctx, st, salt):
    ink(ctx, ellipse(518, 415, 221, 173, 60), SKIN, LW, salt=salt)
    lx, ly = st.get("look", (0, 0))
    blink = st.get("blink", 0)
    br = st.get("brows", "neutral")
    big = 1.15 if br == "up" else 1.0
    for s, ex in ((-1, 467), (1, 572)):
        ey = 392
        if blink > 0.5:
            line(ctx, qbez((ex - 15, ey + 2), (ex, ey + 10), (ex + 15, ey + 2), 6), 8, salt=salt)
        else:
            ink(ctx, ellipse(ex + lx * 9, ey + ly * 9, 14 * big, 21 * big * (1 - 0.7 * blink), 24), INK, 0)
        # brows: small arches
        lift = {"neutral": 0, "up": -20, "frown": 8, "skeptic": -18 if s < 0 else 4, "smug": -8 if s < 0 else 0,
                "worried": -12}[br]
        tilt = {"neutral": 0, "up": 0, "frown": 0.35, "skeptic": 0 if s < 0 else 0.2, "smug": -0.1, "worried": -0.35}[br] * s
        arch = {"frown": 6, "skeptic": 20 if s < 0 else 6}.get(br, 22)
        bx, by = ex - 6 * s * 0 + (-7 if s < 0 else 0), 327 + lift
        p0 = (bx - 23, by + 8 + tilt * 30); p2 = (bx + 23, by + 8 - tilt * 30)
        line(ctx, qbez(p0, (bx, by - arch + 8), p2, 10), 8, salt=salt)
        for p in (p0, p2):
            ink(ctx, ellipse(p[0], p[1], 4.5, 4.5, 10), INK, 0)
    _mouth(ctx, st.get("mouth", 0), st.get("shape", "ah"), st.get("smile", 0.5), st.get("brows") == "smug", salt)


def _mouth(ctx, o, shape, smile, smug, salt):
    x, y = 520, 486
    if o < 0.1:
        dip = 20 + 22 * smile
        a = -8 if smug else 0
        pts = qbez((x - 68, y - 6 + a), (x, y + dip * 1.9), (x + 68, y - 10 - a * 1.5), 14)
        line(ctx, pts, 9, salt=salt)
        for p in (pts[0], pts[-1]):
            ink(ctx, ellipse(p[0], p[1], 5, 5, 10), INK, 0)
        return
    if shape == "oh":
        m = ellipse(x, y + 18, 26 + 6 * o, 18 + 26 * o, 30)
    else:
        w = (62 if shape == "ah" else 70) + 6 * o
        h = (16 + 52 * o) if shape == "ah" else (12 + 26 * o)
        top = qbez((x - w, y - 4), (x, y + 8), (x + w, y - 4), 10)
        bot = bez((x + w, y - 4), (x + w * 0.8, y + h * 1.25), (x - w * 0.8, y + h * 1.25), (x - w, y - 4), 16)
        m = top + bot[1:]
    ink(ctx, m, hexc("#6B1A1F"), 0)
    ctx.save(); path(ctx, m); ctx.clip()
    ink(ctx, ellipse(x, y + 18 + 40 * o, 40, 22 + 10 * o, 24), hexc("#E86A72"), 0)
    if shape == "ee":
        ink(ctx, rrect(x - 80, y - 20, 160, 26, 6), WHITE, 0)
    ctx.restore()
    ink(ctx, m, None, 9, salt=salt)


def _beanie(ctx, salt):
    dome = bez((318, 222), (338, -28), (700, -38), (726, 226), 30)
    ink(ctx, dome + [(726, 260), (318, 260)], GREY, LW, salt=salt)
    top = qbez((292, 216), (520, 84), (750, 224), 24)
    rgt = qbez((750, 224), (790, 282), (738, 340), 8)
    bot = qbez((738, 340), (520, 168), (300, 334), 24)
    lft = qbez((300, 334), (252, 274), (292, 216), 8)
    band = top + rgt[1:] + bot[1:] + lft[1:]
    ink(ctx, band, GREY, LW, salt=salt)
    _arc_text(ctx, "@Mecmation", qbez((308, 286), (520, 136), (738, 292), 60), 70)


def _arc_text(ctx, s, curve, size):
    """Draw text centred along a polyline, each glyph rotated to the curve."""
    ctx.select_font_face("Ubuntu", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(size)
    seg = [math.dist(a, b) for a, b in zip(curve, curve[1:])]
    total = sum(seg)
    adv = [ctx.text_extents(ch)[4] for ch in s]
    width = sum(adv) * 1.02
    pos = (total - width) / 2

    def at(d):
        for (a, b), L in zip(zip(curve, curve[1:]), seg):
            if d <= L:
                t = d / L
                return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t), math.atan2(b[1] - a[1], b[0] - a[0])
            d -= L
        return curve[-1], 0
    for ch, a in zip(s, adv):
        (px, py), ang = at(pos + a / 2)
        ctx.save(); ctx.translate(px, py); ctx.rotate(ang)
        ctx.move_to(-a / 2, size * 0.36); ctx.text_path(ch)
        ctx.set_source_rgba(1, 1, 1, 1); ctx.fill()
        ctx.restore()
        pos += a * 1.02


# ------------------------------------------------------------------ main
def draw_mecmation(ctx, st):
    s = st.get("s", 0.6)
    salt = 23
    ctx.save()
    # shadow on the ground (shrinks while hopping)
    hop = st.get("hop", 0)
    k = max(0.45, 1 - hop / 160)
    ctx.save(); ctx.translate(st["x"], st["ground"] - 6); ctx.scale(1, 0.12)
    ctx.arc(0, 0, 210 * s * k, 0, 2 * math.pi); ctx.set_source_rgba(0, 0, 0, 0.16 * k); ctx.fill(); ctx.restore()

    ctx.translate(st["x"] - 518 * s, st["ground"] - hop - 1455 * s)
    ctx.scale(s, s)
    _legs(ctx, st, salt)
    _shoes(ctx, salt)
    ctx.save()
    _upper_ctx(ctx, st)
    pose = st["pose"]
    behind = {sd for sd in ("L", "R") if pose[sd][2] == "relax"}
    for sd in behind:
        e, h, kind = pose[sd]
        _arm(ctx, sd, SH[sd], e, h, kind, salt, st.get("wave", 0) if sd == "R" else 0)
    _shirt(ctx, salt)
    for sd in ("L", "R"):
        if sd in behind:
            continue
        e, h, kind = pose[sd]
        _arm(ctx, sd, SH[sd], e, h, kind, salt, st.get("wave", 0) if sd == "R" else 0)
    # head: tilt around the neck
    ctx.translate(*NECK); ctx.rotate(st.get("tilt", 0)); ctx.translate(-NECK[0], -NECK[1])
    _head(ctx, st, salt)
    _beanie(ctx, salt)
    ctx.restore()
    ctx.restore()
