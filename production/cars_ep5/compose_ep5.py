"""Episode 5: "Every Mercedes model explained in one minute" (A/B/C/E/S, GL SUVs, G, CL coupes, SL, AMG GT).
House rules: explain once (voice + one visual, no sentence cards), cars always moving, true scale,
yellow captions, full-body character, light sound effects.

usage: python3 compose_ep5.py [--frames t,t,...]
"""
import math, os, subprocess, sys, functools
from PIL import Image, ImageDraw

import compose as C
import compose2 as V
from compose import (W, H, FPS, ease_out, ease_back, font, INK, YEL, WHITE, RED, keycap, tag, stamp, icon, paste_clip, pop,
                     CAR_META, draw_caption, draw_header, draw_character, make_background, B, END)
from compose2 import (draw_car, seg as _seg, SEGS, seg_state, draw_cars, speed_lines, ground_line, hill, sun_rays, drop, ellipse_draw,
                      arrow_draw, gauge, stopwatch, bar, lerp, clamp01, ease_in, draw_puffs, mountains_road, race_track, SHAKES,
                      shake_offset)
from compose_amg import stairs
from compose_audi import flash, car_of

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


def rear_aligned(key, t0, y, sc, rear=150):
    return [(t0, rear + CAR_META[key]['L'] * sc / 2, y, sc)]


@functools.lru_cache(None)
def star_logo(size=230):
    """Generic three-pointed star in a ring (chrome)."""
    S = 3
    s = size * S
    im = Image.new('RGBA', (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    c = s / 2
    for i, (col, w) in enumerate([((40, 42, 46), 30), ((225, 229, 234), 18), ((150, 156, 164), 6)]):
        d.ellipse((12 + i * 6, 12 + i * 6, s - 12 - i * 6, s - 12 - i * 6), outline=col, width=w)
    R = s / 2 - 34
    for k in range(3):
        a = -math.pi / 2 + k * 2 * math.pi / 3
        tip = (c + R * math.cos(a), c + R * math.sin(a))
        l = (c + 0.16 * R * math.cos(a + 2.2), c + 0.16 * R * math.sin(a + 2.2))
        r = (c + 0.16 * R * math.cos(a - 2.2), c + 0.16 * R * math.sin(a - 2.2))
        d.polygon([tip, l, (c, c)], fill=(235, 238, 242), outline=(60, 64, 70))
        d.polygon([tip, r, (c, c)], fill=(160, 166, 174), outline=(60, 64, 70))
    return im.resize((size, size), Image.LANCZOS)


# ----------------------------------------------------------------- timeline
SALOONS = [('A35', 'the A Class', 'A'), ('B', 'while the B', 'B'), ('C300', 'move up', 'C'), ('E', 'the E Class', 'E'), ('S', 'and the S Class', 'S')]
SUVS = [('GLA', 'the GLA', 'A'), ('GLB', 'GLB', 'B'), ('GLC63', 'GLC', 'C'), ('GLE53', 'GLE', 'E'), ('GLS', 'GLS', 'S')]
RECAP = [('A35', 'entry-level'), ('S', 'flagship saloon'), ('GLS', 'an SUV'), ('CLE', 'a coupe'), ('GT', 'a sports')]


def build():
    SEGS.clear()
    seg('S', 0.0, ph('Mercedes uses') - 0.15, enter='none')
    # the letters: five saloons stacked small at true scale
    t = ph('Mercedes uses') - 0.1
    for i, (k, _, _) in enumerate(SALOONS):
        seg(k, t + i * 0.08, ph('the A Class') - 0.12 + i * 0.02, kf=rear_aligned(k, t + i * 0.08, 470 + i * 105, 0.085))
    for i, (k, p, _) in enumerate(SALOONS):
        end = ph(SALOONS[i + 1][1]) - 0.12 if i + 1 < len(SALOONS) else ph('but the same') - 0.12
        seg(k, ph(p) - 0.1, end)
        if k == 'S':
            SEGS[-1]['shine_at'] = ph('luxurious')
    # saloon turns into an SUV
    seg('C300', ph('but the same') - 0.1, ph('the GLA', 1) - 0.12, swaps=[(ph('SUVs', 1) - 0.05, 'GLC63')])
    # GL + letter: each SUV drives through as it's named
    for i, (k, p, _) in enumerate(SUVS):
        end = ph(SUVS[i + 1][1]) - 0.12 if i + 1 < len(SUVS) else ph('following') - 0.12
        seg(k, ph(p) - 0.1, end)
    # size order: GLA vs GLS, rears aligned
    t0 = ph('the GLA is') - 0.1
    seg('GLA', t0, ph('the G Class') - 0.12, kf=rear_aligned('GLA', t0, 640, 0.12))
    seg('GLS', ph('while the GLS') - 0.1, ph('the G Class') - 0.1, kf=rear_aligned('GLS', ph('while the GLS') - 0.1, 900, 0.12))
    # G-Class climbs
    tg, tg2 = ph('the G Class') - 0.1, ph("then there's CL") - 0.12
    y0, y1 = GY + 80, GY - 110
    yl = lambda x: lerp(y0, y1, x / W)
    seg('G63', tg, tg2, kf=[(tg, CX - 120, yl(CX - 120), SC), (tg2, CX + 60, yl(CX + 60), SC)],
        mod=lambda t: (0, 0, math.degrees(math.atan2(y0 - y1, W)), 1))
    seg('CLA', ph("then there's CL") - 0.1, ph('and the CLE') - 0.12)
    seg('CLE', ph('and the CLE') - 0.1, ph('the SL') - 0.12)
    seg('SL', ph('the SL') - 0.1, ph('while the AMG') - 0.12)
    seg('GT', ph('while the AMG') - 0.1, ph('so the letters') - 0.12, burnout=True)
    # recap: one car that changes with each word
    t0 = ph('so the letters') - 0.1
    seg('A35', t0, ph('and if you') - 0.05, swaps=[(ph(p) - 0.05, k) for k, p in RECAP[1:]])


# ----------------------------------------------------------------- hook
def hook(L, t):
    t_grid, t_back = ph('model') + 0.1, ph('Mercedes uses') - 0.15
    order = ['A35', 'B', 'C300', 'CLA', 'E', 'CLE', 'GLA', 'GLB', 'GLC63', 'GLE53', 'GLS', 'G63', 'SL', 'GT']
    cols, cell_w, cell_h, gx0, gy0 = 3, 340, 100, 30, 370
    pos = {k: (gx0 + (i % cols) * cell_w + cell_w / 2, gy0 + (i // cols) * cell_h + 100) for i, k in enumerate(order)}
    hero = (gx0 + 2 * cell_w + cell_w / 2, gy0 + 4 * cell_h + 100)
    gsc = 0.054
    p = 1.0 if t < t_grid else 1 - ease_out((t - t_grid) / 0.4)
    cx, gy, sc = lerp(hero[0], CX, p), lerp(hero[1], GY, p), lerp(gsc, SC, p)
    if t < t_grid:
        speed_lines(L, t, 400, GY - 20, 0.9)
        ground_line(L, t, GY)
    info = draw_car(L, 'S', cx, gy, sc, travel=V.CRUISE * t)
    if p > 0.6:
        draw_puffs(L, info['rear'][0] - 20, info['rear'][1] - 8, t, -1, alpha=0.4, size=(14, 34), seed=99)
    if t >= t_grid:
        for i, k in enumerate(order):
            ta = t_grid + 0.15 + i * 0.03
            if t < ta:
                continue
            sck = gsc * ease_back(clamp01((t - ta) / 0.25))
            if sck > 0.01:
                draw_car(L, k, pos[k][0], pos[k][1], sck, travel=V.CRUISE * t)
    lg = star_logo(210)
    tl = clamp01(t / 0.4)
    lx = lerp(W + 300, W / 2, ease_out(tl))
    ly = 270 if t < t_grid else lerp(270, 250, ease_out((t - t_grid) / 0.3))
    im = lg if tl >= 1 else lg.resize((int(lg.width * (1 + 1.0 * (1 - tl))), lg.height))
    paste_clip(L, im, int(lx - im.width / 2), int(ly - im.height / 2))
    if tl >= 1:
        ellipse_draw(L, lx, ly, 140, 130, t - 0.45)
    if ph('one minute') - 0.1 <= t:
        stopwatch(L, 930, 300, 54, t - ph('one minute'))


# ----------------------------------------------------------------- scenes
def scene_layer(t):
    L = Image.new('RGBA', (W, 1000), (0, 0, 0, 0))
    if ph('the G Class') - 0.1 <= t < ph("then there's CL") - 0.1:
        hill(L, GY + 80, GY - 110)
    if ph('the SL') - 0.1 <= t < ph('while the AMG') - 0.1:
        mountains_road(L, t, GY)
    if ph('while the AMG') - 0.1 <= t < ph('so the letters') - 0.1:
        race_track(L, t, GY)
    if ph('and the S Class') - 0.1 <= t < ph('but the same') - 0.1 and t > ph('flagship'):
        sun_rays(L, CX, GY - 120, t, 0.6)
    stacked = (ph('Mercedes uses') - 0.1 <= t < ph('the A Class') - 0.1) or (ph('the GLA is') - 0.1 <= t < ph('the G Class') - 0.1)
    quiet = (ph('the G Class') - 0.1 <= t < ph("then there's CL") - 0.1) or \
            (ph('following') - 0.1 <= t < ph('the GLA is') - 0.1)
    roads = (ph('the SL') - 0.1 <= t < ph('so the letters') - 0.1)
    active = [s for s in SEGS if seg_state(s, t)]
    if t >= ph('Mercedes uses') - 0.15 and active and not quiet:
        k = max(seg_state(s, t)['lines'] for s in active)
        speed_lines(L, t, 400, GY - 20, k)
        if not roads and not stacked:
            ground_line(L, t, GY)
    if t < ph('Mercedes uses') - 0.15:
        hook(L, t)
    cars = draw_cars(L, t) if t >= ph('Mercedes uses') - 0.15 else {}
    beats(L, t, cars)
    return L


def cur_idx(seq, t, k=1):
    i = 0
    for j, item in enumerate(seq):
        if t >= ph(item[k]) - 0.1:
            i = j
    return i


def height_arrow(L, t, t0, info, key):
    hgt = CAR_META[key]['Hmm'] * SC
    x = min(info['x0'] + info['w'] + 30, 1040)
    arrow_draw(L, (x, GY), (x, GY - hgt), t - t0, col=(80, 84, 90), width=6)


def beats(L, t, cars):
    # ---- letters show where each car sits: A B C E S stacked
    t0, t1 = ph('Mercedes uses') - 0.1, ph('the A Class') - 0.1
    if t0 <= t < t1:
        boxes = bar(L, t, [(l, 'yellow', 66) for _, _, l in SALOONS], y=BAR_Y, t0=t0, gap=18)
        tl = ph('letters')
        for i, (k, _, l) in enumerate(SALOONS):
            if t > tl + i * 0.12:
                pop(L, keycap(l, 'yellow', 40, pad=12), 80, 470 + i * 105 - 30, t - tl - i * 0.12)
        if t > ph('lineup'):
            ellipse_draw(L, W / 2, BAR_Y, (boxes[-1][0] - boxes[0][0]) / 2 + 80, 70, t - ph('lineup'))
    # ---- A, B, C, E, S one by one
    t0, t1 = ph('the A Class') - 0.1, ph('but the same') - 0.1
    if t0 <= t < t1:
        i = cur_idx(SALOONS, t)
        keys = [(l, 'yellow' if j == i else ('dark' if j < i else 'ghost'), 72) for j, (_, _, l) in enumerate(SALOONS)]
        boxes = bar(L, t, keys, y=BAR_Y, t0=t0, gap=16)
        ti = ph(SALOONS[i][1]) - 0.1
        bx = boxes[i]
        ellipse_draw(L, bx[0], bx[1], bx[2] / 2 + 24, bx[3] / 2 + 20, t - ti)
        c = car_of(cars, SALOONS[i][0])
        if SALOONS[i][0] == 'B' and c and t > ph('taller'):
            height_arrow(L, t, ph('taller'), c[2], 'B')
        if SALOONS[i][0] == 'S' and c and t > ph('flagship'):
            _, st, info = c
            drop(L, icon('crown', 140), st['cx'] - 40, info['top'] - 50, t - ph('flagship'), from_y=-150)
    # ---- same letters become SUVs: GL goes in front
    t0, t1 = ph('but the same') - 0.1, ph('the GLA', 1) - 0.1
    if t0 <= t < t1:
        tgl = ph('put GL')
        x_shift = 0 if t < tgl - 0.15 else ease_out(clamp01((t - tgl + 0.15) / 0.2))
        keys = [(l, 'yellow', 66) for _, _, l in SALOONS]
        boxes = bar(L, t, keys, y=BAR_Y + 150 * x_shift, t0=t0 - 5, gap=18)
        if t > tgl:
            pop(L, keycap('GL', 'dark', 90), W / 2, BAR_Y - 20, t - tgl)
            for b in boxes:
                arrow_draw(L, (W / 2, BAR_Y + 45), (b[0], b[1] - b[3] / 2 - 6), t - tgl - 0.25, width=5)
    # ---- GLA GLB GLC GLE GLS
    t0, t1 = ph('the GLA', 1) - 0.1, ph('following') - 0.1
    if t0 <= t < t1:
        i = cur_idx(SUVS, t)
        boxes = bar(L, t, [('GL', 'dark', 84), (SUVS[i][2], 'yellow', 84)], y=BAR_Y, t0=t0)
        ellipse_draw(L, boxes[1][0], boxes[1][1], boxes[1][2] / 2 + 24, boxes[1][3] / 2 + 20, t - ph(SUVS[i][1]) + 0.1)
    # ---- similar size order: staircase A..S
    t0, t1 = ph('following') - 0.1, ph('the GLA is') - 0.1
    if t0 <= t < t1:
        ts = ph('size order') - 0.2
        act = None if t < ts else min(4, int((t - ts) / 0.2))
        stairs(L, t, t0, act, x0=285, y0=760, sw=95, labels=('GLA', 'GLB', 'GLC', 'GLE', 'GLS'))
    # ---- GLA smallest vs GLS top
    t0, t1 = ph('the GLA is') - 0.1, ph('the G Class') - 0.1
    if t0 <= t < t1:
        bar(L, t, [('GLA', 'yellow', 76), ('<', 'ghost', 76), ('GLS', 'yellow' if t > ph('while the GLS') - 0.1 else 'ghost', 76)], y=BAR_Y, t0=t0, gap=24)
        if t > ph('top of'):
            x0 = 150 + CAR_META['GLA']['L'] * 0.12
            x1 = 150 + CAR_META['GLS']['L'] * 0.12
            d = ImageDraw.Draw(L)
            p = ease_out(clamp01((t - ph('top of')) / 0.3))
            yb = 640 + (900 - 640) * p
            for y in range(560, int(yb), 22):
                d.line([(x0, y), (x0, min(y + 12, yb))], fill=RED, width=5)
            if p >= 1:
                arrow_draw(L, (x0 + 4, 925), (x1 + 2, 925), t - ph('top of') - 0.3, col=RED, width=8)
        if t > ph('closer to'):
            pop(L, keycap('S', 'yellow', 56), 900, 470, t - ph('closer to'))
            if t > ph('closer to') + 0.2:
                drop(L, icon('crown', 100), 900, 395, t - ph('closer to') - 0.2, from_y=-150)
    # ---- G-Class
    t0, t1 = ph('the G Class') - 0.1, ph("then there's CL") - 0.1
    if t0 <= t < t1:
        boxes = bar(L, t, [('G', 'dark', 110)], y=BAR_Y, t0=t0, hi=(0, ph('the G Class')))
        if t > ph('G Wagon') - 0.1:
            pop(L, keycap('G-WAGON', 'dark', 50), 820, 430, t - ph('G Wagon') + 0.1)
    # ---- CL = coupe-style
    t0, t1 = ph("then there's CL") - 0.1, ph('like the CLA') - 0.15
    if t0 <= t < t1:
        bar(L, t, [('CL', 'blue', 120)], y=BAR_Y + 40, t0=t0, hi=(0, ph('CL', 1)))
    t0, t1 = ph('like the CLA') - 0.15, ph('and the CLE') - 0.1
    if t0 <= t < t1:
        bar(L, t, [('CL', 'blue', 90), ('A', 'yellow', 90)], y=BAR_Y, t0=t0)
        c = car_of(cars, 'CLA')
        if c and t > ph('coupe', 1):
            _, st, info = c
            x0, top, w = info['x0'], info['top'], info['w']
            arrow_draw(L, (x0 + w * 0.6, top + 6), (x0 + w * 0.08, top + 120), t - ph('coupe', 1), col=RED, width=9)
        if c and t > ph('four-door'):
            _, st, info = c
            ellipse_draw(L, info['x0'] + info['w'] * 0.43, info['top'] + 110, 210, 75, t - ph('four-door'))
    # ---- CLE replaces C and E coupes
    t0, t1 = ph('and the CLE') - 0.1, ph('the SL') - 0.1
    if t0 <= t < t1:
        tr = ph('replaces')
        if t < tr:
            bar(L, t, [('CL', 'blue', 90), ('E', 'yellow', 90)], y=BAR_Y, t0=t0)
        else:
            boxes = bar(L, t, [('C', 'ghost', 70), ('E', 'ghost', 70), ('CLE', 'blue', 80)], y=BAR_Y, t0=tr - 5, gap=40)
            d = ImageDraw.Draw(L)
            for i in range(2):
                q = clamp01((t - ph('C and') - i * 0.25) / 0.2)
                if q > 0:
                    bx = boxes[i]
                    d.line([(bx[0] - 40, BAR_Y + 38), (bx[0] - 40 + 80 * q, BAR_Y - 38)], fill=RED, width=10)
            arrow_draw(L, (boxes[1][0] + 40, BAR_Y), (boxes[2][0] - boxes[2][2] / 2 - 6, BAR_Y), t - ph('Class coupes'), width=7)
            if t > ph('convertibles'):
                ellipse_draw(L, boxes[2][0], boxes[2][1], boxes[2][2] / 2 + 24, boxes[2][3] / 2 + 20, t - ph('convertibles'))
    # ---- SL roadster
    t0, t1 = ph('the SL') - 0.1, ph('while the AMG') - 0.1
    if t0 <= t < t1:
        bar(L, t, [('SL', 'red', 110)], y=BAR_Y, t0=t0, hi=(0, ph('SL', 1)))
        c = car_of(cars, 'SL')
        if c and t > ph('roadster'):
            _, st, info = c
            ellipse_draw(L, info['x0'] + info['w'] * 0.42, info['top'] + 40, 170, 60, t - ph('roadster'))
    # ---- AMG GT
    t0, t1 = ph('while the AMG') - 0.1, ph('so the letters') - 0.1
    if t0 <= t < t1:
        bar(L, t, [('AMG', 'red', 86), ('GT', 'red', 86)], y=BAR_Y, t0=t0, hi=(1, ph('GT', 1)))
        if t > ph('performance') - 0.1:
            v = clamp01((t - ph('performance') + 0.1) / 0.6)
            gauge(L, 900, 500, 90, 0.1 + 0.85 * ease_out(v) + 0.02 * math.sin(t * 50))
    # ---- recap: the letter for each kind of car
    t0, t1 = ph('so the letters') - 0.1, ph('and if you') - 0.05
    if t0 <= t < t1:
        labs = [('A', 'entry-level'), ('S', 'flagship saloon'), ('GLS', 'an SUV'), ('CLE', 'a coupe'), ('GT', 'a sports')]
        i = -1
        for j, (_, p) in enumerate(labs):
            if t >= ph(p) - 0.05:
                i = j
        keys = [(l, 'yellow' if j == i else ('dark' if j < i else 'ghost'), 56) for j, (l, _) in enumerate(labs)]
        boxes = bar(L, t, keys, y=BAR_Y, t0=t0, gap=12)
        if i >= 0:
            bx = boxes[i]
            ellipse_draw(L, bx[0], bx[1], bx[2] / 2 + 20, bx[3] / 2 + 16, t - ph(labs[i][1]) + 0.05)
            flash(L, CX, GY - 120, t - ph(labs[i][1]) + 0.05)
    if t >= ph('and if you') - 0.05 and t < END - 0.25:
        C.cheat_sheet(L, t - ph('and if you') + 0.05)


BG = None


def render(t, fi):
    global BG
    if BG is None:
        BG = make_background().convert('RGBA')
        build()
        SHAKES.clear()
        SHAKES.extend([(ph('put GL'), 0.25, 6), (ph('while the AMG') - 0.1, 0.4, 6), (ph('replaces'), 0.25, 6)])
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
