"""Talk (open mouth) and blink (closed eyes) sprites, painted on the clean cutouts in the characters' own style."""
import os, cv2, numpy as np
from PIL import Image
S = os.path.dirname(os.path.abspath(__file__)); CUT = os.path.join(S, 'matte', 'cut')
ORIG = {'gf': os.path.join(S, 'chars', '84dcbcbb-image.png'), 'bf': os.path.join(S, 'chars', '0d189ee1-image.png')}
# feature boxes in ORIGINAL image coordinates
F = {'gf': dict(mouth=(375, 415, 485, 472), eyes=[(325, 322, 392, 395), (448, 330, 518, 402)], mc=(428, 446), mw=50, eyeW=62),
     'bf': dict(mouth=(452, 312, 568, 366), eyes=[(430, 252, 474, 292), (546, 252, 590, 292)], mc=(509, 341), mw=44, eyeW=44)}
INK = (26, 27, 31)


def offset(cut, kind):
    o = cv2.imread(ORIG[kind]); c = np.asarray(cut)[..., :3][..., ::-1].copy(); a = np.asarray(cut)[..., 3]
    h, w = c.shape[:2]; y0, x0 = h // 8, w // 3
    tpl = c[y0:y0 + 120, x0:x0 + 120]
    res = cv2.matchTemplate(o, tpl, cv2.TM_SQDIFF); _, _, loc, _ = cv2.minMaxLoc(res)
    return loc[0] - x0, loc[1] - y0


def erase(img, boxes):
    dark = (img.max(2) < 90).astype(np.uint8)
    n, lab, st, cen = cv2.connectedComponentsWithStats(dark); m = np.zeros(dark.shape, np.uint8)
    for i in range(1, n):
        cx, cy = cen[i]
        if st[i][4] < 4000 and any(x0 < cx < x1 and y0 < cy < y1 for x0, y0, x1, y1 in boxes):
            m[lab == i] = 255
    m = cv2.dilate(m, np.ones((9, 9), np.uint8)); o = cv2.inpaint(img, m, 11, cv2.INPAINT_TELEA)
    bl = cv2.GaussianBlur(o, (0, 0), 4); m3 = cv2.GaussianBlur(m, (0, 0), 2)[..., None] / 255.
    return (o * (1 - m3) + bl * m3).astype(np.uint8)


def make(name):
    kind = name[:2]; f = F[kind]
    cut = Image.open(os.path.join(CUT, name + '.png')).convert('RGBA')
    ox, oy = offset(cut, kind); sh = lambda b: (b[0] - ox, b[1] - oy, b[2] - ox, b[3] - oy)
    rgb = np.asarray(cut)[..., :3][..., ::-1].copy(); a = np.asarray(cut)[..., 3]
    smiley = name in ('bf_happy', 'gf_touched')
    # talk: open mouth (filled ink shape, like the characters' own surprised mouth)
    t = erase(rgb, [sh(f['mouth'])]); cx, cy = f['mc'][0] - ox, f['mc'][1] - oy
    if smiley:
        cv2.ellipse(t, (cx, cy - 8), (f['mw'] // 2 + 6, f['mw'] // 2 - 4), 0, 0, 180, INK, -1, cv2.LINE_AA)
    else:
        cv2.ellipse(t, (cx, cy), (f['mw'] // 2 - 4, f['mw'] // 3), 0, 0, 360, INK, -1, cv2.LINE_AA)
    out = np.dstack([t[..., ::-1], a]); Image.fromarray(out, 'RGBA').save(os.path.join(CUT, name + '_talk.png'))
    # blink: closed eyes as short downward arcs (skip faces whose eyes are already closed)
    if name != 'bf_happy':
        b = erase(rgb, [sh(e) for e in f['eyes']])
        for e in f['eyes']:
            x0, y0, x1, y1 = sh(e); ex, ey = (x0 + x1) // 2, (y0 + y1) // 2 + 4
            cv2.ellipse(b, (ex, ey), (f['eyeW'] // 2, 9), 0, 10, 170, INK, 7, cv2.LINE_AA)
        Image.fromarray(np.dstack([b[..., ::-1], a]), 'RGBA').save(os.path.join(CUT, name + '_blink.png'))
    print(name, 'offset', ox, oy)


if __name__ == '__main__':
    for n in ['gf_ref', 'gf_soft', 'gf_touched', 'gf_skept', 'bf_ref', 'bf_happy', 'bf_worried', 'bf_smug', 'bf_surprised']:
        make(n)
