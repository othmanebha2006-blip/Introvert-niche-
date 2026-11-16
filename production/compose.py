"""Compose episode 1 ("Your boyfriend wants to hang out") from renders + character cutouts + voice."""
import os, sys, subprocess, json, re
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

S = os.path.dirname(os.path.abspath(__file__))
R = os.path.join(S, 'renders'); C = os.path.join(S, 'chars', 'cut'); F = os.path.join(S, 'fonts')
W, H, FPS = 1080, 1920, 30
PAD = 1.08                       # stills are composed this much larger, for the slow push-in
ZOOM = 0.05                      # 5 % push-in over each shot
ONLY = os.environ.get('ONLY')    # render a single shot index for previews
END = 61.8

# ------------------------------------------------------------------ script (from the voice track)
SEG = [
    (0.12, 1.83, "Your boyfriend wants to hang out."),
    (2.11, 2.92, "You don't."),
    (3.55, 5.13, "You have nothing going on."),
    (6.04, 7.40, "You say you have laundry."),
    (7.87, 8.81, "He says he'll help."),
    (9.15, 10.03, "He likes folding."),
    (10.50, 12.23, "Of fucking course he does."),
    (13.15, 14.57, "You say you have a headache."),
    (14.88, 15.79, "He has Advil"),
    (16.09, 16.81, "in his pocket."),
    (17.40, 17.96, "Why?"),
    (18.84, 20.62, "You say your cousin's in town."),
    (21.12, 22.35, "He'd love to meet him."),
    (22.91, 24.33, "Does he ever give up?"),
    (25.28, 27.02, "You say you have to wash your hair."),
    (27.52, 28.91, "It takes four hours."),
    (29.76, 30.57, "He brought a book."),
    (31.26, 33.07, "When will he take the fucking hint?"),
    (33.88, 35.50, "You are out of excuses."),
    (35.96, 37.61, "You have never run out before."),
    (38.11, 39.66, "You once got out of a wedding."),
    (40.12, 41.03, "You were in it."),
    (42.04, 43.47, "So you tell him the truth."),
    (44.09, 45.13, "\"I just don't want to.\""),
    (45.88, 46.51, "He says,"),
    (46.72, 47.08, "\"Oh."),
    (47.36, 47.88, "Okay.\""),
    (48.48, 49.23, "And leaves."),
    (49.60, 50.35, "Immediately."),
    (51.13, 52.07, "You stand there."),
    (52.70, 54.31, "Now you kinda wanna hang out."),
    (54.81, 55.50, "You call him."),
    (56.03, 57.16, "He's doing laundry."),
    (58.33, 60.59, "Send this to someone who has nothing going on."),
]

# ------------------------------------------------------------------ shot list
# wide:  ('wide', [ (cutout, centre_x_frac, feet_y_frac, height_frac, flip), ... ])
# cu:    ('cu', bg, cutout, crop_bottom_frac, width_frac, top_frac, centre_x_frac)
# prop:  ('prop', prop_render, bg_hex, scale)
GF, BF = 'gf_ref_0', 'bf_ref_0'
WIDE_GF = (GF, 0.68, 0.79, 0.46, False)
WIDE_BF = (BF, 0.32, 0.79, 0.475, False)
SHOTS = [
    (0.00, ('wide', [WIDE_BF, WIDE_GF])),                                    # Your boyfriend wants to hang out.
    (2.00, ('cu', 'room_cu_a', GF, 0.56, 1.10, 0.15, 0.50)),                 # You don't. / nothing going on
    (5.90, ('prop', 'prop_basket', '#7AAAE0', 1.15)),                        # laundry
    (7.75, ('cu', 'room_cu_b', 'bf_happy', 0.50, 1.15, 0.14, 0.50)),         # he'll help, likes folding
    (10.45, ('cu', 'room_cu_a', 'gf_5', 1.0, 0.95, 0.24, 0.50)),             # of fucking course he does
    (13.00, ('cu', 'room_med', GF, 1.0, 0.62, 0.20, 0.52)),                  # headache
    (14.75, ('prop', 'prop_pills', '#D9DEE6', 0.95)),                        # Advil in his pocket
    (17.25, ('cu', 'room_cu_a', 'gf_6', 1.0, 0.95, 0.24, 0.50)),             # Why?
    (18.65, ('wide', [WIDE_BF, WIDE_GF])),                                   # cousin's in town
    (20.95, ('cu', 'room_med', 'bf_13', 1.0, 0.78, 0.16, 0.50)),             # he'd love to meet him (waving)
    (22.75, ('cu', 'room_cu_a', 'gf_7', 1.0, 0.95, 0.24, 0.50)),             # does he ever give up?
    (25.10, ('prop', 'prop_shampoo', '#7AAAE0', 1.15)),                      # wash hair, four hours
    (29.60, ('prop', 'prop_book', '#D9DEE6', 1.15)),                         # he brought a book
    (31.10, ('cu', 'room_cu_a', 'gf_5', 1.0, 0.95, 0.24, 0.50)),             # fucking hint
    (33.70, ('cu', 'room_med', GF, 1.0, 0.62, 0.20, 0.52)),                  # out of excuses
    (37.95, ('prop', 'prop_cake', '#7AAAE0', 0.95)),                         # got out of a wedding
    (39.95, ('cu', 'room_cu_a', GF, 0.56, 1.10, 0.15, 0.50)),                # you were in it
    (41.85, ('wide', [WIDE_BF, WIDE_GF])),                                   # tell him the truth
    (45.70, ('cu', 'room_cu_b', BF, 0.50, 1.15, 0.14, 0.50)),                # he says,
    (46.60, ('cu', 'room_cu_b', 'bf_surprised', 0.50, 1.15, 0.14, 0.50)),    # oh. okay.
    (48.30, ('wide', [('bf_12', 0.20, 0.79, 0.46, True), WIDE_GF])),         # and leaves. immediately.
    (50.95, ('wide', [WIDE_GF])),                                            # you stand there
    (52.55, ('cu', 'room_cu_a', 'gf_soft', 0.56, 1.10, 0.15, 0.50)),         # now you kinda wanna hang out
    (54.65, ('prop', 'prop_phone', '#7AAAE0', 0.95)),                        # you call him
    (55.90, ('void', 'prop_basket', 'bf_14')),                               # he's doing laundry
    (58.15, ('cu', 'room_cu_a', GF, 0.48, 1.25, 0.12, 0.50)),                # send this...
]

_cache = {}


def load(path):
    if path not in _cache:
        _cache[path] = Image.open(path).convert('RGBA')
    return _cache[path]


def char(name):
    return load(os.path.join(C, name + '.png'))


def hexrgb(h):
    h = h.lstrip('#'); return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def sharpen(im):
    return im.filter(ImageFilter.UnsharpMask(radius=2, percent=60, threshold=2))


def contact_shadow(canvas, cx, y, w):
    sh = Image.new('L', canvas.size, 0); d = ImageDraw.Draw(sh)
    d.ellipse((cx - w / 2, y - w * 0.06, cx + w / 2, y + w * 0.06), fill=120)
    sh = sh.filter(ImageFilter.GaussianBlur(w * 0.05))
    dark = Image.new('RGBA', canvas.size, (20, 20, 35, 255)); dark.putalpha(sh)
    canvas.alpha_composite(dark)


def place(canvas, im, x, y, scale):
    im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.LANCZOS)
    if scale > 1.2:
        im = sharpen(im)
    canvas.alpha_composite(im, (int(x), int(y)))


def compose_still(spec):
    Wp, Hp = int(W * PAD), int(H * PAD)
    kind = spec[0]
    if kind == 'wide':
        bg = load(os.path.join(R, 'room_wide.png')).resize((Wp, Hp), Image.LANCZOS)
        cv = bg.copy()
        for name, cx, fy, hf, flip in spec[1]:
            im = char(name)
            if flip:
                im = im.transpose(Image.FLIP_LEFT_RIGHT)
            sc = hf * Hp / im.height
            contact_shadow(cv, cx * Wp, fy * Hp - 4, im.width * sc * 0.95)
            place(cv, im, cx * Wp - im.width * sc / 2, fy * Hp - im.height * sc, sc)
        tb = load(os.path.join(R, 'room_table.png')).resize((Wp, Hp), Image.LANCZOS)
        cv.alpha_composite(tb)
        return cv
    if kind == 'cu':
        _, bgn, name, cropb, wf, top, cx = spec
        cv = load(os.path.join(R, bgn + '.png')).resize((Wp, Hp), Image.LANCZOS).copy()
        im = char(name)
        if cropb < 1.0:
            im = im.crop((0, 0, im.width, int(im.height * cropb)))
        sc = wf * Wp / im.width
        place(cv, im, cx * Wp - im.width * sc / 2, top * Hp, sc)
        return cv
    if kind == 'prop':
        _, pr, col, sc = spec
        cv = Image.new('RGBA', (Wp, Hp), hexrgb(col) + (255,))
        im = load(os.path.join(R, pr + '.png'))
        s = sc * Wp / im.width
        place(cv, im, (Wp - im.width * s) / 2, Hp * 0.40 - im.height * s / 2, s)
        return cv
    if kind == 'void':
        _, pr, name = spec
        cv = Image.new('RGBA', (Wp, Hp), hexrgb('#D9DEE6') + (255,))
        b = load(os.path.join(R, pr + '.png')); s = 0.62 * Wp / b.width
        place(cv, b, Wp * 0.50, Hp * 0.60 - b.height * s * 0.75, s)
        im = char(name); sc = 0.36 * Hp / im.height
        contact_shadow(cv, Wp * 0.32, Hp * 0.60, im.width * sc)
        place(cv, im, Wp * 0.32 - im.width * sc / 2, Hp * 0.60 - im.height * sc, sc)
        return cv


# ------------------------------------------------------------------ captions
FONT = ImageFont.truetype(os.path.join(F, 'BarlowSemiCondensed-ExtraBoldItalic.ttf'), 60)
RED = (224, 0, 16, 255); RED_EDGE = (110, 0, 8, 255)
CAP_Y = int(H * 0.75)
MAXW = int(W * 0.66)


def words_with_times(seg):
    s, e, text = seg
    ws = text.upper().split()
    wt = [len(re.sub(r'[^A-Z0-9]', '', w)) + 1.5 for w in ws]
    tot = sum(wt); t = s; out = []
    for w, k in zip(ws, wt):
        d = (e - s) * k / tot; out.append((w, t, t + d)); t += d
    return out


def pages():
    """Split each segment into caption pages of max 2 lines."""
    out = []
    for i, seg in enumerate(SEG):
        ws = words_with_times(seg)
        # chunk to at most 6 words per page
        chunks = [ws[k:k + 6] for k in range(0, len(ws), 6)]
        if len(chunks) > 1 and len(chunks[-1]) <= 2:
            chunks[-2] += chunks[-1]; chunks.pop()
        nxt = SEG[i + 1][0] if i + 1 < len(SEG) else END
        for j, ch in enumerate(chunks):
            start = ch[0][1]
            cut = min([sh[0] for sh in SHOTS if sh[0] > seg[0] + 0.05] + [END])
            end = chunks[j + 1][0][1] if j + 1 < len(chunks) else min(nxt, seg[1] + 0.35, cut)
            out.append((start, end, ch))
    return out


PAGES = pages()


def layout(ch):
    sp = FONT.getlength(' ')
    lines = [[]]; cur = 0
    for w in ch:
        wl = FONT.getlength(w[0])
        if lines[-1] and cur + sp + wl > MAXW:
            lines.append([]); cur = 0
        lines[-1].append(w); cur += (sp if cur else 0) + wl
    if len(lines) > 2:  # rebalance into 2 lines
        allw = [w for l in lines for w in l]; h = (len(allw) + 1) // 2
        lines = [allw[:h], allw[h:]]
    return lines


_capcache = {}


def caption_layer(t):
    pg = None
    for p in PAGES:
        if p[0] <= t < p[1]:
            pg = p; break
    if pg is None:
        return None
    active = None
    for k, w in enumerate(pg[2]):
        if w[1] <= t:
            active = k
    key = (id(pg), active)
    if key in _capcache:
        return _capcache[key]
    lines = layout(pg[2])
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    shadow = Image.new('L', (W, H), 0)
    d = ImageDraw.Draw(lay); ds = ImageDraw.Draw(shadow)
    asc, desc = FONT.getmetrics(); lh = int(asc * 1.02)
    y0 = CAP_Y - (len(lines) * lh) // 2
    sp = FONT.getlength(' ')
    idx = 0; boxes = []; texts = []
    for li, line in enumerate(lines):
        lw = sum(FONT.getlength(w[0]) for w in line) + sp * (len(line) - 1)
        x = (W - lw) / 2; y = y0 + li * lh
        for w in line:
            wl = FONT.getlength(w[0])
            if idx == active:
                bb = FONT.getbbox(w[0])
                boxes.append((x - 9, y + bb[1] - 7, x + wl + 9, y + bb[3] + 7))
            texts.append((x, y, w[0])); x += wl + sp; idx += 1
    for x, y, s in texts:
        ds.text((x + 3, y + 4), s, font=FONT, fill=190)
    shadow = shadow.filter(ImageFilter.GaussianBlur(5))
    sh = Image.new('RGBA', (W, H), (0, 0, 0, 255)); sh.putalpha(shadow)
    lay.alpha_composite(sh)
    for b in boxes:
        d.rounded_rectangle(b, radius=7, fill=RED, outline=RED_EDGE, width=3)
    for x, y, s in texts:
        d.text((x, y), s, font=FONT, fill=(255, 255, 255, 255))
    _capcache[key] = lay
    return lay


# ------------------------------------------------------------------ render
def frames_for(i):
    st = SHOTS[i][0]; en = SHOTS[i + 1][0] if i + 1 < len(SHOTS) else END
    return int(round(st * FPS)), int(round(en * FPS))


def main():
    out = os.path.join(S, 'ep1', 'video_noaudio.mp4')
    rng = range(len(SHOTS)) if ONLY is None else [int(x) for x in ONLY.split(',')]
    if ONLY is not None:
        for i in rng:
            still = compose_still(SHOTS[i][1]).convert('RGB')
            f0, f1 = frames_for(i); t = (f0 + f1) / 2 / FPS
            fr = still.resize((W, H), Image.LANCZOS).convert('RGBA')
            cap = caption_layer(t)
            if cap: fr.alpha_composite(cap)
            fr.convert('RGB').save(os.path.join(S, 'ep1', f'preview_{i:02d}.jpg'), quality=88)
        return
    ff = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS),
                           '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '17', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
    for i in rng:
        still = compose_still(SHOTS[i][1]).convert('RGB')
        f0, f1 = frames_for(i); n = f1 - f0
        Wp, Hp = still.size
        for k in range(n):
            p = k / max(1, n - 1)
            z = 1.0 + ZOOM * p                       # linear push-in
            cw, ch = Wp / z, Hp / z
            cx, cy = Wp / 2, Hp / 2 - (Hp - ch) * 0.06 / ZOOM * 0  # centred push-in
            box = (cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2)
            fr = still.resize((W, H), Image.BILINEAR, box=box).convert('RGBA')
            cap = caption_layer((f0 + k) / FPS)
            if cap:
                fr.alpha_composite(cap)
            ff.stdin.write(fr.convert('RGB').tobytes())
        print('shot', i, 'done', flush=True)
    ff.stdin.close(); ff.wait()


if __name__ == '__main__':
    main()
