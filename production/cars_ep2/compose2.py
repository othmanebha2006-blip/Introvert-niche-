"""Episode 1 v2 — everything moves.

Rules taken from the reference analysis:
  * a car is NEVER parked: wheels spin, speed lines + dust stream behind it, it drives in from the
    left and drives out to the right while the next one arrives;
  * something new happens every 0.5–1 s, locked to the spoken word;
  * props interact with the car (crown drops on the roof, plug flies into the charge port,
    car climbs a rocky hill, slaloms cones, burns out, flames on the V10);
  * a 'decoder bar' at the top always shows the name being explained, with the current part
    circled and a 'part = meaning' card under it.

usage: python3 compose2.py [--frames t,t,...] [--preview t0 t1]
"""
import math, os, random, subprocess, sys, functools
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops

import compose as C
from compose import (W, H, FPS, at, ease_out, ease_back, font, FONT_BLACK, FONT_XB, FONT_MONO, INK, YEL, WHITE, RED,
                     BLUE, GREEN, TEAL, GOLD, ORANGE, keycap, tag, stamp, icon, paste_clip, pop, CAR_META,
                     PX_MM_RENDER, lexus_logo, draw_caption, draw_header, draw_character, make_background, B, END)

CX, GY, SC = 540, 880, 0.172
DIN, DOUT = 0.5, 0.45
CRUISE = 650.0            # virtual road speed in px/s (wheel spin, dust, lines)
DARK = (30, 30, 30)


def ease_in(x):
    x = min(max(x, 0), 1)
    return x * x * x


def lerp(a, b, p):
    return a + (b - a) * p


def clamp01(x):
    return min(max(x, 0.0), 1.0)


# ======================================================================= car rendering
@functools.lru_cache(maxsize=256)
def car_q(key, pxmm_q):
    pxmm = pxmm_q / 1000
    im = Image.open(os.path.join(B, 'png', f'{key}.png')).convert('RGBA')
    f = pxmm / PX_MM_RENDER
    return im.resize((max(1, int(im.width * f)), max(1, int(im.height * f))), Image.LANCZOS)


def car_base(key, pxmm):
    return car_q(key, int(round(pxmm * 1000)))


@functools.lru_cache(None)
def puff(r):
    s = r * 2 + 4
    im = Image.new('RGBA', (s, s), (0, 0, 0, 0))
    a = np.zeros((s, s), np.float32)
    yy, xx = np.mgrid[0:s, 0:s]
    d = np.sqrt((xx - s / 2) ** 2 + (yy - s / 2) ** 2) / r
    a = np.clip(1 - d, 0, 1) ** 1.6
    arr = np.zeros((s, s, 4), np.uint8)
    arr[..., :3] = 205
    arr[..., 3] = (a * 255).astype(np.uint8)
    return Image.fromarray(arr)


def draw_puffs(L, x, y, t, t0, rate=0.06, life=0.7, drift=380, size=(10, 46), alpha=0.55, seed=0, rise=60):
    """Stateless dust/smoke trail emitted at (x,y) from time t0 on, trailing to the LEFT."""
    if t < t0:
        return
    rng = random.Random(seed)
    k_last = int((t - t0) / rate)
    for k in range(max(0, k_last - int(life / rate) - 1), k_last + 1):
        born = t0 + k * rate
        age = t - born
        if age < 0 or age > life:
            continue
        rr = random.Random(seed * 1000 + k)
        p = age / life
        r = int(lerp(size[0], size[1], p ** 0.6) * rr.uniform(0.7, 1.2))
        px = x - drift * age + rr.uniform(-10, 10)
        py = y - rise * p + rr.uniform(-8, 8)
        im = puff(max(2, r))
        a = int(255 * alpha * (1 - p) ** 1.3)
        if a <= 2:
            continue
        arr = np.asarray(im).copy()
        arr[..., 3] = (arr[..., 3].astype(np.uint16) * a // 255).astype(np.uint8)
        paste_clip(L, Image.fromarray(arr), int(px - im.width / 2), int(py - im.height / 2))


def draw_car(L, key, cx, gy, pxmm, travel=0.0, angle=0.0, alpha=1.0, shine=None, ghost=False, flames=0.0, t=0.0):
    im = car_base(key, pxmm)
    m = CAR_META[key]
    f = pxmm / PX_MM_RENDER * 2
    body = im
    if travel and not ghost:
        body = im.copy()
        mq = []
        for (wx, wy) in m['wheels']:
            wx, wy = wx * f, wy * f
            rr = m['wheel_r'] * f
            r = int(rr * 0.72)
            if r < 4:
                continue
            box = (int(wx - r), int(wy - r), int(wx - r) + 2 * r, int(wy - r) + 2 * r)
            patch = im.crop(box)
            mask = Image.new('L', patch.size, 0)
            ImageDraw.Draw(mask).ellipse((1, 1, 2 * r - 2, 2 * r - 2), fill=255)
            rp = patch.rotate(-math.degrees(travel / max(rr, 1)), resample=Image.BICUBIC)
            body.paste(rp, box[:2], mask)
            # brake calipers don't spin: put the strongly coloured (red / yellow) caliper pixels back
            pa = np.asarray(patch).astype(np.int16)
            sat = pa[..., :3].max(2) - pa[..., :3].min(2)
            cal = (sat > 110) & (((pa[..., 0] > 140) & (pa[..., 1] < 100)) | ((pa[..., 0] > 160) & (pa[..., 1] > 120) & (pa[..., 2] < 70)))
            if cal.any():
                cm = Image.fromarray((cal * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(3))
                body.paste(patch, box[:2], ImageChops.multiply(cm, mask))
    if shine is not None and 0 < shine < 1 and not ghost:
        a = np.asarray(body).astype(np.float32)
        hgt, wid = a.shape[:2]
        yy, xx = np.mgrid[0:hgt, 0:wid]
        pos = lerp(-0.3, 1.3, shine) * (wid + hgt)
        band = np.clip(1 - np.abs((xx + yy * 0.6) - pos) / (wid * 0.08), 0, 1) * 0.75
        a[..., :3] = a[..., :3] * (1 - band[..., None]) + 255 * band[..., None]
        body = Image.fromarray(a.astype(np.uint8))
    if ghost:
        a = np.asarray(im).copy()
        g = np.zeros_like(a)
        g[..., :3] = (150, 154, 160)
        g[..., 3] = (a[..., 3] * 0.35).astype(np.uint8)
        # dashed outline feel: keep only the edge
        e = Image.fromarray(a[..., 3]).filter(ImageFilter.FIND_EDGES)
        g[..., 3] = np.maximum(g[..., 3], (np.asarray(e) > 40) * 190).astype(np.uint8)
        g[..., :3][np.asarray(e) > 40] = (110, 114, 120)
        body = Image.fromarray(g)
    if alpha < 1:
        a = np.asarray(body).copy(); a[..., 3] = (a[..., 3] * alpha).astype(np.uint8); body = Image.fromarray(a)
    gyi = m['ground_y'] * f
    x0, y0 = cx - body.width / 2, gy - gyi
    if not ghost:
        sw = int(body.width * 0.86)
        sh = C.shadow_img(sw, max(8, int(26 * pxmm / SC)))
        paste_clip(L, sh, int(cx - sh.width / 2), int(gy - sh.height / 2 + 4))
    if angle:
        # rotate around the ground contact centre
        big = Image.new('RGBA', (body.width + 2 * body.height, body.height * 3), (0, 0, 0, 0))
        ox, oy = body.height, body.height
        big.alpha_composite(body, (ox, oy))
        pivot = (ox + body.width / 2, oy + gyi)
        big = big.rotate(angle, resample=Image.BICUBIC, center=pivot)
        x0, y0 = cx - pivot[0], gy - pivot[1]
        body = big
    if flames > 0 and not ghost:
        d = ImageDraw.Draw(L)
        ex, ey = x0 + 4 if not angle else x0 + body.height + 4, gy - 0.32 * gyi
        rng = random.Random(int(t * 30))
        for k in range(3):
            ln = (40 + rng.randint(0, 50)) * flames
            d.polygon([(ex, ey - 10), (ex - ln, ey + rng.randint(-6, 6)), (ex, ey + 10)], fill=(255, 150 + k * 40, 30))
    paste_clip(L, body, int(x0), int(y0))
    return dict(x0=x0, y0=y0, w=body.width, rear=(x0 + m['wheels'][0][0] * f, y0 + m['wheels'][0][1] * f + m['wheel_r'] * f),
                front=(x0 + m['wheels'][1][0] * f, y0 + m['wheels'][1][1] * f), roof_y=y0 + 40 * f * 0.2, top=y0)


# ======================================================================= car timeline
SEGS = []


def seg(key, t_in, t_out, kf=None, enter='left', cruise=True, mod=None, burnout=False, exit='right'):
    SEGS.append(dict(key=key, t_in=t_in, t_out=t_out, kf=kf or [(t_in, CX, GY, SC)], enter=enter, cruise=cruise, mod=mod,
                     burnout=burnout, exit=exit))


def kf_at(kf, t):
    if t <= kf[0][0]:
        return kf[0][1:]
    for a, b in zip(kf, kf[1:]):
        if a[0] <= t <= b[0]:
            p = ease_out((t - a[0]) / max(b[0] - a[0], 1e-6))
            return tuple(lerp(x, y, p) for x, y in zip(a[1:], b[1:]))
    return kf[-1][1:]


def seg_state(s, t):
    if t < s['t_in'] or t > s['t_out'] + DOUT:
        return None
    cx, gy, sc = kf_at(s['kf'], t)
    m = CAR_META[s['key']]
    wpx = m['L'] * sc + 200
    speed = CRUISE if s['cruise'] else 0
    lines = 0.45 if s['cruise'] else 0
    p_in = (t - s['t_in']) / DIN
    if s['enter'] == 'left' and p_in < 1:
        cx = lerp(-wpx / 2, cx, ease_out(p_in)); speed = CRUISE * 1.8; lines = 1
    elif s['enter'] == 'zoom' and p_in < 1:
        sc = sc * lerp(0.15, 1, ease_out(p_in)); gy = lerp(gy - 120, gy, ease_out(p_in)); speed = CRUISE; lines = 1
    angle = 0
    if t > s['t_out']:
        p = (t - s['t_out']) / DOUT
        cx = cx + ease_in(p) * (W + wpx)
        speed = CRUISE * 2.2; lines = 1
    dx = dy = 0
    if s['mod']:
        dx, dy, angle, dsc = s['mod'](t)
        sc *= dsc
    travel = CRUISE * (t - s['t_in']) + (cx - CX) if (s['cruise'] or t > s['t_out'] or p_in < 1) else (cx - CX)
    return dict(cx=cx + dx, gy=gy + dy, sc=sc, angle=angle, speed=speed, lines=lines, travel=travel)


def draw_cars(L, t, layer='all'):
    out = {}
    for i, s in enumerate(SEGS):
        st = seg_state(s, t)
        if not st:
            continue
        shine = None
        if s.get('shine_at') is not None:
            sp = (t - s['shine_at']) / 0.6
            shine = sp if 0 < sp < 1 else None
        info = draw_car(L, s['key'], st['cx'], st['gy'], st['sc'], travel=st['travel'], angle=st['angle'], shine=shine,
                        flames=s.get('flames', lambda t: 0)(t), t=t)
        if st['speed'] > 0:
            rx, ry = info['rear']
            big = s['burnout'] and t < s['t_in'] + 1.0
            draw_puffs(L, rx - 20, ry - 8, t, s['t_in'], rate=0.045 if big else 0.07, life=0.9 if big else 0.55,
                       drift=420 if not big else 220, size=(14, 70 if big else 34), alpha=0.75 if big else 0.4, seed=i + 1,
                       rise=90 if big else 40)
        out[s['key'] + str(i)] = (s, st, info)
    return out


# ======================================================================= backdrops & fx
def speed_lines(L, t, y0, y1, k=1.0, seed=3, n=14, cols=((170, 174, 180), (196, 200, 206), (120, 126, 134))):
    if k <= 0.02:
        return
    d = ImageDraw.Draw(L)
    rng = random.Random(seed)
    for i in range(n):
        y = rng.uniform(y0, y1)
        ln = rng.uniform(80, 260) * (0.5 + k)
        sp = rng.uniform(900, 1700)
        x = W + 300 - ((t * sp + rng.uniform(0, 3000)) % (W + 600))
        d.line([(x, y), (x + ln, y)], fill=cols[i % len(cols)], width=rng.choice([3, 4, 6]))


def ground_line(L, t, y, speed=CRUISE):
    d = ImageDraw.Draw(L)
    for k in range(-1, 14):
        x = (k * 110 - (t * speed) % 110)
        d.line([(x, y + 14), (x + 50, y + 14)], fill=(190, 194, 200), width=4)


def city(L, t, gy):
    d = ImageDraw.Draw(L)
    rng = random.Random(9)
    blds = [(rng.randint(60, 140), rng.randint(140, 360)) for _ in range(30)]
    total = sum(w for w, h in blds) + 30 * 12
    off = (t * 140) % total
    x = -off
    while x <= W:
        for w_, h_ in blds:
            if x > W:
                break
            if x + w_ > -10:
                d.rectangle((x, gy - h_, x + w_, gy), fill=(210, 216, 226), outline=(184, 190, 200), width=3)
                for yy in range(gy - h_ + 16, gy - 20, 34):
                    for xx in range(int(x) + 12, int(x + w_) - 14, 26):
                        d.rectangle((xx, yy, xx + 12, yy + 16), fill=(236, 240, 246))
            x += w_ + 12


def cones(L, t, gy, t0):
    for k in range(8):
        x = W + 100 + k * 260 - (t - t0) * 700
        if -80 < x < W + 80:
            ic = cone_img()
            paste_clip(L, ic, int(x - ic.width / 2), int(gy - ic.height + 6))


@functools.lru_cache(None)
def cone_img():
    im = Image.new('RGBA', (70, 90), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.polygon([(35, 4), (60, 80), (10, 80)], fill=(255, 120, 20), outline=INK)
    d.line([(35, 4), (60, 80), (10, 80), (35, 4)], fill=INK, width=4)
    d.polygon([(24, 40), (46, 40), (50, 54), (20, 54)], fill=WHITE)
    d.rectangle((2, 78, 68, 88), fill=(220, 90, 10), outline=INK, width=3)
    return im


def sun_rays(L, cx, cy, t, k=1.0):
    over = Image.new('RGBA', (W, 900), (0, 0, 0, 0))
    d = ImageDraw.Draw(over)
    n = 14
    for i in range(n):
        a0 = t * 0.6 + i * 2 * math.pi / n
        a1 = a0 + math.pi / n * 0.55
        R = 900
        d.polygon([(cx, cy), (cx + R * math.cos(a0), cy + R * math.sin(a0)), (cx + R * math.cos(a1), cy + R * math.sin(a1))],
                  fill=(255, 214, 80, int(70 * k)))
    L.alpha_composite(over, (0, 0))


def hill(L, slope_y0, slope_y1):
    d = ImageDraw.Draw(L)
    d.polygon([(0, slope_y0), (W, slope_y1), (W, 1060), (0, 1060)], fill=(150, 120, 86))
    d.line([(0, slope_y0), (W, slope_y1)], fill=INK, width=5)
    rng = random.Random(4)
    for k in range(16):
        x = rng.randint(0, W)
        y = lerp(slope_y0, slope_y1, x / W) + rng.randint(12, 140)
        r = rng.randint(14, 40)
        d.ellipse((x - r, y - r * 0.7, x + r, y + r * 0.7), fill=(118, 112, 100), outline=INK, width=3)


def race_track(L, t, gy):
    d = ImageDraw.Draw(L)
    f = icon('fuji', 520)
    paste_clip(L, f, int(W / 2 - 260 + 140), int(gy - 520 + 70))
    d.rectangle((0, gy - 6, W, gy + 60), fill=(92, 96, 102))
    off = (t * 900) % 120
    for k in range(-1, 12):
        x = k * 120 - off
        d.rectangle((x, gy + 52, x + 60, gy + 66), fill=RED)
        d.rectangle((x + 60, gy + 52, x + 120, gy + 66), fill=WHITE)


def mountains_road(L, t, gy):
    d = ImageDraw.Draw(L)
    for layer, (col, h_, sp, step) in enumerate([((206, 214, 226), 260, 40, 380), ((186, 196, 210), 180, 90, 300)]):
        off = (t * sp) % step
        pts = [(-step - off, gy)]
        x = -step - off
        rng = random.Random(layer + 7)
        while x < W + step:
            pts.append((x + step / 2, gy - h_ * rng.uniform(0.6, 1.0)))
            x += step
            pts.append((x, gy - h_ * 0.2))
        pts.append((W + step, gy))
        d.polygon(pts, fill=col)
    d.rectangle((0, gy - 4, W, gy + 40), fill=(90, 94, 100))
    off = (t * 900) % 140
    for k in range(-1, 10):
        x = k * 140 - off
        d.rectangle((x, gy + 16, x + 70, gy + 22), fill=(240, 240, 240))


# ======================================================================= props
def drop(L, im, cx, y_rest, t_rel, dur=0.5, from_y=-200):
    if t_rel < 0:
        return
    p = clamp01(t_rel / dur)
    k = ease_back(p)
    y = lerp(from_y, y_rest, k)
    paste_clip(L, im, int(cx - im.width / 2), int(y - im.height / 2))


def ellipse_draw(L, cx, cy, rx, ry, t_rel, dur=0.35, col=YEL, width=9):
    if t_rel < 0:
        return
    p = clamp01(t_rel / dur)
    d = ImageDraw.Draw(L)
    start = 200
    span = 380 * ease_out(p)
    d.arc((cx - rx, cy - ry, cx + rx, cy + ry), start, start + span, fill=INK, width=width + 6)
    d.arc((cx - rx, cy - ry, cx + rx, cy + ry), start, start + span, fill=col, width=width)
    if p >= 1:
        for i, (ax, ay) in enumerate([(cx - rx - 10, cy - ry), (cx + rx + 6, cy - ry + 6), (cx + rx - 20, cy + ry + 4)]):
            tw = 0.6 + 0.4 * math.sin(t_rel * 9 + i * 2)
            s = icon('sparkle', int(34 * tw) + 8)
            paste_clip(L, s, int(ax - s.width / 2), int(ay - s.height / 2))


def arrow_draw(L, p0, p1, t_rel, dur=0.3, col=INK, width=8):
    if t_rel < 0:
        return
    p = ease_out(clamp01(t_rel / dur))
    d = ImageDraw.Draw(L)
    x1, y1 = lerp(p0[0], p1[0], p), lerp(p0[1], p1[1], p)
    d.line([p0, (x1, y1)], fill=col, width=width)
    if p > 0.9:
        a = math.atan2(p1[1] - p0[1], p1[0] - p0[0])
        s = 26
        d.polygon([(x1, y1), (x1 - s * math.cos(a - 0.45), y1 - s * math.sin(a - 0.45)),
                   (x1 - s * math.cos(a + 0.45), y1 - s * math.sin(a + 0.45))], fill=col)


def gauge(L, cx, cy, r, val, red_from=0.8, label=None):
    """val 0..1 needle position."""
    d = ImageDraw.Draw(L)
    d.pieslice((cx - r, cy - r, cx + r, cy + r), 180, 360, fill=WHITE, outline=INK, width=6)
    d.rectangle((cx - r, cy - 3, cx + r, cy + 8), fill=WHITE)
    d.line([(cx - r, cy + 2), (cx + r, cy + 2)], fill=INK, width=6)
    for i in range(10):
        a = math.pi + i * math.pi / 9
        col = RED if i / 9 >= red_from else INK
        d.line([(cx + (r - 26) * math.cos(a), cy + (r - 26) * math.sin(a)), (cx + (r - 8) * math.cos(a), cy + (r - 8) * math.sin(a))],
               fill=col, width=6)
        if label:
            d.text((cx + (r - 52) * math.cos(a), cy + (r - 52) * math.sin(a)), str(i), font=font(FONT_XB, 22), fill=col, anchor='mm')
    a = math.pi + val * math.pi
    d.line([(cx, cy), (cx + (r - 20) * math.cos(a), cy + (r - 20) * math.sin(a))], fill=RED, width=8)
    d.ellipse((cx - 14, cy - 14, cx + 14, cy + 14), fill=INK)
    if label:
        d.text((cx, cy - r * 0.32), label, font=font(FONT_MONO, 26), fill=(80, 84, 90), anchor='mm')


def engine_anim(L, cx, cy, s, t):
    d = ImageDraw.Draw(L)
    w, h = 300 * s, 200 * s
    d.rounded_rectangle((cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2), radius=16, fill=(160, 166, 174), outline=INK, width=6)
    for i in range(3):
        px = cx - w / 3 + i * w / 3
        off = math.sin(t * 18 + i * 2.1) * 26 * s
        d.rectangle((px - 26 * s, cy - h / 2 - 90 * s + off, px + 26 * s, cy - h / 2 - 20 * s + off), fill=(200, 204, 210), outline=INK, width=5)
        d.line([(px, cy - h / 2 - 20 * s + off), (px, cy - h / 2 + 30 * s)], fill=INK, width=6)
    for i in range(3):
        px = cx - w / 3 + i * w / 3
        d.ellipse((px - 22 * s, cy - 22 * s, px + 22 * s, cy + 22 * s), fill=(90, 94, 100), outline=INK, width=4)


def battery_anim(L, cx, cy, s, level, col=(40, 200, 120)):
    d = ImageDraw.Draw(L)
    w, h = 240 * s, 130 * s
    d.rounded_rectangle((cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2), radius=14, fill=WHITE, outline=INK, width=7)
    d.rectangle((cx + w / 2, cy - h / 5, cx + w / 2 + 18 * s, cy + h / 5), fill=INK)
    fw = (w - 24) * clamp01(level)
    if fw > 2:
        d.rounded_rectangle((cx - w / 2 + 12, cy - h / 2 + 12, cx - w / 2 + 12 + fw, cy + h / 2 - 12), radius=8, fill=col)
    d.text((cx, cy), f'{int(clamp01(level) * 100)}%', font=font(FONT_BLACK, int(44 * s)), fill=INK, anchor='mm')


def energy_flow(L, p0, p1, t, col=(60, 160, 255)):
    d = ImageDraw.Draw(L)
    n = 8
    for k in range(n):
        p = ((t * 1.6) + k / n) % 1
        x, y = lerp(p0[0], p1[0], p), lerp(p0[1], p1[1], p)
        d.ellipse((x - 9, y - 9, x + 9, y + 9), fill=col, outline=INK, width=2)


def sparks(L, x, y, t, n=10, seed=1):
    d = ImageDraw.Draw(L)
    rng = random.Random(int(t * 20) + seed)
    for _ in range(n):
        a = rng.uniform(0, 2 * math.pi); r0 = rng.uniform(10, 30); r1 = r0 + rng.uniform(20, 50)
        d.line([(x + r0 * math.cos(a), y + r0 * math.sin(a)), (x + r1 * math.cos(a), y + r1 * math.sin(a))], fill=(255, 210, 40), width=5)


def stopwatch(L, cx, cy, r, t):
    d = ImageDraw.Draw(L)
    d.rectangle((cx - 14, cy - r - 30, cx + 14, cy - r - 4), fill=INK)
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=WHITE, outline=INK, width=8)
    a = -math.pi / 2 + t * 2 * math.pi / 1.0
    d.pieslice((cx - r + 12, cy - r + 12, cx + r - 12, cy + r - 12), -90, math.degrees(a), fill=(255, 220, 90))
    d.line([(cx, cy), (cx + (r - 16) * math.cos(a), cy + (r - 16) * math.sin(a))], fill=RED, width=8)
    d.ellipse((cx - 10, cy - 10, cx + 10, cy + 10), fill=INK)


def counter_key(L, t, cx, cy, seq, t0, step=0.07, style='yellow', size=74):
    """Rolling number keycap: steps through seq starting at t0."""
    if t < t0:
        v = seq[0]
    else:
        v = seq[min(len(seq) - 1, int((t - t0) / step))]
    im = keycap(str(v), style, size)
    paste_clip(L, im, int(cx - im.width / 2), int(cy - im.height / 2))


def route(L, t_rel, x0, y0, dur=1.6):
    d = ImageDraw.Draw(L)
    pts = [(x0, y0 + 120), (x0 + 120, y0 + 40), (x0 + 220, y0 + 110), (x0 + 330, y0 + 20), (x0 + 430, y0 + 70)]
    p = clamp01(t_rel / dur)
    segs = len(pts) - 1
    upto = p * segs
    for i in range(segs):
        if i < upto:
            q = min(1, upto - i)
            a, b = pts[i], pts[i + 1]
            d.line([a, (lerp(a[0], b[0], q), lerp(a[1], b[1], q))], fill=(60, 60, 60), width=14)
            d.line([a, (lerp(a[0], b[0], q), lerp(a[1], b[1], q))], fill=WHITE, width=4)
    for (x, y), c in [(pts[0], GREEN), (pts[-1], RED)]:
        if c == RED and p < 1:
            continue
        d.ellipse((x - 16, y - 34, x + 16, y - 2), fill=c, outline=INK, width=4)
    km = int(800 * p)
    d.text((x0 + 215, y0 + 170), f'{km} km', font=font(FONT_BLACK, 46), fill=INK, anchor='mm')


# ======================================================================= decoder bar
def bar(L, t, keys, y=330, t0=None, hi=None, gap=14):
    """keys: list of (label, style, size). hi: index to circle (ellipse draws from hi_t)."""
    ims = [keycap(l, s, sz) for l, s, sz in keys]
    total = sum(i.width for i in ims) + gap * (len(ims) - 1)
    x = W / 2 - total / 2
    boxes = []
    for i, im in enumerate(ims):
        tr = (t - t0 - i * 0.06) if t0 is not None else 9
        if tr >= 0:
            yy = lerp(-120, y, ease_back(clamp01(tr / 0.35)))
            paste_clip(L, im, int(x), int(yy - im.height / 2))
        boxes.append((x + im.width / 2, y, im.width, im.height))
        x += im.width + gap
    if hi:
        idx, ht = hi
        bx, by, bw, bh = boxes[idx]
        ellipse_draw(L, bx, by, bw / 2 + 34, bh / 2 + 26, t - ht)
    return boxes


def meaning(L, t, ta, text, col, y=470, x=W / 2, fg=None, size=42):
    if t < ta:
        return
    fg = fg or (INK if col in (YEL, WHITE, GOLD) else WHITE)
    pop(L, tag(text, bg=col, fg=fg, size=size), x, y, t - ta)


# ======================================================================= timeline
def build():
    SEGS.clear()
    T = {}
    T['two'] = at('two letters'); T['kind'] = at('kind of car')
    # --- hook handled in scene; NX cruises after the grid collapses
    seg('NX', 2.55, at('IS and ES') - 0.2, enter='none')
    # --- saloons: two lanes, then IS takes the centre
    tIS, tE, tIS2 = at('IS and ES') - 0.12, at('ES', 1) - 0.1, at('the IS is') - 0.1
    seg('IS', tIS, at('while the ES') - 0.12, kf=[(tIS, CX, 640, 0.11), (tIS2, CX, 640, 0.11), (tIS2 + 0.4, CX, GY, SC)])
    seg('ES', tE, tIS2 - 0.05, kf=[(tE, CX, 900, 0.11)])
    tES = at('while the ES') - 0.1
    seg('ES', tES, at('LS is the') - 0.12)
    tLS = at('LS is the') - 0.1
    seg('LS', tLS, at('and put an X') + 0.1)
    SEGS[-1]['shine_at'] = at('luxury')
    tS = at('SUV', 1) - 0.55
    for i, k in enumerate(['LX', 'GX', 'RX', 'NX', 'UX']):
        Lpx = CAR_META[k]['L'] * 0.15
        seg(k, tS + i * 0.1, at('UX is') - 0.2 + i * 0.02, kf=[(tS + i * 0.1, 120 + Lpx / 2 + 25, 860, 0.15)])
    seg('UX', at('UX is') - 0.1, at('NX is') - 0.12)
    tn = at('nimble')
    seg('NX', at('NX is') - 0.1, at('RX is') - 0.12,
        mod=lambda t, tn=tn: (0, 26 * math.sin((t - tn) * 9) if t > tn else 0, 3 * math.cos((t - tn) * 9) if t > tn else 0, 1))
    seg('RX', at('RX is') - 0.1, at('GX is') - 0.12)
    tg, tg2 = at('GX is') - 0.1, at('and LX is') - 0.12
    y0, y1 = GY + 80, GY - 110
    yl = lambda x: lerp(y0, y1, x / W)
    seg('GX', tg, tg2, kf=[(tg, CX - 120, yl(CX - 120), SC), (tg2, CX + 60, yl(CX + 60), SC)],
        mod=lambda t: (0, 0, math.degrees(math.atan2(y0 - y1, W)), 1))
    tlx = at('and LX is') - 0.1
    seg('LX', tlx, at('then comes the') - 0.12)
    SEGS[-1]['shine_at'] = at('flagship', 2)
    seg('RX', at('then comes the') - 0.1, at('which used to') - 0.12)
    seg('NX', at('h plus') - 0.12, at('and e means') - 0.12, cruise=False)
    seg('RX', at('so an RX') - 0.1, at("then there's F") - 0.12)
    seg('IS', at("then there's F") - 0.1, at('but F is') + 0.2)
    SEGS[-1]['shine_at'] = at('look')
    trc = at('RC F') - 0.5
    seg('RCF', trc, at('Lexus also uses') - 0.12, burnout=True)
    SEGS[-1]['flames'] = lambda t, a=at('high-performance'): 0
    tls = at('luxury-focused') - 0.1
    seg('LS', tls, at('while the LC') - 0.12, kf=[(tls, CX, 700, 0.12)])
    seg('LX', tls + 0.45, at('while the LC') - 0.1, kf=[(tls + 0.45, CX, 960, 0.12)])
    seg('LC', at('while the LC') - 0.1, at('And the LFA') - 0.12)
    tv = at('V10')
    seg('LFA', at('And the LFA') - 0.1, at('So an NX') - 0.12, burnout=True,
        mod=lambda t, tv=tv: ((random.Random(int(t * 60)).uniform(-4, 4) if tv < t < tv + 1.0 else 0), 0, 0, 1 + 0.12 * ease_out(clamp01((t - at('far beyond')) / 0.4))))
    SEGS[-1]['flames'] = lambda t, tv=tv: 1.0 if tv < t < tv + 1.2 else 0
    SEGS[-1]['shine_at'] = at('far beyond')
    seg('NX', at('So an NX') - 0.1, at('and if you') - 0.05)
    return T


SHAKES = []


def shake_offset(t):
    for t0, dur, amp in SHAKES:
        if t0 <= t < t0 + dur:
            k = 1 - (t - t0) / dur
            r = random.Random(int(t * 60))
            return int(r.uniform(-amp, amp) * k), int(r.uniform(-amp, amp) * k)
    return 0, 0


# ======================================================================= scenes
def scene_layer(t):
    L = Image.new('RGBA', (W, 1060), (0, 0, 0, 0))
    a = at
    # ---------------- backdrops (behind cars)
    if a('UX is') - 0.1 <= t < a('NX is') - 0.1:
        city(L, t, GY + 4)
    if a('nimble') - 0.3 <= t < a('RX is'):
        pass  # cones drawn after ground
    if a('radiant') - 0.2 <= t < a('GX is') - 0.1:
        sun_rays(L, CX, GY - 140, t, clamp01((t - a('radiant') + 0.2) / 0.3))
    if a('GX is') - 0.1 <= t < a('and LX is') - 0.1:
        hill(L, GY + 80, GY - 110)
    if a('and the F comes') - 0.1 <= t < a('Lexus also uses') - 0.1:
        race_track(L, t, GY)
    if a('while the LC') - 0.1 <= t < a('And the LFA') - 0.1:
        mountains_road(L, t, GY)
    if a('legendary') <= t < a('So an NX') - 0.1:
        sun_rays(L, CX, GY - 120, t, 0.8)

    # ---------------- generic motion: speed lines + ground dashes when a hero car cruises
    active = [s for s in SEGS if seg_state(s, t)]
    if active and not (a('GX is') - 0.1 <= t < a('and LX is') - 0.1) and not (a('h plus') - 0.1 <= t < a('and e means') - 0.1):
        k = max(seg_state(s, t)['lines'] for s in active)
        if not (a('UX is') - 0.1 <= t < a('NX is') - 0.1):
            speed_lines(L, t, 420, GY - 20, k)
        if not (a('and the F comes') - 0.1 <= t < a('Lexus also uses') - 0.1 or a('while the LC') - 0.1 <= t < a('And the LFA') - 0.1):
            if any(abs(seg_state(s, t)['gy'] - GY) < 4 for s in active):
                ground_line(L, t, GY)
    if a('nimble') - 0.3 <= t < a('RX is') - 0.1:
        cones(L, t, GY, a('nimble') - 0.3)

    # ---------------- HOOK (0 – 2.6 s)
    if t < 2.6:
        hook(L, t)
    # ---------------- ghosts behind cars (size comparisons)
    tIS2 = a('the IS is') - 0.1
    if tIS2 + 0.3 <= t < a('while the ES') - 0.1 and t > a('smaller') - 0.1:
        Lp = CAR_META['ES']['L'] * SC
        Li = CAR_META['IS']['L'] * SC
        draw_car(L, 'ES', CX - Li / 2 + Lp / 2, GY, SC, ghost=True)
    if a('larger') - 0.1 <= t < a('GX is') - 0.1:
        Lp = CAR_META['NX']['L'] * SC; Lr = CAR_META['RX']['L'] * SC
        draw_car(L, 'NX', CX - Lr / 2 + Lp / 2, GY, SC, ghost=True)

    cars = draw_cars(L, t)

    # ---------------- props & explanation per beat
    beats(L, t, cars)
    return L


def hook(L, t):
    # NX cruising, logo flies in, then zoom-out to the full range grid, then back
    a = at
    t_grid, t_back = a('model') - 0.05, a('Lexus names') - 0.05
    order = ['UX', 'NX', 'RX', 'GX', 'LX', 'IS', 'ES', 'LS', 'RCF', 'LC', 'LFA']
    cols, cell_w, cell_h, gx0, gy0 = 3, 340, 132, 30, 470
    pos = {k: (gx0 + (i % cols) * cell_w + cell_w / 2, gy0 + (i // cols) * cell_h + 110) for i, k in enumerate(order)}
    gsc = 0.058
    if t < t_grid:
        p = 1.0
    elif t < t_back:
        p = 1 - ease_out((t - t_grid) / 0.4)
    else:
        p = ease_out((t - t_back) / 0.45)
    # NX between hero and its grid slot
    nx, ny = pos['NX']
    cx, gy, sc = lerp(nx, CX, p), lerp(ny, GY, p), lerp(gsc, SC, p)
    if p > 0.97:
        speed_lines(L, t, 420, GY - 20, 0.8)
        ground_line(L, t, GY)
    st_travel = CRUISE * t
    info = draw_car(L, 'NX', cx, gy, sc, travel=st_travel)
    if p > 0.6:
        draw_puffs(L, info['rear'][0] - 20, info['rear'][1] - 8, t, -1, alpha=0.4, size=(14, 34), seed=99)
    # the rest of the range pops in around it
    if t >= t_grid and t < t_back + 0.4:
        for i, k in enumerate(order):
            if k == 'NX':
                continue
            ta = t_grid + 0.15 + i * 0.035
            if t < ta:
                continue
            x, y = pos[k]
            if t >= t_back:
                q = ease_in((t - t_back) / 0.35)
                x = x + (W + 400) * q * (1 if i % 2 else -1)
            sc_k = gsc * ease_back(clamp01((t - ta) / 0.25))
            if sc_k > 0.01:
                draw_car(L, k, x, y, sc_k, travel=CRUISE * t)
        if t < t_back:
            meaning(L, t, t_grid + 0.5, '11 MODELS', RED, y=410, x=170, size=40)
    # logo flies in from the right with motion blur, then sits above
    lg = lexus_logo(250)
    tl = clamp01(t / 0.4)
    lx = lerp(W + 300, W / 2, ease_out(tl))
    ly = 300 if t < t_grid else lerp(300, 255, ease_out((t - t_grid) / 0.3))
    if t < t_back:
        if tl < 1:
            blur = lg.resize((int(lg.width * (1 + 1.2 * (1 - tl))), lg.height))
            paste_clip(L, blur, int(lx - blur.width / 2), int(ly - blur.height / 2))
        else:
            paste_clip(L, lg, int(lx - lg.width / 2), int(ly - lg.height / 2))
            ellipse_draw(L, lx, ly, 175, 108, t - 0.45)
    if a('one minute') - 0.1 <= t < t_back:
        stopwatch(L, 900, 300, 62, t - a('one minute'))


def beats(L, t, cars):
    a = at
    # -------- names start with two letters / tell you the kind of car
    if 2.55 <= t < a('IS and ES') - 0.15:
        boxes = bar(L, t, [('NX', 'yellow' if t > a('two letters') else 'dark', 70), ('450', 'dark', 70), ('h+', 'dark', 70), ('F SPORT', 'dark', 70)],
                    t0=2.1, hi=(0, a('two letters')))
        if a('two letters') + 0.2 < t < a('kind of car'):
            meaning(L, t, a('two letters') + 0.2, 'FIRST 2 LETTERS', DARK, y=470, x=boxes[0][0] + 120)
        tk = a('kind of car')
        if t > a('tell you') - 0.1:
            arrow_draw(L, (boxes[0][0], 400), (CX - 60, GY - 330), t - a('tell you') + 0.1)
        if t > tk:
            for i, (k, lab) in enumerate([('IS', 'SALOON'), ('NX', 'SUV'), ('LC', 'COUPE')]):
                ta = tk + i * 0.18
                if t > ta:
                    x = 220 + i * 320
                    pop(L, keycap(lab, ['blue', 'yellow', 'red'][i], 36, pad=14), x, 990 - 520, t - ta)
    # -------- saloons
    if a('IS and ES') - 0.15 <= t < a('the IS is') - 0.1:
        tIS = a('IS and ES') - 0.12
        pop(L, keycap('IS', 'yellow', 58), 110, 600, t - tIS - 0.3)
        pop(L, keycap('ES', 'yellow', 58), 110, 860, t - a('ES', 1) - 0.25)
        if t > a('saloons'):
            meaning(L, t, a('saloons'), 'SALOON = 4 DOORS + A BOOT', BLUE, y=380, size=40)
    # -------- IS smaller / sportier
    if a('the IS is') - 0.1 <= t < a('while the ES') - 0.1:
        bar(L, t, [('IS', 'yellow', 80)], t0=a('the IS is') - 0.1)
        if t > a('smaller'):
            Li, Le = CAR_META['IS']['L'] * SC, CAR_META['ES']['L'] * SC
            dim(L, t - a('smaller'), CX - Li / 2, CX + Li / 2, GY + 36, '4.71 m')
            dim(L, t - a('smaller') - 0.2, CX - Li / 2, CX - Li / 2 + Le, GY + 82, 'ES 4.98 m', col=(150, 154, 160))
            meaning(L, t, a('smaller'), 'SMALLER', DARK, y=470, x=300)
        if t > a('sportier'):
            meaning(L, t, a('sportier'), 'SPORTIER', RED, y=470, x=780)
            speed_lines(L, t, 420, GY - 20, 1.6, seed=8)
    # -------- ES comfort / executive
    if a('while the ES') - 0.1 <= t < a('LS is the') - 0.1:
        bar(L, t, [('ES', 'yellow', 80)], t0=a('while the ES') - 0.1)
        if t > a('comfortable'):
            drop(L, icon('sofa', 150), 200, 520, t - a('comfortable'))
            meaning(L, t, a('comfortable') + 0.1, 'COMFORT', BLUE, y=470, x=780)
        if t > a('executive'):
            drop(L, icon('tie', 130), 880, 600, t - a('executive'))
            meaning(L, t, a('executive') + 0.1, 'EXECUTIVE CAR', DARK, y=990)
    # -------- LS flagship
    if a('LS is the') - 0.1 <= t < a('and put an X') - 0.05:
        bar(L, t, [('LS', 'gold', 80)], t0=a('LS is the') - 0.1)
        lsinfo = [v for k, v in cars.items() if v[0]['key'] == 'LS']
        if t > a('flagship') and lsinfo:
            _, st, info = lsinfo[0]
            drop(L, icon('crown', 150), st['cx'] - 40, info['top'] - 50, t - a('flagship'), from_y=-150)
            meaning(L, t, a('flagship') + 0.15, 'FLAGSHIP = TOP OF THE RANGE', GOLD, y=990, size=38)
        if t > a('luxury'):
            meaning(L, t, a('luxury'), 'LUXURY', GOLD, y=470, x=800)
    # -------- X = SUV
    if a('and put an X') - 0.05 <= t < a('UX is') - 0.1:
        tx = a('X', 1)
        keys = [('?', 'ghost', 80), ('X' if t > tx else '?', 'red' if t > tx else 'ghost', 80)]
        bar(L, t, keys, t0=a('and put an X') - 0.05, hi=(1, a('the end')) if t > a('the end') else None)
        if t > tx:
            drop(L, keycap('X', 'red', 80), 0, 0, -1)
        if a('the end') < t:
            meaning(L, t, a('the end'), 'LAST LETTER', DARK, y=470)
        if t > a('SUV', 1):
            meaning(L, t, a('SUV', 1), '...X = SUV', ORANGE, y=990, size=48)
            for i, k in enumerate(['LX', 'GX', 'RX', 'NX', 'UX']):
                pass
    # -------- each SUV: [letter][X] + meaning
    suv_beats = [('UX is', 'U', 'urban', 'U = URBAN', BLUE, 'city crossover'), ('NX is', 'N', 'nimble', 'N = NIMBLE', TEAL, 'agile, mid-size'),
                 ('RX is', 'R', 'radiant', 'R = RADIANT', ORANGE, 'larger, family'), ('GX is', 'G', 'rugged', 'G = RUGGED', (110, 120, 80), 'real off-roader'),
                 ('and LX is', 'L', 'flagship', 'L = LUXURY FLAGSHIP', GOLD, 'biggest & most lux')]
    for i, (ph, letter, word, text, col, sub) in enumerate(suv_beats):
        t0 = a(ph) - 0.1
        t1 = a(suv_beats[i + 1][0]) - 0.1 if i + 1 < len(suv_beats) else a('then comes the') - 0.1
        if t0 <= t < t1:
            tw = a(word, 2) if word == 'flagship' else a(word)
            bar(L, t, [(letter, 'yellow' if t > tw else 'dark', 84), ('X', 'red', 84)], t0=t0, hi=(0, tw))
            meaning(L, t, tw, text, col, y=470, size=46)
            meaning(L, t, tw + 0.35, sub.upper(), WHITE, y=990, size=36)
            if letter == 'R' and t > a('larger'):
                meaning(L, t, a('larger'), 'LARGER THAN NX', DARK, y=560, size=34)
            if letter == 'L' and t > tw:
                lx = [v for k, v in cars.items() if v[0]['key'] == 'LX']
                if lx:
                    _, st, info = lx[0]
                    drop(L, icon('crown', 150), st['cx'] - 60, info['top'] - 50, t - tw, from_y=-150)
            if letter == 'G' and t > a('off-roader'):
                meaning(L, t, a('off-roader'), 'OFF-ROAD', DARK, y=560, size=36)
    # -------- numbers
    if a('then comes the') - 0.1 <= t < a('which used to') - 0.1:
        t5 = a('500', 1)
        seq = [350] if t < t5 else [350, 375, 400, 425, 450, 475, 500]
        boxes = bar(L, t, [('RX', 'dark', 80), ('350', 'ghost', 80)], t0=a('then comes the') - 0.1, hi=(1, a('number')))
        if t > a('350') - 0.1:
            counter_key(L, t, boxes[1][0], boxes[1][1], seq, t5, style='yellow', size=80)
        meaning(L, t, a('number'), 'THE NUMBER', DARK, y=470)
    if a('which used to') - 0.1 <= t < a('but today it') - 0.1:
        t0 = a('which used to') - 0.1
        s = ease_back(clamp01((t - t0) / 0.35))
        if s > 0.05:
            engine_anim(L, 300, 700, s, t)
        if t > a('engine size') - 0.4:
            meaning(L, t, a('engine size') - 0.4, '3.5 LITRES', WHITE, y=880, x=300, size=44)
        if t > a('engine size'):
            arrow_draw(L, (500, 700), (690, 700), t - a('engine size'))
            if t > a('engine size') + 0.3:
                pop(L, keycap('350', 'yellow', 96), 860, 700, t - a('engine size') - 0.3)
        if t > a('roughly'):
            meaning(L, t, a('roughly'), 'IN THE PAST', DARK, y=400)
    if a('but today it') - 0.1 <= t < a('an h means') - 0.1:
        t0 = a('but today it') - 0.1
        meaning(L, t, t0, 'TODAY', RED, y=400, size=46)
        engine_anim(L, 200, 650, 0.6, t)
        if t > a('powertrain') - 0.2:
            battery_anim(L, 540, 640, 0.9, (t - a('powertrain') + 0.2) / 1.2)
            meaning(L, t, a('powertrain'), 'POWERTRAIN', GREEN, y=820, x=360)
        if t > a('performance'):
            v = clamp01((t - a('performance')) / 0.6)
            gauge(L, 870, 700, 150, 0.1 + 0.85 * ease_out(v) + 0.02 * math.sin(t * 40), label='x1000')
            meaning(L, t, a('performance'), 'PERFORMANCE', RED, y=820, x=780)
    # -------- h / h+ / e
    if a('an h means') - 0.1 <= t < a('h plus') - 0.1:
        t0 = a('an h means') - 0.1
        bar(L, t, [('RX', 'ghost', 70), ('500', 'ghost', 70), ('h', 'blue', 90)], t0=t0, hi=(2, a('h', 1)))
        engine_anim(L, 280, 700, 0.75, t)
        battery_anim(L, 800, 700, 0.9, 0.6 + 0.1 * math.sin(t * 3), col=(60, 160, 255))
        energy_flow(L, (420, 700), (680, 700), t)
        meaning(L, t, a('hybrid', 1), 'h = HYBRID  (PETROL + ELECTRIC)', BLUE, y=990, size=36)
    if a('h plus') - 0.1 <= t < a('and e means') - 0.1:
        t0 = a('h plus') - 0.1
        bar(L, t, [('NX', 'ghost', 70), ('450', 'ghost', 70), ('h+', 'green', 90)], t0=t0, hi=(2, a('plus')))
        nxs = [v for k, v in cars.items() if v[0]['key'] == 'NX']
        if nxs:
            _, st, info = nxs[0]
            port = (info['rear'][0] + 70, info['top'] + (GY - info['top']) * 0.42)
            tp = a('plug-in') - 0.25
            p = ease_out(clamp01((t - tp) / 0.45))
            px, py = lerp(W + 100, port[0] + 40, p), lerp(380, port[1], p)
            d = ImageDraw.Draw(L)
            d.line([(W + 40, 360), (px + 40, py)], fill=INK, width=12)
            d.line([(W + 40, 360), (px + 40, py)], fill=(40, 170, 100), width=6)
            pl = icon('plug', 120).rotate(90, expand=True)
            paste_clip(L, pl, int(px - 20), int(py - pl.height / 2))
            if p >= 1:
                sparks(L, port[0], port[1], t, seed=3) if t < tp + 0.9 else None
                battery_anim(L, 300, 450, 0.75, (t - tp - 0.45) / 1.2)
        meaning(L, t, a('plug-in') + 0.1, 'h+ = PLUG-IN HYBRID  (CHARGE IT)', GREEN, y=990, size=36)
    if a('and e means') - 0.1 <= t < a('so an RX') - 0.1:
        t0 = a('and e means') - 0.1
        bar(L, t, [('e', 'teal', 110)], t0=t0, hi=(0, a('e', 1)))
        battery_anim(L, 540, 680, 1.4, (t - t0) / 1.3, col=(40, 200, 210))
        for i in range(3):
            if (t * 4 + i) % 3 < 1.2:
                b = icon('bolt', 110)
                paste_clip(L, b, int(200 + i * 300 - 55), int(520 - 55 + 10 * math.sin(t * 9 + i)))
        meaning(L, t, a('fully'), 'e = FULLY ELECTRIC  (NO PETROL)', TEAL, y=990, size=36)
    # -------- RX 500h decoded
    if a('so an RX') - 0.1 <= t < a("then there's F") - 0.1:
        t0 = a('so an RX') - 0.1
        th, ts = a('hybrid', 3), a('hybrid SUV') + 0.3
        st_ = lambda cond, s: s if cond else 'dark'
        boxes = bar(L, t, [('RX', st_(t > ts, 'yellow'), 80), ('500', 'dark', 80), ('h', st_(t > th, 'blue'), 80)], t0=t0)
        if t > th:
            pop(L, tag('HYBRID', bg=BLUE, size=32), boxes[2][0], 430, t - th)
        if t > ts:
            pop(L, tag('SUV', bg=ORANGE, size=32), boxes[0][0], 430, t - ts)
        if t > a('not a'):
            pop(L, tag('500 = POWER', bg=DARK, size=32), boxes[1][0], 430, t - a('not a'))
            pop(L, stamp('NOT 5.0 LITRES'), W / 2, 600, t - a('not a') - 0.1, dur=0.18, scale_from=1.8)
    # -------- F SPORT
    if a("then there's F") - 0.1 <= t < a('but F is') - 0.1:
        t0 = a("then there's F") - 0.1
        bar(L, t, [('IS', 'ghost', 70), ('300', 'ghost', 70), ('F SPORT', 'dark', 80)], t0=t0, hi=(2, a('F Sport', 1)))
        iss = [v for k, v in cars.items() if v[0]['key'] == 'IS']
        if iss and t > a('look'):
            _, st, info = iss[0]
            arrow_draw(L, (200, 480), (info['front'][0] - 20, info['front'][1] - 40), t - a('look'))
            meaning(L, t, a('look'), 'SPORTY LOOK', DARK, y=470, x=230, size=36)
        if t > a('feel', 1):
            meaning(L, t, a('feel', 1), '+ SPORTY FEEL', RED, y=470, x=800, size=36)
        meaning(L, t, t0 + 0.4, 'F SPORT = TRIM PACKAGE', WHITE, y=990, size=38)
    # -------- F performance
    if a('but F is') - 0.1 <= t < a('and the F comes') - 0.1:
        t0 = a('but F is') - 0.1
        bar(L, t, [('F SPORT', 'ghost', 70), ('≠' if False else '/', 'ghost', 70), ('F', 'red', 100)], t0=t0, hi=(2, a('F', 4)) if False else None)
        if t > a('different'):
            pop(L, stamp('NOT THE SAME!', color=RED, size=52, angle=-6), W / 2, 480, t - a('different'), dur=0.18, scale_from=1.8)
        if t > a('high-performance') and t < a('RC F') - 0.3:
            v = clamp01((t - a('high-performance')) / 0.7)
            gauge(L, W / 2, 790, 190, 0.05 + 0.9 * ease_out(v) + 0.02 * math.sin(t * 50), label='x1000 rpm')
        meaning(L, t, a('high-performance') + 0.2, 'F = HIGH-PERFORMANCE DIVISION', RED, y=990, size=36)
        if t > a('RC F') - 0.1:
            pop(L, keycap('RC F', 'red', 60), 860, 560, t - a('RC F') + 0.1)
    if a('and the F comes') - 0.1 <= t < a('Lexus also uses') - 0.1:
        t0 = a('and the F comes') - 0.1
        bar(L, t, [('F', 'red', 100)], t0=t0 - 5)
        flag = icon('flag', 150).rotate(6 * math.sin(t * 12), resample=Image.BICUBIC)
        paste_clip(L, flag, 860, 380)
        jp = icon('japan', 130)
        if t > a('Japan'):
            pop(L, jp, 160, 440, t - a('Japan'))
        meaning(L, t, a('Fuji'), 'F = FUJI SPEEDWAY', DARK, y=990, size=44)
    # -------- L = luxury
    if a('Lexus also uses') - 0.1 <= t < a('while the LC') - 0.1:
        t0 = a('Lexus also uses') - 0.1
        bar(L, t, [('L', 'gold', 100)], t0=t0, hi=(0, a('L', 1)))
        meaning(L, t, a('luxury-focused'), 'L = LUXURY', GOLD, y=470, size=46)
        for key, tt in (('LS', a('LS and')), ('LX', a('LX', 2))):
            s_ = [v for k, v in cars.items() if v[0]['key'] == key]
            if s_ and t > tt + 0.3:
                _, st, info = s_[0]
                pop(L, keycap(key, 'gold', 44, pad=14), info['x0'] - 50 if info['x0'] > 80 else 70, info['top'] + 50, t - tt - 0.3)
    # -------- LC grand tourer
    if a('while the LC') - 0.1 <= t < a('And the LFA') - 0.1:
        t0 = a('while the LC') - 0.1
        bar(L, t, [('L', 'gold', 80), ('C', 'red', 80)], t0=t0)
        meaning(L, t, a('grand'), 'GRAND TOURER', RED, y=470, x=300, size=40)
        meaning(L, t, a('coupe'), '2-DOOR COUPE', DARK, y=470, x=800, size=36)
        if t > a('long journeys') - 0.1:
            route(L, t - a('long journeys') + 0.1, 330, 520)
        meaning(L, t, a('sporty feel'), 'LONG TRIPS + SPORTY FEEL', BLUE, y=990, size=38)
    # -------- LFA
    if a('And the LFA') - 0.1 <= t < a('So an NX') - 0.1:
        t0 = a('And the LFA') - 0.1
        bar(L, t, [('LFA', 'yellow', 84)], t0=t0)
        meaning(L, t, a('legendary'), 'LEGENDARY', GOLD, y=470, x=270, size=40)
        tv = a('V10')
        if t > tv - 0.1:
            gauge(L, 830, 560, 130, clamp01(0.15 + 0.85 * ease_out((t - tv + 0.1) / 0.5)) - (0.04 * math.sin(t * 60) if t < tv + 1 else 0), red_from=0.88, label='9,000 rpm')
            pop(L, icon('v10', 150), 830, 650, t - tv)
        meaning(L, t, a('supercar'), 'V10 SUPERCAR · ONLY 500 BUILT', RED, y=990, size=36)
        if t > a('far beyond'):
            pop(L, icon('trophy', 150), 150, 600, t - a('far beyond'))
            for i, (x, y) in enumerate([(240, 760), (900, 760), (720, 430)]):
                tw = 0.6 + 0.4 * math.sin(t * 7 + i * 2)
                pop(L, icon('sparkle', int(56 * tw) + 10), x, y, t - a('far beyond') - i * 0.06)
        if t > a('saloons', 2):
            meaning(L, t, a('saloons', 2), 'BEYOND SALOONS & SUVs', DARK, y=560, x=270, size=32)
    # -------- recap
    if a('So an NX') - 0.1 <= t < a('and if you') - 0.05:
        t0 = a('So an NX') - 0.1
        tn, t4, tf = a('NX', 2), a('450h+'), a('F Sport', 2)
        tnim, tplug, tpkg = a('nimble crossover'), a('plug-in hybrid', 2), a('package')
        hi = lambda x, s: s if t >= x else 'dark'
        boxes = bar(L, t, [('NX', hi(tn, 'yellow'), 66), ('450', hi(t4, 'yellow'), 66), ('h+', hi(t4, 'green'), 66), ('F SPORT', hi(tf, 'red'), 66)], t0=t0)
        cur = 0 if t < t4 else (2 if t < tf else 3)
        if t < tnim + 0.2:
            cur = 0
        elif t < tplug:
            cur = 2
        else:
            cur = 3 if t >= tpkg - 0.4 else 2
        ht = {0: tn, 2: tplug, 3: tpkg - 0.4}[cur]
        bx, by, bw, bh = boxes[cur]
        ellipse_draw(L, bx, by, bw / 2 + 28, bh / 2 + 22, t - ht)
        y = 470
        for ta, lab, col in [(tnim, 'NX = NIMBLE CROSSOVER', TEAL), (tplug, '450h+ = PLUG-IN HYBRID', GREEN), (tpkg - 0.3, 'F SPORT = SPORTY PACKAGE', RED)]:
            meaning(L, t, ta, lab, col, y=y, size=36)
            y += 74
    # -------- end card
    if t >= a('and if you') - 0.05 and t < END - 0.25:
        C.cheat_sheet(L, t - a('and if you') + 0.05)


def dim(L, tr, x0, x1, y, label, col=(80, 84, 90)):
    if tr < 0:
        return
    p = ease_out(clamp01(tr / 0.35))
    d = ImageDraw.Draw(L)
    xe = lerp(x0, x1, p)
    d.line([(x0, y), (xe, y)], fill=col, width=4)
    d.line([(x0, y - 12), (x0, y + 12)], fill=col, width=4)
    if p > 0.98:
        d.line([(x1, y - 12), (x1, y + 12)], fill=col, width=4)
        f = font(FONT_MONO, 30)
        tw = d.textlength(label, font=f)
        mx = (x0 + x1) / 2
        d.rectangle((mx - tw / 2 - 10, y - 20, mx + tw / 2 + 10, y + 20), fill=(236, 237, 239))
        d.text((mx, y), label, font=f, fill=col, anchor='mm')


# ======================================================================= frame
BG = None


def render(t, fi):
    global BG
    if BG is None:
        BG = make_background().convert('RGBA')
        build()
        SHAKES.extend([(at('X', 1), 0.25, 10), (at('not a') + 0.1, 0.3, 14), (at('different'), 0.25, 10), (at('V10'), 0.8, 7), (at('RC F') - 0.4, 0.5, 6)])
    fr = BG.copy()
    tt = t if t < END - 0.25 else 0.02   # loop: last frames = first frame
    L = scene_layer(tt)
    ox, oy = shake_offset(tt)
    fr.alpha_composite(L, (ox, oy))
    draw_header(fr, t)
    draw_caption(fr, t)
    draw_character(fr, t, fi)
    return fr.convert('RGB')


def main():
    args = sys.argv[1:]
    if args and args[0] == '--frames':
        os.makedirs(os.path.join(B, 'frames2'), exist_ok=True)
        for s in args[1].split(','):
            t = float(s)
            render(t, int(t * FPS)).save(os.path.join(B, 'frames2', f'f_{t:06.2f}.png'))
        return
    t0, t1, out = 0.0, END, os.path.join(B, 'video2_noaudio.mp4')
    if args and args[0] == '--preview':
        t0, t1, out = float(args[1]), float(args[2]), os.path.join(B, 'preview2.mp4')
    p = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                          '-c:v', 'libx264', '-preset', 'medium', '-crf', '16', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
    for fi in range(int(t0 * FPS), int(t1 * FPS)):
        p.stdin.write(render(fi / FPS, fi).tobytes())
        if fi % 300 == 0:
            print('frame', fi, flush=True)
    p.stdin.close(); p.wait()
    print('wrote', out)


if __name__ == '__main__':
    main()
