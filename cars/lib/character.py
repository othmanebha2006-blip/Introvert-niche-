"""The presenter: an original character (beanie, round glasses, teal hoodie), drawn in ink.

draw_presenter(ctx, st) where st holds: x, y (head centre), mouth (0..1 open), shape ('ah','ee','oh'),
blink (0..1), brows ('neutral','up','skeptic','frown','smug'), look (dx, dy) pupil offset, pose (dict of arm
targets, already interpolated), tilt (radians), smile (-1..1).
"""
import math
from ink import *

SKIN = hexc("#F4CDB0"); SKIN_D = hexc("#DFA585")
HAIR = hexc("#3B2A22")
BEANIE = hexc("#E3A42A"); BEANIE_D = hexc("#B97F17")
HOOD = hexc("#2E8C82"); HOOD_D = hexc("#21665F")
WHITE = hexc("#FFFFFF")

# arm poses: per arm (elbow, hand) offsets from the shoulder, hand type
POSES = {
    "rest":    {"L": ((-60, 170), (-10, 300), "fist"), "R": ((60, 170), (10, 300), "fist")},
    "hips":    {"L": ((-110, 130), (-20, 250), "fist"), "R": ((110, 130), (20, 250), "fist")},
    "explain": {"L": ((-80, 160), (60, 70), "open"), "R": ((110, 130), (20, 250), "fist")},
    "point":   {"L": ((-110, 30), (-60, -150), "point"), "R": ((110, 130), (20, 250), "fist")},
    "shrug":   {"L": ((-140, 120), (-190, 10), "open"), "R": ((140, 120), (190, 10), "open")},
    "count":   {"L": ((-80, 160), (40, 50), "open"), "R": ((80, 160), (-40, 60), "point")},
    "thumb":   {"L": ((-110, 130), (-20, 250), "fist"), "R": ((80, 150), (-10, 40), "thumb")},
}


def lerp_pose(a, b, t):
    out = {}
    for side in ("L", "R"):
        (e1, h1, k1), (e2, h2, k2) = POSES[a][side], POSES[b][side]
        e = (e1[0] + (e2[0] - e1[0]) * t, e1[1] + (e2[1] - e1[1]) * t)
        h = (h1[0] + (h2[0] - h1[0]) * t, h1[1] + (h2[1] - h1[1]) * t)
        out[side] = (e, h, k2 if t > 0.5 else k1)
    return out


def _arm(ctx, sh, el, ha, kind, side, salt):
    pts = qbez(sh, el, ha, 14)
    # sleeve: ink outline under a colour stroke
    for w, c in ((86, INK), (76, HOOD)):
        line(ctx, pts, w, c, sketch=(c is INK), salt=salt)
    # sleeve shading along the outside
    line(ctx, [(p[0] + (8 if side == "R" else -8), p[1] + 4) for p in pts[2:-2]], 14, HOOD_D, sketch=False)
    # cuff
    d = (ha[0] - el[0], ha[1] - el[1]); n = math.hypot(*d) or 1; d = (d[0] / n, d[1] / n)
    cx, cy = ha[0] - d[0] * 18, ha[1] - d[1] * 18
    line(ctx, [(cx - d[1] * 36, cy + d[0] * 36), (cx + d[1] * 36, cy - d[0] * 36)], 4, salt=salt)
    _hand(ctx, ha, d, kind, side, salt)


def _hand(ctx, p, d, kind, side, salt):
    x, y = p[0] + d[0] * 16, p[1] + d[1] * 16
    ang = math.atan2(d[1], d[0])
    ctx.save(); ctx.translate(x, y); ctx.rotate(ang)
    mir = -1 if side == "R" else 1
    if kind == "point":
        finger = rrect(14, -12 * mir - 12, 70, 24, 12)
        ink(ctx, finger, SKIN, 4, salt=salt)
        ink(ctx, ellipse(4, 0, 32, 28), SKIN, 4, salt=salt)
        line(ctx, [(-6, 10 * mir), (16, 14 * mir)], 3, salt=salt)
    elif kind == "open":
        for i, a in enumerate((-0.55, -0.2, 0.15, 0.5)):
            fx, fy = math.cos(a) * 30, math.sin(a) * 30
            ink(ctx, ellipse(fx + math.cos(a) * 14, fy + math.sin(a) * 14, 15, 10, 20), SKIN, 3.5, salt=salt + i)
        ink(ctx, ellipse(0, 0, 33, 30), SKIN, 4, salt=salt)
        ink(ctx, ellipse(-4, 28 * mir, 18, 11), SKIN, 3.5, salt=salt)
    elif kind == "thumb":
        ink(ctx, ellipse(4, 0, 32, 30), SKIN, 4, salt=salt)
        ctx.rotate(-ang - math.pi / 2)
        ink(ctx, rrect(-9, -62, 18, 40, 9), SKIN, 4, salt=salt)
    else:
        ink(ctx, ellipse(4, 0, 32, 30), SKIN, 4, salt=salt)
        for k in (-12, 4, 18):
            line(ctx, [(20, k * mir * 0.8), (32, k * mir * 0.8)], 3, salt=salt)
    ctx.restore()


def draw_presenter(ctx, st):
    x, y = st["x"], st["y"]
    salt = 11
    sh_y = y + 200
    shL, shR = (x - 175, sh_y + 30), (x + 175, sh_y + 30)
    pose = st["pose"]

    # ---- torso (hoodie) ----
    torso = rpoly([(x - 120, sh_y - 5), (x + 120, sh_y - 5), (x + 230, sh_y + 60), (x + 250, y + 900),
                   (x - 250, y + 900), (x - 230, sh_y + 60)], [40, 40, 70, 0, 0, 70])
    ink(ctx, torso, None, 5, grad=lin_grad(x - 250, 0, x + 250, 0, [(0, HOOD_D), (0.25, HOOD), (0.8, HOOD), (1, HOOD_D)]), salt=salt)
    # pocket + centre seam
    ink(ctx, rpoly([(x - 120, y + 560), (x + 120, y + 560), (x + 170, y + 700), (x - 170, y + 700)], 18), HOOD_D, 4, salt=salt)
    # hood collar behind neck
    ink(ctx, rpoly([(x - 135, sh_y - 30), (x + 135, sh_y - 30), (x + 95, sh_y + 70), (x - 95, sh_y + 70)], 45),
        HOOD_D, 5, salt=salt)
    # neck
    ink(ctx, rpoly([(x - 45, y + 130), (x + 45, y + 130), (x + 48, sh_y + 25), (x - 48, sh_y + 25)], 12), SKIN_D, 4, salt=salt)
    ink(ctx, ellipse(x, sh_y + 22, 62, 24, 30, 0, math.pi), HOOD, 4, salt=salt)
    # drawstrings
    for s in (-1, 1):
        sx = x + s * 38
        line(ctx, [(sx, sh_y + 35), (sx + s * 6, sh_y + 120), (sx + s * 2, sh_y + 175)], 6, WHITE, sketch=False)
        line(ctx, [(sx, sh_y + 35), (sx + s * 6, sh_y + 120), (sx + s * 2, sh_y + 175)], 2, salt=salt)
        ink(ctx, rrect(sx + s * 2 - 6, sh_y + 172, 12, 24, 5), hexc("#D8D8D8"), 3, salt=salt)

    # ---- arms ----
    for side, sh in (("L", shL), ("R", shR)):
        e, h, k = pose[side]
        _arm(ctx, sh, (sh[0] + e[0], sh[1] + e[1]), (sh[0] + h[0], sh[1] + h[1]), k, side, salt)

    # ---- head ----
    ctx.save()
    ctx.translate(x, y + 120); ctx.rotate(st.get("tilt", 0)); ctx.translate(-x, -(y + 120))
    hx, hy = x, y
    # ears
    for s in (-1, 1):
        ink(ctx, ellipse(hx + s * 142, hy + 20, 26, 36), SKIN, 4.5, salt=salt)
        line(ctx, ellipse(hx + s * 144, hy + 22, 11, 18, 12, 1.0 if s > 0 else 2.2, 4.0 if s > 0 else 5.4), 3, SKIN_D, salt=salt)
    # hair at sides/back
    for s in (-1, 1):
        tufts = [(hx + s * 112, hy - 90), (hx + s * 160, hy - 60), (hx + s * 146, hy - 35), (hx + s * 168, hy - 10),
                 (hx + s * 140, hy + 5), (hx + s * 120, hy - 20)]
        ink(ctx, rpoly(tufts, 10), HAIR, 4, salt=salt)
    face = rpoly([(hx - 140, hy - 110), (hx + 140, hy - 110), (hx + 148, hy + 30), (hx + 95, hy + 150),
                  (hx - 95, hy + 150), (hx - 148, hy + 30)], [70, 70, 70, 60, 60, 70])
    ink(ctx, face, None, 5, grad=rad_grad(hx - 30, hy - 30, 20, 220, [(0, shade(SKIN, 0.08)), (0.75, SKIN), (1, SKIN_D)]), salt=salt)
    # cheeks
    for s in (-1, 1):
        ctx.save(); ctx.translate(hx + s * 92, hy + 62); ctx.scale(1, 0.6)
        ctx.arc(0, 0, 28, 0, 2 * math.pi); ctx.set_source_rgba(0.93, 0.5, 0.45, 0.28); ctx.fill(); ctx.restore()
    # fringe
    fringe = [(hx - 140, hy - 70), (hx - 110, hy - 40), (hx - 85, hy - 70), (hx - 50, hy - 45), (hx - 25, hy - 78),
              (hx + 15, hy - 50), (hx + 40, hy - 80), (hx + 80, hy - 52), (hx + 105, hy - 82), (hx + 142, hy - 60),
              (hx + 145, hy - 120), (hx - 145, hy - 120)]
    ink(ctx, rpoly(fringe, 12), HAIR, 4.5, salt=salt)
    # beanie
    bean = rpoly([(hx - 158, hy - 95), (hx - 150, hy - 200), (hx - 60, hy - 262), (hx + 60, hy - 262),
                  (hx + 150, hy - 200), (hx + 158, hy - 95)], [10, 60, 60, 60, 60, 10])
    ink(ctx, bean, None, 5, grad=lin_grad(hx - 160, 0, hx + 160, 0, [(0, BEANIE_D), (0.3, BEANIE), (0.75, BEANIE), (1, BEANIE_D)]), salt=salt)
    for i in range(-5, 6):
        line(ctx, [(hx + i * 26, hy - 150 - (36 - abs(i) * 5)), (hx + i * 27.5, hy - 140)], 2.5, BEANIE_D, salt=salt + i)
    cuff = rpoly([(hx - 166, hy - 140), (hx + 166, hy - 140), (hx + 170, hy - 82), (hx - 170, hy - 82)], 14)
    ink(ctx, cuff, BEANIE, 5, salt=salt)
    for i in range(-7, 8):
        line(ctx, [(hx + i * 22, hy - 132), (hx + i * 22.3, hy - 90)], 2.2, BEANIE_D, salt=salt + i)
    # label patch
    ink(ctx, rrect(hx + 70, hy - 128, 54, 32, 6), hexc("#1E1F24"), 3, salt=salt)

    # ---- face features ----
    lx, ly = st.get("look", (0, 0))
    blink = st.get("blink", 0)
    br = st.get("brows", "neutral")
    for s in (-1, 1):
        ex, ey = hx + s * 55, hy + 8
        # eye
        if blink > 0.5:
            line(ctx, [(ex - 16, ey + 2), (ex, ey + 6), (ex + 16, ey + 2)], 5, salt=salt)
        else:
            ink(ctx, ellipse(ex, ey, 22, 24 * (1 - blink * 0.8)), WHITE, 0)
            ink(ctx, ellipse(ex + lx * 8, ey + ly * 8, 11, 12 * (1 - blink)), INK, 0)
            ink(ctx, ellipse(ex + lx * 8 - 4, ey + ly * 8 - 5, 3.5, 3.5, 10), WHITE, 0)
        # glasses
        ink(ctx, ellipse(ex, ey, 46, 44), (1, 1, 1, 0.12), 6, hexc("#20232A"), salt=salt)
        line(ctx, [(ex - s * 0, ey - 30), (ex - 18, ey - 20)], 3, (1, 1, 1, 0.55), sketch=False)
        # brows
        a = {"neutral": 0, "up": -0.12, "frown": 0.28, "skeptic": 0.25 if s < 0 else -0.25, "smug": -0.15 if s < 0 else 0.05,
             "worried": -0.3}[br] * s
        lift = {"neutral": 0, "up": -18, "frown": 6, "skeptic": 4 if s < 0 else -16, "smug": -6, "worried": -10}[br]
        by = ey - 64 + lift
        line(ctx, [(ex - 30, by + a * 40), (ex, by - 4), (ex + 30, by - a * 40)], 11, HAIR, salt=salt)
    # bridge + arms of glasses
    line(ctx, [(hx - 10, hy + 2), (hx, hy - 4), (hx + 10, hy + 2)], 5, hexc("#20232A"), salt=salt)
    for s in (-1, 1):
        line(ctx, [(hx + s * 101, hy + 2), (hx + s * 140, hy - 4)], 5, hexc("#20232A"), salt=salt)
    # nose
    line(ctx, [(hx + 4, hy + 40), (hx + 14, hy + 62), (hx - 2, hy + 68)], 4, SKIN_D, salt=salt)
    # mouth
    _mouth(ctx, hx, hy + 102, st.get("mouth", 0), st.get("shape", "ah"), st.get("smile", 0.2), salt)
    ctx.restore()


def _mouth(ctx, x, y, o, shape, smile, salt):
    if o < 0.08:
        c = 10 * smile
        line(ctx, [(x - 34, y - c), (x, y + c * 0.6), (x + 34, y - c)], 5, salt=salt)
        return
    w = {"ah": 34, "ee": 40, "oh": 22}[shape] + 6 * o
    h = {"ah": 34, "ee": 18, "oh": 30}[shape] * (0.35 + 0.65 * o)
    m = rpoly([(x - w, y - 4 - smile * 6), (x + w, y - 4 - smile * 6), (x + w * 0.65, y + h), (x - w * 0.65, y + h)],
              [w * 0.5, w * 0.5, h * 0.6, h * 0.6]) if shape != "oh" else ellipse(x, y + h / 2 - 4, w, h / 2 + 4)
    ink(ctx, m, hexc("#5A1E22"), 5, salt=salt)
    ctx.save(); path(ctx, m); ctx.clip()
    if shape != "oh":
        ink(ctx, rrect(x - w, y - 12, 2 * w, 16 if shape == "ee" else 13, 4), WHITE, 0)
    ink(ctx, ellipse(x, y + h + 6, w * 0.6, h * 0.45 + 4), hexc("#D9626B"), 0)
    ctx.restore()
    ink(ctx, m, None, 5, salt=salt)
