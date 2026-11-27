"""Episode 3: "Audi model names explained in one minute".
Uses the ep2 motion system (compose2), the shared helpers from compose_amg, the house captions (v4)
and the full-body character. Cars are the user's ChatGPT images (build/png), true scale.

usage: python3 compose_audi.py [--frames t,t,...]
"""
import math, os, random, subprocess, sys, functools
import numpy as np
from PIL import Image, ImageDraw

import compose as C
import compose2 as V
from compose import (W, H, FPS, ease_out, ease_back, font, FONT_BLACK, FONT_XB, FONT_MONO, INK, YEL, WHITE, RED, BLUE,
                     GREEN, TEAL, GOLD, ORANGE, keycap, tag, stamp, icon, paste_clip, pop, CAR_META, draw_caption, draw_header,
                     draw_character, make_background, B, END)
from compose2 import (draw_car, seg, SEGS, seg_state, draw_cars, speed_lines, ground_line, hill, sun_rays, drop, ellipse_draw,
                      arrow_draw, gauge, engine_anim, battery_anim, energy_flow, sparks, stopwatch, bar, meaning, dim, lerp, clamp01,
                      ease_in, draw_puffs, mountains_road, race_track, city, SHAKES, shake_offset, DARK)
from compose_amg import chassis, stairs

V.GY = GY = 820
V.CX = CX = 540
SC = V.SC = 0.168
BAR_Y = 300
TAG_LOW = 930


def ph(p, k=1):
    return C.at(p, k)


# ----------------------------------------------------------------- extra drawings
@functools.lru_cache(None)
def audi_rings(size=420):
    S = 3
    w, h = size * S, int(size * 0.36) * S
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    r = h * 0.42
    step = r * 1.32
    x0 = w / 2 - step * 1.5
    for i in range(4):
        cx, cy = x0 + i * step, h / 2
        for k, (col, wd) in enumerate([((40, 42, 46), 26), ((230, 234, 238), 16), ((150, 156, 164), 5)]):
            d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=col, width=wd * S // 3 * 2)
    return im.resize((size, int(size * 0.36)), Image.LANCZOS)


@functools.lru_cache(None)
def pump(col=(30, 170, 100), label='P', size=200):
    S = 3
    s = size * S
    im = Image.new('RGBA', (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    lw = 7 * S
    d.rounded_rectangle((s * .18, s * .12, s * .62, s * .92), radius=18 * S, fill=col, outline=INK, width=lw)
    d.rounded_rectangle((s * .25, s * .2, s * .55, s * .42), radius=8 * S, fill=(240, 244, 248), outline=INK, width=lw // 2)
    d.rectangle((s * .12, s * .88, s * .68, s * .96), fill=INK)
    d.line([(s * .62, s * .3), (s * .78, s * .3), (s * .82, s * .7), (s * .86, s * .7)], fill=INK, width=lw, joint='curve')
    d.rectangle((s * .78, s * .2, s * .9, s * .34), fill=(90, 94, 100), outline=INK, width=lw // 2)
    d.text((s * .4, s * .66), label, font=font(FONT_BLACK, int(s * .22)), fill=WHITE, anchor='mm', stroke_width=2 * S, stroke_fill=INK)
    return im.resize((size, size), Image.LANCZOS)


@functools.lru_cache(None)
def flag_de(w=180):
    h = int(w * 0.6)
    im = Image.new('RGBA', (w + 8, h + 8), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for i, c in enumerate([(20, 20, 20), (221, 0, 0), (255, 206, 0)]):
        d.rectangle((4, 4 + i * h / 3, w + 4, 4 + (i + 1) * h / 3), fill=c)
    d.rectangle((4, 4, w + 4, h + 4), outline=INK, width=5)
    return im


@functools.lru_cache(None)
def money(n, size=70):
    txt = '$' * n
    return tag(txt, bg=(40, 160, 90), size=size // 2 + 6)


def flash(L, cx, cy, t_rel, dur=0.35, r=420):
    if not 0 <= t_rel < dur:
        return
    p = t_rel / dur
    over = Image.new('RGBA', L.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(over)
    rr = r * (0.4 + 0.8 * p)
    d.ellipse((cx - rr, cy - rr * 0.45, cx + rr, cy + rr * 0.45), fill=(255, 255, 255, int(200 * (1 - p))))
    L.alpha_composite(over)
    for i in range(10):
        a = i * math.pi / 5
        d2 = ImageDraw.Draw(L)
        r0, r1 = rr * 0.7, rr * (0.9 + 0.3 * p)
        d2.line([(cx + r0 * math.cos(a), cy + r0 * 0.45 * math.sin(a)), (cx + r1 * math.cos(a), cy + r1 * 0.45 * math.sin(a))],
                fill=(255, 210, 31), width=7)


def car_of(cars, key):
    v = [v for k, v in cars.items() if v[0]['key'] == key]
    return v[0] if v else None


# ----------------------------------------------------------------- timeline
def build():
    SEGS.clear()
    seg('RS6', 0.0, ph('Audi uses') - 0.15, enter='none')
    # two letters: A car and Q car in two lanes
    t = ph('Audi uses') - 0.1
    seg('A6', t, ph('A is') - 0.12, kf=[(t, CX, 640, 0.11)])
    seg('Q7', t + 0.25, ph('A is') - 0.1, kf=[(t + 0.25, CX, 900, 0.11)])
    seg('A3', ph('A3') - 0.35, ph('A6', 1) - 0.12)
    seg('A6', ph('A6', 1) - 0.1, ph('while Q') - 0.12)
    seg('Q7', ph('while Q') - 0.1, ph('from the compact') - 0.12)
    # Q3 -> Q7 -> Q8 size line-up (true scale, stacked)
    tq = ph('compact Q3') - 0.15
    for i, (k, tt) in enumerate([('Q3', tq), ('Q7', ph('larger Q7') - 0.1), ('Q8', ph('Q8') - 0.1)]):
        seg(k, tt, ph('the number tells') - 0.12 + i * 0.03, kf=[(tt, CX, 505 + i * 182, 0.108)])
    # badges section
    seg('A5', ph('TFSI') - 0.12, ph('TDI') - 0.12)
    seg('A6', ph('TDI') - 0.1, ph('and e-tron') - 0.12)
    seg('Q6E', ph('and e-tron') - 0.1, ph('while e-hybrid') - 0.12, cruise=False)
    seg('A5EH', ph('while e-hybrid') - 0.1, ph('the body style') - 0.12, cruise=False)
    # body styles
    tb = ph('the body style') - 0.1
    for i, k in enumerate(['A6AV', 'A5', 'A6']):
        seg(k, tb + i * 0.12, ph('Avant is') - 0.15 + i * 0.03, kf=[(tb + i * 0.12, CX, 520 + i * 165, 0.12)])
    seg('A6AV', ph('Avant is') - 0.1, ph('Sportback gives') - 0.12)
    seg('A5', ph('Sportback gives') - 0.1, ph('and Sedan') - 0.12)
    seg('A6', ph('and Sedan') - 0.1, ph("then there's the") - 0.12)
    # performance
    seg('S5', ph('S means') - 0.1, ph('and RS comes') - 0.12)
    seg('RS5', ph('and RS comes') - 0.1, ph('so an A5') - 0.12, burnout=True)
    t5 = ph('so an A5') - 0.1
    seg('A5', t5, ph('but S line') - 0.12, swaps=[(ph('S5', 1) - 0.05, 'S5'), (ph('RS 5') - 0.05, 'RS5')])
    seg('A5SL', ph('but S line') - 0.1, ph('quattro is') - 0.12)
    seg('A5', ph('and newer') - 0.1, ph('so an RS') - 0.12, cruise=True)
    seg('RS6', ph('so an RS') - 0.1, ph('and if you') - 0.05)
    SEGS[-1]['shine_at'] = ph('high-performance')
    SEGS[-1]['flames'] = lambda t, tx=ph('extra performance'): 1.0 if tx < t < tx + 0.9 else 0


# patch seg() to accept swaps
_seg = seg


def seg(key, t_in, t_out, swaps=None, **kw):
    _seg(key, t_in, t_out, **kw)
    if swaps:
        SEGS[-1]['swaps'] = swaps


def hook(L, t):
    t_grid, t_back = ph('explained') - 0.05, ph('Audi uses') - 0.15
    order = ['A3', 'A5', 'A6', 'A6AV', 'S5', 'RS5', 'Q3', 'Q6E', 'Q7', 'Q8', 'A5SL', 'A5EH']
    cols, cell_w, cell_h, gx0, gy0 = 3, 340, 112, 30, 380
    pos = {k: (gx0 + (i % cols) * cell_w + cell_w / 2, gy0 + (i // cols) * cell_h + 110) for i, k in enumerate(order)}
    hero_pos = (CX, gy0 + 4 * cell_h + 110)
    gsc = 0.058
    if t < t_grid:
        p = 1.0
    elif t < t_back:
        p = 1 - ease_out((t - t_grid) / 0.4)
    else:
        p = 1.0
    cx, gy, sc = lerp(hero_pos[0], CX, p), lerp(hero_pos[1], GY, p), lerp(gsc, SC, p)
    if t < t_grid or t >= t_back:
        speed_lines(L, t, 400, GY - 20, 0.9)
        ground_line(L, t, GY)
    if t >= t_back:
        return
    info = draw_car(L, 'RS6', cx, gy, sc, travel=V.CRUISE * t, flames=1.0 if t < 0.6 else 0, t=t)
    if p > 0.6:
        draw_puffs(L, info['rear'][0] - 20, info['rear'][1] - 8, t, -1, alpha=0.4, size=(14, 34), seed=99)
    if t >= t_grid:
        for i, k in enumerate(order):
            ta = t_grid + 0.15 + i * 0.035
            if t < ta:
                continue
            x, y = pos[k]
            sck = gsc * ease_back(clamp01((t - ta) / 0.25))
            if sck > 0.01:
                draw_car(L, k, x, y, sck, travel=V.CRUISE * t)
        meaning(L, t, t_grid + 0.5, 'THE AUDI RANGE', RED, y=360, x=300, size=34)
    lg = audi_rings(420)
    tl = clamp01(t / 0.4)
    lx = lerp(W + 400, W / 2, ease_out(tl))
    ly = 290 if t < t_grid else lerp(290, 250, ease_out((t - t_grid) / 0.3))
    im = lg if tl >= 1 else lg.resize((int(lg.width * (1 + 1.0 * (1 - tl))), lg.height))
    paste_clip(L, im, int(lx - im.width / 2), int(ly - im.height / 2))
    if tl >= 1:
        ellipse_draw(L, lx, ly, 250, 95, t - 0.45)
    if ph('one minute') - 0.1 <= t:
        stopwatch(L, 930, 400, 54, t - ph('one minute'))


def scene_layer(t):
    L = Image.new('RGBA', (W, 1000), (0, 0, 0, 0))
    # backdrops
    if ph('and RS comes') - 0.1 <= t < ph('so an A5') - 0.1:
        race_track(L, t, GY)
    if ph('and newer') - 0.1 <= t < ph('so an RS') - 0.1:
        pass
    if ph('so an RS') - 0.1 <= t < ph('and if you') - 0.05:
        mountains_road(L, t, GY)
    stacked = (ph('Audi uses') - 0.1 <= t < ph('A is') - 0.1) or (ph('compact Q3') - 0.2 <= t < ph('the number tells') - 0.1) or \
              (ph('the body style') - 0.1 <= t < ph('Avant is') - 0.1)
    still = (ph('and e-tron') - 0.1 <= t < ph('the body style') - 0.1)
    roads = (ph('and RS comes') - 0.1 <= t < ph('so an A5') - 0.1) or (ph('so an RS') - 0.1 <= t < ph('and if you') - 0.05)
    active = [s for s in SEGS if seg_state(s, t)]
    if t >= ph('Audi uses') - 0.15 and active and not still:
        k = max(seg_state(s, t)['lines'] for s in active)
        speed_lines(L, t, 400, GY - 20, k)
        if not roads and not stacked:
            ground_line(L, t, GY)
    if t < ph('Audi uses'):
        hook(L, t)
    cars = draw_cars(L, t) if t >= ph('Audi uses') - 0.15 else {}
    beats(L, t, cars)
    return L


def beats(L, t, cars):
    # ---- two main letters
    t0, t1 = ph('Audi uses') - 0.1, ph('A is') - 0.1
    if t0 <= t < t1:
        boxes = bar(L, t, [('A', 'yellow', 110), ('Q', 'yellow', 110)], y=BAR_Y, t0=t0, gap=80, hi=(0, ph('two main')))
        meaning(L, t, ph('two main'), '2 MAIN LETTERS', DARK, y=430, size=38)
        if t > ph('separate'):
            pop(L, keycap('A', 'yellow', 44, pad=14), 90, 590, t - ph('separate'))
            pop(L, keycap('Q', 'yellow', 44, pad=14), 90, 850, t - ph('separate') - 0.1)
    # ---- A = lower-bodied
    t0, t1 = ph('A is') - 0.1, ph('while Q') - 0.1
    if t0 <= t < t1:
        k = 'A3' if t < ph('A6', 1) else 'A6'
        bar(L, t, [('A', 'yellow', 100), ('3' if k == 'A3' else '6', 'dark', 100)], y=BAR_Y, t0=t0, hi=(0, ph('A is')))
        meaning(L, t, ph('lower-bodied'), 'A = LOWER CARS', YEL, y=430, size=42)
        if t > ph('lower-bodied') + 0.3:
            c = car_of(cars, k)
            if c:
                _, st, info = c
                hgt = CAR_META[k]['Hmm'] * SC
                d = ImageDraw.Draw(L)
                x = info['x0'] + info['w'] + 30
                arrow_draw(L, (x, GY), (x, GY - hgt), t - ph('lower-bodied') - 0.3, col=(80, 84, 90), width=6)
                if t > ph('lower-bodied') + 0.6:
                    d.text((x + 14, GY - hgt / 2), f"{CAR_META[k]['Hmm'] / 1000:.2f} m", font=font(FONT_MONO, 28), fill=(80, 84, 90), anchor='lm')
        meaning(L, t, ph('A3') - 0.2, 'HATCH · SALOON · ESTATE', WHITE, y=TAG_LOW, size=34)
    # ---- Q = SUV
    t0, t1 = ph('while Q') - 0.1, ph('from the compact') - 0.1
    if t0 <= t < t1:
        bar(L, t, [('Q', 'yellow', 110)], y=BAR_Y, t0=t0, hi=(0, ph('Q is')))
        meaning(L, t, ph('SUVs'), 'Q = SUV', ORANGE, y=430, size=46)
        c = car_of(cars, 'Q7')
        if c and t > ph('SUVs'):
            _, st, info = c
            hgt = CAR_META['Q7']['Hmm'] * SC
            x = info['x0'] + info['w'] + 20
            arrow_draw(L, (min(x, 1040), GY), (min(x, 1040), GY - hgt), t - ph('SUVs'), col=(80, 84, 90), width=6)
            meaning(L, t, ph('SUVs') + 0.3, 'TALLER', DARK, y=GY - hgt - 40, x=min(x, 1000) - 40, size=28)
    # ---- Q3 / Q7 / Q8 sizes
    t0, t1 = ph('from the compact') - 0.1, ph('the number tells') - 0.1
    if t0 <= t < t1:
        labs = [('Q3', ph('compact Q3')), ('Q7', ph('larger Q7')), ('Q8', ph('Q8'))]
        keys = [(l, 'yellow' if t > tt else 'ghost', 80) for l, tt in labs]
        boxes = bar(L, t, keys, y=BAR_Y, t0=t0, gap=24)
        cur = 0 if t < labs[1][1] else (1 if t < labs[2][1] else 2)
        ellipse_draw(L, boxes[cur][0], boxes[cur][1], boxes[cur][2] / 2 + 26, boxes[cur][3] / 2 + 22, t - labs[cur][1])
        for i, (k, tt) in enumerate(labs):
            if t > tt + 0.35:
                Lm = CAR_META[k]['L']
                c = car_of(cars, k)
                if c:
                    _, st, info = c
                    pop(L, tag(f'{Lm / 1000:.2f} m', bg=WHITE, fg=INK, size=26), info['x0'] + info['w'] + 70 if info['x0'] + info['w'] < 960 else 990,
                        505 + i * 182 - 40, t - tt - 0.35)
        meaning(L, t, ph('compact'), 'COMPACT', BLUE, y=410, x=200, size=30)
        meaning(L, t, ph('larger'), 'LARGER', DARK, y=410, x=880, size=30)
    # ---- number = position, higher = bigger & pricier
    t0, t1 = ph('the number tells') - 0.1, ph("but the number") - 0.1
    if t0 <= t < t1:
        bar(L, t, [('Q', 'yellow', 80), ('#', 'yellow', 80)], y=BAR_Y, t0=t0, hi=(1, ph('number', 1)))
        meaning(L, t, ph('where the car'), 'NUMBER = POSITION IN THE RANGE', DARK, y=420, size=32)
        labels = ('3', '5', '7', '8')
        act = None
        th = ph('higher')
        if t > th:
            act = min(3, int((t - th) / 0.45))
        stairs(L, t, t0 + 0.3, act, x0=330, y0=800, sw=95, labels=labels)
        if t > ph('bigger'):
            meaning(L, t, ph('bigger'), 'HIGHER = BIGGER + PRICIER', BLUE, y=TAG_LOW - 10, x=W / 2, size=34)
        if t > ph('expensive') - 0.1:
            for i in range(4):
                if t > ph('expensive') - 0.1 + i * 0.12:
                    pop(L, money(i + 1), 330 + i * 103 + 47, 836, t - ph('expensive') + 0.1 - i * 0.12)
    # ---- number isn't the engine
    t0, t1 = ph('but the number') - 0.1, ph('TFSI') - 0.1
    if t0 <= t < t1:
        bar(L, t, [('Q', 'ghost', 80), ('7', 'yellow', 80)], y=BAR_Y, t0=t0)
        engine_anim(L, 540, 640, 0.9, t)
        if t > ph('the engine') - 0.05:
            pop(L, stamp('NOT THE ENGINE', size=58), W / 2, 520, t - ph('the engine') + 0.05, dur=0.18, scale_from=1.8)
        if t > ph('badges'):
            for i, (lab, st) in enumerate([('TFSI', 'dark'), ('TDI', 'dark'), ('e-tron', 'green'), ('e-hybrid', 'teal')]):
                pop(L, keycap(lab, st, 44, pad=14), 150 + i * 250, 830, t - ph('badges') - i * 0.1)
    # ---- TFSI / TDI
    for ph0, ph1, lab, col, nm, txt in [('TFSI', 'TDI', 'TFSI', (30, 170, 100), 'P', 'TFSI = PETROL'), ('TDI', 'and e-tron', 'TDI', (40, 40, 40), 'D', 'TDI = DIESEL')]:
        t0, t1 = ph(ph0) - 0.1, ph(ph1) - 0.1
        if t0 <= t < t1:
            key = 'A5' if lab == 'TFSI' else 'A6'
            bar(L, t, [(key[:2], 'ghost', 70), ('40', 'ghost', 70), (lab, 'dark', 90)], y=BAR_Y, t0=t0, hi=(2, ph(ph0)))
            pop(L, pump(col, nm, 170), 150, 520, t - t0 - 0.15)
            meaning(L, t, t0 + 0.35, txt, GREEN if lab == 'TFSI' else DARK, y=TAG_LOW, size=42)
    # ---- e-tron
    t0, t1 = ph('and e-tron') - 0.1, ph('while e-hybrid') - 0.1
    if t0 <= t < t1:
        bar(L, t, [('Q6', 'ghost', 70), ('e-tron', 'green', 90)], y=BAR_Y, t0=t0, hi=(1, ph('e-tron')))
        c = car_of(cars, 'Q6E')
        if c:
            _, st, info = c
            port = (info['front'][0] - 90, info['top'] + (GY - info['top']) * 0.38)
            tp = ph('fully') - 0.35
            p = ease_out(clamp01((t - tp) / 0.45))
            px, py = lerp(W + 100, port[0] + 30, p), lerp(380, port[1], p)
            d = ImageDraw.Draw(L)
            d.line([(W + 40, 360), (px + 40, py)], fill=INK, width=12)
            d.line([(W + 40, 360), (px + 40, py)], fill=(40, 170, 100), width=6)
            pl = icon('plug', 110).rotate(90, expand=True)
            paste_clip(L, pl, int(px - 20), int(py - pl.height / 2))
            if p >= 1:
                if t < tp + 0.9:
                    sparks(L, port[0], port[1], t, seed=4)
                battery_anim(L, 240, 440, 0.75, (t - tp - 0.45) / 1.0, col=(40, 200, 120))
        meaning(L, t, ph('fully'), 'e-tron = FULLY ELECTRIC', GREEN, y=TAG_LOW, size=40)
    # ---- e-hybrid
    t0, t1 = ph('while e-hybrid') - 0.1, ph('the body style') - 0.1
    if t0 <= t < t1:
        bar(L, t, [('A5', 'ghost', 70), ('e-hybrid', 'teal', 90)], y=BAR_Y, t0=t0, hi=(1, ph('e-hybrid')))
        engine_anim(L, 200, 470, 0.55, t)
        battery_anim(L, 880, 470, 0.6, 0.55 + 0.1 * math.sin(t * 3), col=(60, 160, 255))
        energy_flow(L, (300, 470), (780, 470), t)
        meaning(L, t, ph('plug-in hybrid'), 'e-hybrid = PLUG-IN HYBRID', TEAL, y=TAG_LOW, size=38)
    # ---- body style
    t0, t1 = ph('the body style') - 0.1, ph('Avant is') - 0.1
    if t0 <= t < t1:
        meaning(L, t, t0 + 0.1, 'BODY STYLE', DARK, y=BAR_Y, size=48)
        for i, (lab, col) in enumerate([('AVANT', BLUE), ('SPORTBACK', RED), ('SEDAN', DARK)]):
            pop(L, tag(lab, bg=col, size=26), 110, 520 + i * 165 - 40, t - t0 - 0.3 - i * 0.12)
    # ---- Avant / Sportback / Sedan
    body = [('Avant is', 'Sportback gives', 'A6AV', 'Avant', BLUE, 'AVANT = ESTATE', 'estate'),
            ('Sportback gives', 'and Sedan', 'A5', 'Sportback', RED, 'SPORTBACK = SLOPING ROOF', 'sloping'),
            ('and Sedan', "then there's the", 'A6', 'Sedan', DARK, 'SEDAN = SALOON', 'saloon')]
    for p0, p1, key, lab, col, txt, word in body:
        t0, t1 = ph(p0) - 0.1, ph(p1) - 0.1
        if t0 <= t < t1:
            bar(L, t, [(key[:2], 'ghost', 70), (lab, 'red' if col == RED else ('blue' if col == BLUE else 'dark'), 80)], y=BAR_Y, t0=t0,
                hi=(1, t0 + 0.2))
            meaning(L, t, ph(word, 1), txt, col, y=TAG_LOW, size=38)
            c = car_of(cars, key)
            if c and t > ph(word, 1) - 0.1:
                _, st, info = c
                x0, top, w = info['x0'], info['top'], info['w']
                tr = t - ph(word, 1) + 0.1
                if key == 'A6AV':        # long roof + big boot
                    ellipse_draw(L, x0 + w * 0.16, top + 90, 150, 110, tr)
                    meaning(L, t, ph(word, 1) + 0.3, 'BIG BOOT', DARK, y=top - 30, x=x0 + w * 0.16 + 40, size=28)
                elif key == 'A5':        # sloping roof line
                    arrow_draw(L, (x0 + w * 0.55, top + 8), (x0 + w * 0.05, top + 120), tr, col=RED, width=9)
                    meaning(L, t, ph(word, 1) + 0.3, 'HATCH OPENS WITH THE GLASS', DARK, y=top - 40, size=26)
                else:                    # separate boot
                    ellipse_draw(L, x0 + w * 0.1, top + 140, 120, 70, tr)
                    meaning(L, t, ph(word, 1) + 0.3, 'SEPARATE BOOT', DARK, y=top - 30, x=x0 + w * 0.12 + 60, size=28)
    # ---- performance side
    t0, t1 = ph("then there's the") - 0.1, ph('S means') - 0.1
    if t0 <= t < t1:
        meaning(L, t, t0 + 0.1, 'PERFORMANCE', RED, y=BAR_Y, size=52)
        v = clamp01((t - t0 - 0.2) / 0.8)
        gauge(L, W / 2, 720, 200, 0.05 + 0.9 * ease_out(v) + 0.02 * math.sin(t * 50), label='x1000 rpm')
    # ---- S
    t0, t1 = ph('S means') - 0.1, ph('and RS comes') - 0.1
    if t0 <= t < t1:
        bar(L, t, [('S', 'red', 96), ('5', 'dark', 96)], y=BAR_Y, t0=t0, hi=(0, ph('S means')))
        meaning(L, t, ph('sporty model'), 'S = SPORTY MODEL', RED, y=TAG_LOW, size=40)
        if t > ph('sporty model'):
            v = clamp01((t - ph('sporty model')) / 0.5)
            gauge(L, 900, 520, 90, 0.2 + 0.55 * ease_out(v))
    # ---- RS = RennSport
    t0, t1 = ph('and RS comes') - 0.1, ph('so an A5') - 0.1
    if t0 <= t < t1:
        boxes = bar(L, t, [('R', 'red', 100), ('S', 'red', 100)], y=BAR_Y, t0=t0, gap=40)
        tr, ts = ph('RennSport'), ph('RennSport') + 0.3
        if t > tr:
            pop(L, tag('RENN', bg=RED, size=34), boxes[0][0], 420, t - tr)
            pop(L, tag('SPORT', bg=RED, size=34), boxes[1][0], 420, t - ts)
        if t > ph('German'):
            pop(L, flag_de(150), 150, 480, t - ph('German'))
        meaning(L, t, ph('racing'), 'RS = RACING SPORT', RED, y=TAG_LOW, size=42)
    # ---- A5 -> S5 -> RS 5
    t0, t1 = ph('so an A5') - 0.1, ph('but S line') - 0.1
    if t0 <= t < t1:
        ts5, trs = ph('S5', 1) - 0.05, ph('RS 5') - 0.05
        lev = 0 if t < ts5 else (1 if t < trs else 2)
        keys = [('A5', 'yellow' if lev == 0 else 'ghost', 74), ('S5', 'red' if lev == 1 else 'ghost', 74), ('RS 5', 'red' if lev == 2 else 'ghost', 74)]
        boxes = bar(L, t, keys, y=BAR_Y, t0=t0, gap=60)
        for i in range(2):
            if lev > i:
                arrow_draw(L, (boxes[i][0] + boxes[i][2] / 2 + 6, BAR_Y), (boxes[i + 1][0] - boxes[i + 1][2] / 2 - 6, BAR_Y), t - [ts5, trs][i], width=7)
        ht = [t0 + 0.2, ts5, trs][lev]
        bx = boxes[lev]
        ellipse_draw(L, bx[0], bx[1], bx[2] / 2 + 24, bx[3] / 2 + 20, t - ht)
        flash(L, CX, GY - 120, t - ts5)
        flash(L, CX, GY - 120, t - trs)
        v = [0.25, 0.6, 0.93][lev]
        gauge(L, 900, 520, 90, v + 0.02 * math.sin(t * 40))
        meaning(L, t, ht + 0.1, ['NORMAL', 'SPORTY S', 'FULL RS'][lev], [DARK, RED, RED][lev], y=TAG_LOW, size=42)
    # ---- S line
    t0, t1 = ph('but S line') - 0.1, ph('quattro is') - 0.1
    if t0 <= t < t1:
        bar(L, t, [('A5', 'ghost', 70), ('S line', 'white', 80)], y=BAR_Y, t0=t0, hi=(1, ph('S line')))
        if t > ph('different'):
            pop(L, stamp('NOT AN S5', size=56, angle=-7), 830, 430, t - ph('different'), dur=0.18, scale_from=1.8)
        meaning(L, t, ph('styling package'), 'S LINE = STYLING PACKAGE', WHITE, y=TAG_LOW, size=36)
        c = car_of(cars, 'A5SL')
        if c and t > ph('sportier details'):
            _, st, info = c
            fx, fy = info['front']
            rx, ry = info['rear']
            tr = t - ph('sportier details')
            ellipse_draw(L, rx, ry, 85, 85, tr)
            ellipse_draw(L, info['x0'] + info['w'] - 40, GY - 70, 75, 60, tr - 0.15)
            meaning(L, t, ph('sportier details'), 'SPORTY BUMPERS + WHEELS', BLUE, y=430, x=310, size=28)
        if t > ph('not a full'):
            gauge(L, 170, 560, 80, 0.22 + 0.02 * math.sin(t * 30))
            pop(L, tag('SAME POWER', bg=DARK, size=26), 170, 640, t - ph('not a full'))
    # ---- quattro
    t0, t1 = ph('quattro is') - 0.1, ph('and newer') - 0.1
    if t0 <= t < t1:
        bar(L, t, [('quattro', 'teal', 90)], y=BAR_Y, t0=t0, hi=(0, ph('quattro', 1)))
        chassis(L, t, t0 + 0.1, ph("Audi's") - 0.05, cy=620)
        meaning(L, t, ph('all-wheel-drive'), 'QUATTRO = ALL-WHEEL DRIVE', TEAL, y=TAG_LOW, size=38)
    # ---- old power numbers
    t0, t1 = ph('and newer') - 0.1, ph('so an RS') - 0.1
    if t0 <= t < t1:
        told = ph('old power')
        t40, t45 = ph('40'), ph('45')
        num = '40' if t < t45 else '45'
        boxes = bar(L, t, [('A5', 'yellow', 74), (num, 'yellow' if t > t40 - 0.2 else 'ghost', 74), ('TFSI', 'dark', 74)], y=BAR_Y, t0=t0)
        if t > ph('moving away'):
            # number slides away and gets crossed out
            bx = boxes[1]
            p = ease_in(clamp01((t - ph('because')) / 0.4)) if t > ph('because') else 0
            d = ImageDraw.Draw(L)
            if t > told:
                q = clamp01((t - told) / 0.25)
                d.line([(bx[0] - 50, BAR_Y + 40), (bx[0] - 50 + 100 * q, BAR_Y - 40)], fill=RED, width=12)
            if p > 0:
                pop(L, stamp('OLD SYSTEM', size=48, angle=6), bx[0], 440, t - ph('because') - 0.2, dur=0.18, scale_from=1.6)
        meaning(L, t, told, 'OLD POWER NUMBERS', DARK, y=430 if t < ph('because') else 1200, size=34)
        if t > ph('size'):
            labs = ('A3', 'A5', 'A6', 'A8')
            act = min(3, int((t - ph('size')) / 0.35))
            stairs(L, t, ph('size') - 0.2, act, x0=650, y0=600, sw=85, labels=labs)
            meaning(L, t, ph('size'), 'NAME = SIZE + POSITION', BLUE, y=TAG_LOW, size=38)
    # ---- recap
    t0, t1 = ph('so an RS') - 0.1, ph('and if you') - 0.05
    if t0 <= t < t1:
        labs = [('RS 6', 'red', ph('RS 6')), ('Avant', 'blue', ph('Avant', 2)), ('performance', 'yellow', ph('performance', 2)), ('quattro', 'teal', ph('quattro', 2))]
        keys = [(l, s if t > tt else 'dark', 44) for l, s, tt in labs]
        boxes = bar(L, t, keys, y=BAR_Y, t0=t0, gap=8)
        expl = [(ph('high-performance'), 0, 'RS 6 = HIGH-PERFORMANCE', RED), (ph('estate', 2), 1, 'AVANT = ESTATE', BLUE),
                (ph('sharper'), 0, 'SHARPER RS SETUP', RED), (ph('extra performance'), 2, 'EXTRA PERFORMANCE', YEL),
                (ph('all-wheel drive'), 3, 'QUATTRO = AWD', TEAL)]
        cur = None
        for tt, idx, lab, col in expl:
            if t > tt:
                cur = (tt, idx)
        if cur:
            bx = boxes[cur[1]]
            ellipse_draw(L, bx[0], bx[1], bx[2] / 2 + 20, bx[3] / 2 + 16, t - cur[0])
        y = 400
        for tt, idx, lab, col in expl:
            if t > tt:
                pop(L, tag(lab, bg=col, fg=INK if col in (YEL, GOLD) else WHITE, size=28), W / 2, y, t - tt)
            y += 56
    if t >= ph('and if you') - 0.05 and t < END - 0.25:
        C.cheat_sheet(L, t - ph('and if you') + 0.05)


BG = None


def render(t, fi):
    global BG
    if BG is None:
        BG = make_background().convert('RGBA')
        build()
        SHAKES.clear()
        SHAKES.extend([(ph('the engine') - 0.05, 0.25, 10), (ph('different'), 0.25, 10), (ph('RS 5') - 0.05, 0.35, 8),
                       (ph('and RS comes') - 0.1, 0.4, 6), (ph('extra performance'), 0.5, 6)])
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
