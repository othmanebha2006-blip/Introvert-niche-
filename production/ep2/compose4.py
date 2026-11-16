"""Episode 2 v2: animated compositor.
3D set renders + the user's exact characters (clean cutouts / cut-out puppetry) with
voice-driven mouth flaps, blinks, breathing, per-scene lighting match, shadows, props, captions."""
import os, sys, json, math, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy import ndimage
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import captions_lib as CAP
from compose3 import SEG, END

S = os.path.dirname(os.path.abspath(__file__))
BG = os.path.join(S, 'bg2'); CUT = os.path.join(S, 'matte', 'cut'); PUP = os.path.join(S, 'matte', 'pup')
W, H, FPS = 1080, 1920, 30
PAD = 1.08; ZOOM = 0.05
ONLY = os.environ.get('ONLY'); PREVIEW_T = os.environ.get('PT')
HANDS = json.load(open(os.path.join(PUP, 'hands.json')))

# ---------------------------------------------------------------- who is talking (quoted dialogue only)
SPEAK = [('bf', 1.40, 2.73), ('bf', 10.94, 11.88), ('gf', 12.90, 13.35), ('gf', 22.95, 23.85), ('bf', 25.0, 25.48),
         ('bf', 25.69, 26.35), ('gf', 39.6, 40.71), ('bf', 42.08, 42.60), ('bf', 48.9, 50.19), ('gf', 51.1, 52.11),
         ('bf', 53.1, 55.21), ('bf', 65.02, 65.45), ('bf', 73.72, 74.95), ('gf', 76.2, 77.51), ('bf', 78.65, 79.95),
         ('bf', 82.6, 83.21), ('bf', 83.45, 84.27), ('bf', 89.1, 92.39), ('bf', 99.2, 101.35)]

# voice envelope for mouth flaps
_wav = subprocess.run(['ffmpeg', '-v', 'error', '-i', os.path.join(S, 'ep2', 'voice.mp3'), '-ac', '1', '-ar', '16000', '-f', 's16le', '-'],
                      capture_output=True).stdout
_a = np.frombuffer(_wav, np.int16).astype(np.float32) / 32768
_hop = 16000 // FPS
ENV = np.array([np.sqrt(np.mean(_a[i * _hop:(i + 1) * _hop] ** 2) + 1e-9) for i in range(len(_a) // _hop)])
ENV_DB = 20 * np.log10(ENV)


def talking(who, t):
    if not any(w == who and a <= t <= b for w, a, b in SPEAK):
        return False
    f = int(t * FPS)
    if f >= len(ENV_DB):
        return False
    # open on loud frames, hold for 2 frames, alternate so it reads as speech
    loud = ENV_DB[max(0, f - 1):f + 1].max() > -24
    return loud and (f // 2) % 2 == 0 or (loud and ENV_DB[f] > -18)


def blinking(who, t):
    period = 3.7 if who == 'gf' else 4.3
    off = 1.1 if who == 'gf' else 2.6
    ph = (t + off) % period
    return ph < 0.13


# ---------------------------------------------------------------- scene lighting grades
GRADE = {
    'lr':    dict(mult=(1.0, 0.975, 0.94), rim=((255, 205, 150), 0.30, 'left'), drop=(0.022, 0.012, 0.32)),
    'rack':  dict(mult=(1.0, 0.975, 0.94), rim=((255, 205, 150), 0.30, 'left'), drop=(0.03, 0.01, 0.30)),
    'car':   dict(mult=(0.60, 0.64, 0.82), rim=((255, 172, 95), 0.70, 'left'), drop=(0.02, 0.01, 0.40)),
    'store': dict(mult=(0.80, 0.76, 0.78), rim=((255, 214, 150), 0.75, 'both'), drop=None),
    'gas':   dict(mult=(0.90, 0.93, 1.0), rim=((235, 242, 255), 0.45, 'top'), drop=None),
    'truck': dict(mult=(0.42, 0.46, 0.62), rim=((255, 240, 210), 0.5, 'top'), drop=None),
}
SCENE_OF = lambda bgname: ('lr' if bgname.startswith('lr_') and bgname != 'lr_rack' else 'rack' if bgname == 'lr_rack' else
                           'car' if bgname.startswith('car') else 'store' if bgname.startswith('store') else
                           'truck' if bgname == 'gas_truck' else 'gas')


def grade_sprite(im, g):
    a = np.asarray(im).astype(np.float32); rgb = a[..., :3]; al = a[..., 3] / 255
    rgb = rgb * np.array(g['mult'])[None, None]
    col, strength, side = g['rim']
    k = max(3, int(im.width * 0.025))
    def shifted(dx, dy):
        return ndimage.shift(al, (dy, dx), order=0, mode='constant', cval=0)
    if side == 'left':
        edge = al * (1 - shifted(k, 0))
    elif side == 'right':
        edge = al * (1 - shifted(-k, 0))
    elif side == 'both':
        edge = al * np.maximum(1 - shifted(k, 0), 1 - shifted(-k, 0))
    else:
        edge = al * (1 - shifted(0, k))
    edge = ndimage.gaussian_filter(edge, k * 0.45) * al
    rgb = rgb + (np.array(col)[None, None] - rgb) * (edge[..., None] * strength)
    a[..., :3] = rgb.clip(0, 255)
    return Image.fromarray(a.astype(np.uint8), 'RGBA')


# ---------------------------------------------------------------- shot language
def CH(face, pose=None, who=None, **kw):
    """character layer. face e.g. 'bf_happy'; pose None|'phone'|'raise'|'point'|static sheet name."""
    d = dict(face=face, pose=pose, who=who or face[:2]); d.update(kw); return ('char', d)


def bg(n): return ('bg', n)
def fg(n): return ('fg', n)
def prop(n, cx, cy, w, rot=0, hand=None): return ('prop', dict(name=n, cx=cx, cy=cy, w=w, rot=rot, hand=hand))


def CU(face, pose=None, **kw):
    base = dict(cx=0.5, top=0.135, h=1.9 if face.startswith('gf') else 1.82, crop=0.56)
    base.update(kw); return CH(face, pose, **base)


LR_SIT_BF = dict(cx=0.36, top=0.305, h=0.50, crop=0.78)
LR_SIT_GF = dict(cx=0.63, top=0.325, h=0.47, crop=0.79)
LR_STAND_GF = dict(cx=0.80, top=0.235, h=0.56, crop=0.84)
CAR_GF = dict(cx=0.255, top=0.245, h=1.0, crop=0.48)
CAR_BF = dict(cx=0.745, top=0.215, h=1.02, crop=0.48)
CARCU_BF = dict(cx=0.5, top=0.17, h=1.75, crop=0.5)
CARCU_GF = dict(cx=0.5, top=0.18, h=1.85, crop=0.5)
ST_BF = dict(cx=0.34, top=0.43, h=0.42, shadow=0.85)
ST_GF = dict(cx=0.66, top=0.455, h=0.395, shadow=0.85)
GS_BF = dict(cx=0.33, top=0.39, h=0.50, shadow=0.89)
GS_GF = dict(cx=0.67, top=0.42, h=0.465, shadow=0.89)

SHOTS = [
    (0.00, [bg('lr_wide'), CH('bf_happy', **LR_SIT_BF), CH('gf_soft', **LR_SIT_GF), fg('lr_wide_fg')]),
    (3.10, [bg('lr_cu_gf'), CU('gf_touched')]),
    (5.60, [bg('lr_cu_bf'), CU('bf_happy')]),
    (9.15, [bg('lr_cu_gf'), CU('gf_skept')]),
    (10.80, [bg('lr_cu_bf'), CU('bf_smug')]),
    (12.25, [bg('lr_rack'), CH('gf_skept', cx=0.30, top=0.27, h=0.80, crop=0.9)]),
    (18.35, [bg('lr_wide'), CH('bf_ref', **LR_SIT_BF), CH('gf_ref', **LR_STAND_GF), fg('lr_wide_fg')]),
    (22.25, [bg('lr_cu_gf'), CU('gf_ref')]),
    (24.25, [bg('lr_cu_bf'), CH('bf_smug', 'raise', cx=0.56, top=0.16, h=1.35, crop=0.6)]),
    (26.80, [bg('lr_wide'), CH('bf_ref', **LR_SIT_BF), CH('gf_ref', **LR_STAND_GF), fg('lr_wide_fg')]),
    (28.10, [bg('lr_cu_bf'), CU('bf_ref', 'phone'), prop('prop_phone', 0, 0, 0.30, 8, hand=(0.03, -0.06))]),
    (31.50, [bg('lr_cu_bf'), CU('bf_ref', 'phone', top=0.05, h=1.5), prop('prop_phone', 0.5, 0.74, 1.15, 0)]),
    (33.90, [bg('lr_cu_bf'), CU('bf_worried', 'phone'), prop('prop_phone', 0, 0, 0.30, -6, hand=(0.03, -0.06))]),
    (38.85, [bg('lr_cu_gf'), CU('gf_skept')]),
    (41.15, [bg('lr_cu_bf'), CU('bf_worried')]),
    (42.95, [bg('lr_cu_gf'), CU('gf_ref')]),
    (46.90, [bg('car_wide'), CH('gf_ref', **CAR_GF), CH('bf_ref', **CAR_BF), fg('car_wide_fg')]),
    (48.20, [bg('car_cu_bf'), CH('bf_happy', **CARCU_BF)]),
    (50.40, [bg('car_cu_gf'), CH('gf_skept', **CARCU_GF)]),
    (52.40, [bg('car_cu_bf'), CH('bf_worried', **CARCU_BF)]),
    (56.70, [bg('car_cu_gf'), CH('gf_ref', **CARCU_GF)]),
    (57.90, [bg('car_wide'), CH('gf_ref', **CAR_GF), CH('bf_smug', **CAR_BF), fg('car_wide_fg')]),
    (63.30, [bg('car_cu_bf'), CH('bf_surprised', 'point', cx=0.62, top=0.16, h=1.5, crop=0.55)]),
    (65.80, [bg('store_wide'), CH('bf_surprised', **ST_BF), CH('gf_ref', **ST_GF)]),
    (68.55, [bg('store_cu'), CU('gf_ref')]),
    (72.80, [bg('store_cu'), CU('bf_worried')]),
    (75.40, [bg('store_cu'), CU('gf_skept')]),
    (77.95, [bg('store_cu'), CU('bf_happy')]),
    (80.35, [bg('store_wide'), CH('bf_smug', 'raise', cx=0.32, top=0.40, h=0.42, shadow=0.85), CH('gf_skept', **ST_GF)]),
    (84.90, [bg('gas_wide'), CH('bf_happy', 'point', cx=0.30, top=0.39, h=0.50, shadow=0.89), CH('gf_ref', **GS_GF)]),
    (87.10, [bg('gas_med'), CH('bf_happy', 'phone', cx=0.33, top=0.27, h=0.70, crop=0.8), CH('gf_ref', cx=0.70, top=0.30, h=0.66, crop=0.8),
             prop('prop_sandwich', 0, 0, 0.17, -8, hand=(0.01, -0.012))]),
    (89.90, [bg('gas_low'), CH('bf_happy', 'raise', cx=0.40, top=0.40, h=0.50, shadow=0.92), CH('gf_ref', cx=0.70, top=0.46, h=0.46, shadow=0.92)]),
    (92.80, [bg('car_wide'), CH('gf_ref', **CAR_GF), CH('bf_happy', **CAR_BF), prop('prop_sandwich', 0.265, 0.56, 0.30, 8), fg('car_wide_fg')]),
    (95.30, [bg('gas_truck'), CH('gf_3', who='-', cx=0.28, top=0.74, h=0.8, crop=0.33, static=True),
             CH('bf_3', who='-', cx=0.72, top=0.72, h=0.84, crop=0.33, static=True)]),
    (97.70, [bg('car_cu_bf'), CH('bf_happy', **CARCU_BF)]),
    (101.70, [bg('car_cu_gf'), CH('gf_ref', **CARCU_GF)]),
    (103.20, [bg('car_cu_bf'), CH('bf_happy', cx=0.5, top=0.12, h=2.1, crop=0.45)]),
]


# ---------------------------------------------------------------- sprite loading
_c = {}


def sprite_path(face, pose, state):
    suf = {'base': '', 'talk': '_talk', 'blink': '_blink'}[state]
    if pose:
        p = os.path.join(PUP, f'{face}{suf}_{pose}.png')
        return p if os.path.exists(p) else os.path.join(PUP, f'{face}_{pose}.png')
    p = os.path.join(CUT, f'{face}{suf}.png')
    return p if os.path.exists(p) else os.path.join(CUT, f'{face}.png')


def prepare_char(d, scene, Wp, Hp):
    """returns dict state -> (sprite RGBA, x, y), plus shadow and hand position"""
    states = {}
    base_im = Image.open(sprite_path(d['face'], d['pose'], 'base')).convert('RGBA')
    s = d['h'] * Hp / base_im.height
    for st in ('base', 'talk', 'blink'):
        if d.get('static') and st != 'base':
            continue
        im = Image.open(sprite_path(d['face'], d['pose'], st)).convert('RGBA')
        if d.get('crop', 1.0) < 1.0:
            im = im.crop((0, 0, im.width, int(im.height * d['crop'])))
        im = grade_sprite(im, GRADE[scene])
        im = im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.LANCZOS)
        if s > 1.3:
            im = im.filter(ImageFilter.UnsharpMask(radius=2, percent=45, threshold=2))
        states[st] = im
    x = d['cx'] * Wp - states['base'].width / 2; y = d['top'] * Hp
    hand = None
    if d['pose'] and f"{d['face']}_{d['pose']}" in HANDS:
        hx, hy = HANDS[f"{d['face']}_{d['pose']}"]
        hand = (x + hx * base_im.width * s, y + hy * base_im.height * s)
    return dict(states=states, x=x, y=y, who=d['who'], hand=hand, shadow=d.get('shadow'), static=d.get('static', False))


def drop_shadow(sprite, g):
    if not g or not g.get('drop'):
        return None
    dx, dy, op = g['drop']
    a = sprite.getchannel('A').filter(ImageFilter.GaussianBlur(sprite.width * 0.02))
    sh = Image.new('RGBA', sprite.size, (15, 12, 25, 255)); sh.putalpha(a.point(lambda v: int(v * op)))
    return sh, dx, dy


def contact_shadow(cv, cx, y, w):
    sh = Image.new('L', cv.size, 0); d = ImageDraw.Draw(sh)
    d.ellipse((cx - w / 2, y - w * 0.07, cx + w / 2, y + w * 0.07), fill=140)
    sh = sh.filter(ImageFilter.GaussianBlur(w * 0.06))
    dark = Image.new('RGBA', cv.size, (8, 8, 16, 255)); dark.putalpha(sh); cv.alpha_composite(dark)


def prepare_shot(layers):
    Wp, Hp = int(W * PAD), int(H * PAD)
    scene = SCENE_OF([L[1] for L in layers if L[0] == 'bg'][0])
    g = GRADE[scene]
    back = Image.new('RGBA', (Wp, Hp), (0, 0, 0, 255)); items = []
    for L in layers:
        if L[0] == 'bg':
            back.alpha_composite(Image.open(os.path.join(BG, L[1] + '.png')).convert('RGBA').resize((Wp, Hp), Image.LANCZOS))
        elif L[0] == 'char':
            c = prepare_char(L[1], scene, Wp, Hp)
            if c['shadow']:
                contact_shadow(back, c['x'] + c['states']['base'].width / 2, c['shadow'] * Hp, c['states']['base'].width * 0.9)
            ds = drop_shadow(c['states']['base'], g)
            if ds:
                sh, dx, dy = ds; back.alpha_composite(sh, (int(c['x'] + dx * Wp), int(c['y'] + dy * Hp)))
            items.append(('char', c))
        elif L[0] == 'prop':
            p = L[1]; im = Image.open(os.path.join(BG, p['name'] + '.png')).convert('RGBA'); im = im.crop(im.getbbox())
            if p['rot']:
                im = im.rotate(p['rot'], resample=Image.BICUBIC, expand=True)
            im = grade_sprite(im, dict(g, rim=(g['rim'][0], g['rim'][1] * 0.5, g['rim'][2])))
            sc = p['w'] * Wp / im.width
            im = im.resize((max(1, int(im.width * sc)), max(1, int(im.height * sc))), Image.LANCZOS)
            items.append(('prop', dict(im=im, p=p)))
        elif L[0] == 'fg':
            items.append(('fg', Image.open(os.path.join(BG, L[1] + '.png')).convert('RGBA').resize((Wp, Hp), Image.LANCZOS)))
    # resolve prop positions that follow a hand (use the last character with a hand)
    hands = [it[1]['hand'] for it in items if it[0] == 'char' and it[1]['hand']]
    for it in items:
        if it[0] == 'prop':
            p = it[1]['p']; im = it[1]['im']
            if p['hand'] and hands:
                hx, hy = hands[-1]; it[1]['xy'] = (hx - im.width / 2 + p['hand'][0] * Wp, hy - im.height / 2 + p['hand'][1] * Hp)
            else:
                it[1]['xy'] = (p['cx'] * Wp - im.width / 2, p['cy'] * Hp - im.height / 2)
    return back, items


def frame(back, items, t, t0):
    fr = back.copy()
    for kind, it in items:
        if kind == 'char':
            st = 'base'
            if not it['static']:
                if talking(it['who'], t) and 'talk' in it['states']:
                    st = 'talk'
                elif blinking(it['who'], t) and 'blink' in it['states']:
                    st = 'blink'
            im = it['states'][st]
            # breathing: tiny vertical scale anchored at the bottom
            k = 1.0 + 0.0045 * math.sin(2 * math.pi * (t - t0) / 3.3 + (0 if it['who'] == 'bf' else 1.7))
            if not it['static']:
                nh = int(round(im.height * k)); im2 = im.resize((im.width, nh), Image.BILINEAR)
                fr.alpha_composite(im2, (int(it['x']), int(it['y'] + im.height - nh)))
            else:
                fr.alpha_composite(im, (int(it['x']), int(it['y'])))
        elif kind == 'prop':
            x, y = it['xy']; fr.alpha_composite(it['im'], (int(x), int(y)))
        elif kind == 'fg':
            fr.alpha_composite(it)
    return fr


def ease(p):
    return p * p * (3 - 2 * p)


def main():
    CAP.configure(SEG, [(t, None) for t, _ in SHOTS], END)
    rng = range(len(SHOTS)) if ONLY is None else [int(x) for x in ONLY.split(',')]
    if PREVIEW_T is not None or ONLY is not None:
        for i in rng:
            st = SHOTS[i][0]; en = SHOTS[i + 1][0] if i + 1 < len(SHOTS) else END
            t = float(PREVIEW_T) if PREVIEW_T else (st + en) / 2
            back, items = prepare_shot(SHOTS[i][1])
            fr = frame(back, items, t, st).resize((W, H), Image.LANCZOS)
            cap = CAP.caption_layer(t)
            if cap: fr.alpha_composite(cap)
            fr.convert('RGB').save(os.path.join(S, 'ep2', f'v2_{i:02d}.jpg'), quality=86)
        return
    out = os.path.join(S, 'ep2', 'video2_noaudio.mp4')
    ff = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                           '-c:v', 'libx264', '-preset', 'medium', '-crf', '16', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
    for i in rng:
        st = SHOTS[i][0]; en = SHOTS[i + 1][0] if i + 1 < len(SHOTS) else END
        f0, f1 = int(round(st * FPS)), int(round(en * FPS)); n = f1 - f0
        back, items = prepare_shot(SHOTS[i][1]); Wp, Hp = back.size
        for k in range(n):
            t = (f0 + k) / FPS
            img = frame(back, items, t, st)
            z = 1.0 + ZOOM * ease(k / max(1, n - 1)); cw, chh = Wp / z, Hp / z
            box = (Wp / 2 - cw / 2, Hp / 2 - chh / 2, Wp / 2 + cw / 2, Hp / 2 + chh / 2)
            fr = img.resize((W, H), Image.BILINEAR, box=box)
            cap = CAP.caption_layer(t)
            if cap: fr.alpha_composite(cap)
            ff.stdin.write(fr.convert('RGB').tobytes())
        print('shot', i, flush=True)
    ff.stdin.close(); ff.wait()


if __name__ == '__main__':
    main()
