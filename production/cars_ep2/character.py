"""Cut the @Mecmation character out of its white-background animation and build
mouth / blink patches so it can be lip-synced to any voiceover.

usage: python3 character.py <character_video.mp4> <out_dir>
"""
import sys, os, json, subprocess, glob
import numpy as np
from PIL import Image, ImageDraw

SCALE = 0.72          # source 1080x1920 -> sprite scale used in the final frame
CROP = (0, 330, 1080, 1920)  # keep hat-top down to feet

MOUTH_BOX = (770, 888, 110)   # y0, y1, half-width around head centre (source px)
EYE_BOX = (690, 765, 125)


def skin_cx(a):
    h = a[550:1000].astype(int)
    sk = (abs(h[..., 0] - 247) < 15) & (abs(h[..., 1] - 205) < 20) & (abs(h[..., 2] - 160) < 25)
    _, x = np.where(sk)
    return int((x.min() + x.max()) // 2)


def classify(a, cx):
    m = a[770:900, cx - 110:cx + 110].astype(int)
    dark = int((m.sum(2) < 250).sum())
    e = a[680:760, cx - 110:cx + 110].astype(int)
    eye = int((e.sum(2) < 250).sum())
    best = min([('m0', 740), ('m1', 1525), ('m2', 1930), ('m3', 2935), ('m4', 4960)], key=lambda kv: abs(dark - kv[1]))
    return best[0], eye < 1500


def key_white(img, cx):
    """Alpha from white background: everything white that is NOT enclosed in the face/logo/shoes."""
    rgb = img.copy()
    W, H = rgb.size
    a = np.asarray(rgb).astype(int)
    white = (a.min(2) > 225)
    # label white components by repeated flood fill on a marker image
    mark = Image.fromarray((white * 255).astype(np.uint8))
    alpha = np.full((H, W), 255, np.uint8)
    seen = np.zeros((H, W), bool)
    ys, xs = np.where(white)
    # sample seeds on a coarse grid to keep it fast
    for y in range(0, H, 6):
        row = white[y]
        for x in np.where(row[::6])[0] * 6:
            if seen[y, x] or not white[y, x]:
                continue
            m = mark.copy()
            ImageDraw.floodfill(m, (int(x), int(y)), 128, thresh=0)
            comp = np.asarray(m) == 128
            seen |= comp
            cy_, cx_ = np.where(comp)
            area = comp.sum()
            touches_border = cy_.min() == 0 or cx_.min() == 0 or cy_.max() == H - 1 or cx_.max() == W - 1
            # keep small enclosed whites (teeth, eye glints, logo, shoe stripes) and anything in the face/logo zone
            in_face = (abs(cx_.mean() - cx) < 220) and (550 < cy_.mean() + CROP[1] < 1150)
            if touches_border or (area > 2500 and not in_face):
                alpha[comp] = 0
    # soften the edge a little
    al = Image.fromarray(alpha)
    out = img.convert('RGBA')
    out.putalpha(al)
    return out


def main(video, out):
    os.makedirs(out, exist_ok=True)
    tmp = os.path.join(out, '_src')
    os.makedirs(tmp, exist_ok=True)
    if not glob.glob(tmp + '/*.png'):
        subprocess.run(['ffmpeg', '-v', 'error', '-i', video, '-vf', 'fps=15', tmp + '/%04d.png'], check=True)
    fs = sorted(glob.glob(tmp + '/*.png'))
    info = []
    patches_done = set()
    for i, f in enumerate(fs):
        a = np.asarray(Image.open(f).convert('RGB'))
        cx = skin_cx(a)
        mouth, blink = classify(a, cx)
        info.append(dict(i=i, cx=cx, mouth=mouth, blink=bool(blink)))
        if mouth not in patches_done and not blink:
            y0, y1, hw = MOUTH_BOX
            Image.fromarray(a[y0:y1, cx - hw:cx + hw]).save(f'{out}/mouth_{mouth}.png')
            patches_done.add(mouth)
        if blink and 'blink' not in patches_done:
            y0, y1, hw = EYE_BOX
            Image.fromarray(a[y0:y1, cx - hw:cx + hw]).save(f'{out}/eyes_blink.png'); patches_done.add('blink')
        if i == 0:
            y0, y1, hw = EYE_BOX
            Image.fromarray(a[y0:y1, cx - hw:cx + hw]).save(f'{out}/eyes_open.png')
    # body poses: dedupe on the body only (below the chin), key each unique pose once
    poses, pose_of = {}, []
    for k, f in enumerate(fs):
        im = Image.open(f).convert('RGB')
        sig = np.asarray(im.crop((0, 930, 1080, 1900)).resize((54, 48))).astype(np.int16)
        hit = None
        for pid, ps in poses.items():
            if np.abs(ps['sig'] - sig).mean() < 2.0 and abs(ps['cx'] - info[k]['cx']) < 4:
                hit = pid; break
        if hit is None:
            hit = len(poses)
            poses[hit] = dict(sig=sig, cx=info[k]['cx'], src=k)
        pose_of.append(hit)
    print('unique poses', len(poses))
    for pid, ps in poses.items():
        im = Image.open(fs[ps['src']]).convert('RGB')
        a = np.asarray(im).copy()
        cx = ps['cx']
        # normalise face: closed smile + open eyes, so overlays always start clean
        m1 = np.asarray(Image.open(f'{out}/mouth_m1.png'))
        y0, y1, hw = MOUTH_BOX; a[y0:y1, cx - hw:cx + hw] = m1
        eo = np.asarray(Image.open(f'{out}/eyes_open.png'))
        y0, y1, hw = EYE_BOX; a[y0:y1, cx - hw:cx + hw] = eo
        im = Image.fromarray(a).crop(CROP)
        cut = key_white(im, cx)
        cut = cut.resize((int(cut.width * SCALE), int(cut.height * SCALE)), Image.LANCZOS)
        cut.save(f'{out}/pose_{pid:03d}.png')
    json.dump(dict(frames=info, pose_of=pose_of, poses={p: dict(cx=v['cx']) for p, v in poses.items()},
                   scale=SCALE, crop=CROP, mouth_box=MOUTH_BOX, eye_box=EYE_BOX, fps=15), open(f'{out}/character.json', 'w'))


if __name__ == '__main__':
    main(*sys.argv[1:3])
