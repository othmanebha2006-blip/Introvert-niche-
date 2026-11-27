"""Episode 4: "Every Audi model explained in one minute" (A/Q, numbers, S/RS, engine letters, quattro).
House rules: explain once (voice + one visual, no sentence cards), cars always moving, true scale,
yellow captions, full-body character, light sound effects.

usage: python3 compose_ep4.py [--frames t,t,...]
"""
import math, os, subprocess, sys
from PIL import Image, ImageDraw

import compose as C
import compose2 as V
from compose import (W, H, FPS, ease_out, ease_back, font, FONT_MONO, INK, YEL, WHITE, RED, keycap, tag, stamp, icon, paste_clip, pop,
                     CAR_META, draw_caption, draw_header, draw_character, make_background, B, END)
from compose2 import (draw_car, seg as _seg, SEGS, seg_state, draw_cars, speed_lines, ground_line, drop, ellipse_draw, arrow_draw, gauge,
                      engine_anim, battery_anim, energy_flow, sparks, stopwatch, bar, lerp, clamp01, ease_in, draw_puffs, mountains_road,
                      race_track, SHAKES, shake_offset)
from compose_amg import chassis, stairs
from compose_audi import audi_rings, pump, flag_de, flash, car_of

V.GY = GY = 820
V.CX = CX = 540
SC = V.SC = 0.168
BAR_Y = 300


def ph(p, k=1):
    return C.at(p, k)


def seg(key, t_in, t_out, swaps=None, **kw):
    _seg(key, t_in, t_out, **kw)
    if swaps:
        SEGS[-1]['swaps'] = swaps


def rear_aligned(key, y, sc, rear=150):
    return [(0, rear + CAR_META[key]['L'] * sc / 2, y, sc)]


# ----------------------------------------------------------------- timeline
A_SEQ = [('A3', 'A is'), ('A4', 'A4'), ('A5', 'A5'), ('A6', 'A6')]
Q_SEQ = [('Q3', 'while Q'), ('Q5', 'Q5'), ('Q7', 'Q7'), ('Q8', 'Q8')]


def build():
    SEGS.clear()
    seg('RSQ8', 0.0, ph('Audi has') - 0.15, enter='none')
    t = ph('Audi has') - 0.1
    seg('A6', t, ph('A is') - 0.12, kf=[(t, CX, 640, 0.11)])
    seg('Q7', t + 0.25, ph('A is') - 0.1, kf=[(t + 0.25, CX, 900, 0.11)])
    for seq, end in ((A_SEQ, 'while Q'), (Q_SEQ, 'and the higher')):
        for i, (k, p) in enumerate(seq):
            t_out = ph(seq[i + 1][1]) - 0.12 if i + 1 < len(seq) else ph(end) - 0.12
            seg(k, ph(p) - 0.1, t_out)
    # size comparisons, rear bumpers aligned so the length difference is visible
    for (a, b, start, end) in (('A3', 'A6', 'so an A3', 'and a Q5'), ('Q5', 'Q8', 'and a Q5', 'but the name')):
        t0 = ph(start) - 0.1
        for j, (k, y) in enumerate(((a, 640), (b, 900))):
            kf = rear_aligned(k, y, 0.12)
            kf[0] = (t0 + j * 0.2,) + kf[0][1:]
            seg(k, t0 + j * 0.2, ph(end) - 0.12 + j * 0.02, kf=kf)
    # S / RS
    seg('A3', ph('but the name') - 0.1, ph('and RS takes') - 0.12, swaps=[(ph('S3', 1) - 0.05, 'S3')])
    seg('RS3', ph('and RS takes') - 0.1, ph('so the A3') - 0.12, burnout=True)
    seg('A3', ph('so the A3') - 0.1, ph('and the same') - 0.12, swaps=[(ph('S3', 2) - 0.05, 'S3'), (ph('RS3') - 0.05, 'RS3')])
    seg('Q8', ph('and the same') - 0.1, ph('then the letters') - 0.12, swaps=[(ph('SUVs') - 0.05, 'RSQ8')])
    # engine letters
    seg('A5', ph('TFSI is') - 0.12, ph('TDI is') - 0.12)
    seg('A6', ph('TDI is') - 0.1, ph('TFSI e') - 0.12)
    seg('A5EH', ph('TFSI e') - 0.1, ph('and e-tron') - 0.12, cruise=False)
    seg('Q6E', ph('and e-tron') - 0.1, ph('quattro is') - 0.12, cruise=False)
    # recap
    seg('RSQ8', ph('so an RS') - 0.1, ph('and if you') - 0.05)
    SEGS[-1]['shine_at'] = ph('high-performance')


# ----------------------------------------------------------------- hook
def hook(L, t):
    t_grid, t_back = ph('explained') - 0.05, ph('Audi has') - 0.15
    order = ['A3', 'A4', 'A5', 'A6', 'S3', 'RS3', 'Q3', 'Q5', 'Q7', 'Q8', 'Q6E', 'A5EH']
    cols, cell_w, cell_h, gx0, gy0 = 3, 340, 112, 30, 380
    pos = {k: (gx0 + (i % cols) * cell_w + cell_w / 2, gy0 + (i // cols) * cell_h + 110) for i, k in enumerate(order)}
    hero = (CX, gy0 + 4 * cell_h + 110)
    gsc = 0.058
    p = 1.0 if t < t_grid else 1 - ease_out((t - t_grid) / 0.4)
    cx, gy, sc = lerp(hero[0], CX, p), lerp(hero[1], GY, p), lerp(gsc, SC, p)
    if t < t_grid:
        speed_lines(L, t, 400, GY - 20, 0.9)
        ground_line(L, t, GY)
    info = draw_car(L, 'RSQ8', cx, gy, sc, travel=V.CRUISE * t, flames=1.0 if t < 0.6 else 0, t=t)
    if p > 0.6:
        draw_puffs(L, info['rear'][0] - 20, info['rear'][1] - 8, t, -1, alpha=0.4, size=(14, 34), seed=99)
    if t >= t_grid:
        for i, k in enumerate(order):
            ta = t_grid + 0.15 + i * 0.035
            if t < ta:
                continue
            sck = gsc * ease_back(clamp01((t - ta) / 0.25))
            if sck > 0.01:
                draw_car(L, k, pos[k][0], pos[k][1], sck, travel=V.CRUISE * t)
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


# ----------------------------------------------------------------- scenes
def scene_layer(t):
    L = Image.new('RGBA', (W, 1000), (0, 0, 0, 0))
    if ph('and RS takes') - 0.1 <= t < ph('so the A3') - 0.1:
        race_track(L, t, GY)
    if ph('so an RS') - 0.1 <= t < ph('and if you') - 0.05:
        mountains_road(L, t, GY)
    stacked = (ph('Audi has') - 0.1 <= t < ph('A is') - 0.1) or (ph('so an A3') - 0.1 <= t < ph('but the name') - 0.1)
    still = ph('TFSI e') - 0.1 <= t < ph('quattro is') - 0.1
    roads = (ph('and RS takes') - 0.1 <= t < ph('so the A3') - 0.1) or (ph('so an RS') - 0.1 <= t < ph('and if you') - 0.05)
    active = [s for s in SEGS if seg_state(s, t)]
    if t >= ph('Audi has') - 0.15 and active and not still:
        k = max(seg_state(s, t)['lines'] for s in active)
        speed_lines(L, t, 400, GY - 20, k)
        if not roads and not stacked:
            ground_line(L, t, GY)
    if t < ph('Audi has') - 0.15:
        hook(L, t)
    cars = draw_cars(L, t) if t >= ph('Audi has') - 0.15 else {}
    beats(L, t, cars)
    return L


def current(seq, t):
    k = seq[0][0]
    for key, p in seq:
        if t >= ph(p) - 0.1:
            k = key
    return k


def plug_in(L, t, cars, key, t_plug, col=(40, 170, 100), front=False):
    c = car_of(cars, key)
    if not c:
        return
    _, st, info = c
    if front:
        port = (info['front'][0] - 90, info['top'] + (GY - info['top']) * 0.38)
    else:
        port = (info['rear'][0] + 70, info['top'] + (GY - info['top']) * 0.42)
    p = ease_out(clamp01((t - t_plug) / 0.45))
    px, py = lerp(W + 100, port[0] + 30, p), lerp(380, port[1], p)
    d = ImageDraw.Draw(L)
    d.line([(W + 40, 360), (px + 40, py)], fill=INK, width=12)
    d.line([(W + 40, 360), (px + 40, py)], fill=col, width=6)
    pl = icon('plug', 110).rotate(90, expand=True)
    paste_clip(L, pl, int(px - 20), int(py - pl.height / 2))
    if p >= 1:
        if t < t_plug + 0.9:
            sparks(L, port[0], port[1], t, seed=4)
        battery_anim(L, 240, 440, 0.75, (t - t_plug - 0.45) / 1.0, col=(40, 200, 120))


def beats(L, t, cars):
    # ---- two types: A and Q
    t0, t1 = ph('Audi has') - 0.1, ph('A is') - 0.1
    if t0 <= t < t1:
        ta, tq = ph('A models'), ph('Q models')
        boxes = bar(L, t, [('A', 'yellow', 110), ('Q', 'yellow', 110)], y=BAR_Y, t0=t0, gap=80)
        if t > ta:
            i = 0 if t < tq else 1
            ellipse_draw(L, boxes[i][0], boxes[i][1], boxes[i][2] / 2 + 30, boxes[i][3] / 2 + 26, t - (ta if i == 0 else tq))
            pop(L, keycap('A', 'yellow', 44, pad=14), 90, 590, t - ta)
        if t > tq:
            pop(L, keycap('Q', 'yellow', 44, pad=14), 90, 850, t - tq)
    # ---- A models (A3 A4 A5 A6) and Q models (Q3 Q5 Q7 Q8)
    for seq, letter, t0, t1 in ((A_SEQ, 'A', ph('A is') - 0.1, ph('while Q') - 0.1), (Q_SEQ, 'Q', ph('while Q') - 0.1, ph('and the higher') - 0.1)):
        if t0 <= t < t1:
            k = current(seq, t)
            first = ph(seq[1][1]) - 0.1 if letter == 'A' else ph('smaller')
            num = k[1] if t >= (ph('A3') - 0.1 if letter == 'A' else ph('Q3') - 0.1) else '?'
            boxes = bar(L, t, [(letter, 'yellow', 100), (num, 'dark' if num != '?' else 'ghost', 100)], y=BAR_Y, t0=t0, hi=(0, t0 + 0.15))
            # the number key flips each time a new model is named
            for key, p in seq:
                if abs(t - (ph(p) - 0.1)) < 0.25 and key == k and t > t0 + 0.3:
                    ellipse_draw(L, boxes[1][0], boxes[1][1], boxes[1][2] / 2 + 24, boxes[1][3] / 2 + 20, t - ph(p) + 0.1)
    # ---- higher number = bigger and more luxurious
    t0, t1 = ph('and the higher') - 0.1, ph('so an A3') - 0.1
    if t0 <= t < t1:
        th = ph('higher')
        act = None if t < th else min(5, int((t - th) / 0.28))
        stairs(L, t, t0 + 0.1, act, x0=250, y0=780, sw=88, labels=('3', '4', '5', '6', '7', '8'))
        if t > ph('luxurious'):
            drop(L, icon('crown', 120), 250 + 5 * 96 + 44, 780 - (60 + 5 * 55) - 90, t - ph('luxurious'), from_y=-150)
            for i, (x, y) in enumerate([(720, 380), (860, 450), (600, 470)]):
                tw = 0.6 + 0.4 * math.sin(t * 7 + i * 2)
                pop(L, icon('sparkle', int(50 * tw) + 10), x, y, t - ph('luxurious') - i * 0.06)
    # ---- A3 vs A6, Q5 vs Q8 (true scale, rears aligned)
    for a, b, start, end in (('A3', 'A6', 'so an A3', 'and a Q5'), ('Q5', 'Q8', 'and a Q5', 'but the name')):
        t0, t1 = ph(start) - 0.1, ph(end) - 0.1
        if t0 <= t < t1:
            bar(L, t, [(a, 'yellow', 84), ('<', 'ghost', 84), (b, 'yellow', 84)], y=BAR_Y, t0=t0, gap=24)
            tc = ph('smaller than') if a == 'A3' else ph('sits below')
            if t > tc:
                x0 = 150 + CAR_META[a]['L'] * 0.12
                x1 = 150 + CAR_META[b]['L'] * 0.12
                d = ImageDraw.Draw(L)
                p = ease_out(clamp01((t - tc) / 0.3))
                yb = 640 + (900 - 640) * p
                for y in range(560, int(yb), 22):           # dashed line down from the smaller car's nose
                    d.line([(x0, y), (x0, min(y + 12, yb))], fill=RED, width=5)
                if p >= 1:
                    arrow_draw(L, (x0 + 4, 925), (x1 + 2, 925), t - tc - 0.3, col=RED, width=8)
    # ---- add an S
    t0, t1 = ph('but the name') - 0.1, ph('and RS takes') - 0.1
    if t0 <= t < t1:
        tS, tS3 = ph('add an S'), ph('S3', 1) - 0.05
        keys = [('A', 'ghost' if t > tS else 'yellow', 100), ('3', 'dark', 100)] if t < tS else [('S', 'red', 100), ('3', 'dark', 100)]
        boxes = bar(L, t, keys, y=BAR_Y, t0=t0)
        if t > tS:
            ellipse_draw(L, boxes[0][0], boxes[0][1], boxes[0][2] / 2 + 28, boxes[0][3] / 2 + 24, t - tS)
        flash(L, CX, GY - 120, t - tS3)
        v = 0.25 if t < tS3 else 0.25 + 0.4 * ease_out(clamp01((t - tS3) / 0.5))
        if t > ph('more performance') - 0.2:
            gauge(L, 900, 520, 90, v + 0.02 * math.sin(t * 40))
    # ---- RS = RennSport
    t0, t1 = ph('and RS takes') - 0.1, ph('so the A3') - 0.1
    if t0 <= t < t1:
        boxes = bar(L, t, [('R', 'red', 100), ('S', 'red', 100)], y=BAR_Y, t0=t0, gap=40)
        tr = ph('RennSport')
        if t > tr:
            pop(L, tag('RENN', bg=RED, size=34), boxes[0][0], 420, t - tr)
            pop(L, tag('SPORT', bg=RED, size=34), boxes[1][0], 420, t - tr - 0.3)
        if t > ph('German'):
            pop(L, flag_de(150), 150, 480, t - ph('German'))
    # ---- A3 -> S3 -> RS3
    t0, t1 = ph('so the A3') - 0.1, ph('and the same') - 0.1
    if t0 <= t < t1:
        ts3, trs = ph('S3', 2) - 0.05, ph('RS3') - 0.05
        lev = 0 if t < ts3 else (1 if t < trs else 2)
        keys = [('A3', 'yellow' if lev == 0 else 'ghost', 74), ('S3', 'red' if lev == 1 else 'ghost', 74), ('RS 3', 'red' if lev == 2 else 'ghost', 74)]
        boxes = bar(L, t, keys, y=BAR_Y, t0=t0, gap=60)
        for i in range(2):
            if lev > i:
                arrow_draw(L, (boxes[i][0] + boxes[i][2] / 2 + 6, BAR_Y), (boxes[i + 1][0] - boxes[i + 1][2] / 2 - 6, BAR_Y), t - [ts3, trs][i], width=7)
        bx = boxes[lev]
        ellipse_draw(L, bx[0], bx[1], bx[2] / 2 + 24, bx[3] / 2 + 20, t - [t0 + 0.2, ts3, trs][lev])
        flash(L, CX, GY - 120, t - ts3)
        flash(L, CX, GY - 120, t - trs)
        gauge(L, 900, 520, 90, [0.25, 0.6, 0.93][lev] + 0.02 * math.sin(t * 40))
    # ---- same idea for SUVs: Q8 -> RS Q8
    t0, t1 = ph('and the same') - 0.1, ph('then the letters') - 0.1
    if t0 <= t < t1:
        tq = ph('SUVs') - 0.05
        keys = [('Q8', 'yellow' if t < tq else 'ghost', 80), ('RS Q8', 'red' if t >= tq else 'ghost', 80)]
        boxes = bar(L, t, keys, y=BAR_Y, t0=t0, gap=80)
        if t >= tq:
            arrow_draw(L, (boxes[0][0] + boxes[0][2] / 2 + 6, BAR_Y), (boxes[1][0] - boxes[1][2] / 2 - 6, BAR_Y), t - tq, width=7)
            ellipse_draw(L, boxes[1][0], boxes[1][1], boxes[1][2] / 2 + 24, boxes[1][3] / 2 + 20, t - tq)
        flash(L, CX, GY - 130, t - tq)
    # ---- letters at the end: what's under the hood
    t0, t1 = ph('then the letters') - 0.1, ph('TFSI is') - 0.1
    if t0 <= t < t1:
        boxes = bar(L, t, [('Q5', 'ghost', 80), ('40', 'ghost', 80), ('????', 'dark', 80)], y=BAR_Y, t0=t0)
        if t > ph('at the end'):
            ellipse_draw(L, boxes[2][0], boxes[2][1], boxes[2][2] / 2 + 26, boxes[2][3] / 2 + 22, t - ph('at the end'))
        if t > ph('under the hood') - 0.2:
            s = ease_back(clamp01((t - ph('under the hood') + 0.2) / 0.35))
            if s > 0.05:
                engine_anim(L, 540, 660, 0.9 * s, t)
    # ---- TFSI / TDI
    for p0, p1, lab, col, nm, key in (('TFSI is', 'TDI is', 'TFSI', (30, 170, 100), 'P', 'A5'), ('TDI is', 'TFSI e', 'TDI', (40, 40, 40), 'D', 'A6')):
        t0, t1 = ph(p0) - 0.1, ph(p1) - 0.1
        if t0 <= t < t1:
            bar(L, t, [(key, 'ghost', 70), ('40', 'ghost', 70), (lab, 'dark', 90)], y=BAR_Y, t0=t0, hi=(2, t0 + 0.1))
            pop(L, pump(col, nm, 170), 150, 520, t - ph('petrol' if lab == 'TFSI' else 'diesel'))
    # ---- TFSI e (plug-in hybrid)
    t0, t1 = ph('TFSI e') - 0.1, ph('and e-tron') - 0.1
    if t0 <= t < t1:
        bar(L, t, [('A5', 'ghost', 70), ('TFSI e', 'teal', 90)], y=BAR_Y, t0=t0, hi=(1, t0 + 0.1))
        plug_in(L, t, cars, 'A5EH', ph('plug-in') - 0.3)
        if t > ph('hybrid') - 0.1:
            engine_anim(L, 800, 450, 0.45, t)
    # ---- e-tron (electric)
    t0, t1 = ph('and e-tron') - 0.1, ph('quattro is') - 0.1
    if t0 <= t < t1:
        bar(L, t, [('Q6', 'ghost', 70), ('e-tron', 'green', 90)], y=BAR_Y, t0=t0, hi=(1, ph('e-tron')))
        plug_in(L, t, cars, 'Q6E', ph('fully') - 0.35, front=True)
        for i in range(2):
            if t > ph('electric') and (t * 4 + i) % 3 < 1.2:
                b = icon('bolt', 90)
                paste_clip(L, b, int(700 + i * 160), int(400 + 10 * math.sin(t * 9 + i)))
    # ---- quattro
    t0, t1 = ph('quattro is') - 0.1, ph('so an RS') - 0.1
    if t0 <= t < t1:
        bar(L, t, [('quattro', 'teal', 90)], y=BAR_Y, t0=t0, hi=(0, ph('quattro', 1)))
        chassis(L, t, t0 + 0.1, ph('all-wheel-drive') - 0.05, cy=620)
    # ---- recap: RS Q8 TFSI quattro
    t0, t1 = ph('so an RS') - 0.1, ph('and if you') - 0.05
    if t0 <= t < t1:
        labs = [('RS', 'red', ph('high-performance')), ('Q8', 'yellow', ph('Q8 SUV')), ('TFSI', 'dark', ph('petrol-powered')),
                ('quattro', 'teal', ph('all-wheel drive'))]
        keys = [(l, s if t > tt else 'ghost', 70) for l, s, tt in labs]
        boxes = bar(L, t, keys, y=BAR_Y, t0=t0, gap=14)
        cur = None
        for i, (l, s, tt) in enumerate(labs):
            if t > tt:
                cur = (i, tt)
        if cur:
            bx = boxes[cur[0]]
            ellipse_draw(L, bx[0], bx[1], bx[2] / 2 + 22, bx[3] / 2 + 18, t - cur[1])
        if t > ph('high-performance'):
            v = clamp01((t - ph('high-performance')) / 0.5)
            gauge(L, 170, 520, 85, 0.2 + 0.73 * ease_out(v) + 0.02 * math.sin(t * 40))
        if t > ph('petrol-powered'):
            pop(L, pump((30, 170, 100), 'P', 130), 910, 500, t - ph('petrol-powered'))
    if t >= ph('and if you') - 0.05 and t < END - 0.25:
        C.cheat_sheet(L, t - ph('and if you') + 0.05)


BG = None


def render(t, fi):
    global BG
    if BG is None:
        BG = make_background().convert('RGBA')
        build()
        SHAKES.clear()
        SHAKES.extend([(ph('S3', 1) - 0.05, 0.3, 7), (ph('RS3') - 0.05, 0.35, 8), (ph('SUVs') - 0.05, 0.35, 8), (ph('and RS takes') - 0.1, 0.4, 6)])
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
