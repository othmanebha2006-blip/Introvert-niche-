"""Episode 2 compositor: 3D set renders + the user's exact character cutouts + props + foreground layers + captions."""
import os, sys, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import captions_lib as CAP

S = os.path.dirname(os.path.abspath(__file__))
BG = os.path.join(S, 'bg2'); CUT = os.path.join(S, 'matte', 'cut')
W, H, FPS = 1080, 1920, 30
PAD = 1.08; ZOOM = 0.05
END = 106.19
ONLY = os.environ.get('ONLY')

SEG = [
    (0.12, 1.26, "Your boyfriend says,"), (1.40, 2.73, "\"I'll plan the date this time.\""),
    (3.26, 5.19, "You almost fucking cry."), (5.76, 8.62, "Three years, and finally he's stepping up."),
    (9.31, 10.54, "You ask where we're going."), (10.94, 11.88, "\"It's a surprise.\""),
    (12.38, 13.35, "You say okay,"), (13.60, 17.61, "and spend two days choosing an outfit for a place that doesn't exist."),
    (18.49, 19.50, "Saturday comes."), (19.74, 20.87, "You're ready at seven."), (21.18, 22.09, "He's on the couch."),
    (22.40, 23.85, "You say, \"Shouldn't we go?\""), (24.38, 25.48, "He says, \"Yeah,"), (25.69, 26.35, "give me a minute.\""),
    (26.94, 27.59, "You wait."), (28.22, 31.24, "He opens his phone and types \"restaurants near me.\""),
    (31.64, 32.33, "Near him."), (32.67, 33.64, "Near the couch."), (34.04, 35.37, "He's planning it live."),
    (35.58, 38.47, "Like a man defusing a bomb he built himself."), (39.00, 40.71, "You say, \"Did you book anything?\""),
    (41.28, 41.87, "He says,"), (42.08, 42.60, "\"Kind of.\""), (43.16, 45.16, "Kind of is not a reservation."),
    (45.47, 46.31, "It's a prayer."), (47.07, 48.01, "You get in the car."), (48.35, 50.19, "He says, \"So there's this place.\""),
    (50.56, 52.11, "You say, \"What's it called?\""), (52.57, 53.99, "He says, \"I forgot,"), (54.14, 55.21, "but it's by the thing.\""),
    (55.74, 56.49, "The thing."), (56.83, 57.48, "Excellent."),
    (58.04, 62.89, "You drive for 20 minutes while he squints at buildings like a pirate looking for land."),
    (63.45, 64.65, "Finally, he points."), (65.02, 65.45, "\"There.\""), (65.92, 66.83, "It's closed."), (67.36, 68.07, "Permanently."),
    (68.64, 70.51, "There's a different restaurant in the window."), (70.75, 72.36, "A fucking mattress store."),
    (72.96, 73.58, "He says,"), (73.72, 74.95, "\"It was here last year.\""), (75.55, 77.51, "You say, \"We've never been here.\""),
    (78.11, 79.95, "He says, \"My cousin told me.\""), (80.51, 81.74, "You suggest a place."), (82.11, 83.21, "He says, \"No."),
    (83.45, 84.27, "I have a plan.\""), (85.05, 86.79, "The plan is a gas station."),
    (87.26, 89.80, "He buys you a sandwich and says, \"See?"), (89.98, 90.95, "It's romantic."), (91.10, 92.39, "We're under the stars.\""),
    (92.96, 94.12, "You eat it in the car."), (94.43, 95.15, "In the dark."), (95.39, 97.23, "Watching a guy fill up a truck."),
    (97.82, 101.35, "Then he looks at you and says, \"Best date ever, right?\""), (101.85, 102.70, "You look at him."),
    (103.29, 105.77, "Somehow, he's actually serious."),
]


# ------------------------------------------------------------------ layer helpers
def bg(name): return ('bg', name)
def fg(name): return ('fg', name)
def ch(name, cx, top, h, crop=1.0, flip=False, shadow=None): return ('char', name, cx, top, h, crop, flip, shadow)
def pr(name, cx, cy, w, rot=0): return ('prop', name, cx, cy, w, rot)
def flat(color): return ('flat', color)


# CU = bust from a hi-res full-body reference (top 56 % = head to waist)
def CU_GF(name='gf_ref', cx=0.5): return ch(name, cx, 0.14, 1.95, 0.56)
def CU_BF(name='bf_ref', cx=0.5): return ch(name, cx, 0.13, 1.85, 0.56)

# living-room wide: seated behind the coffee table (table fg hides the crop edge)
LR_BF = lambda n='bf_ref': ch(n, 0.36, 0.305, 0.50, 0.78)
LR_GF = lambda n='gf_ref': ch(n, 0.63, 0.325, 0.47, 0.79)
LR_GF_STAND = lambda n='gf_ref': ch(n, 0.80, 0.235, 0.56, 0.84)
# car wide: busts behind the dashboard
CAR_GF = lambda n='gf_ref': ch(n, 0.255, 0.245, 1.0, 0.48)
CAR_BF = lambda n='bf_ref': ch(n, 0.745, 0.215, 1.02, 0.48)
# car close-ups (dash cam)
CARCU_BF = lambda n='bf_ref': ch(n, 0.5, 0.17, 1.75, 0.5)
CARCU_GF = lambda n='gf_ref': ch(n, 0.5, 0.18, 1.85, 0.5)
# store / gas wides: full figures on the pavement
ST_BF = lambda n='bf_ref': ch(n, 0.34, 0.43, 0.42, shadow=0.85)
ST_GF = lambda n='gf_ref': ch(n, 0.66, 0.455, 0.395, shadow=0.85)
GS_BF = lambda n='bf_ref': ch(n, 0.33, 0.39, 0.50, shadow=0.89)
GS_GF = lambda n='gf_ref': ch(n, 0.67, 0.42, 0.465, shadow=0.89)

SHOTS = [
    (0.00, [bg('lr_wide'), LR_BF('bf_happy'), LR_GF('gf_soft'), fg('lr_wide_fg')]),
    (3.10, [bg('lr_cu_gf'), CU_GF('gf_touched')]),
    (5.60, [bg('lr_cu_bf'), CU_BF('bf_happy')]),
    (9.15, [bg('lr_cu_gf'), CU_GF('gf_skept')]),
    (10.80, [bg('lr_cu_bf'), CU_BF('bf_smug')]),
    (12.25, [bg('lr_rack'), ch('gf_1', 0.30, 0.30, 0.78, 0.86)]),
    (18.35, [bg('lr_wide'), LR_BF('bf_ref'), LR_GF_STAND('gf_ref'), fg('lr_wide_fg')]),
    (22.25, [bg('lr_cu_gf'), ch('gf_7', 0.5, 0.16, 1.15, 1.0)]),
    (24.25, [bg('lr_cu_bf'), ch('bf_13', 0.5, 0.2, 1.15, 0.75)]),
    (26.80, [bg('lr_wide'), LR_BF('bf_ref'), LR_GF_STAND('gf_ref'), fg('lr_wide_fg')]),
    (28.10, [bg('lr_cu_bf'), CU_BF('bf_ref'), pr('prop_phone', 0.50, 0.86, 0.95, 4)]),
    (31.50, [bg('lr_cu_bf'), ch('bf_ref', 0.5, 0.06, 1.45, 0.5), pr('prop_phone', 0.5, 0.78, 1.25, 0)]),
    (33.90, [bg('lr_cu_bf'), CU_BF('bf_worried'), pr('prop_phone', 0.50, 0.86, 0.95, -4)]),
    (38.85, [bg('lr_cu_gf'), CU_GF('gf_skept')]),
    (41.15, [bg('lr_cu_bf'), CU_BF('bf_worried')]),
    (42.95, [bg('lr_cu_gf'), CU_GF('gf_ref')]),
    (46.90, [bg('car_wide'), CAR_GF('gf_ref'), CAR_BF('bf_ref'), fg('car_wide_fg')]),
    (48.20, [bg('car_cu_bf'), CARCU_BF('bf_happy')]),
    (50.40, [bg('car_cu_gf'), CARCU_GF('gf_skept')]),
    (52.40, [bg('car_cu_bf'), CARCU_BF('bf_worried')]),
    (56.70, [bg('car_cu_gf'), ch('gf_5', 0.5, 0.2, 1.05, 1.0)]),
    (57.90, [bg('car_wide'), CAR_GF('gf_ref'), ch('bf_11', 0.745, 0.215, 1.05, 0.48), fg('car_wide_fg')]),
    (63.30, [bg('car_cu_bf'), ch('bf_13', 0.5, 0.2, 1.15, 0.75)]),
    (65.80, [bg('store_wide'), ST_BF('bf_surprised'), ST_GF('gf_ref')]),
    (68.55, [bg('store_cu'), CU_GF('gf_ref')]),
    (72.80, [bg('store_cu'), ch('bf_11', 0.5, 0.2, 1.15, 0.75)]),
    (75.40, [bg('store_cu'), CU_GF('gf_skept')]),
    (77.95, [bg('store_cu'), CU_BF('bf_worried')]),
    (80.35, [bg('store_wide'), ST_BF('bf_smug'), ST_GF('gf_1')]),
    (84.90, [bg('gas_wide'), GS_BF('bf_happy'), GS_GF('gf_ref')]),
    (87.10, [bg('gas_med'), ch('bf_happy', 0.33, 0.27, 0.70, 0.8), ch('gf_ref', 0.70, 0.30, 0.66, 0.8), pr('prop_sandwich', 0.215, 0.70, 0.30, -10)]),
    (89.90, [bg('gas_low'), ch('bf_13', 0.40, 0.42, 0.50, shadow=0.92), ch('gf_0', 0.68, 0.46, 0.46, shadow=0.92)]),
    (92.80, [bg('car_wide'), CAR_GF('gf_ref'), CAR_BF('bf_happy'), pr('prop_sandwich', 0.265, 0.56, 0.30, 8), fg('car_wide_fg')]),
    (95.30, [bg('gas_truck'), ch('gf_3', 0.28, 0.74, 0.8, 0.33), ch('bf_3', 0.72, 0.72, 0.84, 0.33)]),
    (97.70, [bg('car_cu_bf'), CARCU_BF('bf_happy')]),
    (101.70, [bg('car_cu_gf'), CARCU_GF('gf_ref')]),
    (103.20, [bg('car_cu_bf'), ch('bf_happy', 0.5, 0.12, 2.1, 0.45)]),
]

_c = {}


def load(path):
    if path not in _c:
        _c[path] = Image.open(path).convert('RGBA')
    return _c[path]


def contact_shadow(cv, cx, y, w):
    sh = Image.new('L', cv.size, 0); d = ImageDraw.Draw(sh)
    d.ellipse((cx - w / 2, y - w * 0.07, cx + w / 2, y + w * 0.07), fill=130)
    sh = sh.filter(ImageFilter.GaussianBlur(w * 0.06))
    dark = Image.new('RGBA', cv.size, (10, 10, 20, 255)); dark.putalpha(sh); cv.alpha_composite(dark)


def place(cv, im, x, y, s):
    im = im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.LANCZOS)
    if s > 1.3:
        im = im.filter(ImageFilter.UnsharpMask(radius=2, percent=50, threshold=2))
    cv.alpha_composite(im, (int(round(x)), int(round(y))))


def still(layers):
    Wp, Hp = int(W * PAD), int(H * PAD)
    cv = Image.new('RGBA', (Wp, Hp), (0, 0, 0, 255))
    for L in layers:
        k = L[0]
        if k in ('bg', 'fg'):
            cv.alpha_composite(load(os.path.join(BG, L[1] + '.png')).resize((Wp, Hp), Image.LANCZOS))
        elif k == 'char':
            _, name, cx, top, h, crop, flip, shadow = L
            im = load(os.path.join(CUT, name + '.png'))
            if flip:
                im = im.transpose(Image.FLIP_LEFT_RIGHT)
            s = h * Hp / im.height
            if crop < 1.0:
                im = im.crop((0, 0, im.width, int(im.height * crop)))
            if shadow:
                contact_shadow(cv, cx * Wp, shadow * Hp, im.width * s * 0.9)
            place(cv, im, cx * Wp - im.width * s / 2, top * Hp, s)
        elif k == 'prop':
            _, name, cx, cy, w, rot = L
            im = load(os.path.join(BG, name + '.png'))
            bb = im.getbbox(); im = im.crop(bb)
            if rot:
                im = im.rotate(rot, resample=Image.BICUBIC, expand=True)
            s = w * Wp / max(im.width, 1) * (im.width / max(im.width, im.height))
            place(cv, im, cx * Wp - im.width * s / 2, cy * Hp - im.height * s / 2, s)
    return cv.convert('RGB')


def main():
    CAP.configure(SEG, [(t, None) for t, _ in SHOTS], END)
    rng = range(len(SHOTS)) if ONLY is None else [int(x) for x in ONLY.split(',')]
    if ONLY is not None:
        for i in rng:
            st = SHOTS[i][0]; en = SHOTS[i + 1][0] if i + 1 < len(SHOTS) else END
            fr = still(SHOTS[i][1]).resize((W, H), Image.LANCZOS).convert('RGBA')
            cap = CAP.caption_layer((st + en) / 2)
            if cap: fr.alpha_composite(cap)
            fr.convert('RGB').save(os.path.join(S, 'ep2', f'pv_{i:02d}.jpg'), quality=85)
        return
    out = os.path.join(S, 'ep2', 'video_noaudio.mp4')
    ff = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                           '-c:v', 'libx264', '-preset', 'medium', '-crf', '17', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
    for i in rng:
        st = SHOTS[i][0]; en = SHOTS[i + 1][0] if i + 1 < len(SHOTS) else END
        f0, f1 = int(round(st * FPS)), int(round(en * FPS)); n = f1 - f0
        img = still(SHOTS[i][1]); Wp, Hp = img.size
        for k in range(n):
            z = 1.0 + ZOOM * k / max(1, n - 1); cw, chh = Wp / z, Hp / z
            box = (Wp / 2 - cw / 2, Hp / 2 - chh / 2, Wp / 2 + cw / 2, Hp / 2 + chh / 2)
            fr = img.resize((W, H), Image.BILINEAR, box=box).convert('RGBA')
            cap = CAP.caption_layer((f0 + k) / FPS)
            if cap: fr.alpha_composite(cap)
            ff.stdin.write(fr.convert('RGB').tobytes())
        print('shot', i, flush=True)
    ff.stdin.close(); ff.wait()


if __name__ == '__main__':
    main()
