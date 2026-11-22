"""Sketchy-ink vector primitives on top of pycairo.

Every shape is a list of points. `ink()` fills it and strokes it with a hand-drawn
line whose wobble changes every few frames ("line boil"), like a drawn cartoon.
"""
import math, cairo

INK = (0.11, 0.12, 0.14)
BOIL = {"seed": 0, "amp": 1.3}


def set_boil(frame, every=4, amp=1.3):
    BOIL["seed"] = frame // every
    BOIL["amp"] = amp


def hexc(h, a=1.0):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)) + (a,)


def mix(c1, c2, t):
    return tuple(a + (b - a) * t for a, b in zip(c1, c2))


def shade(c, k):
    """k<0 darker, k>0 lighter."""
    if k < 0:
        return mix(c, (0, 0, 0, c[3]), -k)
    return mix(c, (1, 1, 1, c[3]), k)


# ---------- geometry ----------
def bez(p0, p1, p2, p3, n=16):
    out = []
    for i in range(n + 1):
        t = i / n; u = 1 - t
        out.append((u**3 * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t**3 * p3[0],
                    u**3 * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t**3 * p3[1]))
    return out


def qbez(p0, p1, p2, n=8):
    out = []
    for i in range(n + 1):
        t = i / n; u = 1 - t
        out.append((u * u * p0[0] + 2 * u * t * p1[0] + t * t * p2[0], u * u * p0[1] + 2 * u * t * p1[1] + t * t * p2[1]))
    return out


def rpoly(pts, r):
    """Polygon with rounded corners. r: number or list per vertex."""
    n = len(pts); out = []
    rs = r if isinstance(r, (list, tuple)) else [r] * n
    for i in range(n):
        p0, p1, p2 = pts[i - 1], pts[i], pts[(i + 1) % n]
        rr = rs[i]
        if rr <= 0:
            out.append(p1); continue
        d1 = math.dist(p0, p1); d2 = math.dist(p1, p2)
        if d1 < 1e-6 or d2 < 1e-6:
            out.append(p1); continue
        a = min(rr, d1 / 2.05); b = min(rr, d2 / 2.05)
        s = (p1[0] + (p0[0] - p1[0]) * a / d1, p1[1] + (p0[1] - p1[1]) * a / d1)
        e = (p1[0] + (p2[0] - p1[0]) * b / d2, p1[1] + (p2[1] - p1[1]) * b / d2)
        out += qbez(s, p1, e, 6)
    return out


def ellipse(cx, cy, rx, ry, n=48, a0=0, a1=2 * math.pi):
    return [(cx + rx * math.cos(a0 + (a1 - a0) * i / n), cy + ry * math.sin(a0 + (a1 - a0) * i / n)) for i in range(n + 1)]


def rrect(x, y, w, h, r):
    return rpoly([(x, y), (x + w, y), (x + w, y + h), (x, y + h)], r)


def resample(pts, step=6, closed=False):
    if closed:
        pts = list(pts) + [pts[0]]
    out = [pts[0]]
    for a, b in zip(pts, pts[1:]):
        d = math.dist(a, b)
        k = max(1, int(d / step))
        for i in range(1, k + 1):
            out.append((a[0] + (b[0] - a[0]) * i / k, a[1] + (b[1] - a[1]) * i / k))
    return out


def _noise(x, y, s):
    return (math.sin(x * 0.031 + s * 1.7) * 0.6 + math.sin(y * 0.027 + s * 2.3 + 1.1) * 0.5
            + math.sin((x + y) * 0.071 + s * 3.1) * 0.35)


def wobble(pts, amp=None, salt=0):
    amp = BOIL["amp"] if amp is None else amp
    s = BOIL["seed"] * 7.13 + salt
    return [(x + amp * _noise(x, y, s), y + amp * _noise(y + 50, x - 30, s + 5)) for x, y in pts]


def path(ctx, pts, closed=True):
    ctx.move_to(*pts[0])
    for p in pts[1:]:
        ctx.line_to(*p)
    if closed:
        ctx.close_path()


def ink(ctx, pts, fill=None, w=4.0, color=INK, closed=True, sketch=True, salt=0, grad=None):
    """Fill (colour or cairo pattern) then stroke with a wobbly ink line."""
    if fill is not None or grad is not None:
        path(ctx, pts, closed)
        if grad is not None:
            ctx.set_source(grad)
        else:
            ctx.set_source_rgba(*fill)
        ctx.fill()
    if w > 0:
        q = wobble(resample(pts, 7, closed), salt=salt) if sketch else pts
        path(ctx, q, closed and not sketch)
        ctx.set_source_rgba(*color)
        ctx.set_line_width(w)
        ctx.set_line_join(cairo.LINE_JOIN_ROUND)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.stroke()


def line(ctx, pts, w=4.0, color=INK, sketch=True, salt=0):
    ink(ctx, pts, None, w, color, closed=False, sketch=sketch, salt=salt)


def lin_grad(x0, y0, x1, y1, stops):
    g = cairo.LinearGradient(x0, y0, x1, y1)
    for t, c in stops:
        g.add_color_stop_rgba(t, *c)
    return g


def rad_grad(cx, cy, r0, r1, stops):
    g = cairo.RadialGradient(cx, cy, r0, cx, cy, r1)
    for t, c in stops:
        g.add_color_stop_rgba(t, *c)
    return g


def ease(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def ease_out_back(t, s=1.7):
    t = max(0.0, min(1.0, t)) - 1
    return t * t * ((s + 1) * t + s) + 1


def ease_out(t):
    t = max(0.0, min(1.0, t))
    return 1 - (1 - t) ** 3
