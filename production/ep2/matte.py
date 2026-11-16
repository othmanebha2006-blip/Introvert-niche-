"""Clean character cutouts: BiRefNet + alpha matting, erode 2px, feather 1px, white-spill decontamination."""
import os, sys
import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage
from rembg import new_session, remove

S = os.path.dirname(os.path.abspath(__file__))
SRC = [('84dcbcbb-image.png', 'gf_ref'), ('0d189ee1-image.png', 'bf_ref'),
       ('efdc538f-image.png', 'gf'), ('cade9d91-image.png', 'bf'),
       ('gf_soft_full.png', 'gf_soft'), ('bf_happy_full.png', 'bf_happy'), ('bf_surprised_full.png', 'bf_surprised'),
       ('gf_touched_full.png', 'gf_touched'), ('gf_skept_full.png', 'gf_skept'), ('bf_worried_full.png', 'bf_worried'), ('bf_smug_full.png', 'bf_smug')]
OUT = os.path.join(S, 'matte', 'cut'); os.makedirs(OUT, exist_ok=True)
sess = new_session('birefnet-general')


def clean(rgb, alpha):
    a = alpha.astype(np.float32) / 255.0
    # erode 2 px (on the solid core), then feather 1 px
    core = a > 0.5
    core = ndimage.binary_erosion(core, iterations=2)
    a2 = np.minimum(a, ndimage.gaussian_filter(core.astype(np.float32), 1.0) * 1.0)
    a2 = ndimage.gaussian_filter(a2, 0.6)
    a2[~ndimage.binary_dilation(core, iterations=2)] = 0
    # decontaminate: unmix the white background from edge pixels, F = (C - (1-a)*255) / a
    c = rgb.astype(np.float32)
    aa = np.clip(a, 0.05, 1)[..., None]
    F = (c - (1 - aa) * 255.0) / aa
    F = np.clip(F, 0, 255)
    # for weak-alpha pixels, pull colour from the nearest solid interior pixel
    solid = a > 0.95
    idx = ndimage.distance_transform_edt(~solid, return_distances=False, return_indices=True)
    inner = c[idx[0], idx[1]]
    w = np.clip((a - 0.3) / 0.65, 0, 1)[..., None]
    F = F * w + inner * (1 - w)
    edge = (a2 > 0) & (a2 < 0.999)
    out = c.copy(); out[edge] = F[edge]
    return out.astype(np.uint8), (a2 * 255).astype(np.uint8)


for src, name in [SRC[int(i)] for i in sys.argv[1:]]:
    im = Image.open(os.path.join(S, 'chars', src)).convert('RGB')
    rgba = remove(im, session=sess, alpha_matting=True, alpha_matting_foreground_threshold=240,
                  alpha_matting_background_threshold=15, alpha_matting_erode_size=8, post_process_mask=False)
    alpha = np.asarray(rgba)[..., 3]
    rgb, a = clean(np.asarray(im), alpha)
    lab, n = ndimage.label(ndimage.binary_dilation(a > 20, iterations=6))
    sls = [sl for sl in ndimage.find_objects(lab) if (sl[0].stop - sl[0].start) * (sl[1].stop - sl[1].start) > 20000]
    sls = sorted(sls, key=lambda s: (round(s[0].start / 150), s[1].start))
    for k, sl in enumerate(sls):
        m = (lab[sl] == (lab[sl][lab[sl] > 0][0] if False else lab[sl])).astype(bool)
        part = np.dstack([rgb[sl], np.where(lab[sl] > 0, a[sl], 0)])
        fn = f'{name}_{k}.png' if len(sls) > 1 or name in ('gf', 'bf') else f'{name}.png'
        Image.fromarray(part, 'RGBA').save(os.path.join(OUT, fn))
    print(src, '->', len(sls), 'cutouts', flush=True)
