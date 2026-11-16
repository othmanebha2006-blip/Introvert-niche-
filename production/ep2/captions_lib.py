import os, re
from PIL import Image, ImageDraw, ImageFont, ImageFilter
S = os.path.dirname(os.path.abspath(__file__)); F = os.path.join(S, 'fonts')
W, H = 1080, 1920
SEG = []; SHOTS = []; END = 0
def configure(seg, shots, end):
    global SEG, SHOTS, END, PAGES
    SEG[:] = seg; SHOTS[:] = shots; END = end; PAGES[:] = pages(); _capcache.clear()
PAGES = []
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


