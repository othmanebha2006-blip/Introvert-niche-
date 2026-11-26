"""The opening hook, built like the reference videos (frame by frame analysis of 4 of them):

- the hero car is HUGE (~95% of the width, may be cut off at the edge), low, right above the caption
- it is DRIVING from frame 0 and keeps driving through the whole hook and the first rule (4-5 s):
  a road under it with lane dashes rushing past, grey speed streaks, exhaust puffs behind the rear wheel,
  blurred spinning wheels, a light suspension bounce, plus a background "ticker" that scrolls (parallax)
- the topic (the badge that the ending decodes) is visible from frame 0; on the topic word "?" marks pop and
  rings orbit it; on "explained" its pieces shake and glint.
"""
import math, cairo
from ink import *
from car import draw_car, WHEELS, YS
from widgets import *


def road(ctx, t, y, speed=1500.0):
    """side-view road: asphalt band, edge lines, white lane dashes moving right -> left"""
    ctx.set_source(lin_grad(0, y - 6, 0, y + 70, [(0, hexc("#8E939A")), (0.15, hexc("#A7ACB3")), (1, hexc("#C4C8CE"))]))
    ctx.rectangle(0, y - 6, 1080, 76); ctx.fill()
    line(ctx, [(0, y - 6), (1080, y - 6)], 3, hexc("#6F747B"), sketch=False)
    off = (t * speed) % 260
    for i in range(-1, 6):
        x0 = i * 260 - off
        ink(ctx, rrect(x0, y + 26, 130, 12, 6), hexc("#F4F5F7"), 0)


def streaks(ctx, t, y_top, y_bot, speed=2400.0, seed=1, color=(0.45, 0.48, 0.53), n=14):
    """horizontal speed lines flying from right to left"""
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    for i in range(n):
        r1 = (math.sin(i * 12.9898 + seed) * 43758.5453) % 1
        r2 = (math.sin(i * 78.233 + seed) * 12345.678) % 1
        yy = y_top + (y_bot - y_top) * r1
        ln = 60 + 220 * r2
        x = 1180 - ((t * speed * (0.6 + 0.8 * r2) + r1 * 1400) % 1500)
        ctx.move_to(x, yy); ctx.line_to(x + ln, yy)
        ctx.set_source_rgba(*color, 0.35 + 0.35 * r2); ctx.set_line_width(4 + 4 * r1); ctx.stroke()


def puffs(ctx, t, x, y):
    """small exhaust puffs drifting back from the rear bumper"""
    for i in range(4):
        ph = (t * 1.8 + i / 4) % 1
        r = 8 + ph * 22
        ink(ctx, ellipse(x - ph * 160, y - ph * 18, r, r, 18), (1, 1, 1, 0.75 * (1 - ph)), 2.5, (0.55, 0.58, 0.63, 0.7 * (1 - ph)), sketch=False)


def wheel_blur(ctx, kind, x, y, L, t):
    wr, wf, R = WHEELS[kind]; ys = YS[kind]
    for wx in (wr, wf):
        cx, cy = x + wx * L, y - R * L
        rr = R * L * 0.7
        ctx.set_source(rad_grad(cx, cy, rr * 0.2, rr, [(0, (0.78, 0.8, 0.83, 0.55)), (1, (0.55, 0.58, 0.62, 0.35))]))
        ctx.arc(cx, cy, rr, 0, 2 * math.pi); ctx.fill()
        for k in range(3):
            a0 = -t * 30 + k * 2.1
            ctx.new_sub_path(); ctx.arc(cx, cy, rr * (0.45 + 0.17 * k), a0, a0 + 1.6)
            ctx.set_source_rgba(1, 1, 1, 0.5); ctx.set_line_width(3); ctx.stroke()


def driving_car(ctx, t, kind, paint, L=990.0, x=20.0, y=905.0, ticker=None, **kw):
    """the hook car: drives on the spot with the world rushing past. ticker(ctx, t) draws a scrolling backdrop."""
    if ticker:
        ticker(ctx, t)
    streaks(ctx, t, y - 0.5 * L * YS[kind], y - 40, seed=2)
    road(ctx, t, y + 2)
    bounce = 3.0 * math.sin(t * 17) + 1.5 * math.sin(t * 29)
    draw_car(ctx, kind, x, y - bounce, L, paint, -t * 32, **kw)
    wheel_blur(ctx, kind, x, y - bounce, L, t)
    puffs(ctx, t, x + 0.01 * L, y - 0.06 * L)
    streaks(ctx, t + 0.37, y - 0.22 * L * YS[kind], y - 10, seed=7, n=6, color=(0.5, 0.53, 0.58))


def topic_fx(ctx, t, cx, cy, w, h, t_topic, t_explained):
    """? marks + orbiting rings on the topic word, glints on 'explained'"""
    if t > t_topic:
        p = ease_out_back(min(1, (t - t_topic) / 0.35))
        for i in range(3):
            a = t * (1.6 + 0.4 * i) + i * 2.1
            ctx.save(); ctx.translate(cx, cy); ctx.rotate(0.15 * i - 0.1)
            ctx.scale(w * (0.62 + 0.06 * i) * p, h * (0.9 + 0.12 * i) * p)
            ctx.arc(0, 0, 1, a, a + 4.2); ctx.restore()
            ctx.set_source_rgba(0.95, 0.75, 0.15, 0.85 - 0.2 * i); ctx.set_line_width(5); ctx.stroke()
        for i, (qx, qy) in enumerate([(-0.45, -0.75), (0.05, -0.95), (0.48, -0.7), (-0.2, 0.8), (0.35, 0.85)]):
            bob = math.sin(t * 6 + i) * 6
            s = max(0.02, ease_out_back(min(1, (t - t_topic - 0.06 * i) / 0.3))) if t > t_topic + 0.06 * i else 0
            if s > 0:
                ctx.save(); ctx.translate(cx + qx * w, cy + qy * h + bob); ctx.scale(s, s)
                ink(ctx, ellipse(0, 0, 24, 24, 24), hexc("#FFFFFF"), 4)
                label(ctx, "?", 0, 2, 36, RED); ctx.restore()
    if t > t_explained:
        for i in range(4):
            ph = (t * 2.2 + i * 0.25) % 1
            sparkle(ctx, cx - w * 0.45 + i * w * 0.3, cy - h * 0.5 + (i % 2) * h, 22 * (1 - abs(ph - 0.5) * 2) + 6, t + i)
