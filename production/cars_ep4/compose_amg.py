"""Episode 2 — "Every Mercedes-AMG car explained in one minute".
Same motion system as ep1 v2 (compose2): cars always driving, props interacting, decoder bar + meaning cards.
Layout change: the @Mecmation character is shown FULL BODY under the caption.

usage: python3 compose_amg.py [--frames t,t,...]
"""
import math, os, random, subprocess, sys, functools
import numpy as np
from PIL import Image, ImageDraw

import compose as C
import compose2 as V
from compose import (W, H, FPS, at, ease_out, ease_back, font, FONT_BLACK, FONT_XB, FONT_MONO, INK, YEL, WHITE, RED, BLUE,
                     GREEN, TEAL, GOLD, ORANGE, keycap, tag, stamp, icon, paste_clip, pop, CAR_META, draw_caption, draw_header,
                     draw_character, make_background, B, END)
from compose2 import (draw_car, seg, SEGS, seg_state, draw_cars, speed_lines, ground_line, hill, sun_rays, drop, ellipse_draw,
                      arrow_draw, gauge, engine_anim, battery_anim, energy_flow, sparks, stopwatch, bar, meaning, dim, lerp, clamp01,
                      ease_in, draw_puffs, mountains_road, race_track, SHAKES, shake_offset, DARK)

# layout: scene sits higher so the full-body character fits under the caption
V.GY = GY = 820
V.CX = CX = 540
SC = V.SC = 0.168
BAR_Y = 300
TAG_LOW = 930
a = at


def ph(p, k=1):
    return at(p, k)


# ----------------------------------------------------------------- extra icons
@functools.lru_cache(None)
def person(name, col=(90, 120, 170)):
    im = Image.new('RGBA', (220, 250), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse((70, 10, 150, 90), fill=(250, 205, 160), outline=INK, width=6)
    d.pieslice((30, 95, 190, 255), 180, 360, fill=col, outline=INK, width=6)
    d.rectangle((30, 172, 190, 180), fill=col)
    return im


@functools.lru_cache(None)
def town_sign(name='Großaspach', size=1.0):
    f = font(FONT_BLACK, int(54 * size))
    tw = f.getbbox(name)[2]
    w, h = int(tw + 80 * size), int(130 * size)
    im = Image.new('RGBA', (w + 12, h + 12), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle((8, 8, w + 8, h + 8), fill=(0, 0, 0, 60))
    d.rectangle((2, 2, w + 2, h + 2), fill=(255, 214, 0), outline=INK, width=int(10 * size))
    d.rectangle((14 * size, 14 * size, w - 10 * size, h - 10 * size), outline=INK, width=int(4 * size))
    d.text((w / 2 + 2, h / 2 + 2), name, font=f, fill=INK, anchor='mm')
    return im


@functools.lru_cache(None)
def amg_word(size=150):
    f = font(FONT_BLACK, size)
    tw = f.getbbox('AMG')[2]
    im = Image.new('RGBA', (int(tw * 1.25), int(size * 1.4)), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.text((10 + 6, 8 + 8), 'AMG', font=f, fill=(0, 0, 0, 90))
    d.text((10, 8), 'AMG', font=f, fill=(225, 229, 234), stroke_width=6, stroke_fill=INK)
    a = np.asarray(im).astype(np.float32)
    hh = a.shape[0]
    grad = np.linspace(1.15, 0.55, hh)[:, None]
    mask = (a[..., 3] > 0) & (a[..., :3].sum(2) > 300)
    a[..., :3][mask] = np.clip(a[..., :3][mask] * np.repeat(grad, a.shape[1], 1)[mask][:, None], 0, 255)
    out = Image.fromarray(a.astype(np.uint8))
    sk = out.transform(out.size, Image.AFFINE, (1, 0.22, -0.11 * out.height, 0, 1, 0), resample=Image.BICUBIC)  # italic slant
    return sk


def spring(L, cx, cy, h, comp, w=56):
    d = ImageDraw.Draw(L)
    n = 7
    hh = h * (1 - 0.35 * comp)
    pts = []
    for i in range(n * 2 + 1):
        pts.append((cx + (w / 2 if i % 2 else -w / 2), cy - hh / 2 + hh * i / (n * 2)))
    d.line(pts, fill=INK, width=12, joint='curve')
    d.line(pts, fill=(255, 160, 30), width=6, joint='curve')
    d.rectangle((cx - w / 2 - 10, cy - hh / 2 - 14, cx + w / 2 + 10, cy - hh / 2), fill=(150, 154, 160), outline=INK, width=4)
    d.rectangle((cx - w / 2 - 10, cy + hh / 2, cx + w / 2 + 10, cy + hh / 2 + 14), fill=(150, 154, 160), outline=INK, width=4)


def stairs(L, t, t0, active, x0=620, y0=600, sw=100, labels=('35', '43', '53', '63')):
    """Bar-chart staircase of performance levels; 'active' index glows."""
    d = ImageDraw.Draw(L)
    for i, lab in enumerate(labels):
        p = ease_back(clamp01((t - t0 - i * 0.12) / 0.35))
        if p <= 0:
            continue
        hgt = (60 + i * 55) * p
        x = x0 + i * (sw + 8)
        on = i == active
        col = (255, 210, 31) if on else ((240, 240, 240) if i < (active if active is not None else 99) else (220, 222, 226))
        d.rounded_rectangle((x, y0 - hgt, x + sw, y0), radius=10, fill=col, outline=INK, width=5)
        if p > 0.6:
            d.text((x + sw / 2, y0 - hgt - 30), lab, font=font(FONT_BLACK, 42), fill=INK if on else (110, 114, 120), anchor='mm')
    if active == 3 and t > t0:
        pass


def chassis(L, t, t0, lit_t, cx=540, cy=620):
    d = ImageDraw.Draw(L)
    p = ease_back(clamp01((t - t0) / 0.4))
    if p <= 0:
        return
    w, h = 560 * p, 260 * p
    d.rounded_rectangle((cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2), radius=30, outline=INK, width=10)
    d.line([(cx - w / 2 + 40, cy), (cx + w / 2 - 40, cy)], fill=INK, width=12)
    d.rounded_rectangle((cx - 60 * p, cy - 40 * p, cx + 60 * p, cy + 40 * p), radius=10, fill=(150, 154, 160), outline=INK, width=6)
    wheels = [(-1, -1), (1, -1), (-1, 1), (1, 1)]
    for i, (sx, sy) in enumerate(wheels):
        wx, wy = cx + sx * (w / 2), cy + sy * (h / 2)
        lit = t > lit_t + i * 0.15
        d.rounded_rectangle((wx - 46 * p, wy - 70 * p, wx + 46 * p, wy + 70 * p), radius=14, fill=(255, 210, 31) if lit else (40, 40, 40),
                            outline=INK, width=6)
        if lit:
            # torque arrows spinning
            k = (t * 3 + i * 0.25) % 1
            ay = wy - 50 * p + 100 * p * k
            d.polygon([(wx + sx * 70 * p, ay - 14), (wx + sx * 70 * p, ay + 14), (wx + sx * 96 * p, ay)], fill=RED)
    for sx in (-1, 1):
        d.line([(cx + sx * 60 * p, cy), (cx + sx * (w / 2), cy)], fill=(80, 84, 90), width=10)


def v8_badge(size=150):
    im = Image.new('RGBA', (size, int(size * 0.6)), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((4, 4, size - 4, size * 0.6 - 4), radius=16, fill=INK)
    d.text((size / 2, size * 0.3), 'V8', font=font(FONT_BLACK, int(size * 0.38)), fill=(255, 80, 70), anchor='mm')
    return im


# ----------------------------------------------------------------- timeline
def build():
    SEGS.clear()
    seg('GT', 2.9, ph('it\'s Mercedes\'') - 0.15, enter='none', kf=[(2.9, CX, GY, SC)])
    t = ph("it's Mercedes'") - 0.1
    seg('C63', t, ph('but AMG Line') - 0.12)
    SEGS[-1]['shine_at'] = ph('upgrades') if False else ph('performance upgrades')
    seg('C300', ph('but AMG Line') - 0.1, ph('the number tells') - 0.12)
    seg('A35', ph('35 is') - 0.15, ph('43 sits') - 0.12)
    seg('C43', ph('43 sits') - 0.1, ph('53 brings') - 0.12)
    seg('E53', ph('53 brings') - 0.1, ph('and 63 is') - 0.12)
    seg('S63', ph('and 63 is') - 0.1, ph('but these numbers') - 0.12)
    SEGS[-1]['shine_at'] = ph('top of the range')
    seg('GT', ph("then there's 55") - 0.1, ph('S means') - 0.12, burnout=True)
    SEGS[-1]['flames'] = lambda t, tv=ph('V8 models'): 1.0 if tv < t < tv + 1.0 else 0
    seg('C63', ph('S means') - 0.1, ph('and E PERFORMANCE') - 0.12)
    SEGS[-1]['shine_at'] = ph('sharper')
    seg('GLC63', ph('and E PERFORMANCE') - 0.12, ph('4MATIC+ is') - 0.12, cruise=False)
    seg('GT', ph('and GT is') - 0.1, ph('while G 63') - 0.12)
    tg, tg2 = ph('while G 63') - 0.1, ph('so an AMG') - 0.12
    y0, y1 = GY + 80, GY - 110
    yl = lambda x: lerp(y0, y1, x / W)
    seg('G63', tg, tg2, kf=[(tg, CX - 120, yl(CX - 120), SC), (tg2, CX + 60, yl(CX + 60), SC)],
        mod=lambda t: (0, 0, math.degrees(math.atan2(y0 - y1, W)), 1))
    seg('GLC63', ph('so an AMG') - 0.1, ph('and if you') - 0.05)


def hook(L, t):
    t_grid, t_back = ph('AMG', 1) + 0.1, ph('AMG stands') - 0.1
    order = ['A35', 'C43', 'C63', 'E53', 'S63', 'GT', 'GLC63', 'GLE53', 'G63']
    cols, cell_w, cell_h, gx0, gy0 = 3, 340, 140, 30, 430
    pos = {k: (gx0 + (i % cols) * cell_w + cell_w / 2, gy0 + (i // cols) * cell_h + 110) for i, k in enumerate(order)}
    gsc = 0.058
    if t < t_grid:
        p = 1.0
    elif t < t_back:
        p = 1 - ease_out((t - t_grid) / 0.4)
    else:
        p = ease_out((t - t_back) / 0.45)
    gx, gyy = pos['GT']
    cx, gy, sc = lerp(gx, CX, p), lerp(gyy, GY, p), lerp(gsc, SC, p)
    if p > 0.97:
        speed_lines(L, t, 400, GY - 20, 0.9)
        ground_line(L, t, GY)
    info = draw_car(L, 'GT', cx, gy, sc, travel=V.CRUISE * t, flames=1.0 if t < 0.6 else 0, t=t)
    if p > 0.6:
        draw_puffs(L, info['rear'][0] - 20, info['rear'][1] - 8, t, -1, alpha=0.4, size=(14, 34), seed=99)
    if t_grid <= t < t_back + 0.4:
        for i, k in enumerate(order):
            if k == 'GT':
                continue
            ta = t_grid + 0.15 + i * 0.04
            if t < ta:
                continue
            x, y = pos[k]
            if t >= t_back:
                x += (W + 400) * ease_in((t - t_back) / 0.35) * (1 if i % 2 else -1)
            sck = gsc * ease_back(clamp01((t - ta) / 0.25))
            if sck > 0.01:
                draw_car(L, k, x, y, sck, travel=V.CRUISE * t)
        if t < t_back:
            meaning(L, t, t_grid + 0.5, 'THE WHOLE AMG RANGE', RED, y=390, x=330, size=34)
    # AMG wordmark flies in
    lg = amg_word(150)
    tl = clamp01(t / 0.4)
    lx = lerp(W + 300, W / 2, ease_out(tl))
    ly = 290 if t < t_grid else lerp(290, 250, ease_out((t - t_grid) / 0.3))
    if t < t_back:
        im = lg if tl >= 1 else lg.resize((int(lg.width * (1 + 1.2 * (1 - tl))), lg.height))
        paste_clip(L, im, int(lx - im.width / 2), int(ly - im.height / 2))
        if tl >= 1:
            ellipse_draw(L, lx, ly, 200, 100, t - 0.45)
    if ph('one minute') - 0.1 <= t < t_back:
        stopwatch(L, 920, 280, 58, t - ph('one minute'))


def scene_layer(t):
    L = Image.new('RGBA', (W, 1000), (0, 0, 0, 0))
    # backdrops
    if ph('while G 63') - 0.1 <= t < ph('so an AMG') - 0.1:
        hill(L, GY + 80, GY - 110)
    if ph('then there\'s 55') - 0.1 <= t < ph('S means') - 0.1:
        race_track(L, t, GY)
    if ph('and GT is') - 0.1 <= t < ph('while G 63') - 0.1:
        mountains_road(L, t, GY)
    if ph('top of the range') - 0.1 <= t < ph('but these numbers') - 0.1:
        sun_rays(L, CX, GY - 120, t, 0.7)
    active = [s for s in SEGS if seg_state(s, t)]
    quiet = (ph('while G 63') - 0.1 <= t < ph('so an AMG') - 0.1) or (ph('and E PERFORMANCE') - 0.1 <= t < ph('4MATIC+ is') - 0.1)
    roads = (ph("then there's 55") - 0.1 <= t < ph('S means') - 0.1) or (ph('and GT is') - 0.1 <= t < ph('while G 63') - 0.1)
    if active and not quiet:
        k = max(seg_state(s, t)['lines'] for s in active)
        speed_lines(L, t, 400, GY - 20, k)
        if not roads:
            ground_line(L, t, GY)
    if t < ph('AMG stands') + 0.4:
        hook(L, t)
    cars = draw_cars(L, t)
    beats(L, t, cars)
    return L


def car_of(cars, key):
    v = [v for k, v in cars.items() if v[0]['key'] == key]
    return v[0] if v else None


def beats(L, t, cars):
    # ---- AMG = Aufrecht Melcher Großaspach
    t0, t1 = ph('AMG stands') - 0.1, ph("it's Mercedes'") - 0.1
    if t0 <= t < t1:
        ta, tm, tg = ph('Aufrecht', 1), ph('Melcher'), ph('Großaspach')
        boxes = bar(L, t, [('A', 'red' if t > ta else 'dark', 110), ('M', 'red' if t > tm else 'dark', 110), ('G', 'red' if t > tg else 'dark', 110)],
                    y=BAR_Y + 20, t0=t0, gap=40)
        cur = 0 if t < tm else (1 if t < tg else 2)
        ht = [ta, tm, tg][cur]
        bx, by, bw, bh = boxes[cur]
        ellipse_draw(L, bx, by, bw / 2 + 30, bh / 2 + 26, t - ht)
        # names drop under each letter
        for i, (tt, nm) in enumerate([(ta, 'AUFRECHT'), (tm, 'MELCHER'), (tg, 'GROSSASPACH')]):
            if t > tt:
                x = boxes[i][0]
                yy = 470 + (i % 2) * 0
                pop(L, tag(nm, bg=BLUE if i < 2 else (90, 90, 90), size=30), x, 470, t - tt)
        tf, tt_, tb = ph('founders'), ph('the town'), ph('born')
        if t > tf:
            for i in range(2):
                x = boxes[i][0]
                drop(L, person('f%d' % i, (90, 120, 170) if i == 0 else (120, 90, 150)), x, 640, t - tf - i * 0.12, from_y=-200)
            meaning(L, t, tf + 0.2, 'THE FOUNDERS', DARK, y=790, x=(boxes[0][0] + boxes[1][0]) / 2, size=34)
        if t > tg - 0.05:
            ts = town_sign('Großaspach', 0.8)
            drop(L, ts, boxes[2][0] + 20, 640, t - tg + 0.05, from_y=-200)
        if t > tt_:
            meaning(L, t, tt_, 'THE TOWN', (90, 90, 90), y=790, x=boxes[2][0] + 20, size=34)
        if t > tb:
            arrow_draw(L, (boxes[0][0] + 60, 700), (boxes[2][0] - 140, 660), t - tb, col=RED)
            meaning(L, t, tb + 0.25, "AUFRECHT'S BIRTHPLACE", RED, y=TAG_LOW, size=34)
    # ---- performance division
    t0, t1 = ph("it's Mercedes'") - 0.1, ph('a full AMG') - 0.1
    if t0 <= t < t1:
        pop(L, amg_word(110), W / 2, BAR_Y, t - t0)
        meaning(L, t, ph('performance division'), "MERCEDES' PERFORMANCE DIVISION", RED, y=420, size=34)
        if t > ph('division') - 0.2:
            v = clamp01((t - ph('division') + 0.2) / 0.6)
            gauge(L, 880, 520, 110, 0.1 + 0.85 * ease_out(v) + 0.02 * math.sin(t * 40))
    # ---- full AMG
    t0, t1 = ph('a full AMG') - 0.1, ph('but AMG Line') - 0.1
    if t0 <= t < t1:
        bar(L, t, [('AMG', 'red', 74), ('C', 'dark', 74), ('63', 'yellow', 74)], y=BAR_Y, t0=t0)
        meaning(L, t, ph('full AMG'), 'FULL AMG', RED, y=410, x=200, size=36)
        c = car_of(cars, 'C63')
        if c:
            _, st, info = c
            fx, fy = info['front']
            rx, ry = info['rear']
            te, tsu, tpu = ph('own engine'), ph('suspension'), ph('performance upgrades')
            if t > te:
                engine_anim(L, 760, 470, 0.45, t)
                arrow_draw(L, (760, 520), (fx + 10, info['top'] + 120), t - te, col=ORANGE)
                meaning(L, t, te + 0.15, 'OWN ENGINE', ORANGE, y=560, x=880, size=30)
            if t > tsu:
                comp = 0.5 + 0.5 * math.sin((t - tsu) * 10)
                spring(L, 160, 560, 150, comp)
                arrow_draw(L, (200, 620), (rx - 20, ry - 20), t - tsu, col=ORANGE)
                meaning(L, t, tsu + 0.15, 'SUSPENSION', ORANGE, y=430 + 210, x=160 + 0, size=28) if False else meaning(L, t, tsu + 0.15, 'SUSPENSION', ORANGE, y=470, x=180, size=30)
            if t > tpu:
                ellipse_draw(L, fx, fy, 70, 70, t - tpu, col=RED)
                meaning(L, t, tpu + 0.1, 'BRAKES · POWER · UPGRADES', DARK, y=TAG_LOW, size=34)
    # ---- AMG Line
    t0, t1 = ph('but AMG Line') - 0.1, ph('the number tells') - 0.1
    if t0 <= t < t1:
        bar(L, t, [('C 300', 'dark', 70), ('AMG Line', 'white', 70)], y=BAR_Y, t0=t0, hi=(1, ph('AMG Line')))
        meaning(L, t, ph('sporty trim'), 'AMG LINE = SPORTY TRIM', WHITE, y=420, size=36)
        c = car_of(cars, 'C300')
        if c:
            _, st, info = c
            fx, fy = info['front']
            rx, ry = info['rear']
            if t > ph('bigger wheels'):
                ellipse_draw(L, rx, ry - 58, 75, 75, t - ph('bigger wheels'))
                meaning(L, t, ph('bigger wheels'), 'BIGGER WHEELS', BLUE, y=510, x=230, size=30)
            if t > ph('aggressive bumpers'):
                ellipse_draw(L, info['x0'] + info['w'] - 40, GY - 60, 80, 60, t - ph('aggressive bumpers'))
                meaning(L, t, ph('aggressive bumpers'), 'SPORTY BUMPERS', BLUE, y=510, x=860, size=30)
        if t > ph('no extra'):
            gauge(L, 540, 560, 100, 0.22 + 0.02 * math.sin(t * 30))
            pop(L, stamp('NO EXTRA POWER', size=56), W / 2, 690, t - ph('no extra'), dur=0.18, scale_from=1.8)
    # ---- the number = performance level (staircase)
    t0, t1 = ph('the number tells') - 0.1, ph('but these numbers') - 0.1
    if t0 <= t < t1:
        lv = [(ph('35 is'), 0), (ph('43 sits'), 1), (ph('53 brings'), 2), (ph('and 63 is') + 0.1, 3)]
        act = None
        for tt, i in lv:
            if t > tt:
                act = i
        if act is None:
            stairs(L, t, t0 + 0.2, None, x0=340, y0=780, sw=90)
            meaning(L, t, ph('performance level'), 'NUMBER = PERFORMANCE LEVEL', DARK, y=TAG_LOW - 20, size=36)
            bar(L, t, [('AMG', 'red', 70), ('##', 'yellow', 70)], y=BAR_Y, t0=t0, hi=(1, ph('number')))
        else:
            labs = ['35', '43', '53', '63']
            stairs(L, t, t0 - 5, act, x0=650, y0=520, sw=90)
            bar(L, t, [('AMG', 'red', 70), (labs[act], 'yellow', 70)], y=BAR_Y, t0=t0 - 5)
            texts = ['ENTRY POINT', 'ONE STEP UP', 'MORE PERFORMANCE', 'TOP OF THE RANGE']
            meaning(L, t, lv[act][0] + 0.15, texts[act], [GREEN, BLUE, ORANGE, RED][act], y=TAG_LOW, size=40)
            nm = ['A 35', 'C 43', 'E 53', 'S 63'][act]
            meaning(L, t, lv[act][0] + 0.3, nm, WHITE, y=420, x=200, size=34)
            if act == 3:
                c = car_of(cars, 'S63')
                if c:
                    _, st, info = c
                    drop(L, icon('crown', 130), st['cx'] - 40, info['top'] - 40, t - ph('top of the range'), from_y=-150)
    # ---- numbers aren't engine size
    t0, t1 = ph('but these numbers') - 0.1, ph('a 63 can') - 0.1
    if t0 <= t < t1:
        bar(L, t, [('63', 'yellow', 110)], y=BAR_Y + 20, t0=t0)
        engine_anim(L, 540, 640, 0.9, t)
        if t > ph('engine size') - 0.2:
            pop(L, stamp('NOT 6.3 LITRES', size=60), W / 2, 520, t - ph('engine size') + 0.2, dur=0.18, scale_from=1.8)
        meaning(L, t, ph("don't"), "≠ ENGINE SIZE" if False else 'NOT THE ENGINE SIZE', DARK, y=TAG_LOW, size=38)
    # ---- 63 = V8 or plug-in hybrid
    t0, t1 = ph('a 63 can') - 0.1, ph("then there's 55") - 0.1
    if t0 <= t < t1:
        bar(L, t, [('63', 'yellow', 100)], y=BAR_Y + 10, t0=t0 - 5)
        tv, tp = ph('a V8'), ph('plug-in hybrid', 1)
        if t > tv - 0.1:
            engine_anim(L, 270, 640, 0.75, t)
            pop(L, v8_badge(140), 270, 480, t - tv + 0.1)
            meaning(L, t, tv, 'V8', RED, y=790, x=270, size=40)
        if t > ph('or even'):
            d = ImageDraw.Draw(L)
            pop(L, tag('OR', bg=WHITE, fg=INK, size=40), W / 2, 640, t - ph('or even'))
        if t > tp - 0.1:
            pop(L, icon('plug', 140), 720, 520, t - tp + 0.1)
            battery_anim(L, 860, 650, 0.7, (t - tp) / 1.2)
            meaning(L, t, tp, 'PLUG-IN HYBRID', GREEN, y=790, x=800, size=36)
    # ---- 55 on V8 / AMG GT
    t0, t1 = ph("then there's 55") - 0.1, ph('S means') - 0.1
    if t0 <= t < t1:
        bar(L, t, [('55', 'yellow', 100)], y=BAR_Y, t0=t0)
        if t > ph('V8 models'):
            pop(L, v8_badge(150), 880, 440, t - ph('V8 models'))
            meaning(L, t, ph('powerful'), 'POWERFUL V8', RED, y=440, x=230, size=36)
        if t > ph('AMG GT', 1) - 0.1:
            meaning(L, t, ph('AMG GT', 1), 'e.g. AMG GT 55', WHITE, y=TAG_LOW, size=38)
    # ---- S = sharper
    t0, t1 = ph('S means') - 0.1, ph('and E PERFORMANCE') - 0.1
    if t0 <= t < t1:
        bar(L, t, [('C', 'dark', 80), ('63', 'yellow', 80), ('S', 'red', 96)], y=BAR_Y, t0=t0, hi=(2, ph('S means')))
        meaning(L, t, ph('sharper'), 'S = EVEN SHARPER', RED, y=430, size=42)
        if t > ph('sharper'):
            speed_lines(L, t, 420, GY - 20, 1.6, seed=11)
            v = clamp01((t - ph('sharper')) / 0.5)
            gauge(L, 900, 560, 90, 0.3 + 0.65 * ease_out(v))
        meaning(L, t, ph('version'), 'MORE POWER, MORE TRACK', DARK, y=TAG_LOW, size=34)
    # ---- E PERFORMANCE
    t0, t1 = ph('and E PERFORMANCE') - 0.1, ph('4MATIC+ is') - 0.1
    if t0 <= t < t1:
        bar(L, t, [('63', 'ghost', 70), ('S', 'ghost', 70), ('E PERFORMANCE', 'green', 70)], y=BAR_Y, t0=t0, hi=(2, ph('PERFORMANCE means')))
        c = car_of(cars, 'GLC63')
        if c:
            _, st, info = c
            port = (info['rear'][0] + 70, info['top'] + (GY - info['top']) * 0.42)
            tp = ph('high-performance plug-in') - 0.3
            p = ease_out(clamp01((t - tp) / 0.45))
            px, py = lerp(W + 100, port[0] + 40, p), lerp(380, port[1], p)
            d = ImageDraw.Draw(L)
            d.line([(W + 40, 360), (px + 40, py)], fill=INK, width=12)
            d.line([(W + 40, 360), (px + 40, py)], fill=(40, 170, 100), width=6)
            pl = icon('plug', 120).rotate(90, expand=True)
            paste_clip(L, pl, int(px - 20), int(py - pl.height / 2))
            if p >= 1:
                if t < tp + 0.9:
                    sparks(L, port[0], port[1], t, seed=5)
                battery_anim(L, 260, 440, 0.7, (t - tp - 0.45) / 1.4)
        meaning(L, t, ph('high-performance plug-in') + 0.2, 'E PERFORMANCE = PLUG-IN HYBRID', GREEN, y=TAG_LOW, size=34)
    # ---- 4MATIC+
    t0, t1 = ph('4MATIC+ is') - 0.1, ph('and GT is') - 0.1
    if t0 <= t < t1:
        bar(L, t, [('4MATIC+', 'teal', 90)], y=BAR_Y, t0=t0, hi=(0, ph('4MATIC+ is')))
        chassis(L, t, t0 + 0.1, ph('all-wheel-drive'), cy=620)
        meaning(L, t, ph('all-wheel-drive'), '4MATIC+ = ALL-WHEEL DRIVE', TEAL, y=TAG_LOW, size=38)
        meaning(L, t, ph("AMG's"), "AMG'S OWN SYSTEM", DARK, y=440, size=32)
    # ---- GT family
    t0, t1 = ph('and GT is') - 0.1, ph('while G 63') - 0.1
    if t0 <= t < t1:
        bar(L, t, [('GT', 'red', 100)], y=BAR_Y, t0=t0, hi=(0, ph('GT is')))
        meaning(L, t, ph('sports car'), 'GT = SPORTS CAR FAMILY', RED, y=TAG_LOW, size=38)
    # ---- G 63
    t0, t1 = ph('while G 63') - 0.1, ph('so an AMG') - 0.1
    if t0 <= t < t1:
        bar(L, t, [('G', 'dark', 90), ('63', 'yellow', 90)], y=BAR_Y, t0=t0, hi=(0, ph('G-Class')))
        meaning(L, t, ph('high-performance version'), 'HIGH-PERFORMANCE', RED, y=420, x=250, size=34)
        if t > ph('G-Class') - 0.1:
            pop(L, tag('G-CLASS = GELÄNDEWAGEN (OFF-ROADER)', bg=(110, 120, 80), size=30), W / 2, 500, t - ph('G-Class') + 0.1)
    # ---- recap
    t0, t1 = ph('so an AMG') - 0.1, ph('and if you') - 0.05
    if t0 <= t < t1:
        name_t = [ph('AMG', 6) if False else ph('an AMG GLC') + 0.15, ph('GLC 63'), ph('GLC 63') + 0.35, ph('63 S E') + 0.3, ph('S E PERFORMANCE') + 0.25,
                  ph('4MATIC+', 2)]
        labs = [('AMG', 'red'), ('GLC', 'yellow'), ('63', 'yellow'), ('S', 'red'), ('E PERF', 'green'), ('4MATIC+', 'teal')]
        keys = [(l, s if t > name_t[i] else 'dark', 40) for i, (l, s) in enumerate(labs)]
        boxes = bar(L, t, keys, y=BAR_Y, t0=t0, gap=6)
        expl = [(ph('performance SUV'), 1, 'PERFORMANCE SUV', YEL), (ph('top-tier'), 2, 'TOP-TIER AMG', GOLD), (ph('extra-powerful'), 3, 'EXTRA-POWERFUL S', RED),
                (ph('plug-in hybrid', 3), 4, 'PLUG-IN HYBRID', GREEN), (ph('all-wheel drive'), 5, 'ALL-WHEEL DRIVE', TEAL)]
        cur = None
        for tt, idx, lab, col in expl:
            if t > tt:
                cur = (tt, idx)
        if cur:
            bx, by, bw, bh = boxes[cur[1]]
            ellipse_draw(L, bx, by, bw / 2 + 22, bh / 2 + 18, t - cur[0])
        y = 400
        for tt, idx, lab, col in expl:
            if t > tt:
                pop(L, tag(f'{labs[idx][0]} = {lab}', bg=col, fg=INK if col in (YEL, GOLD) else WHITE, size=30), W / 2, y, t - tt)
            y += 62
    if t >= ph('and if you') - 0.05 and t < END - 0.25:
        C.cheat_sheet(L, t - ph('and if you') + 0.05)


BG = None


def render(t, fi):
    global BG
    if BG is None:
        BG = make_background().convert('RGBA')
        build()
        SHAKES.clear()
        SHAKES.extend([(ph('no extra'), 0.25, 10), (ph('engine size') - 0.2, 0.25, 10), (ph('V8 models'), 0.6, 6), (ph("then there's 55") - 0.1, 0.4, 6)])
    fr = BG.copy()
    tt = t if t < END - 0.25 else 0.02
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
        os.makedirs(os.path.join(B, 'frames'), exist_ok=True)
        for s in args[1].split(','):
            t = float(s)
            render(t, int(t * FPS)).save(os.path.join(B, 'frames', f'f_{t:06.2f}.png'))
        return
    out = os.path.join(B, 'video_noaudio.mp4')
    p = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                          '-c:v', 'libx264', '-preset', 'medium', '-crf', '16', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
    for fi in range(int(END * FPS)):
        p.stdin.write(render(fi / FPS, fi).tobytes())
        if fi % 300 == 0:
            print('frame', fi, flush=True)
    p.stdin.close(); p.wait()
    print('wrote', out)


if __name__ == '__main__':
    main()
